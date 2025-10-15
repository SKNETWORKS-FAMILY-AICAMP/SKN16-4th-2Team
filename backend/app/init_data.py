"""
초기 데이터 생성 스크립트
테스트용 사용자 및 샘플 데이터 생성
"""
from sqlmodel import Session, select
from app.database import engine
from app.models.user import User, UserRole
from app.models.mentor import MentorMenteeRelation, ExamScore
from app.utils.auth import get_password_hash
import json
from datetime import datetime


def create_initial_users(session: Session):
    """초기 사용자 생성"""
    print("Creating initial users...")
    
    # 기존 사용자 확인
    existing_admin = session.exec(select(User).where(User.email == "admin@bank.com")).first()
    if existing_admin:
        print("Users already exist. Skipping...")
        return
    
    users = [
        # 관리자
        User(
            email="admin@bank.com",
            hashed_password=get_password_hash("admin123"),
            name="관리자",
            role=UserRole.ADMIN,
            team="운영팀",
            phone="010-1111-1111"
        ),
        # 멘토
        User(
            email="mentor@bank.com",
            hashed_password=get_password_hash("mentor123"),
            name="김멘토",
            role=UserRole.MENTOR,
            team="영업1팀",
            phone="010-2222-2222",
            interests="금융투자, 리더십",
            hobbies="독서, 테니스",
            encouragement_message="함께 성장해나가요! 언제든 편하게 질문하세요."
        ),
        User(
            email="mentor2@bank.com",
            hashed_password=get_password_hash("mentor123"),
            name="이멘토",
            role=UserRole.MENTOR,
            team="영업2팀",
            phone="010-2222-3333",
            interests="재무분석, 컨설팅",
            hobbies="골프, 영화감상",
            encouragement_message="체계적으로 배워나가면 반드시 성공할 수 있어요!"
        ),
        # 멘티
        User(
            email="mentee@bank.com",
            hashed_password=get_password_hash("mentee123"),
            name="박신입",
            role=UserRole.MENTEE,
            team="영업1팀",
            phone="010-3333-3333",
            interests="디지털금융, 마케팅",
            hobbies="운동, 여행"
        ),
        User(
            email="mentee2@bank.com",
            hashed_password=get_password_hash("mentee123"),
            name="최신입",
            role=UserRole.MENTEE,
            team="영업2팀",
            phone="010-3333-4444",
            interests="고객관리, 상품기획",
            hobbies="그림그리기, 음악감상"
        ),
    ]
    
    for user in users:
        session.add(user)
    
    session.commit()
    print(f"✅ Created {len(users)} users")


def create_mentor_relations(session: Session):
    """멘토-멘티 관계 생성"""
    print("Creating mentor-mentee relations...")
    
    # 기존 관계 확인
    existing_relation = session.exec(select(MentorMenteeRelation)).first()
    if existing_relation:
        print("Relations already exist. Skipping...")
        return
    
    # 멘토와 멘티 조회
    mentor1 = session.exec(select(User).where(User.email == "mentor@bank.com")).first()
    mentor2 = session.exec(select(User).where(User.email == "mentor2@bank.com")).first()
    mentee1 = session.exec(select(User).where(User.email == "mentee@bank.com")).first()
    mentee2 = session.exec(select(User).where(User.email == "mentee2@bank.com")).first()
    
    if not all([mentor1, mentor2, mentee1, mentee2]):
        print("Users not found. Skipping relations...")
        return
    
    relations = [
        MentorMenteeRelation(
            mentor_id=mentor1.id,
            mentee_id=mentee1.id,
            is_active=True,
            notes="같은 팀 배정. 적극적이고 학습 의지가 높음."
        ),
        MentorMenteeRelation(
            mentor_id=mentor2.id,
            mentee_id=mentee2.id,
            is_active=True,
            notes="꼼꼼한 성격. 이론적 학습 선호."
        ),
    ]
    
    for relation in relations:
        session.add(relation)
    
    session.commit()
    print(f"✅ Created {len(relations)} mentor-mentee relations")


def create_exam_scores(session: Session):
    """샘플 시험 점수 생성"""
    print("Creating sample exam scores...")
    
    # 멘티 조회
    mentee1 = session.exec(select(User).where(User.email == "mentee@bank.com")).first()
    mentee2 = session.exec(select(User).where(User.email == "mentee2@bank.com")).first()
    
    if not all([mentee1, mentee2]):
        print("Mentees not found. Skipping exam scores...")
        return
    
    exams = [
        ExamScore(
            mentee_id=mentee1.id,
            exam_name="1차 종합평가",
            exam_date=datetime.utcnow(),
            score_data=json.dumps({
                "은행업무": 85,
                "상품지식": 78,
                "고객응대": 92,
                "법규준수": 88,
                "IT활용": 75,
                "영업실적": 80
            }, ensure_ascii=False),
            total_score=83.0,
            grade="B+",
            feedback="전반적으로 우수합니다. 특히 고객응대 능력이 뛰어납니다. IT 활용 능력을 더 향상시키면 좋겠습니다."
        ),
        ExamScore(
            mentee_id=mentee2.id,
            exam_name="1차 종합평가",
            exam_date=datetime.utcnow(),
            score_data=json.dumps({
                "은행업무": 90,
                "상품지식": 88,
                "고객응대": 82,
                "법규준수": 95,
                "IT활용": 85,
                "영업실적": 78
            }, ensure_ascii=False),
            total_score=86.3,
            grade="A-",
            feedback="이론적 지식이 탄탄합니다. 실제 영업 상황에서의 경험을 더 쌓아보세요."
        ),
    ]
    
    for exam in exams:
        session.add(exam)
    
    session.commit()
    print(f"✅ Created {len(exams)} exam scores")


def init_all_data():
    """모든 초기 데이터 생성"""
    print("\n🚀 Initializing data...\n")
    
    # 먼저 데이터베이스 테이블 생성
    from app.database import init_db
    init_db()
    
    with Session(engine) as session:
        create_initial_users(session)
        create_mentor_relations(session)
        create_exam_scores(session)
    
    print("\n✅ All data initialized successfully!\n")
    print("Test accounts:")
    print("  Admin:  admin@bank.com / admin123")
    print("  Mentor: mentor@bank.com / mentor123")
    print("  Mentee: mentee@bank.com / mentee123")


if __name__ == "__main__":
    init_all_data()

