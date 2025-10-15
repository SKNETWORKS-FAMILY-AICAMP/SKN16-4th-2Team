<<<<<<< HEAD
# 은행 신입사원 멘토 시스템

RAG 기반 LLM 챗봇을 중심으로 한 종합적인 온보딩 플랫폼입니다.

## 프로젝트 개요

이 시스템은 멘토의 지식을 체계화하여 신입사원이 부담 없이 학습할 수 있는 환경을 제공합니다.

## 주요 기능

- **사용자 관리**: 관리자, 멘토, 멘티 역할 기반 시스템
- **RAG 챗봇**: LangChain + OpenAI + pgvector 기반 지능형 챗봇
- **자료실**: 관리자가 업로드한 문서 관리 및 검색
- **익명 게시판**: 완전 익명 보장 대나무숲
- **대시보드**: 멘토/멘티별 맞춤 대시보드 및 분석

## 기술 스택

### 백엔드
- FastAPI
- SQLModel (ORM)
- PostgreSQL + pgvector
- LangChain
- OpenAI API

### 프론트엔드
- React 18
- TypeScript
- Tailwind CSS
- Recharts (데이터 시각화)
- Framer Motion (애니메이션)

## Git 저장소

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git
cd SKN16-4th-2Team
```

**협업 가이드**: [GIT_COLLABORATION_GUIDE.md](./GIT_COLLABORATION_GUIDE.md) 참고

## 설치 및 실행

### Docker Compose 사용 (권장)

```bash
# 프로젝트 클론 후
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API 문서: http://localhost:8000/docs

### 로컬 개발 환경

#### 백엔드

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# .env 파일 수정
uvicorn app.main:app --reload
```

#### 프론트엔드

```bash
cd frontend
npm install
npm start
```

## 프로젝트 구조

```
mentor-system/
├── backend/
│   ├── app/
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── routers/        # API 엔드포인트
│   │   ├── services/       # 비즈니스 로직
│   │   ├── utils/          # 유틸리티 함수
│   │   ├── database.py     # DB 설정
│   │   └── main.py         # FastAPI 앱
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   └── utils/          # 유틸리티
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 기본 계정

시스템 초기화 시 아래 계정이 생성됩니다:

- **관리자**: admin@bank.com / admin123
- **멘토**: mentor@bank.com / mentor123
- **멘티**: mentee@bank.com / mentee123

## 개발 가이드

### API 엔드포인트

- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/chat/` - 챗봇 대화
- `POST /api/documents/upload` - 문서 업로드 (관리자만)
- `GET /api/documents/` - 문서 목록
- `POST /api/posts/` - 게시글 작성
- `GET /api/dashboard/mentee` - 멘티 대시보드
- `GET /api/dashboard/mentor` - 멘토 대시보드

### 보안

- JWT 기반 인증
- bcrypt 비밀번호 해싱
- 역할 기반 접근 제어 (RBAC)
- CORS 설정

## 라이선스

이 프로젝트는 교육용 목적으로 개발되었습니다.


=======
# SKN16-4th-2Team
SKN 16기 4차 단위프로젝트
>>>>>>> ce6c6ebd861ab0f896d1c749fd7e52b7fa2e8de1
