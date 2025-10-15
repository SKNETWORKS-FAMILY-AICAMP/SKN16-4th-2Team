"""
사용자 모델
역할: admin, mentor, mentee
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    MENTOR = "mentor"
    MENTEE = "mentee"


class User(SQLModel, table=True):
    """사용자 모델"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    name: str
    role: UserRole = Field(default=UserRole.MENTEE)
    
    # 프로필 정보
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    mbti: Optional[str] = None
    interests: Optional[str] = None  # JSON 문자열로 저장
    hobbies: Optional[str] = None
    specialties: Optional[str] = None
    team: Optional[str] = None  # 팀 배정
    
    # 멘토 전용 필드
    encouragement_message: Optional[str] = None  # 응원 메시지
    
    # 시스템 필드
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """회원가입 요청 모델"""
    email: str
    password: str
    name: str
    role: UserRole = UserRole.MENTEE
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    mbti: Optional[str] = None
    interests: Optional[str] = None
    hobbies: Optional[str] = None
    specialties: Optional[str] = None
    team: Optional[str] = None
    encouragement_message: Optional[str] = None


class UserRead(SQLModel):
    """사용자 정보 응답 모델 (비밀번호 제외)"""
    id: int
    email: str
    name: str
    role: UserRole
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    mbti: Optional[str] = None
    interests: Optional[str] = None
    hobbies: Optional[str] = None
    specialties: Optional[str] = None
    team: Optional[str] = None
    encouragement_message: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserUpdate(SQLModel):
    """사용자 정보 수정 모델"""
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    mbti: Optional[str] = None
    interests: Optional[str] = None
    hobbies: Optional[str] = None
    specialties: Optional[str] = None
    team: Optional[str] = None
    encouragement_message: Optional[str] = None
    password: Optional[str] = None


class Token(SQLModel):
    """JWT 토큰 응답 모델"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """토큰 페이로드 데이터"""
    email: Optional[str] = None
    role: Optional[str] = None


