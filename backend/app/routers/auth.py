"""
인증 API 라우터
회원가입, 로그인, 토큰 관리
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models.user import User, UserCreate, UserRead, UserUpdate, Token
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_active_admin
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    """
    회원가입
    - 이메일 중복 확인
    - 비밀번호 해싱
    - 사용자 정보 저장
    """
    # 이메일 중복 확인
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 사용자 생성
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        role=user_data.role,
        photo_url=user_data.photo_url,
        phone=user_data.phone,
        interests=user_data.interests,
        hobbies=user_data.hobbies,
        specialties=user_data.specialties,
        team=user_data.team,
        team_number=user_data.team_number,
        employee_number=user_data.employee_number,
        join_year=user_data.join_year,
        position=user_data.position,
        extension=user_data.extension,
        emergency_contact=user_data.emergency_contact,
        encouragement_message=user_data.encouragement_message
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    로그인
    - 이메일/비밀번호 검증
    - JWT 토큰 발급 (액세스 토큰 + 리프레시 토큰)
    """
    # 사용자 조회
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    
    # 사용자 존재 여부 및 비밀번호 확인
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비활성 사용자 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # 토큰 생성
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """현재 로그인한 사용자 정보 조회"""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    현재 사용자 정보 수정
    """
    # 수정할 필드만 업데이트
    update_data = user_update.dict(exclude_unset=True)
    
    # 비밀번호 변경 시 해싱
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user


@router.get("/users", response_model=List[UserRead])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """
    전체 사용자 목록 조회 (관리자만 가능)
    """
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """
    사용자 삭제 (관리자만 가능)
    실제로는 is_active를 False로 설정 (소프트 삭제)
    """
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    session.add(user)
    session.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/find-id")
async def find_id(
    name: str,
    employee_number: str,
    session: Session = Depends(get_session)
):
    """
    아이디(이메일) 찾기
    - 이름과 사원번호로 이메일 찾기
    """
    statement = select(User).where(User.name == name, User.employee_number == employee_number)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with provided information"
        )
    
    return {
        "email": user.email
    }


@router.post("/reset-password")
async def reset_password(
    email: str,
    employee_number: str,
    new_password: str,
    session: Session = Depends(get_session)
):
    """
    비밀번호 재설정
    - 이메일과 사원번호로 본인 확인
    - 새 비밀번호로 변경
    """
    statement = select(User).where(User.email == email, User.employee_number == employee_number)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with provided information"
        )
    
    # 새 비밀번호 해싱 및 저장
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    
    return {
        "message": "Password has been reset successfully",
        "email": email
    }