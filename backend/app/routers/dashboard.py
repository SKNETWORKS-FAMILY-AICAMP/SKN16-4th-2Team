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
    MentorDashboard, MenteeDashboard, LearningProgress, Feedback, FeedbackComment
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
    
    # 6가지 지표 성적 데이터 (샘플 데이터 - 추후 실제 데이터로 대체)
    performance_scores = {
        "banking": 85,  # 은행업무
        "product_knowledge": 78,  # 상품지식
        "customer_service": 92,  # 고객응대
        "compliance": 88,  # 법규준수
        "it_usage": 75,  # IT활용
        "sales_performance": 80  # 영업실적
    }
    
    # 최근 피드백 조회
    feedbacks_statement = (
        select(Feedback)
        .where(Feedback.mentee_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .limit(5)
    )
    recent_feedbacks = session.exec(feedbacks_statement).all()
    
    feedback_list = []
    for feedback in recent_feedbacks:
        mentor_statement = select(User).where(User.id == feedback.mentor_id)
        mentor = session.exec(mentor_statement).first()
        
        feedback_list.append({
            "id": feedback.id,
            "feedback_text": feedback.feedback_text,
            "feedback_type": feedback.feedback_type,
            "color_section": feedback.color_section,
            "is_read": feedback.is_read,
            "created_at": feedback.created_at.isoformat(),
            "mentor_name": mentor.name if mentor else "알 수 없음"
        })
    
    return MenteeDashboard(
        mentee_id=current_user.id,
        mentor_info=mentor_info,
        exam_scores=exam_scores,
        learning_progress=learning_progress,
        recent_chats=recent_chats,
        performance_scores=performance_scores,
        recent_feedbacks=feedback_list
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
                
                # 개별 성과 지표 추가 (멘토 대시보드용)
                score_data = json.loads(recent_exam.score_data) if recent_exam.score_data else {}
                mentee_info["performance_scores"] = {
                    "banking": score_data.get("은행업무", recent_exam.total_score),
                    "product_knowledge": score_data.get("상품지식", recent_exam.total_score),
                    "customer_service": score_data.get("고객응대", recent_exam.total_score),
                    "compliance": score_data.get("법규준수", recent_exam.total_score),
                    "it_usage": score_data.get("IT활용", recent_exam.total_score),
                    "sales_performance": score_data.get("영업실적", recent_exam.total_score)
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


@router.post("/feedback")
async def create_feedback(
    request: dict,
    current_user: User = Depends(get_current_active_mentor),
    session: Session = Depends(get_session)
):
    """
    멘토가 멘티에게 피드백 전송
    """
    mentee_id = request.get("mentee_id")
    feedback_text = request.get("feedback_text")
    feedback_type = request.get("feedback_type", "general")
    
    if not mentee_id or not feedback_text:
        raise HTTPException(
            status_code=400,
            detail="mentee_id와 feedback_text는 필수입니다."
        )
    # 멘토-멘티 관계 확인
    relation_statement = select(MentorMenteeRelation).where(
        MentorMenteeRelation.mentor_id == current_user.id,
        MentorMenteeRelation.mentee_id == mentee_id,
        MentorMenteeRelation.is_active == True
    )
    relation = session.exec(relation_statement).first()
    
    if not relation:
        raise HTTPException(
            status_code=403,
            detail="해당 멘티와의 관계가 없거나 비활성화되어 있습니다."
        )
    
    # 피드백 생성
    feedback = Feedback(
        mentor_id=current_user.id,
        mentee_id=mentee_id,
        feedback_text=feedback_text,
        feedback_type=feedback_type
    )
    
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    
    return {
        "message": "피드백이 성공적으로 전송되었습니다.",
        "feedback_id": feedback.id
    }


@router.get("/feedback/{mentee_id}")
async def get_feedbacks_for_mentee(
    mentee_id: int,
    current_user: User = Depends(get_current_active_mentor),
    session: Session = Depends(get_session)
):
    """
    특정 멘티에 대한 피드백 목록 조회 (멘토용)
    """
    # 멘토-멘티 관계 확인
    relation_statement = select(MentorMenteeRelation).where(
        MentorMenteeRelation.mentor_id == current_user.id,
        MentorMenteeRelation.mentee_id == mentee_id,
        MentorMenteeRelation.is_active == True
    )
    relation = session.exec(relation_statement).first()
    
    if not relation:
        raise HTTPException(
            status_code=403,
            detail="해당 멘티와의 관계가 없거나 비활성화되어 있습니다."
        )
    
    # 피드백 목록 조회
    feedbacks_statement = (
        select(Feedback)
        .where(Feedback.mentee_id == mentee_id)
        .order_by(Feedback.created_at.desc())
    )
    feedbacks = session.exec(feedbacks_statement).all()
    
    return [
        {
            "id": feedback.id,
            "feedback_text": feedback.feedback_text,
            "feedback_type": feedback.feedback_type,
            "is_read": feedback.is_read,
            "created_at": feedback.created_at.isoformat(),
            "read_at": feedback.read_at.isoformat() if feedback.read_at else None
        }
        for feedback in feedbacks
    ]


@router.get("/mentee/feedbacks")
async def get_mentee_feedbacks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    멘티가 받은 피드백 목록 조회
    """
    # 멘티가 받은 피드백 조회
    feedbacks_statement = (
        select(Feedback)
        .where(Feedback.mentee_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .limit(10)
    )
    feedbacks = session.exec(feedbacks_statement).all()
    
    # 멘토 정보도 함께 조회
    feedback_list = []
    for feedback in feedbacks:
        mentor_statement = select(User).where(User.id == feedback.mentor_id)
        mentor = session.exec(mentor_statement).first()
        
        feedback_list.append({
            "id": feedback.id,
            "feedback_text": feedback.feedback_text,
            "feedback_type": feedback.feedback_type,
            "color_section": feedback.color_section,
            "is_read": feedback.is_read,
            "created_at": feedback.created_at.isoformat(),
            "mentor_name": mentor.name if mentor else "알 수 없음",
            "mentor_team": mentor.team if mentor else None
        })
    
    return feedback_list


@router.put("/feedback/{feedback_id}/read")
async def mark_feedback_as_read(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    피드백을 읽음으로 표시
    """
    feedback_statement = select(Feedback).where(
        Feedback.id == feedback_id,
        Feedback.mentee_id == current_user.id
    )
    feedback = session.exec(feedback_statement).first()
    
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="피드백을 찾을 수 없습니다."
        )
    
    feedback.is_read = True
    feedback.read_at = datetime.utcnow()
    
    session.add(feedback)
    session.commit()
    
    return {"message": "피드백을 읽음으로 표시했습니다."}


# ============ 피드백 댓글 API ============

@router.post("/feedback/{feedback_id}/comments")
async def create_comment(
    feedback_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    피드백에 댓글 작성 (멘토 또는 멘티)
    """
    comment_text = request.get("comment_text")
    
    if not comment_text:
        raise HTTPException(
            status_code=400,
            detail="comment_text는 필수입니다."
        )
    
    # 피드백 존재 여부 확인
    feedback_statement = select(Feedback).where(Feedback.id == feedback_id)
    feedback = session.exec(feedback_statement).first()
    
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="피드백을 찾을 수 없습니다."
        )
    
    # 권한 확인: 피드백의 멘토 또는 멘티만 댓글 작성 가능
    if current_user.id not in [feedback.mentor_id, feedback.mentee_id]:
        raise HTTPException(
            status_code=403,
            detail="이 피드백에 댓글을 작성할 권한이 없습니다."
        )
    
    # 댓글 생성
    comment = FeedbackComment(
        feedback_id=feedback_id,
        user_id=current_user.id,
        comment_text=comment_text
    )
    
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    return {
        "message": "댓글이 성공적으로 작성되었습니다.",
        "comment_id": comment.id
    }


@router.get("/feedback/{feedback_id}/comments")
async def get_comments(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    특정 피드백의 댓글 목록 조회
    """
    # 피드백 존재 및 권한 확인
    feedback_statement = select(Feedback).where(Feedback.id == feedback_id)
    feedback = session.exec(feedback_statement).first()
    
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="피드백을 찾을 수 없습니다."
        )
    
    # 권한 확인
    if current_user.id not in [feedback.mentor_id, feedback.mentee_id]:
        raise HTTPException(
            status_code=403,
            detail="이 피드백의 댓글을 볼 권한이 없습니다."
        )
    
    # 댓글 조회
    comments_statement = (
        select(FeedbackComment)
        .where(
            FeedbackComment.feedback_id == feedback_id,
            FeedbackComment.is_deleted == False
        )
        .order_by(FeedbackComment.created_at.asc())
    )
    comments = session.exec(comments_statement).all()
    
    comment_list = []
    for comment in comments:
        # 작성자 정보 조회
        user_statement = select(User).where(User.id == comment.user_id)
        user = session.exec(user_statement).first()
        
        comment_list.append({
            "id": comment.id,
            "user_id": comment.user_id,
            "user_name": user.name if user else "알 수 없음",
            "user_role": user.role if user else None,
            "comment_text": comment.comment_text,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat()
        })
    
    return {
        "feedback_id": feedback_id,
        "comments": comment_list
    }


@router.delete("/feedback/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    댓글 삭제 (작성자만 가능)
    """
    comment_statement = select(FeedbackComment).where(
        FeedbackComment.id == comment_id
    )
    comment = session.exec(comment_statement).first()
    
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="댓글을 찾을 수 없습니다."
        )
    
    # 권한 확인: 작성자만 삭제 가능
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="댓글을 삭제할 권한이 없습니다."
        )
    
    # Soft delete
    comment.is_deleted = True
    session.add(comment)
    session.commit()
    
    return {"message": "댓글이 성공적으로 삭제되었습니다."}

