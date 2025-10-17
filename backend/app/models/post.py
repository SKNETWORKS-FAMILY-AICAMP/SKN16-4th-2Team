"""
익명 게시판 (대나무숲) 모델
완전 익명성 보장
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional, List
from datetime import datetime


class Post(SQLModel, table=True):
    """게시글 모델"""
    __tablename__ = "posts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str = Field(sa_column=Column(Text))
    
    # 익명성 보장: 작성자 ID는 저장하지만 표시하지 않음
    author_id: int = Field(foreign_key="users.id")
    
    # 통계
    view_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    
    # 시스템 필드
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)


class PostCreate(SQLModel):
    """게시글 작성 요청 모델"""
    title: str
    content: str


class PostRead(SQLModel):
    """게시글 응답 모델 (익명 처리)"""
    id: int
    title: str
    content: str
    view_count: int
    comment_count: int
    like_count: int = 0  # 추천 수
    dislike_count: int = 0  # 비추천 수
    user_liked: bool = False  # 현재 사용자가 추천했는지
    user_disliked: bool = False  # 현재 사용자가 비추천했는지
    created_at: datetime
    updated_at: datetime
    author_alias: str = "익명1"  # 항상 익명1로 표시


class Comment(SQLModel, table=True):
    """댓글 모델"""
    __tablename__ = "comments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id")
    content: str = Field(sa_column=Column(Text))
    
    # 익명성 보장
    author_id: int = Field(foreign_key="users.id")
    
    # 댓글 순서 (익명2, 익명3... 순서 결정)
    comment_order: int = Field(default=0)
    
    # 시스템 필드
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)


class CommentCreate(SQLModel):
    """댓글 작성 요청 모델"""
    post_id: int
    content: str


class CommentRead(SQLModel):
    """댓글 응답 모델 (익명 처리)"""
    id: int
    post_id: int
    content: str
    like_count: int = 0  # 추천 수
    dislike_count: int = 0  # 비추천 수
    user_liked: bool = False  # 현재 사용자가 추천했는지
    user_disliked: bool = False  # 현재 사용자가 비추천했는지
    created_at: datetime
    author_alias: str  # 익명2, 익명3... 형태
    is_author: bool = False  # 현재 사용자가 작성자인지
    is_admin: bool = False   # 현재 사용자가 관리자인지


class PostDetail(SQLModel):
    """게시글 상세 정보 (댓글 포함)"""
    post: PostRead
    comments: List[CommentRead] = []
    is_author: bool = False  # 현재 사용자가 작성자인지
    is_admin: bool = False   # 현재 사용자가 관리자인지


class PostLike(SQLModel, table=True):
    """게시글 추천/비추천 모델"""
    __tablename__ = "post_likes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id")
    user_id: int = Field(foreign_key="users.id")
    is_like: bool = Field(default=True)  # True: 추천, False: 비추천
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 복합 유니크 제약: 한 사용자는 한 게시글에 대해 하나의 추천/비추천만 가능
    __table_args__ = (
        {"extend_existing": True}
    )


class CommentLike(SQLModel, table=True):
    """댓글 추천/비추천 모델"""
    __tablename__ = "comment_likes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(foreign_key="comments.id")
    user_id: int = Field(foreign_key="users.id")
    is_like: bool = Field(default=True)  # True: 추천, False: 비추천
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 복합 유니크 제약: 한 사용자는 한 댓글에 대해 하나의 추천/비추천만 가능
    __table_args__ = (
        {"extend_existing": True}
    )


