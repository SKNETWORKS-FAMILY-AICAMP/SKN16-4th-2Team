#!/bin/bash

# 은행 신입사원 멘토 시스템 설정 스크립트
echo "🚀 은행 신입사원 멘토 시스템 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Docker 설치 확인
print_step "Docker 설치 확인 중..."
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되지 않았습니다. Docker를 먼저 설치해주세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose가 설치되지 않았습니다. Docker Compose를 먼저 설치해주세요."
    exit 1
fi

print_success "Docker 및 Docker Compose가 설치되어 있습니다."

# 2. .env 파일 생성
print_step ".env 파일 생성 중..."
if [ ! -f "backend/.env" ]; then
    cp backend/env.example backend/.env
    print_success ".env 파일이 생성되었습니다."
    print_warning "backend/.env 파일에서 OPENAI_API_KEY를 설정해주세요."
else
    print_success ".env 파일이 이미 존재합니다."
fi

# 3. Docker 컨테이너 빌드 및 실행
print_step "Docker 컨테이너 빌드 및 실행 중..."
docker-compose down
docker-compose up -d --build

# 4. 데이터베이스 초기화 대기
print_step "데이터베이스 초기화 대기 중..."
sleep 10

# 5. 초기 데이터 생성
print_step "초기 데이터 생성 중..."
docker exec cant-backend-1 python -c "from app.init_data import init_all_data; init_all_data()"

# 6. 서비스 상태 확인
print_step "서비스 상태 확인 중..."
echo "백엔드 상태:"
docker-compose ps backend

echo "프론트엔드 상태:"
docker-compose ps frontend

echo "데이터베이스 상태:"
docker-compose ps db

# 7. 완료 메시지
print_success "설정이 완료되었습니다!"
echo ""
echo "🌐 서비스 접속 정보:"
echo "  - 프론트엔드: http://localhost:3000"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - API 문서: http://localhost:8000/docs"
echo ""
echo "🔑 테스트 계정:"
echo "  - 관리자: admin@bank.com / admin123"
echo "  - 멘토: mentor@bank.com / mentor123"
echo "  - 멘티: mentee@bank.com / mentee123"
echo ""
echo "📝 추가 설정:"
echo "  - OpenAI API 키 설정: backend/.env 파일에서 OPENAI_API_KEY 설정"
echo "  - 로그 확인: docker-compose logs -f [service_name]"
echo "  - 서비스 중지: docker-compose down"
echo "  - 서비스 재시작: docker-compose up -d"
