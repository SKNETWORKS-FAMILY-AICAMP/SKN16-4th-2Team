"""
RAG (Retrieval-Augmented Generation) 챗봇 서비스
LangChain + OpenAI + pgvector 기반
"""
from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document as LangChainDocument
from sqlmodel import Session, select
from sqlalchemy import text
import json
from datetime import datetime

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.models.mentor import ChatHistory

class RAGService:
    """RAG 챗봇 서비스 클래스"""
    
    def __init__(self, session: Session):
        self.session = session
        
        # 텍스트 분할기 설정
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # OpenAI 임베딩 모델 (lazy initialization)
        self._embeddings = None
        
        # LLM 모델 (lazy initialization)
        self._llm = None
    
    @property
    def embeddings(self):
        """임베딩 모델 lazy initialization"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model="text-embedding-ada-002"
            )
        return self._embeddings
    
    @property
    def llm(self):
        """LLM 모델 lazy initialization"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model="gpt-4o",
                temperature=0.7
            )
        return self._llm
    
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
            chunks = self.text_splitter.split_text(content)
            
            # 각 청크에 대해 임베딩 생성 및 저장
            for idx, chunk in enumerate(chunks):
                # 임베딩 생성
                embedding = self.embeddings.embed_query(chunk)
                
                # 데이터베이스에 저장
                chunk_obj = DocumentChunk(
                    document_id=document_id,
                    content=chunk,
                    chunk_index=idx,
                    embedding=embedding
                )
                self.session.add(chunk_obj)
            
            # 문서 인덱싱 완료 표시
            statement = select(Document).where(Document.id == document_id)
            document = self.session.exec(statement).first()
            if document:
                document.is_indexed = True
                self.session.add(document)
            
            self.session.commit()
            return True
        
        except Exception as e:
            print(f"Error indexing document: {e}")
            self.session.rollback()
            return False
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        벡터 유사도 검색
        Args:
            query: 검색 쿼리
            k: 반환할 결과 개수
        Returns:
            List[Dict]: 관련 문서 청크 목록
        """
        # 쿼리 임베딩 생성
        query_embedding = self.embeddings.embed_query(query)
        
        # pgvector를 사용한 유사도 검색
        # cosine distance를 사용 (1 - cosine_similarity)
        sql_query = text(f"""
            SELECT 
                dc.id,
                dc.document_id,
                dc.content,
                dc.chunk_index,
                d.title,
                d.category,
                1 - (dc.embedding <=> :query_embedding::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.is_indexed = true
            ORDER BY dc.embedding <=> :query_embedding::vector
            LIMIT :k
        """)
        
        result = self.session.exec(
            sql_query,
            {"query_embedding": str(query_embedding), "k": k}
        )
        
        documents = []
        for row in result:
            documents.append({
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "chunk_index": row[3],
                "title": row[4],
                "category": row[5],
                "similarity": float(row[6])
            })
        
        return documents
    
    async def generate_answer(
        self,
        question: str,
        user_id: int,
        context_docs: Optional[List[Dict]] = None
    ) -> Dict:
        """
        질문에 대한 답변 생성 (RAG)
        Args:
            question: 사용자 질문
            user_id: 사용자 ID
            context_docs: 컨텍스트 문서 (없으면 자동 검색)
        Returns:
            Dict: 답변 및 메타데이터
        """
        start_time = datetime.utcnow()
        
        # 컨텍스트 문서가 없으면 검색
        if context_docs is None:
            context_docs = await self.similarity_search(question, k=5)
        
        # 컨텍스트 구성
        context = "\n\n".join([
            f"[{doc['category']} - {doc['title']}]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # 프롬프트 구성
        prompt = f"""당신은 은행 신입사원을 돕는 친절한 멘토입니다.
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
        
        # LLM으로 답변 생성
        response = self.llm.invoke(prompt)
        answer = response.content
        
        # 응답 시간 계산
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 대화 기록 저장
        chat_history = ChatHistory(
            user_id=user_id,
            user_message=question,
            bot_response=answer,
            source_documents=json.dumps([
                {"title": doc["title"], "category": doc["category"]}
                for doc in context_docs
            ], ensure_ascii=False),
            response_time=response_time
        )
        self.session.add(chat_history)
        self.session.commit()
        
        return {
            "answer": answer,
            "sources": context_docs,
            "response_time": response_time
        }
    
    async def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        사용자의 채팅 기록 조회
        Args:
            user_id: 사용자 ID
            limit: 반환할 기록 개수
        Returns:
            List[Dict]: 채팅 기록
        """
        statement = (
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        
        histories = self.session.exec(statement).all()
        
        return [
            {
                "user_message": h.user_message,
                "bot_response": h.bot_response,
                "created_at": h.created_at.isoformat(),
                "sources": json.loads(h.source_documents) if h.source_documents else []
            }
            for h in reversed(list(histories))
        ]

