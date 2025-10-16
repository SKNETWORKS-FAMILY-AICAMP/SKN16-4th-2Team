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
            
            # pgvector를 사용한 유사도 검색 (배열 문자열로 변환)
            query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            sql = text(f"""
                SELECT 
                    dc.content,
                    dc.chunk_index,
                    d.title,
                    d.category,
                    d.id as document_id,
                    1 - (dc.embedding <=> '{query_embedding_str}'::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.is_indexed = true AND d.category = 'RAG'
                ORDER BY dc.embedding <=> '{query_embedding_str}'::vector
                LIMIT :k
            """)
            
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
        
        # 온보딩 관련 질문이 아니면 간단한 GPT 답변
        if not detected_part:
            gpt_answer = await self._generate_gpt_fallback(question, [])
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            try:
                chat_history = ChatHistory(
                    user_id=user_id,
                    user_message=question,
                    bot_response=gpt_answer,
                    source_documents=json.dumps([], ensure_ascii=False),
                    response_time=response_time
                )
                self.session.add(chat_history)
                self.session.commit()
            except Exception as e:
                print(f"Chat history save error: {e}")
                self.session.rollback()
            
            return {
                "answer": gpt_answer,
                "sources": [],
                "response_time": response_time,
                "answer_type": "gpt"
            }
        
        # 1단계: RAG 검색 시도 (온보딩 관련 질문) - 가중치 증가
        if context_docs is None:
            context_docs = await self.similarity_search(question, k=8)  # 더 많은 문서 검색
        
        # 컨텍스트 구성 (제목에서 "RAG - " 제거)
        context = "\n\n".join([
            f"[{doc['title'].replace('RAG - ', '')}]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # 온보딩 교육용 RAG 답변 생성
        part_info = {
            "수신": "고객이 은행에 돈을 맡기는 업무 (예금, 적금 등)",
            "여신": "고객에게 돈을 빌려주는 업무 (대출, 신용평가 등)", 
            "외환": "외국 돈을 사고팔거나 송금하는 업무"
        }
        
        rag_prompt = f"""당신은 은행 신입사원 온보딩을 담당하는 AI 튜터입니다.
현재 {detected_part} 파트 교육 중이며, {part_info[detected_part]}에 대해 설명하고 있습니다.

다음 자료를 참고하여 답변해주세요:
{context}

질문: {question}

답변 규칙:
1. 신입사원이 이해하기 쉽게 따뜻하고 교육적인 톤으로 답변
2. 어려운 은행 용어는 쉬운 표현과 함께 설명
3. 반드시 다음 순서로 구성:
   - ① 핵심 개념 요약 (한 문단)
   - ② 실제 현장 예시 (구체적인 상황이나 숫자 포함)
   - ③ 실무 유의사항 (주의할 점이나 팁)
4. 답변은 3-4문단 이내로 간결하게
5. 신입사원이 회사에 자연스럽게 적응할 수 있도록 격려하는 톤 유지
6. 답변에 참고자료나 출처 정보는 절대 포함하지 마세요

답변:"""
        
        # RAG 답변 생성
        rag_answer = self._call_gpt(rag_prompt)
        
        # 답변 품질 평가 (중요 단어 필터링 포함)
        is_rag_adequate = self._evaluate_answer_quality(rag_answer, context_docs, question)

        if is_rag_adequate and context_docs:
            # RAG 답변이 적절하면 그대로 사용
            # 고품질 문서만 참고자료로 사용 (임계값 낮춤)
            high_quality_docs = [doc for doc in context_docs if doc.get('similarity', 0) >= 0.75]
            
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

        # 유사도 임계값을 0.75로 낮춰서 더 많은 문서를 허용 (RAG 가중치 증가)
        if context_docs and all(doc.get('similarity', 0) < 0.75 for doc in context_docs):
            print("All documents have low similarity")
            return False

        # 관련성 높은 문서가 있는지 확인 (임계값 낮춤)
        high_quality_docs = [doc for doc in context_docs if doc.get('similarity', 0) >= 0.75]
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
            return "안녕하세요! 😊 은행 신입사원 온보딩을 도와드리는 AI 튜터입니다. 수신(예금), 여신(대출), 외환(환전·송금) 파트 중 궁금한 업무가 있으시면 언제든 물어보세요!"
        
        # 온보딩 관련 질문이지만 RAG 문서가 없는 경우
        gpt_prompt = f"""당신은 은행 신입사원 온보딩을 담당하는 AI 튜터입니다.
신입사원이 회사에 자연스럽게 적응할 수 있도록 도와주세요.

질문: {question}

답변 규칙:
1. 신입사원이 이해하기 쉽게 따뜻하고 교육적인 톤으로 답변
2. 어려운 은행 용어는 쉬운 표현과 함께 설명
3. 반드시 다음 순서로 구성:
   - ① 핵심 개념 요약 (한 문단)
   - ② 실제 현장 예시 (구체적인 상황이나 숫자 포함)
   - ③ 실무 유의사항 (주의할 점이나 팁)
4. 답변은 3-4문단 이내로 간결하게
5. 신입사원이 회사에 자연스럽게 적응할 수 있도록 격려하는 톤 유지
6. 불확실한 내용은 "일반적으로" 또는 "보통"이라는 표현 사용

답변:"""
        
        # GPT로 답변 생성
        return self._call_gpt(gpt_prompt)