# 🚀 Git 협업 가이드 (초보자용)

> SKN16-4th-2Team 프로젝트 협업 매뉴얼

## 📋 목차
1. [처음 시작하기](#1-처음-시작하기)
2. [일상적인 작업 흐름](#2-일상적인-작업-흐름)
3. [브랜치 전략](#3-브랜치-전략)
4. [충돌 해결하기](#4-충돌-해결하기)
5. [자주 사용하는 명령어](#5-자주-사용하는-명령어)
6. [주의사항](#6-주의사항)

---

## 1. 처음 시작하기

### 1-1. 프로젝트 클론하기
처음 작업을 시작하는 팀원은 아래 명령어로 프로젝트를 다운로드하세요.

```bash
# 원하는 폴더로 이동한 후
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team.git

# 프로젝트 폴더로 이동
cd SKN16-4th-2Team
```

### 1-2. Git 사용자 정보 설정
```bash
# 자신의 이름과 이메일 설정 (최초 1회만)
git config --global user.name "본인이름"
git config --global user.email "본인이메일@example.com"
```

---

## 2. 일상적인 작업 흐름

### ✨ 기본 원칙
**절대 main 브랜치에서 직접 작업하지 마세요!**  
항상 자신만의 브랜치를 만들어서 작업합니다.

### 📝 작업 시작 전 체크리스트

```bash
# 1️⃣ main 브랜치로 이동
git checkout main

# 2️⃣ 최신 코드 받아오기
git pull origin main

# 3️⃣ 새로운 브랜치 만들기 (기능 이름으로)
git checkout -b feature/로그인기능
# 예시: feature/dashboard, feature/chat, fix/login-bug
```

### 💻 작업 중

```bash
# 작업하면서 수시로 저장
git add .
git commit -m "로그인 UI 작성 완료"

# 여러 번 커밋해도 괜찮아요!
git commit -m "로그인 API 연동"
git commit -m "에러 처리 추가"
```

### ✅ 작업 완료 후

```bash
# 1️⃣ 내 브랜치를 GitHub에 올리기
git push origin feature/로그인기능

# 2️⃣ GitHub 웹사이트에서 Pull Request(PR) 생성
# - https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-2Team/pulls
# - "New Pull Request" 버튼 클릭
# - 내 브랜치 선택 → main으로 합치기 요청
# - 제목과 설명 작성

# 3️⃣ PM(또는 다른 팀원)이 코드 리뷰 후 승인하면 merge
```

---

## 3. 브랜치 전략

### 브랜치 이름 규칙

```
feature/기능명    - 새로운 기능 개발
fix/버그명       - 버그 수정
docs/문서명      - 문서 작업
refactor/내용    - 코드 개선
```

### 예시
- `feature/anonymous-board` - 익명 게시판 기능
- `feature/chat-bot` - 챗봇 기능
- `fix/login-error` - 로그인 오류 수정
- `docs/readme-update` - README 업데이트

---

## 4. 충돌 해결하기

### 충돌이 발생하는 경우
여러 명이 같은 파일의 같은 부분을 수정했을 때 발생합니다.

### 해결 방법

```bash
# 1️⃣ main 브랜치의 최신 코드 가져오기
git checkout main
git pull origin main

# 2️⃣ 내 브랜치로 돌아가기
git checkout feature/내브랜치

# 3️⃣ main의 변경사항 가져오기
git merge main

# 4️⃣ 충돌이 발생하면 파일을 열어서 수정
# VS Code에서 충돌 부분이 표시됩니다
# <<<<<<< HEAD
# 내 코드
# =======
# 다른 사람 코드
# >>>>>>> main

# 5️⃣ 충돌 해결 후 다시 커밋
git add .
git commit -m "충돌 해결"
git push origin feature/내브랜치
```

---

## 5. 자주 사용하는 명령어

### 기본 명령어

```bash
# 현재 상태 확인
git status

# 변경사항 확인
git diff

# 커밋 이력 보기
git log --oneline

# 브랜치 목록 보기
git branch -a

# 브랜치 전환
git checkout 브랜치명

# 최신 코드 받기
git pull

# 코드 올리기
git push
```

### Git Graph 명령어

```bash
# 그래프로 히스토리 보기 (간단)
git lg

# 그래프로 히스토리 보기 (상세)
git log --oneline --graph --all --decorate

# 최근 10개 커밋만 그래프로 보기
git log --oneline --graph --all --decorate -10
```

### 실수했을 때

```bash
# 마지막 커밋 메시지 수정
git commit --amend -m "새로운 메시지"

# 파일 추가 취소 (add 취소)
git reset HEAD 파일명

# 변경사항 버리기 (조심!)
git checkout -- 파일명

# 마지막 커밋 취소 (변경사항은 유지)
git reset --soft HEAD~1
```

---

## 6. 주의사항

### ⚠️ 절대 하지 말 것

1. **main 브랜치에서 직접 작업하지 마세요**
   ```bash
   # ❌ 나쁜 예
   git checkout main
   # 파일 수정...
   git add .
   git commit -m "작업"
   git push
   ```

2. **`git push -f` (force push) 사용 금지**
   - 다른 사람의 작업을 날릴 수 있습니다!

3. **민감한 정보 커밋 금지**
   - API 키, 비밀번호, `.env` 파일 등

### ✅ 좋은 습관

1. **자주 커밋하기**
   - 작은 단위로 자주 커밋하는 것이 좋습니다

2. **의미 있는 커밋 메시지**
   ```bash
   # ✅ 좋은 예
   git commit -m "로그인 폼 유효성 검사 추가"
   git commit -m "대시보드 차트 렌더링 성능 개선"
   
   # ❌ 나쁜 예
   git commit -m "수정"
   git commit -m "ㅇㅇ"
   ```

3. **작업 시작 전 pull 받기**
   ```bash
   git checkout main
   git pull origin main
   ```

4. **하루에 한 번은 push 하기**
   - 작업한 내용을 GitHub에 올려두면 백업도 되고 팀원들도 확인할 수 있습니다

---

## 🆘 도움이 필요할 때

### 명령어가 막혔을 때
```bash
# 현재 상태 확인
git status

# 문제가 있으면 팀에 공유하기
```

### 자주 묻는 질문 (FAQ)

**Q: 브랜치를 삭제하고 싶어요**
```bash
# 로컬 브랜치 삭제
git branch -d feature/완료한기능

# 원격 브랜치 삭제
git push origin --delete feature/완료한기능
```

**Q: 다른 브랜치의 특정 커밋만 가져오고 싶어요**
```bash
git cherry-pick 커밋해시
```

**Q: 잘못된 브랜치에서 작업했어요**
```bash
# 변경사항을 임시 저장
git stash

# 올바른 브랜치로 이동
git checkout 올바른브랜치

# 변경사항 복원
git stash pop
```

---

## 📊 Git Graph 사용법

### VS Code에서 Git Graph 보기

1. **VS Code 좌측 사이드바** → **Source Control** (또는 `Ctrl+Shift+G`)
2. **"Git Graph"** 버튼 클릭
3. 브랜치와 커밋이 시각적으로 표시됩니다!

### 터미널에서 Git Graph 보기

```bash
# 간단한 그래프 (별칭 사용)
git lg

# 상세한 그래프
git log --oneline --graph --all --decorate

# 최근 10개 커밋만
git log --oneline --graph --all --decorate -10
```

### Git Graph의 장점

- ✅ **브랜치 분기/병합** 한눈에 파악
- ✅ **팀원들의 작업 진행상황** 추적
- ✅ **충돌 지점** 쉽게 찾기
- ✅ **커밋 히스토리** 시각적 확인

---

## 📞 연락처

문제가 생기면 PM에게 연락하세요!

**행복한 협업 되세요! 🎉**

