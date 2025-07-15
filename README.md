# 업무관리시스템 (Work Management System)

네이버 디자인을 참고한 직관적이고 효율적인 업무 관리 시스템입니다.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.1+-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 목차

- [주요 기능](#주요-기능)
- [시스템 구조](#시스템-구조)
- [설치 및 실행](#설치-및-실행)
- [사용법](#사용법)
- [기능별 상세 가이드](#기능별-상세-가이드)
- [디자인 시스템](#디자인-시스템)
- [API 문서](#api-문서)
- [개발 가이드](#개발-가이드)
- [문제 해결](#문제-해결)
- [기여하기](#기여하기)

## 🚀 주요 기능

### 📊 대시보드
- **실시간 업무 현황** 통계 카드로 한눈에 파악
- **우선순위별 업무 분포** 시각적 표시
- **최근 활동 타임라인** 업무 진행 상황 추적
- **빠른 작업** 버튼으로 즉시 업무 생성

### 📝 업무 관리 (Task Management)
- **업무 생성/수정/삭제** 완전한 CRUD 기능
- **우선순위 설정** (긴급/높음/보통/낮음)
- **상태 관리** (대기/진행중/완료/중단)
- **카테고리 분류** 업무 체계적 관리
- **마감일 설정** 일정 관리
- **담당자 지정** 협업 지원
- **댓글 시스템** 업무별 소통
- **파일 첨부** 관련 자료 관리
- **검색 및 필터링** 빠른 업무 찾기

### 📅 워크로그 (Work Log)
- **주간 업무 기록** 체계적 업무 일지
- **월별 주차 표시** (예: 7월 1주차) 직관적 표시
- **마크다운 지원** 풍부한 텍스트 편집
- **이번 주 성과** 및 **다음 주 계획** 구분 기록
- **파일 첨부** 업무 관련 자료 보관
- **타임라인 뷰** 시간순 업무 기록 확인

### 📈 리포트 (Reports)
- **주간 리포트 생성** 자동화된 업무 요약
- **팀 워크로그 요약** 팀 단위 업무 현황
- **통계 분석** 업무 효율성 측정
- **PDF 내보내기** 보고서 공유

### 👥 사용자 관리 (User Management)
- **프로필 관리** 개인 정보 설정
- **권한 관리** 역할별 접근 제어
- **팀 관리** 조직 구조 반영
- **알림 시스템** 실시간 업데이트

## 🏗️ 시스템 구조

```
gemini/
├── 📁 accounts/          # 사용자 계정 관리
├── 📁 config/            # Django 설정
├── 📁 dashboard/         # 대시보드 기능
├── 📁 notifications/     # 알림 시스템
├── 📁 reports/           # 리포트 생성
├── 📁 static/            # 정적 파일 (CSS, JS, 이미지)
│   ├── 📁 css/
│   │   └── naver-style.css
│   └── 📁 js/
│       └── app.js
├── 📁 task/              # 업무 관리
├── 📁 teams/             # 팀 관리
├── 📁 templates/         # HTML 템플릿
│   ├── base.html
│   ├── base_simple.html
│   └── 📁 dashboard/
├── 📁 worklog/           # 워크로그 관리
├── 📄 manage.py          # Django 관리 스크립트
└── 📄 requirements.txt   # 의존성 패키지
```

## 🛠️ 설치 및 실행

### 시스템 요구사항
- Python 3.8 이상
- Django 5.1 이상
- SQLite (기본) 또는 PostgreSQL/MySQL

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd gemini
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 설정
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 관리자 계정 생성
```bash
python manage.py createsuperuser
```

### 6. 서버 실행
```bash
python manage.py runserver
```

### 7. 브라우저에서 접속
```
http://127.0.0.1:8000
```

## 📖 사용법

### 첫 로그인 후 설정

1. **프로필 설정**
   - 우상단 사용자 메뉴 → "프로필 편집"
   - 표시 이름, 연락처 등 개인 정보 입력

2. **카테고리 생성**
   - 사이드바 → "카테고리"
   - 업무 분류를 위한 카테고리 생성 (예: 개발, 기획, 디자인)

3. **첫 업무 등록**
   - 대시보드 → "새 업무" 버튼
   - 제목, 설명, 우선순위, 마감일 설정

### 일상적인 업무 흐름

#### 📅 주간 업무 계획
1. **월요일**: 이번 주 워크로그 작성
   - "워크로그" → "새 워크로그 작성"
   - 이번 주 계획 및 목표 기록

2. **업무 진행 중**: 상태 업데이트
   - 업무 상세 페이지에서 "시작하기" 버튼
   - 진행 상황에 따라 상태 변경

3. **금요일**: 주간 마무리
   - 워크로그에 이번 주 성과 기록
   - 다음 주 계획 업데이트

## 🎯 기능별 상세 가이드

### 📊 대시보드 활용

#### 통계 카드 읽기
- **전체 업무**: 등록된 모든 업무 수
- **대기중 업무**: 아직 시작하지 않은 업무
- **진행중 업무**: 현재 작업 중인 업무
- **완료된 업무**: 성공적으로 완료된 업무

#### 빠른 작업 활용
- **새 업무 등록**: 즉시 업무 생성
- **워크로그 작성**: 주간 업무 기록
- **주간 리포트 작성**: 업무 요약 보고서

### 📝 업무 관리 마스터하기

#### 효과적인 업무 작성법
```markdown
제목: [카테고리] 구체적인 업무 내용
예시: [개발] 사용자 로그인 기능 구현

설명:
- 목적: 사용자 인증 시스템 구축
- 요구사항:
  * 이메일/비밀번호 로그인
  * 소셜 로그인 (구글, 네이버)
  * 비밀번호 찾기 기능
- 완료 기준: 테스트 통과 및 배포 완료
```

#### 우선순위 설정 가이드
- **🔴 긴급**: 즉시 처리 필요, 서비스 장애 등
- **🟠 높음**: 이번 주 내 완료 필요
- **🟡 보통**: 2주 내 완료 목표
- **🟢 낮음**: 여유 있을 때 처리

#### 상태 관리 워크플로우
```
대기 → 진행중 → 완료
  ↓       ↓
 중단 ← 중단
```

### 📅 워크로그 작성 가이드

#### 효과적인 워크로그 구조
```markdown
## 이번 주 수행 업무

### 주요 성과
- **[프로젝트명]** 기능 A 개발 완료 (80% → 100%)
- **[프로젝트명]** 버그 수정 3건 처리
- **팀 미팅** 주간 진행 상황 공유

### 이슈 및 해결방안
- **이슈**: 외부 API 연동 지연
- **해결**: 대체 API 검토 및 적용 예정

### 학습 및 개선사항
- React Hook 사용법 학습
- 코드 리뷰 프로세스 개선 제안

## 다음 주 계획

### 우선순위 업무
1. 기능 B 개발 착수
2. 성능 최적화 작업
3. 문서화 작업

### 목표
- 기능 B 50% 진행
- 응답 속도 20% 개선
```

#### 마크다운 활용 팁
- **굵은 글씨**: `**중요한 내용**`
- *기울임*: `*강조할 내용*`
- 목록: `- 항목` 또는 `1. 번호 목록`
- 코드: `` `코드` `` 또는 ```코드 블록```
- 링크: `[텍스트](URL)`

### 📈 리포트 활용

#### 주간 리포트 생성
1. "리포트" → "주간 리포트 작성"
2. 해당 주차 선택
3. 자동 생성된 데이터 확인 및 보완
4. PDF 내보내기로 공유

#### 팀 워크로그 요약
- 팀원들의 주간 업무 현황 통합 확인
- 프로젝트별 진행 상황 파악
- 리소스 배분 최적화 참고 자료

## 🎨 디자인 시스템

### 네이버 스타일 적용
- **색상**: 네이버 그린 (#03C75A) 기반 팔레트
- **타이포그래피**: Noto Sans KR 폰트
- **아이콘**: Font Awesome 6.4.0
- **레이아웃**: 반응형 그리드 시스템

### 일관된 UI 컴포넌트
- **버튼**: 그라데이션 효과 및 호버 애니메이션
- **카드**: 부드러운 그림자 및 상승 효과
- **폼**: 네이버 그린 포커스 컬러
- **테이블**: 깔끔한 행 구분 및 호버 효과

### 접근성 고려사항
- 키보드 네비게이션 지원
- 스크린 리더 친화적 구조
- 충분한 색상 대비 (4.5:1)
- 의미 있는 alt 텍스트

## 🔧 API 문서

### 업무 관리 API
```python
# 업무 목록 조회
GET /task/

# 업무 생성
POST /task/create/

# 업무 상세 조회
GET /task/<id>/

# 업무 수정
PUT /task/<id>/update/

# 업무 삭제
DELETE /task/<id>/delete/

# 업무 상태 변경
POST /task/<id>/status/
```

### 워크로그 API
```python
# 워크로그 목록
GET /worklog/

# 워크로그 생성
POST /worklog/create/

# 사용자 업무 목록 (AJAX)
GET /worklog/api/tasks/

# 업무 추가 (AJAX)
POST /worklog/api/add-task/
```

## 👨‍💻 개발 가이드

### 개발 환경 설정
```bash
# 개발 서버 실행 (디버그 모드)
python manage.py runserver --settings=config.settings.dev

# 테스트 실행
python manage.py test

# 코드 스타일 검사
flake8 .

# 정적 파일 수집 (배포 시)
python manage.py collectstatic
```

### 새로운 앱 추가
```bash
# 새 앱 생성
python manage.py startapp new_app

# settings.py에 앱 추가
INSTALLED_APPS = [
    ...
    'new_app',
]

# URL 패턴 추가
# config/urls.py
path('new_app/', include('new_app.urls')),
```

### 데이터베이스 마이그레이션
```bash
# 마이그레이션 파일 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 마이그레이션 상태 확인
python manage.py showmigrations
```

### 커스텀 템플릿 태그
```python
# templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def priority_color(priority):
    colors = {
        'urgent': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'success'
    }
    return colors.get(priority, 'secondary')
```

## 🔍 문제 해결

### 자주 발생하는 문제

#### 1. 서버 실행 오류
```bash
# 포트 충돌 시
python manage.py runserver 8001

# 마이그레이션 필요 시
python manage.py migrate
```

#### 2. 정적 파일 로딩 실패
```bash
# 개발 환경에서
python manage.py collectstatic

# settings.py 확인
DEBUG = True
STATIC_URL = '/static/'
```

#### 3. 템플릿 오류
- 템플릿 경로 확인: `templates/app_name/template.html`
- 상속 구조 확인: `{% extends 'base.html' %}`
- 블록 태그 닫힘 확인: `{% endblock %}`

#### 4. URL 패턴 오류
```python
# urls.py에서 이름 확인
path('tasks/', views.TaskListView.as_view(), name='task_list'),

# 템플릿에서 올바른 참조
{% url 'task_list' %}
```

### 로그 확인
```python
# settings.py에 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🚀 배포 가이드

### 프로덕션 설정
```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 보안 설정
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 환경 변수 설정
```bash
# .env 파일 생성
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
DEBUG=False
```

### Docker 배포
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application"]
```

## 🤝 기여하기

### 개발 참여 방법
1. 이슈 등록 또는 기존 이슈 확인
2. 브랜치 생성: `git checkout -b feature/new-feature`
3. 코드 작성 및 테스트
4. 커밋: `git commit -m "Add new feature"`
5. 푸시: `git push origin feature/new-feature`
6. Pull Request 생성

### 코딩 컨벤션
- PEP 8 스타일 가이드 준수
- 함수/클래스에 독스트링 작성
- 의미 있는 변수명 사용
- 테스트 코드 작성

### 버그 리포트
이슈 등록 시 다음 정보 포함:
- 운영체제 및 브라우저 정보
- 재현 단계
- 예상 결과 vs 실제 결과
- 스크린샷 (필요시)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원 및 문의

- **이슈 등록**: [GitHub Issues](https://github.com/your-repo/issues)
- **문서**: [Wiki](https://github.com/your-repo/wiki)
- **이메일**: support@your-domain.com

---

## 📈 업데이트 로그

### v1.2.0 (2024-07-08)
- ✨ 월별 주차 표시 시스템 도입 (7월 1주차)
- 🎨 네이버 스타일 디자인 시스템 적용
- 🐛 워크로그 템플릿 오류 수정
- 📱 반응형 디자인 개선

### v1.1.0 (2024-07-07)
- 📊 대시보드 통계 기능 추가
- 🔍 고급 검색 및 필터링
- 📎 파일 첨부 기능
- 🔔 실시간 알림 시스템

### v1.0.0 (2024-07-04)
- 🎉 초기 릴리스
- 📝 기본 업무 관리 기능
- 📅 워크로그 시스템
- 👥 사용자 관리

---

**업무관리시스템**으로 더 효율적이고 체계적인 업무 관리를 시작하세요! 🚀
