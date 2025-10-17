"""
관리자 전용 API 라우터
DB 관리, 사용자 관리, 시스템 모니터링 기능
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import json

from ..database import get_session
from ..models.user import User, UserRole
from ..models.mentor import MentorMenteeRelation, ExamScore, ChatHistory, Feedback
from ..models.document import Document
from ..models.post import Post, Comment
from ..utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """관리자 대시보드 통계"""
    try:
        # 사용자 통계
        total_users = session.exec(select(func.count(User.id))).first()
        mentors = session.exec(select(func.count(User.id)).where(User.role == UserRole.MENTOR)).first()
        mentees = session.exec(select(func.count(User.id)).where(User.role == UserRole.MENTEE)).first()
        
        # 활성 매칭 수
        active_relations = session.exec(
            select(func.count(MentorMenteeRelation.id)).where(MentorMenteeRelation.is_active == True)
        ).first()
        
        # 최근 활동 통계 (최근 7일)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_chats = session.exec(
            select(func.count(ChatHistory.id)).where(ChatHistory.created_at >= week_ago)
        ).first()
        
        recent_exams = session.exec(
            select(func.count(ExamScore.id)).where(ExamScore.created_at >= week_ago)
        ).first()
        
        recent_posts = session.exec(
            select(func.count(Post.id)).where(Post.created_at >= week_ago)
        ).first()
        
        return {
            "users": {
                "total": total_users,
                "mentors": mentors,
                "mentees": mentees,
                "active_relations": active_relations
            },
            "activities": {
                "recent_chats": recent_chats,
                "recent_exams": recent_exams,
                "recent_posts": recent_posts
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """전체 사용자 목록 조회"""
    try:
        query = select(User)
        
        # 역할 필터
        if role:
            query = query.where(User.role == role)
        
        # 검색 필터
        if search:
            query = query.where(
                User.name.contains(search) | 
                User.email.contains(search)
            )
        
        # 정렬 및 페이지네이션
        query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)
        
        users = session.exec(query).all()
        total = session.exec(select(func.count(User.id))).first()
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 실패: {str(e)}")


@router.get("/mentor-mentee-relations")
async def get_mentor_mentee_relations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """멘토-멘티 관계 목록 조회"""
    try:
        query = select(
            MentorMenteeRelation,
            User.name.label("mentor_name"),
            User.email.label("mentor_email")
        ).join(
            User, MentorMenteeRelation.mentor_id == User.id
        ).join(
            User, MentorMenteeRelation.mentee_id == User.id, aliased=True
        )
        
        if is_active is not None:
            query = query.where(MentorMenteeRelation.is_active == is_active)
        
        query = query.order_by(desc(MentorMenteeRelation.matched_at)).offset(skip).limit(limit)
        
        relations = session.exec(query).all()
        total = session.exec(select(func.count(MentorMenteeRelation.id))).first()
        
        return {
            "relations": relations,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"멘토-멘티 관계 조회 실패: {str(e)}")


@router.get("/learning-history")
async def get_learning_history(
    user_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """학습 이력 조회 (채팅, 시험, 피드백 통합)"""
    try:
        # 채팅 이력
        chat_query = select(
            ChatHistory.id,
            ChatHistory.user_id,
            ChatHistory.user_message,
            ChatHistory.created_at,
            User.name.label("user_name"),
            func.literal("chat").label("type")
        ).join(User, ChatHistory.user_id == User.id)
        
        # 시험 점수
        exam_query = select(
            ExamScore.id,
            ExamScore.mentee_id.label("user_id"),
            ExamScore.exam_name.label("user_message"),
            ExamScore.created_at,
            User.name.label("user_name"),
            func.literal("exam").label("type")
        ).join(User, ExamScore.mentee_id == User.id)
        
        # 피드백
        feedback_query = select(
            Feedback.id,
            Feedback.mentee_id.label("user_id"),
            Feedback.feedback_text.label("user_message"),
            Feedback.created_at,
            User.name.label("user_name"),
            func.literal("feedback").label("type")
        ).join(User, Feedback.mentee_id == User.id)
        
        # 필터 적용
        if user_id:
            chat_query = chat_query.where(ChatHistory.user_id == user_id)
            exam_query = exam_query.where(ExamScore.mentee_id == user_id)
            feedback_query = feedback_query.where(Feedback.mentee_id == user_id)
        
        if start_date:
            chat_query = chat_query.where(ChatHistory.created_at >= start_date)
            exam_query = exam_query.where(ExamScore.created_at >= start_date)
            feedback_query = feedback_query.where(Feedback.created_at >= start_date)
        
        if end_date:
            chat_query = chat_query.where(ChatHistory.created_at <= end_date)
            exam_query = exam_query.where(ExamScore.created_at <= end_date)
            feedback_query = feedback_query.where(Feedback.created_at <= end_date)
        
        # 결과 조합 (실제로는 UNION ALL을 사용해야 하지만 SQLModel 제한으로 인해 개별 조회)
        chat_results = session.exec(chat_query.limit(limit)).all()
        exam_results = session.exec(exam_query.limit(limit)).all()
        feedback_results = session.exec(feedback_query.limit(limit)).all()
        
        # 결과 정렬 및 페이지네이션
        all_results = list(chat_results) + list(exam_results) + list(feedback_results)
        all_results.sort(key=lambda x: x.created_at, reverse=True)
        
        paginated_results = all_results[skip:skip + limit]
        
        return {
            "history": paginated_results,
            "total": len(all_results),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"학습 이력 조회 실패: {str(e)}")


@router.get("/documents")
async def get_all_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """전체 문서 목록 조회"""
    try:
        query = select(Document)
        
        if category:
            query = query.where(Document.category == category)
        
        query = query.order_by(desc(Document.upload_date)).offset(skip).limit(limit)
        
        documents = session.exec(query).all()
        total = session.exec(select(func.count(Document.id))).first()
        
        return {
            "documents": documents,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 목록 조회 실패: {str(e)}")


@router.get("/system-logs")
async def get_system_logs(
    log_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """시스템 로그 조회"""
    try:
        # 실제 프로덕션에서는 별도의 로그 테이블을 사용해야 함
        # 현재는 기존 테이블들의 활동을 로그로 취급
        
        logs = []
        
        # 사용자 활동 로그 (로그인, 회원가입 등)
        user_activities = session.exec(
            select(User.id, User.name, User.email, User.created_at, User.updated_at)
            .order_by(desc(User.updated_at))
            .limit(50)
        ).all()
        
        for user in user_activities:
            logs.append({
                "id": f"user_{user.id}",
                "type": "user_activity",
                "message": f"사용자 {user.name} ({user.email}) 활동",
                "timestamp": user.updated_at,
                "details": {
                    "user_id": user.id,
                    "action": "profile_update" if user.updated_at > user.created_at else "registration"
                }
            })
        
        # 채팅 활동 로그
        chat_activities = session.exec(
            select(ChatHistory.id, ChatHistory.user_id, ChatHistory.created_at, User.name)
            .join(User, ChatHistory.user_id == User.id)
            .order_by(desc(ChatHistory.created_at))
            .limit(50)
        ).all()
        
        for chat in chat_activities:
            logs.append({
                "id": f"chat_{chat.id}",
                "type": "chat_activity",
                "message": f"사용자 {chat.name} 챗봇 사용",
                "timestamp": chat.created_at,
                "details": {
                    "user_id": chat.user_id,
                    "chat_id": chat.id,
                    "action": "chat_message"
                }
            })
        
        # 정렬 및 페이지네이션
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        paginated_logs = logs[skip:skip + limit]
        
        return {
            "logs": paginated_logs,
            "total": len(logs),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 로그 조회 실패: {str(e)}")


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """사용자 역할 변경"""
    try:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        if new_role not in [role.value for role in UserRole]:
            raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다")
        
        user.role = UserRole(new_role)
        user.updated_at = datetime.utcnow()
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {"message": "사용자 역할이 성공적으로 변경되었습니다", "user": user}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"역할 변경 실패: {str(e)}")


@router.post("/mentor-mentee-relations")
async def create_mentor_mentee_relation(
    mentor_id: int,
    mentee_id: int,
    notes: Optional[str] = None,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """새로운 멘토-멘티 관계 생성"""
    try:
        # 멘토와 멘티 존재 확인
        mentor = session.get(User, mentor_id)
        mentee = session.get(User, mentee_id)
        
        if not mentor or mentor.role != UserRole.MENTOR:
            raise HTTPException(status_code=400, detail="유효하지 않은 멘토입니다")
        
        if not mentee or mentee.role != UserRole.MENTEE:
            raise HTTPException(status_code=400, detail="유효하지 않은 멘티입니다")
        
        # 기존 관계 확인
        existing = session.exec(
            select(MentorMenteeRelation)
            .where(
                MentorMenteeRelation.mentor_id == mentor_id,
                MentorMenteeRelation.mentee_id == mentee_id,
                MentorMenteeRelation.is_active == True
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="이미 활성화된 관계가 존재합니다")
        
        # 새 관계 생성
        relation = MentorMenteeRelation(
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            notes=notes,
            matched_at=datetime.utcnow(),
            is_active=True
        )
        
        session.add(relation)
        session.commit()
        session.refresh(relation)
        
        return {"message": "멘토-멘티 관계가 성공적으로 생성되었습니다", "relation": relation}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"관계 생성 실패: {str(e)}")


@router.delete("/mentor-mentee-relations/{relation_id}")
async def deactivate_mentor_mentee_relation(
    relation_id: int,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """멘토-멘티 관계 비활성화"""
    try:
        relation = session.get(MentorMenteeRelation, relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다")
        
        relation.is_active = False
        session.add(relation)
        session.commit()
        
        return {"message": "멘토-멘티 관계가 비활성화되었습니다"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"관계 비활성화 실패: {str(e)}")
