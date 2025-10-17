#!/bin/bash

echo "🔧 서버 디렉토리 권한 설정 중..."

# 서버 디렉토리 생성 및 권한 설정
mkdir -p ./postgres_data
mkdir -p ./uploads

# 권한 설정 (777로 설정하여 Docker 컨테이너에서 접근 가능하도록)
chmod 777 ./uploads
chmod 777 ./postgres_data

echo "✅ 권한 설정 완료!"
echo "📁 업로드 디렉토리: ./uploads"
echo "🗄️ 데이터베이스 디렉토리: ./postgres_data"

# 현재 권한 확인
echo ""
echo "📋 현재 권한 상태:"
ls -la | grep -E "(uploads|postgres_data)"
