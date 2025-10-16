-- PostgreSQL 초기화 스크립트
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 데이터베이스 설정
ALTER DATABASE mentordb SET timezone TO 'Asia/Seoul';

-- 사용자 권한 설정
GRANT ALL PRIVILEGES ON DATABASE mentordb TO mentoruser;
