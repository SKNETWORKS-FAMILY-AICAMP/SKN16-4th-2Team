@echo off
chcp 65001 >nul
echo 🔍 FastAPI 멘토 시스템 문제 진단을 시작합니다...
echo ========================================

REM 1. Docker 상태 확인
echo.
echo 1. 🐳 Docker 컨테이너 상태 확인
echo -----------------------------------
docker --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Docker 설치됨
    docker-compose ps
    
    REM PostgreSQL 컨테이너 확인
    docker-compose ps | findstr "postgres" >nul
    if %errorLevel% == 0 (
        echo ✅ PostgreSQL 컨테이너 실행 중
        
        REM 데이터베이스 연결 테스트
        echo 🔗 데이터베이스 연결 테스트 중...
        docker-compose exec postgres pg_isready -U mentoruser -d mentordb >nul 2>&1
        if %errorLevel% == 0 (
            echo ✅ 데이터베이스 연결 성공
        ) else (
            echo ❌ 데이터베이스 연결 실패
        )
    ) else (
        echo ❌ PostgreSQL 컨테이너가 실행되지 않음
    )
) else (
    echo ❌ Docker가 설치되지 않음
)

REM 2. Docker 볼륨 확인
echo.
echo 2. 💾 Docker 볼륨 상태 확인
echo -----------------------------------
docker volume ls | findstr "postgres" >nul
if %errorLevel% == 0 (
    echo ✅ PostgreSQL 볼륨 존재
    for /f %%i in ('docker volume ls -q ^| findstr postgres') do (
        docker volume inspect %%i | findstr "Mountpoint"
    )
) else (
    echo ❌ PostgreSQL 볼륨이 존재하지 않음
)

REM 3. 사용자 데이터 확인
echo.
echo 3. 👥 사용자 데이터 확인
echo -----------------------------------
docker-compose ps | findstr "postgres" >nul
if %errorLevel% == 0 (
    echo 관리자 계정 확인 중...
    docker-compose exec postgres psql -U mentoruser -d mentordb -c "SELECT email, name, role FROM users WHERE email = 'admin@bank.com';" >nul 2>&1
    if %errorLevel% == 0 (
        echo ✅ 관리자 계정 데이터 확인
        docker-compose exec postgres psql -U mentoruser -d mentordb -c "SELECT email, name, role FROM users WHERE email = 'admin@bank.com';"
    ) else (
        echo ❌ 관리자 계정 데이터 없음
        echo 💡 초기 데이터 생성 필요: python -m app.init_data
    )
    
    echo.
    echo 전체 사용자 수 확인...
    docker-compose exec postgres psql -U mentoruser -d mentordb -c "SELECT COUNT(*) as user_count FROM users;" 2>nul
) else (
    echo ❌ PostgreSQL 컨테이너가 실행되지 않아 확인 불가
)

REM 4. 환경 변수 확인
echo.
echo 4. ⚙️ 환경 변수 확인
echo -----------------------------------
if exist "backend\.env" (
    echo ✅ .env 파일 존재
    findstr "OPENAI_API_KEY=" backend\.env >nul
    if %errorLevel% == 0 (
        findstr "OPENAI_API_KEY=your_openai_api_key_here" backend\.env >nul
        if %errorLevel% == 0 (
            echo ⚠️ OPENAI_API_KEY가 기본값입니다. 실제 키로 변경 필요
        ) else (
            echo ✅ OPENAI_API_KEY 설정됨
        )
    ) else (
        echo ❌ OPENAI_API_KEY 설정되지 않음
    )
) else (
    echo ❌ .env 파일이 존재하지 않음
    echo 💡 backend\.env.example을 복사해서 backend\.env로 만드세요
)

REM 5. 백엔드 서비스 상태
echo.
echo 5. 🚀 백엔드 서비스 상태
echo -----------------------------------
docker-compose ps | findstr "backend" >nul
if %errorLevel% == 0 (
    echo ✅ 백엔드 컨테이너 실행 중
    
    REM API 응답 테스트
    echo API 응답 테스트 중...
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorLevel% == 0 (
        echo ✅ API 서버 응답 정상
        echo 📱 API 문서: http://localhost:8000/docs
    ) else (
        echo ❌ API 서버 응답 없음
        echo 📋 로그 확인: docker-compose logs backend
    )
) else (
    echo ❌ 백엔드 컨테이너가 실행되지 않음
)

REM 6. 추천 해결 방안
echo.
echo 6. 💡 추천 해결 방안
echo -----------------------------------

docker volume ls | findstr "postgres" >nul
if %errorLevel% == 0 (
    docker-compose exec postgres psql -U mentoruser -d mentordb -c "SELECT COUNT(*) FROM users;" 2>nul | findstr " 0" >nul
    if %errorLevel% == 0 (
        echo 🔧 해결방안 1: 초기 데이터 생성
        echo    docker-compose exec backend python -m app.init_data
    )
) else (
    echo 🔧 해결방안 1: 완전 재시작
    echo    docker-compose down -v
    echo    docker-compose up -d
)

echo.
echo 🔧 해결방안 2: 로그 확인
echo    docker-compose logs backend
echo    docker-compose logs postgres

echo.
echo 🔧 해결방안 3: 수동 초기화
echo    1. docker-compose down -v
echo    2. docker volume prune -f
echo    3. docker-compose up -d

echo.
echo 🔧 해결방안 4: setup.bat 재실행
echo    .\setup.bat

echo.
echo ========================================
echo 🏁 진단 완료
echo.
echo 📞 추가 지원이 필요하면 README.md를 확인하거나
echo     개발팀에 문의하세요.
echo.
pause
