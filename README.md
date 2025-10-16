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

## 👥 팀원들을 위한 빠른 시작

### 🎯 처음 설정하는 팀원

```bash
# 1. 프로젝트 클론
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git
cd SKN16-4th-2Team

# 2. 시스템 시작 (모든 것이 자동으로 설정됩니다!)
docker-compose up -d

# 3. 잠시 기다린 후 브라우저에서 접속
# - 프론트엔드: http://localhost:3000
# - API 문서: http://localhost:8000/docs

# 4. 테스트 계정으로 로그인
# - 관리자: admin@bank.com / admin123
# - 멘토: mentor@bank.com / mentor123
# - 멘티: mentee@bank.com / mentee123
```

### 🔄 기존 환경 업데이트하는 팀원

```bash
# 1. 기존 컨테이너 정리
docker-compose down -v

# 2. 최신 코드 가져오기
git pull origin main

# 3. 새로운 설정으로 시작
docker-compose up -d
```

### 🚨 문제가 발생한 경우

```bash
# 자동 진단 도구 실행
.\diagnose.bat

# 또는 수동으로 초기 데이터 재생성
docker-compose exec backend python -m app.init_data
```

## 🚀 빠른 시작

### ⚡ 가장 빠른 방법 (Docker 사용)

```bash
# 1. 프로젝트 클론
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git
cd SKN16-4th-2Team

# 2. 시스템 시작 (자동으로 초기 데이터 생성됨!)
docker-compose up -d

# 3. 브라우저에서 접속
# - 프론트엔드: http://localhost:3000
# - API 문서: http://localhost:8000/docs
```

### 자동 설정 (권장)

**Windows:**
```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git
cd SKN16-4th-2Team
setup.bat
```

**Linux/Mac:**
```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git
cd SKN16-4th-2Team
chmod +x setup.sh
./setup.sh
```

### 수동 설정

#### 1. 환경 변수 설정
```bash
# .env 파일 생성
cp backend/env.example backend/.env

# .env 파일에서 OPENAI_API_KEY 설정 (선택사항)
# nano backend/.env
```

#### 2. Docker로 실행
```bash
docker-compose up -d --build
```

#### 3. 자동 초기화
시스템이 자동으로 초기 데이터를 생성합니다! 별도 실행 불필요.

## 🌐 서비스 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **pgAdmin** (개발환경): http://localhost:5050

## 🔑 테스트 계정

- **관리자**: admin@bank.com / admin123
- **멘토**: mentor@bank.com / mentor123
- **멘티**: mentee@bank.com / mentee123

## 📁 프로젝트 구조

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
│   ├── env.example         # 환경 변수 템플릿
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── store/          # 상태 관리
│   │   └── utils/          # 유틸리티
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── init-db.sql            # PostgreSQL 초기화 스크립트
├── setup.sh               # Linux/Mac 설정 스크립트
├── setup.bat              # Windows 설정 스크립트
├── diagnose.bat           # 시스템 진단 도구
└── CHANGELOG.md           # 변경사항 기록
```

## 🔧 개발 가이드

### API 엔드포인트

- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인
- `GET /auth/me` - 현재 사용자 정보
- `POST /chat/` - 챗봇 대화
- `POST /documents/upload` - 문서 업로드 (관리자만)
- `GET /documents/` - 문서 목록
- `POST /posts/` - 게시글 작성
- `GET /dashboard/mentee` - 멘티 대시보드
- `GET /dashboard/mentor` - 멘토 대시보드

### 보안

- JWT 기반 인증
- bcrypt 비밀번호 해싱
- 역할 기반 접근 제어 (RBAC)
- CORS 설정

## 🛠️ 문제 해결

### 자동 진단 도구
```bash
# Windows
.\diagnose.bat

# 시스템 상태를 자동으로 진단하고 해결방안을 제시합니다
```

### 자주 발생하는 문제

1. **CSP 오류**: 브라우저에서 `unsafe-eval` 오류가 발생하는 경우
   - 해결: 브라우저 캐시 삭제 후 새로고침

2. **데이터베이스 연결 실패**: PostgreSQL 연결 오류
   - 해결: `docker-compose down -v && docker-compose up -d --build`

3. **로그인 실패**: 테스트 계정으로 로그인이 안 되는 경우
   - 해결: `docker-compose exec backend python -m app.init_data`

4. **포트 충돌**: 5432 포트가 이미 사용 중인 경우
   - 해결: `docker-compose down -v` 후 재시작

### 로그 확인

```bash
# 백엔드 로그
docker-compose logs -f backend

# 프론트엔드 로그
docker-compose logs -f frontend

# 데이터베이스 로그
docker-compose logs -f postgres
```

### 개발 환경 도구

```bash
# pgAdmin 실행 (데이터베이스 관리 UI)
docker-compose --profile dev up -d

# 접속: http://localhost:5050
# 이메일: admin@admin.com
# 비밀번호: admin
```

## 🆕 최신 업데이트 (v2.0)

### ✨ 새로운 기능들

- **자동 초기화 시스템**: 컨테이너 시작 시 자동으로 초기 데이터 생성
- **데이터 지속성 보장**: 컨테이너 재시작 시에도 데이터 유지
- **진단 도구**: `diagnose.bat`으로 시스템 상태 자동 진단
- **개발 환경 도구**: pgAdmin 추가로 데이터베이스 관리 편의성 향상
- **포트 최적화**: PostgreSQL 포트를 표준 5432로 변경

### 🔧 주요 개선사항

- **관리자 로그인 문제 완전 해결**
- **중복 생성 방지 로직 강화**
- **데이터 무결성 검증 추가**
- **사용자 친화적 에러 메시지**

### 📋 마이그레이션 가이드

기존 환경에서 업데이트하는 경우:

```bash
# 1. 기존 컨테이너 정리
docker-compose down -v

# 2. 최신 코드 가져오기
git pull origin main

# 3. 새로운 설정으로 시작
docker-compose up -d
```

## 📚 추가 문서

- [협업 가이드](./GIT_COLLABORATION_GUIDE.md)
- [보안 가이드](./SECURITY.md)
- [시작 가이드](./START_HERE.md)
- [변경사항 기록](./CHANGELOG.md)

## 라이선스

이 프로젝트는 교육용 목적으로 개발되었습니다.
