"""
대시보드 API 라우터
멘토/멘티별 대시보드 데이터 제공
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List, Dict
from collections import Counter
import json

from app.database import get_session
from app.models.user import User, UserRead
from app.models.mentor import (
    MentorMenteeRelation, ExamScore, ChatHistory,
    MentorDashboard, MenteeDashboard, LearningProgress
)
from app.utils.auth import get_current_user, get_current_active_mentor

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/mentee", response_model=MenteeDashboard)
async def get_mentee_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    멘티 대시보드 데이터
    - 담당 멘토 정보
    - 시험 점수
    - 학습 진행도
    - 최근 채팅 기록
    """
    # 담당 멘토 정보 조회
    mentor_info = None
    relation_statement = select(MentorMenteeRelation).where(
        MentorMenteeRelation.mentee_id == current_user.id,
        MentorMenteeRelation.is_active == True
    )
    relation = session.exec(relation_statement).first()
    
    if relation:
        mentor_statement = select(User).where(User.id == relation.mentor_id)
        mentor = session.exec(mentor_statement).first()
        if mentor:
            mentor_info = {
                "id": mentor.id,
                "name": mentor.name,
                "team": mentor.team,
                "mbti": mentor.mbti,
                "interests": mentor.interests,
                "hobbies": mentor.hobbies,
                "encouragement_message": mentor.encouragement_message,
                "photo_url": mentor.photo_url
            }
    
    # 시험 점수 조회
    exam_statement = (
        select(ExamScore)
        .where(ExamScore.mentee_id == current_user.id)
        .order_by(ExamScore.exam_date.desc())
    )
    exams = session.exec(exam_statement).all()
    
    exam_scores = []
    for exam in exams:
        exam_scores.append({
            "id": exam.id,
            "exam_name": exam.exam_name,
            "exam_date": exam.exam_date.isoformat(),
            "score_data": json.loads(exam.score_data) if exam.score_data else {},
            "total_score": exam.total_score,
            "grade": exam.grade,
            "feedback": exam.feedback
        })
    
    # 학습 진행도
    chat_count_statement = select(func.count(ChatHistory.id)).where(
        ChatHistory.user_id == current_user.id
    )
    total_chats = session.exec(chat_count_statement).first() or 0
    
    # 최근 대화 주제 추출
    recent_chats_statement = (
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(20)
    )
    recent_chats_data = session.exec(recent_chats_statement).all()
    
    recent_topics = []
    recent_chats = []
    for chat in recent_chats_data[:5]:  # 최근 5개만
        recent_chats.append({
            "user_message": chat.user_message,
            "bot_response": chat.bot_response,
            "created_at": chat.created_at.isoformat()
        })
    
    # 간단한 주제 추출 (첫 50자)
    for chat in recent_chats_data:
        if chat.user_message:
            topic = chat.user_message[:50]
            recent_topics.append(topic)
    
    learning_progress = LearningProgress(
        mentee_id=current_user.id,
        total_chats=total_chats,
        documents_accessed=0,  # 추후 구현
        recent_topics=recent_topics[:10],
        progress_percentage=min(100, total_chats * 5)  # 간단한 진행도 계산
    )
    
    return MenteeDashboard(
        mentee_id=current_user.id,
        mentor_info=mentor_info,
        exam_scores=exam_scores,
        learning_progress=learning_progress,
        recent_chats=recent_chats
    )


@router.get("/mentor", response_model=MentorDashboard)
async def get_mentor_dashboard(
    current_user: User = Depends(get_current_active_mentor),
    session: Session = Depends(get_session)
):
    """
    멘토 대시보드 데이터
    - 담당 멘티 목록
    - 멘티별 성적
    - 자주 묻는 질문 키워드
    """
    # 담당 멘티 목록
    relation_statement = select(MentorMenteeRelation).where(
        MentorMenteeRelation.mentor_id == current_user.id,
        MentorMenteeRelation.is_active == True
    )
    relations = session.exec(relation_statement).all()
    
    mentees = []
    mentee_scores = {}
    all_questions = []
    
    for relation in relations:
        # 멘티 정보
        mentee_statement = select(User).where(User.id == relation.mentee_id)
        mentee = session.exec(mentee_statement).first()
        
        if mentee:
            # 멘티 기본 정보
            mentee_info = {
                "id": mentee.id,
                "name": mentee.name,
                "email": mentee.email,
                "team": mentee.team,
                "mbti": mentee.mbti,
                "interests": mentee.interests,
                "photo_url": mentee.photo_url
            }
            
            # 멘티의 최근 시험 점수
            exam_statement = (
                select(ExamScore)
                .where(ExamScore.mentee_id == mentee.id)
                .order_by(ExamScore.exam_date.desc())
                .limit(1)
            )
            recent_exam = session.exec(exam_statement).first()
            
            if recent_exam:
                mentee_info["recent_score"] = recent_exam.total_score
                mentee_info["recent_exam"] = recent_exam.exam_name
                mentee_scores[mentee.name] = {
                    "total_score": recent_exam.total_score,
                    "score_data": json.loads(recent_exam.score_data) if recent_exam.score_data else {}
                }
            
            # 멘티의 채팅 통계
            chat_count_statement = select(func.count(ChatHistory.id)).where(
                ChatHistory.user_id == mentee.id
            )
            chat_count = session.exec(chat_count_statement).first() or 0
            mentee_info["chat_count"] = chat_count
            
            mentees.append(mentee_info)
            
            # 멘티의 질문 수집 (워드클라우드용)
            chat_statement = (
                select(ChatHistory)
                .where(ChatHistory.user_id == mentee.id)
                .order_by(ChatHistory.created_at.desc())
                .limit(50)
            )
            chats = session.exec(chat_statement).all()
            for chat in chats:
                all_questions.append(chat.user_message)
    
    # 자주 묻는 질문 키워드 추출 (간단한 버전)
    frequent_questions = _extract_keywords(all_questions)
    
    return MentorDashboard(
        mentor_id=current_user.id,
        mentees=mentees,
        frequent_questions=frequent_questions,
        mentee_scores=mentee_scores
    )


@router.post("/assign-mentor")
async def assign_mentor(
    mentee_id: int,
    mentor_id: int,
    current_user: User = Depends(get_current_active_mentor),
    session: Session = Depends(get_session)
):
    """
    멘토-멘티 매칭 (관리자/멘토가 수행)
    """
    # 멘티와 멘토 확인
    mentee_statement = select(User).where(User.id == mentee_id)
    mentee = session.exec(mentee_statement).first()
    
    mentor_statement = select(User).where(User.id == mentor_id)
    mentor = session.exec(mentor_statement).first()
    
    if not mentee or not mentor:
        raise HTTPException(status_code=404, detail="User not found")
    
    if mentee.role != "mentee":
        raise HTTPException(status_code=400, detail="User is not a mentee")
    
    if mentor.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=400, detail="User is not a mentor")
    
    # 기존 관계 비활성화
    existing_statement = select(MentorMenteeRelation).where(
        MentorMenteeRelation.mentee_id == mentee_id,
        MentorMenteeRelation.is_active == True
    )
    existing_relations = session.exec(existing_statement).all()
    for rel in existing_relations:
        rel.is_active = False
        session.add(rel)
    
    # 새 관계 생성
    relation = MentorMenteeRelation(
        mentor_id=mentor_id,
        mentee_id=mentee_id,
        is_active=True
    )
    session.add(relation)
    session.commit()
    
    return {"message": "Mentor assigned successfully"}


@router.post("/exam-score")
async def add_exam_score(
    mentee_id: int,
    exam_name: str,
    score_data: Dict,
    total_score: float,
    grade: str = None,
    current_user: User = Depends(get_current_active_mentor),
    session: Session = Depends(get_session)
):
    """
    시험 점수 추가 (멘토/관리자가 수행)
    """
    from datetime import datetime
    
    exam = ExamScore(
        mentee_id=mentee_id,
        exam_name=exam_name,
        exam_date=datetime.utcnow(),
        score_data=json.dumps(score_data, ensure_ascii=False),
        total_score=total_score,
        grade=grade
    )
    
    session.add(exam)
    session.commit()
    session.refresh(exam)
    
    return {"message": "Exam score added successfully", "exam_id": exam.id}


def _extract_keywords(questions: List[str], top_k: int = 20) -> List[Dict]:
    """
    질문에서 키워드 추출 (간단한 버전)
    실제로는 형태소 분석 등을 사용하면 더 좋습니다.
    """
    # 간단한 공백 기반 단어 분리
    words = []
    for question in questions:
        words.extend(question.split())
    
    # 단어 빈도 계산
    word_counts = Counter(words)
    
    # 상위 키워드 반환
    frequent_words = word_counts.most_common(top_k)
    
    return [
        {"word": word, "count": count}
        for word, count in frequent_words
    ]

