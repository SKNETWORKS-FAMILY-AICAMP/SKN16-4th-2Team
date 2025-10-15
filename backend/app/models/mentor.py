"""
멘토-멘티 관계 및 학습 관리 모델
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text, JSON
from typing import Optional, List, Dict
from datetime import datetime


class MentorMenteeRelation(SQLModel, table=True):
    """멘토-멘티 관계 테이블"""
    __tablename__ = "mentor_mentee_relations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    mentor_id: int = Field(foreign_key="users.id")
    mentee_id: int = Field(foreign_key="users.id")
    
    # 매칭 정보
    matched_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # 메모 (멘토가 멘티에 대해 작성)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))


class ExamScore(SQLModel, table=True):
    """연수원 시험 점수 (멘티용)"""
    __tablename__ = "exam_scores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    mentee_id: int = Field(foreign_key="users.id")
    
    # 시험 정보
    exam_name: str  # 시험명
    exam_date: datetime
    
    # 점수 (레이더 차트용 - 최대 6개 항목)
    score_data: str = Field(sa_column=Column(Text))  # JSON 형태: {"은행업무": 85, "상품지식": 90, ...}
    total_score: float
    
    # 평가
    grade: Optional[str] = None  # A, B, C 등급
    feedback: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatHistory(SQLModel, table=True):
    """챗봇 대화 기록"""
    __tablename__ = "chat_histories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    
    # 대화 내용
    user_message: str = Field(sa_column=Column(Text))
    bot_response: str = Field(sa_column=Column(Text))
    
    # RAG 관련 메타데이터
    source_documents: Optional[str] = None  # JSON 형태로 참조 문서 저장
    response_time: Optional[float] = None  # 응답 시간 (초)
    
    # 피드백
    is_helpful: Optional[bool] = None  # 사용자 피드백
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LearningProgress(SQLModel):
    """학습 진행도 (응답용 모델)"""
    mentee_id: int
    total_chats: int
    documents_accessed: int
    recent_topics: List[str]
    progress_percentage: float


class MentorDashboard(SQLModel):
    """멘토 대시보드 데이터"""
    mentor_id: int
    mentees: List[Dict]  # 담당 멘티 목록
    frequent_questions: List[Dict]  # 자주 묻는 질문 키워드
    mentee_scores: Dict  # 멘티별 성적


class MenteeDashboard(SQLModel):
    """멘티 대시보드 데이터"""
    mentee_id: int
    mentor_info: Optional[Dict] = None  # 담당 멘토 정보
    exam_scores: List[Dict] = []  # 시험 점수 목록
    learning_progress: Optional[LearningProgress] = None
    recent_chats: List[Dict] = []


