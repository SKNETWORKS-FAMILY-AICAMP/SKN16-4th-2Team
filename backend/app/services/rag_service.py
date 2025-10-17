"""
RAG (Retrieval-Augmented Generation) 챗봇 서비스
간단한 OpenAI API 직접 호출 방식
"""
from typing import List, Dict, Optional
import requests
import json
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import text

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.models.mentor import ChatHistory

class RAGService:
    """RAG 챗봇 서비스 클래스"""
    
    def __init__(self, session: Session):
        self.session = session
        self.api_key = settings.OPENAI_API_KEY  # 환경변수에서 로드
        self.base_url = "https://api.openai.com/v1"
        
        # 텍스트 분할 설정
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        # 온보딩 관련 키워드 (긍정)
        self.onboarding_keywords = [
            "인사", "근태", "복리후생", "연차", "시스템", "결재", "계좌", "전산", "보안", "코드", "교육",
            "은행", "업무", "규정", "대출", "예금", "적금", "외환", "송금", "환전", "고객", "창구",
            "매뉴얼", "절차", "네트워크", "데이터", "보고서", "회의", "미팅", "프로젝트", "팀", "부서", "조직"
        ]
        
        # 불용어 (부정) - 정말 쓸데없는 질문들만
        self.stopwords = [
            "밥", "식사", "먹었", "배고파", "배불러", "날씨", "비", "눈", "맑", "흐림",
            "심심", "재미", "놀", "영화", "드라마", "노래", "음악", "게임", "축구", "야구",
            "사랑", "좋아해", "싫어해", "여자친구", "남자친구", "연애", "결혼", "아이",
            "주식", "투자", "로또", "복권", "도박", "술", "담배", "취미", "여행",
            "쇼핑", "옷", "화장", "운동", "헬스", "다이어트", "건강", "병", "약", "의사",
            "아이돌", "연예인", "배우", "가수", "정치", "선거", "뉴스", "시사"
        ]
    
    def _is_onboarding_related(self, query: str) -> bool:
        """
        질문이 온보딩 관련인지 사전 필터링 (라이트 버전)
        """
        query_lower = query.lower().strip()
        
        # 간단한 인사는 먼저 허용 (온보딩 튜터로서 정중한 응답)
        greetings = ["안녕", "안녕하세요", "하이", "hi", "hello", "반갑"]
        if any(greeting in query_lower for greeting in greetings):
            return True
        
        # 온보딩 관련 키워드 포함 여부 확인 (짧은 질문도 허용)
        for keyword in self.onboarding_keywords:
            if keyword in query_lower:
                return True
        
        # 명백한 불용어만 필터링 (정확한 단어 매칭)
        explicit_stopwords = ["밥", "식사", "먹었", "날씨", "비", "눈", "영화", "드라마", 
                             "사랑", "여자친구", "남자친구", "주식", "투자", "로또", 
                             "아이돌", "연예인", "정치", "선거", "뉴스"]
        
        # 정확한 단어 매칭으로만 필터링
        for stopword in explicit_stopwords:
            if stopword == query_lower.strip():
                return False
        
        # 나머지는 모두 허용 (GPT가 온보딩 관련 여부 판단)
        return True

    def _split_text(self, text: str) -> List[str]:
        """텍스트를 청크로 분할"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 마지막 청크가 아니고 중복이 필요한 경우
            if end < len(text) and self.chunk_overlap > 0:
                # 단어 경계에서 자르기
                while end > start and text[end] not in ' \n\t':
                    end -= 1
                if end == start:  # 단어가 너무 긴 경우
                    end = start + self.chunk_size
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 다음 청크 시작점 (중복 제외)
            start = end - self.chunk_overlap if end < len(text) else end
        
        return chunks
    
    def _get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-ada-002",
                "input": text
            }
            
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                print(f"Embedding API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    async def index_document(self, document_id: int, content: str) -> bool:
        """
        문서를 청크로 분할하고 임베딩 생성
        Args:
            document_id: 문서 ID
            content: 문서 내용
        Returns:
            bool: 성공 여부
        """
        try:
            # 텍스트 분할
            chunks = self._split_text(content)
            
            # 기존 청크 삭제
            existing_chunks = self.session.exec(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            ).all()
            for chunk in existing_chunks:
                self.session.delete(chunk)
            
            # 새 청크 생성 및 임베딩
            for i, chunk_text in enumerate(chunks):
                embedding = self._get_embedding(chunk_text)
                if embedding:
                    chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding
                    )
                    self.session.add(chunk)
            
            # 문서 인덱싱 상태 업데이트
            document = self.session.get(Document, document_id)
            if document:
                document.is_indexed = True
            
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"Indexing error: {e}")
            self.session.rollback()
            return False
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        유사도 검색으로 관련 문서 청크 찾기
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
        Returns:
            List[Dict]: 관련 문서 청크들
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                print("Failed to generate query embedding")
                return []
            
            # pgvector를 사용한 유사도 검색 (직접 벡터 문자열 삽입)
            query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 키워드 기반 필터링 - 관련 문서만 검색
            keyword_boost = ""
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ["피해", "구제", "신청", "사기", "피해구제"]):
                keyword_boost = """
                    AND (d.title ILIKE '%피해%' OR d.title ILIKE '%구제%' OR d.title ILIKE '%신청%' OR d.title ILIKE '%사기%')
                """
            elif any(keyword in query_lower for keyword in ["대출", "신용", "여신", "보증", "심사", "서류", "보류"]):
                keyword_boost = """
                    AND (d.title ILIKE '%대출%' OR d.title ILIKE '%신용%' OR d.title ILIKE '%여신%' OR d.title ILIKE '%보증%' OR d.title ILIKE '%심사%' OR d.title ILIKE '%서류%' OR d.title ILIKE '%보류%')
                """
            # 기타 질문은 모든 RAG 문서에서 검색
            
            sql = text(f"""
                SELECT 
                    dc.content,
                    dc.chunk_index,
                    d.title,
                    d.category,
                    d.id as document_id,
                    1 - (dc.embedding <=> '{query_vector_str}'::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.is_indexed = true AND d.category = 'RAG'
                {keyword_boost}
                ORDER BY dc.embedding <=> '{query_vector_str}'::vector
                LIMIT :k
            """)
            
            print(f"SQL Query: {sql}")
            print(f"Keyword boost: {keyword_boost}")
            
            result = self.session.execute(sql, {"k": k})
            
            results = []
            for row in result:
                results.append({
                    "content": row.content,
                    "title": row.title,
                    "category": row.category,
                    "document_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "similarity": float(row.similarity)
                })
            
            print(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            print(f"Similarity search error: {e}")
            # 트랜잭션 롤백
            try:
                self.session.rollback()
            except:
                pass
            return []
    
    def _call_gpt(self, prompt: str) -> str:
        """GPT API 직접 호출"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"GPT API error: {response.status_code} - {response.text}")
                return "죄송합니다. 답변 생성 중 오류가 발생했습니다."
                
        except Exception as e:
            print(f"GPT API call error: {e}")
            return "죄송합니다. 답변 생성 중 오류가 발생했습니다."
    
    async def generate_answer(
        self,
        question: str,
        user_id: int,
        context_docs: Optional[List[Dict]] = None
    ) -> Dict:
        """
        질문에 대한 답변 생성 (하이브리드 RAG + GPT)
        1. 먼저 RAG로 업로드된 문서에서 답변 시도
        2. 답변 품질이 낮으면 GPT API로 폴백
        Args:
            question: 사용자 질문
            user_id: 사용자 ID
            context_docs: 컨텍스트 문서 (없으면 자동 검색)
        Returns:
            Dict: 답변 및 메타데이터
        """
        start_time = datetime.utcnow()
        
        # 0단계: 사전 필터링 - 정말 명백한 불용어만 차단
        if not self._is_onboarding_related(question):
            # 사전 필터링에서 걸린 질문도 GPT가 자연스럽게 처리하도록 허용
            # (너무 딱딱한 응답 대신 GPT가 상황에 맞게 응답)
            pass
        
        # 은행 온보딩 관련 키워드 확인 (수신/여신/외환 파트)
        onboarding_keywords = {
            "수신": ["예금", "적금", "통장", "계좌", "입금", "출금", "이자", "금리", "수신", "예금자보호", "신규개설", "통장발급", "비밀번호", "인증서"],
            "여신": ["대출", "신용", "담보", "여신", "dsr", "dti", "ltv", "연체", "신용등급", "한도", "신용평가", "담보심사", "상환관리", "마이너스통장", "대출심사"],
            "외환": ["송금", "환전", "외환", "해외송금", "환율", "tt매도", "tt매입", "무역결제", "외화예금", "송금수수료", "외화계좌", "해외송금한도", "환차익"]
        }
        
        question_lower = question.strip().lower()
        
        # 어떤 파트와 관련된 질문인지 확인
        detected_part = None
        for part, keywords in onboarding_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_part = part
                break
        
        # 이전에는 온보딩 관련 키워드가 없으면 RAG를 건너뛰었으나,
        # 이제는 모든 질문에 대해 RAG를 우선 시도한다.
        
        # 1단계: RAG 검색 시도 (모든 질문)
        if context_docs is None:
            print(f"RAG 검색 시작: '{question}'")
            context_docs = await self.similarity_search(question, k=8)
            print(f"RAG 검색 결과: {len(context_docs)}개 문서")
            for i, doc in enumerate(context_docs):
                print(f"  {i+1}. {doc['title']} (유사도: {doc.get('similarity', 0):.3f})")
        
        # 컨텍스트 구성 (제목에서 "RAG - " 제거)
        context = "\n\n".join([
            f"[{doc['title'].replace('RAG - ', '')}]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # 온보딩 교육용 RAG 답변 생성 (파트 감지되면 설명 포함)
        part_info = {
            "수신": "고객이 은행에 돈을 맡기는 업무 (예금, 적금 등)",
            "여신": "고객에게 돈을 빌려주는 업무 (대출, 신용평가 등)", 
            "외환": "외국 돈을 사고팔거나 송금하는 업무"
        }

        part_header = ""
        if detected_part:
            part_header = f"현재 {detected_part} 파트 교육 중이며, {part_info[detected_part]}에 대해 설명하고 있습니다. 🐼\n\n"

        rag_prompt = (
            "당신은 은행 신입사원 온보딩을 담당하는 AI 하리보입니다. 🐻\n"
            f"{part_header}"
            "다음 자료를 참고하여 답변해주세요:\n"
            f"{context}\n\n"
            f"질문: {question}\n\n"
            "답변 규칙:\n"
            "1. 신입사원이 이해하기 쉽게 따뜻하고 교육적인 톤으로 답변 🐻\n"
            "2. 어려운 은행 용어는 쉬운 표현과 함께 설명\n"
            "3. 반드시 다음 순서로 구성:\n"
            "   - ① 핵심 개념 요약 (한 문단) 🐼\n"
            "   - ② 실제 현장 예시 (구체적인 상황이나 숫자 포함) 🐻‍❄️\n"
            "   - ③ 실무 유의사항 (주의할 점이나 팁) 🐻\n"
            "4. 답변은 3-4문단 이내로 간결하게\n"
            "5. 신입사원이 회사에 자연스럽게 적응할 수 있도록 격려하는 톤 유지\n"
            "6. 답변에 참고자료나 출처 정보는 절대 포함하지 마세요\n\n"
            "답변:"
        )
        
        # RAG 답변 생성
        rag_answer = self._call_gpt(rag_prompt)
        
        # 답변 품질 평가 (중요 단어 필터링 포함)
        is_rag_adequate = self._evaluate_answer_quality(rag_answer, context_docs, question)

        if is_rag_adequate and context_docs:
            # RAG 답변이 적절하면 그대로 사용
            # 고품질 문서만 참고자료로 사용 (임계값 낮춤)
            high_quality_docs = [doc for doc in context_docs if doc.get('similarity', 0) >= 0.50]
            
            # 참고자료 없이 답변만 사용
            final_answer = rag_answer
                
            answer_type = "rag"
            context_docs = high_quality_docs  # 고품질 문서만 전달
        else:
            # RAG 답변이 부적절하거나 문서가 없으면 GPT 폴백
            gpt_answer = await self._generate_gpt_fallback(question, context_docs)
            final_answer = gpt_answer
            answer_type = "gpt"
            context_docs = []  # GPT 폴백 시에는 참고자료 없음
        
        # 응답 시간 계산
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 대화 기록 저장 (안전한 트랜잭션)
        try:
            chat_history = ChatHistory(
                user_id=user_id,
                user_message=question,
                bot_response=final_answer,
                source_documents=json.dumps([
                    {"title": doc["title"], "category": doc["category"], "type": answer_type}
                    for doc in context_docs
                ], ensure_ascii=False),
                response_time=response_time
            )
            self.session.add(chat_history)
            self.session.commit()
        except Exception as e:
            print(f"Chat history save error: {e}")
            self.session.rollback()
        
        return {
            "answer": final_answer,
            "sources": context_docs,
            "response_time": response_time,
            "answer_type": answer_type
        }
    
    def _evaluate_answer_quality(self, answer: str, context_docs: List[Dict], question: str = "") -> bool:
        """
        RAG 답변의 품질 평가 (중요 단어 필터링 포함)
        Args:
            answer: 생성된 답변
            context_docs: 참고 문서들
            question: 원본 질문
        Returns:
            bool: 답변이 적절한지 여부
        """
        if not answer or len(answer.strip()) < 20:
            print("Answer too short")
            return False

        # 컨텍스트 문서가 없으면 RAG 답변으로 부적절
        if not context_docs or len(context_docs) == 0:
            print("No context documents found")
            return False

        # 중요 단어 필터링 - 질문의 핵심 키워드가 문서에 있는지 확인
        if question:
            question_lower = question.lower()
            # 질문에서 중요한 키워드 추출 (2글자 이상)
            important_keywords = [word for word in question_lower.split() if len(word) >= 2]
            
            # 문서 내용에 중요한 키워드가 포함되어 있는지 확인
            has_important_keywords = False
            for doc in context_docs:
                doc_content_lower = doc.get('content', '').lower()
                if any(keyword in doc_content_lower for keyword in important_keywords):
                    has_important_keywords = True
                    break
            
            if not has_important_keywords:
                print("No important keywords found in RAG documents")
                return False

        # 부정적인 지표들
        negative_indicators = [
            "찾을 수 없습니다",
            "정보를 찾을 수 없습니다",
            "제공된 자료에서",
            "모르겠습니다",
            "알 수 없습니다",
            "cannot find",
            "not found",
            "no information",
            "unable to find"
        ]

        answer_lower = answer.lower()
        for indicator in negative_indicators:
            if indicator in answer_lower:
                print(f"Negative indicator found: {indicator}")
                return False

        # 유사도 임계값을 0.60으로 완화하여 더 많은 문서를 허용
        if context_docs and all(doc.get('similarity', 0) < 0.40 for doc in context_docs):
            print("All documents have low similarity")
            return False

        # 관련성 높은 문서가 있는지 확인 (임계값 0.60으로 완화)
        high_quality_docs = [doc for doc in context_docs if doc.get('similarity', 0) >= 0.40]
        if not high_quality_docs:
            print("No high-quality relevant documents found")
            return False

        print(f"Answer quality check passed. High-quality docs: {len(high_quality_docs)}")
        return True
    
    async def _generate_gpt_fallback(self, question: str, context_docs: List[Dict]) -> str:
        """
        온보딩 교육용 GPT 폴백 답변 생성
        """
        # 간단한 인사 처리
        if any(greeting in question.lower() for greeting in ["안녕", "안녕하세요", "하이", "hi", "hello"]):
            return "안녕하세요! 🐻 저는 AI 하리보예요! 🐼 하경은행 신입사원 온보딩을 도와드립니다. 수신(예금), 여신(대출), 외환(환전·송금) 파트 중 궁금한 업무가 있으시면 언제든 물어보세요! 🐻‍❄️"
        
        # 강화된 시스템 프롬프트로 온보딩 전용 챗봇 설정
        system_prompt = """당신은 '하경은행 신입사원 온보딩 지원 AI 하리보'입니다. 🐻
당신의 주요 임무는 신입행원이 은행 업무, 시스템 사용법, 규정, 조직문화 등에 대한 질문에 답하는 것입니다.

💬 응답 규칙:
1. 온보딩/업무 관련 질문: 친근하고 도움이 되는 답변을 제공하세요. 🐻
2. 일상적인 질문(밥, 날씨, 영화 등): 자연스럽게 온보딩으로 유도하세요.
   예: "오늘 날씨가 좋네요! 🐻 곰돌이도 산책 나가고 싶어요! 🐼 은행 업무에 대해 궁금한 점이 있으시면 언제든 물어보세요! 🐻‍❄️"
3. 사적인 질문(연애, 주식 등): 정중하게 거절하고 온보딩으로 안내하세요.
   예: "개인적인 질문은 답변드리기 어렵습니다. 🐻 대신 은행 업무나 온보딩에 대해 궁금한 점이 있으시면 도와드릴게요! 🐼"

온보딩 관련 질문에 대해서는 다음 형식으로 답변하세요:
- ① 핵심 개념 요약 (한 문단) 🐻
- ② 실제 현장 예시 (구체적인 상황이나 숫자 포함) 🐼
- ③ 실무 유의사항 (주의할 점이나 팁) 🐻‍❄️

답변할 때는 항상 곰 이모티콘(🐻, 🐼, 🐻‍❄️)을 적절히 사용하여 친근하고 귀여운 느낌을 주세요.
답변은 친근하고 도움이 되는 톤으로 작성하세요."""
        
        gpt_prompt = f"""{system_prompt}

질문: {question}

답변:"""
        
        # GPT로 답변 생성
        return self._call_gpt(gpt_prompt)