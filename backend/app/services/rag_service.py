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
        
        # 1단계: RAG 검색 시도
        if context_docs is None:
            context_docs = await self.similarity_search(question, k=5)
        
        # 컨텍스트 구성
        context = "\n\n".join([
            f"[{doc['category']} - {doc['title']}]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # RAG 기반 답변 생성
        rag_prompt = f"""당신은 은행 신입사원을 돕는 친절한 멘토입니다.
아래의 참고 자료를 바탕으로 질문에 답변해주세요.

참고 자료:
{context}

질문: {question}

답변 시 주의사항:
1. 참고 자료에 있는 내용을 중심으로 답변하세요.
2. 참고 자료에 없는 내용이면 "제공된 자료에서 해당 정보를 찾을 수 없습니다"라고 말하세요.
3. 친절하고 이해하기 쉽게 설명하세요.
4. 필요하면 예시를 들어 설명하세요.

답변:"""
        
        # RAG 답변 생성
        rag_answer = self._call_gpt(rag_prompt)
        
        # 답변 품질 평가 (간단한 휴리스틱)
        is_rag_adequate = self._evaluate_answer_quality(rag_answer, context_docs)
        
        if is_rag_adequate and context_docs:
            # RAG 답변이 적절하면 그대로 사용
            final_answer = rag_answer
            answer_type = "rag"
        else:
            # RAG 답변이 부적절하거나 문서가 없으면 GPT 폴백
            gpt_answer = await self._generate_gpt_fallback(question, context_docs)
            final_answer = gpt_answer
            answer_type = "gpt"
        
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
    
    def _evaluate_answer_quality(self, answer: str, context_docs: List[Dict]) -> bool:
        """
        RAG 답변의 품질 평가
        Args:
            answer: 생성된 답변
            context_docs: 참고 문서들
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
        
        # 유사도가 너무 낮은 문서들만 있는 경우
        if context_docs and all(doc.get('similarity', 0) < 0.7 for doc in context_docs):
            print("All documents have low similarity")
            return False
        
        print(f"Answer quality check passed. Context docs: {len(context_docs)}")
        return True
    
    async def _generate_gpt_fallback(self, question: str, context_docs: List[Dict]) -> str:
        """
        GPT 폴백 답변 생성
        """
        # 컨텍스트가 있으면 포함, 없으면 일반적인 답변
        if context_docs:
            context = "\n\n".join([
                f"[{doc['category']} - {doc['title']}]\n{doc['content'][:500]}..."  # 길이 제한
                for doc in context_docs[:3]  # 상위 3개만
            ])
            
            gpt_prompt = f"""당신은 은행 신입사원을 돕는 친절한 멘토입니다.
업로드된 문서에서 일부 관련 정보를 찾았지만, 더 포괄적인 답변을 제공해주세요.

참고 자료 (일부):
{context}

질문: {question}

답변 시 주의사항:
1. 은행 업무와 관련된 일반적인 지식을 바탕으로 답변하세요.
2. 친절하고 이해하기 쉽게 설명하세요.
3. 필요하면 예시를 들어 설명하세요.
4. 불확실한 내용은 "일반적으로" 또는 "보통"이라는 표현을 사용하세요.

답변:"""
        else:
            gpt_prompt = f"""당신은 은행 신입사원을 돕는 친절한 멘토입니다.
업로드된 문서에서 관련 정보를 찾지 못했으므로, 일반적인 은행 업무 지식을 바탕으로 답변해주세요.

질문: {question}

답변 시 주의사항:
1. 은행 업무와 관련된 일반적인 지식을 바탕으로 답변하세요.
2. 친절하고 이해하기 쉽게 설명하세요.
3. 필요하면 예시를 들어 설명하세요.
4. 불확실한 내용은 "일반적으로" 또는 "보통"이라는 표현을 사용하세요.

답변:"""
        
        # GPT로 답변 생성
        return self._call_gpt(gpt_prompt)