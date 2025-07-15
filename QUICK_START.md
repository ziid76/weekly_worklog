# 🚀 빠른 시작 가이드

업무관리시스템을 5분 안에 시작해보세요!

## ⚡ 1분 설치

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd gemini

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 데이터베이스 설정
python manage.py migrate

# 5. 관리자 계정 생성
python manage.py createsuperuser

# 6. 서버 실행
python manage.py runserver
```

## 🎯 첫 사용 (3분)

### 1단계: 로그인 및 프로필 설정
1. http://127.0.0.1:8000 접속
2. 생성한 관리자 계정으로 로그인
3. 우상단 사용자 메뉴 → "프로필 편집"
4. 표시 이름 설정

### 2단계: 카테고리 생성
1. 사이드바 → "카테고리"
2. "새 카테고리 추가" 클릭
3. 예시 카테고리 생성:
   - 개발 (파란색)
   - 기획 (초록색)
   - 디자인 (보라색)

### 3단계: 첫 업무 등록
1. 대시보드 → "새 업무" 버튼
2. 업무 정보 입력:
   ```
   제목: [개발] 로그인 기능 구현
   설명: 사용자 인증 시스템 개발
   우선순위: 높음
   카테고리: 개발
   마감일: 이번 주 금요일
   ```
3. "저장하기" 클릭

## 📅 첫 워크로그 작성 (1분)

1. 사이드바 → "워크로그"
2. "새 워크로그 작성" 클릭
3. 현재 주차 정보 자동 설정 확인
4. 이번 주 내용 작성:
   ```markdown
   ## 이번 주 수행 업무
   - 업무관리시스템 설치 및 설정 완료
   - 첫 번째 업무 등록
   - 시스템 사용법 학습
   
   ## 다음 주 계획
   - 실제 업무 데이터 입력
   - 팀원들과 시스템 공유
   ```
5. "저장하기" 클릭

## 🎉 완료!

축하합니다! 이제 다음 기능들을 사용할 수 있습니다:

### ✅ 즉시 사용 가능한 기능
- **대시보드**: 업무 현황 한눈에 보기
- **업무 관리**: 업무 생성, 수정, 상태 변경
- **워크로그**: 주간 업무 기록 (7월 1주차 형식)
- **검색**: 상단 검색바로 빠른 검색
- **필터링**: 상태, 우선순위별 필터

### 🔄 일상 업무 흐름
1. **월요일**: 이번 주 워크로그 작성
2. **매일**: 업무 상태 업데이트
3. **금요일**: 주간 성과 정리

### 💡 유용한 팁
- **Ctrl+K**: 빠른 검색
- **마크다운**: 워크로그에서 `**굵게**`, `*기울임*` 사용
- **우선순위**: 긴급(빨강) > 높음(주황) > 보통(노랑) > 낮음(초록)
- **월별 주차**: 자동으로 "7월 1주차" 형식 표시

## 🆘 문제 해결

### 서버가 시작되지 않을 때
```bash
# 포트 변경
python manage.py runserver 8001

# 마이그레이션 재실행
python manage.py migrate
```

### 정적 파일이 로드되지 않을 때
```bash
python manage.py collectstatic
```

### 관리자 계정을 잊었을 때
```bash
python manage.py createsuperuser
```

## 📚 더 자세한 정보

- 전체 기능: [README.md](README.md)
- 디자인 가이드: [TEMPLATE_CONSISTENCY.md](TEMPLATE_CONSISTENCY.md)
- 오류 해결: [ERROR_FIXES_AND_IMPROVEMENTS.md](ERROR_FIXES_AND_IMPROVEMENTS.md)

---

**5분 만에 시작 완료!** 이제 효율적인 업무 관리를 시작하세요! 🎯
