@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 은행 신입사원 멘토 시스템 설정 스크립트 (Windows)
echo 🚀 은행 신입사원 멘토 시스템 설정을 시작합니다...

REM 1. Docker 설치 확인
echo 📋 Docker 설치 확인 중...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 설치되지 않았습니다. Docker Desktop을 먼저 설치해주세요.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose가 설치되지 않았습니다. Docker Desktop을 먼저 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Docker 및 Docker Compose가 설치되어 있습니다.

REM 2. .env 파일 생성
echo 📋 .env 파일 생성 중...
if not exist "backend\.env" (
    copy "backend\env.example" "backend\.env" >nul
    echo ✅ .env 파일이 생성되었습니다.
    echo ⚠️  backend\.env 파일에서 OPENAI_API_KEY를 설정해주세요.
) else (
    echo ✅ .env 파일이 이미 존재합니다.
)

REM 3. Docker 컨테이너 빌드 및 실행
echo 📋 Docker 컨테이너 빌드 및 실행 중...
docker-compose down
docker-compose up -d --build

REM 4. 데이터베이스 초기화 대기
echo 📋 데이터베이스 초기화 대기 중...
timeout /t 10 /nobreak >nul

REM 5. 초기 데이터 생성
echo 📋 초기 데이터 생성 중...
docker exec cant-backend-1 python -c "from app.init_data import init_all_data; init_all_data()"

REM 6. 서비스 상태 확인
echo 📋 서비스 상태 확인 중...
echo 백엔드 상태:
docker-compose ps backend

echo 프론트엔드 상태:
docker-compose ps frontend

echo 데이터베이스 상태:
docker-compose ps db

REM 7. 완료 메시지
echo ✅ 설정이 완료되었습니다!
echo.
echo 🌐 서비스 접속 정보:
echo   - 프론트엔드: http://localhost:3000
echo   - 백엔드 API: http://localhost:8000
echo   - API 문서: http://localhost:8000/docs
echo.
echo 🔑 테스트 계정:
echo   - 관리자: admin@bank.com / admin123
echo   - 멘토: mentor@bank.com / mentor123
echo   - 멘티: mentee@bank.com / mentee123
echo.
echo 📝 추가 설정:
echo   - OpenAI API 키 설정: backend\.env 파일에서 OPENAI_API_KEY 설정
echo   - 로그 확인: docker-compose logs -f [service_name]
echo   - 서비스 중지: docker-compose down
echo   - 서비스 재시작: docker-compose up -d

pause
