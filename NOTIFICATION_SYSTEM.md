# 🔔 알림 시스템 완전 가이드

업무관리시스템의 알림(Notification) 시스템이 동작하는 모든 경우와 사용법을 상세히 설명합니다.

## 📋 목차

1. [알림 시스템 개요](#알림-시스템-개요)
2. [알림이 발생하는 경우](#알림이-발생하는-경우)
3. [알림 유형별 상세 설명](#알림-유형별-상세-설명)
4. [자동 알림 시스템](#자동-알림-시스템)
5. [알림 관리 방법](#알림-관리-방법)
6. [개발자 가이드](#개발자-가이드)

---

## 🎯 알림 시스템 개요

### 알림의 목적
- **실시간 소통**: 업무 진행 상황을 즉시 공유
- **업무 누락 방지**: 중요한 업무나 마감일을 놓치지 않도록 알림
- **협업 효율성**: 팀원 간의 원활한 협업 지원
- **책임감 향상**: 할당된 업무에 대한 인식 제고

### 알림 전달 방식
- **웹 알림**: 시스템 내 알림 센터
- **실시간 표시**: 상단 네비게이션 바의 알림 아이콘
- **읽음/읽지 않음 상태**: 알림 상태 관리

---

## 🚨 알림이 발생하는 경우

### 1. 📝 업무 할당 시 (task_assigned)

#### 발생 조건
```python
# 새 업무 생성 시 담당자 지정
- 업무 생성자가 다른 사용자를 담당자로 지정
- 기존 업무에 새로운 담당자 추가

# 알림 대상
- 새로 할당된 담당자들 (업무 생성자 제외)
```

#### 알림 내용
- **제목**: "새 업무가 할당되었습니다"
- **메시지**: "[업무제목] 업무가 [할당자명]님에 의해 할당되었습니다."
- **관련 업무**: 해당 업무 링크 포함

#### 실제 예시
```
제목: 새 업무가 할당되었습니다
메시지: "사용자 로그인 기능 구현" 업무가 김팀장님에 의해 할당되었습니다.
시간: 2024-07-08 14:30
```

### 2. 💬 댓글 추가 시 (comment_added)

#### 발생 조건
```python
# 업무에 댓글 작성 시
- 업무 작성자에게 알림 (댓글 작성자가 아닌 경우)
- 업무 담당자들에게 알림 (작성자, 댓글 작성자 제외)
```

#### 알림 대상
1. **업무 작성자**: 자신이 만든 업무에 댓글이 달린 경우
2. **업무 담당자들**: 담당하고 있는 업무에 댓글이 달린 경우

#### 알림 내용
- **업무 작성자용**: "[업무제목] 업무에 [댓글작성자]님이 댓글을 추가했습니다."
- **담당자용**: "담당하고 있는 [업무제목] 업무에 새 댓글이 추가되었습니다."

#### 실제 예시
```
제목: 새 댓글이 추가되었습니다
메시지: "API 개발" 업무에 이개발님이 댓글을 추가했습니다.
내용: "진행률 80% 완료했습니다. 내일 테스트 예정입니다."
```

### 3. 🔄 업무 상태 변경 시 (task_assigned)

#### 발생 조건
```python
# 업무 상태가 변경될 때
- 대기 → 진행중
- 진행중 → 완료
- 완료 → 대기 (재작업)
- 모든 상태 → 중단
```

#### 알림 대상
1. **업무 작성자**: 자신이 만든 업무의 상태가 변경된 경우
2. **업무 담당자들**: 담당하고 있는 업무의 상태가 변경된 경우

#### 알림 내용
- **상태 변경 전후**: "대기"에서 "진행중"으로 변경
- **변경자 정보**: 누가 상태를 변경했는지 표시

#### 실제 예시
```
제목: 업무 상태가 변경되었습니다
메시지: "데이터베이스 설계" 업무가 "대기"에서 "진행중"로 변경되었습니다.
변경자: 박개발님
시간: 2024-07-08 09:15
```

### 4. ⏰ 마감일 임박 시 (task_due)

#### 발생 조건
```python
# 자동 체크 시스템 (매일 오전 9시 실행)
- 마감일 1일 전
- 마감일 3일 전
- 중복 알림 방지 (하루에 한 번만)
```

#### 알림 대상
1. **업무 작성자**: 자신이 만든 업무의 마감일이 임박
2. **업무 담당자들**: 담당하고 있는 업무의 마감일이 임박

#### 알림 내용
- **남은 일수**: 정확한 남은 일수 표시
- **마감 일시**: 구체적인 마감 날짜와 시간
- **긴급도**: 1일 전은 더 강조된 메시지

#### 실제 예시
```
제목: 업무 마감일이 1일 남았습니다
메시지: "프로젝트 발표 준비" 업무의 마감일이 1일 남았습니다. (2024-07-09 18:00)
상태: 🔴 긴급
```

### 5. 🚨 마감일 초과 시 (task_overdue)

#### 발생 조건
```python
# 자동 체크 시스템 (매일 오전 9시 실행)
- 마감일이 지난 업무 (상태가 '완료'가 아닌 경우)
- 중복 알림 방지 (하루에 한 번만)
```

#### 알림 대상
1. **업무 작성자**: 자신이 만든 업무의 마감일이 지남
2. **업무 담당자들**: 담당하고 있는 업무의 마감일이 지남

#### 알림 내용
- **지연 일수**: 마감일로부터 며칠 지났는지 표시
- **긴급 처리**: 빠른 처리 필요성 강조
- **우선순위**: 다른 알림보다 높은 우선순위

#### 실제 예시
```
제목: 업무 마감일이 3일 지났습니다
메시지: "버그 수정" 업무의 마감일이 3일 지났습니다. 긴급 처리가 필요합니다.
상태: 🔴 지연
지연일수: 3일
```

### 6. 📅 워크로그 작성 알림 (worklog_reminder)

#### 발생 조건
```python
# 자동 체크 시스템 (매주 금요일 오후 실행)
- 이번 주 워크로그를 작성하지 않은 사용자
- 활성 사용자만 대상
- 주당 한 번만 알림
```

#### 알림 대상
- **워크로그 미작성자**: 이번 주 워크로그를 아직 작성하지 않은 모든 사용자

#### 알림 내용
- **주차 정보**: 몇 년 몇 주차인지 명시
- **작성 독려**: 업무 기록의 중요성 강조
- **직접 링크**: 워크로그 작성 페이지로 바로 이동

#### 실제 예시
```
제목: 워크로그 작성 알림
메시지: 2024년 28주차 워크로그를 아직 작성하지 않으셨습니다. 이번 주 업무 내용을 기록해주세요.
주차: 7월 1주차
마감: 금요일까지
```

---

## 📊 알림 유형별 상세 설명

### 알림 우선순위

#### 🔴 높은 우선순위
1. **task_overdue** (마감일 초과)
2. **task_due** (마감일 임박 - 1일 전)

#### 🟡 중간 우선순위
3. **task_due** (마감일 임박 - 3일 전)
4. **task_assigned** (업무 할당)

#### 🟢 낮은 우선순위
5. **comment_added** (댓글 추가)
6. **worklog_reminder** (워크로그 작성 알림)

### 알림 색상 구분

```css
/* Admin 페이지에서의 색상 구분 */
- 업무 마감일 임박: 🟡 노란색
- 업무 마감일 초과: 🔴 빨간색  
- 업무 할당: 🔵 파란색
- 댓글 추가: 🟢 초록색
- 워크로그 작성 알림: 🟣 보라색
```

---

## ⚙️ 자동 알림 시스템

### 실행 방법

#### 수동 실행
```bash
# 모든 알림 체크
python manage.py check_notifications

# 마감일 관련 알림만 체크
python manage.py check_notifications --type due_dates

# 워크로그 알림만 체크
python manage.py check_notifications --type worklog
```

#### 자동 실행 (Cron 설정)
```bash
# crontab -e 로 편집
# 매일 오전 9시에 마감일 알림 체크
0 9 * * * cd /path/to/project && python manage.py check_notifications --type due_dates

# 매주 금요일 오후 5시에 워크로그 알림 체크
0 17 * * 5 cd /path/to/project && python manage.py check_notifications --type worklog
```

### 중복 알림 방지

#### 일일 알림 제한
```python
# 같은 업무에 대해 하루에 한 번만 알림
today_notifications = Notification.objects.filter(
    task=task,
    notification_type='task_due',
    created_at__date=now.date()
)

if not today_notifications.exists():
    # 알림 생성
```

#### 주간 알림 제한
```python
# 워크로그 알림은 주당 한 번만
existing_reminder = Notification.objects.filter(
    user=user,
    notification_type='worklog_reminder',
    created_at__week=week_number,
    created_at__year=year
)
```

---

## 🎛️ 알림 관리 방법

### 사용자 인터페이스

#### 알림 확인
1. **상단 네비게이션**: 🔔 알림 아이콘 클릭
2. **알림 개수**: 읽지 않은 알림 개수 표시
3. **알림 목록**: 최근 알림 10개 표시

#### 알림 상태 관리
```python
# 읽음 처리
- 개별 알림 클릭 시 자동으로 읽음 처리
- "모두 읽음" 버튼으로 일괄 처리

# 삭제
- 개별 삭제 가능
- 읽은 알림 일괄 삭제 가능
```

### Admin 페이지에서 관리

#### 대량 작업
```python
# 선택된 알림들을 읽음으로 표시
actions = ['mark_as_read', 'mark_as_unread', 'delete_read_notifications']

# 읽은 알림만 선별 삭제
def delete_read_notifications(self, request, queryset):
    read_notifications = queryset.filter(is_read=True)
    count = read_notifications.count()
    read_notifications.delete()
```

#### 필터링 및 검색
```python
# 필터 옵션
list_filter = [
    'notification_type',  # 알림 유형별
    'is_read',           # 읽음 상태별
    'created_at',        # 생성일별
    'user'               # 사용자별
]

# 검색 필드
search_fields = [
    'title',             # 제목
    'message',           # 메시지 내용
    'user__username',    # 사용자명
    'task__title'        # 관련 업무 제목
]
```

---

## 👨‍💻 개발자 가이드

### 새로운 알림 추가

#### 1. 알림 유형 정의
```python
# notifications/models.py
NOTIFICATION_TYPES = (
    ('task_due', '업무 마감일 임박'),
    ('task_overdue', '업무 마감일 초과'),
    ('task_assigned', '업무 할당'),
    ('comment_added', '댓글 추가'),
    ('worklog_reminder', '워크로그 작성 알림'),
    ('new_type', '새로운 알림 유형'),  # 추가
)
```

#### 2. 알림 생성 함수 작성
```python
# notifications/utils.py
def notify_new_feature(user, message):
    """새로운 기능 알림"""
    return create_notification(
        user=user,
        notification_type='new_type',
        title='새로운 기능이 추가되었습니다',
        message=message
    )
```

#### 3. 뷰에서 알림 호출
```python
# views.py
from notifications.utils import notify_new_feature

def some_view(request):
    # 특정 조건에서 알림 생성
    notify_new_feature(request.user, "새로운 기능을 확인해보세요!")
```

### 알림 템플릿 커스터마이징

#### 알림 메시지 템플릿
```python
# 동적 메시지 생성
def create_dynamic_message(task, user, action):
    templates = {
        'assigned': f'{user.get_full_name()}님이 "{task.title}" 업무를 할당했습니다.',
        'completed': f'"{task.title}" 업무가 완료되었습니다.',
        'commented': f'"{task.title}" 업무에 새 댓글이 추가되었습니다.'
    }
    return templates.get(action, '알림이 있습니다.')
```

### 성능 최적화

#### 대량 알림 처리
```python
# 벌크 생성으로 성능 향상
notifications = []
for user in users:
    notifications.append(
        Notification(
            user=user,
            notification_type='bulk_notification',
            title='공지사항',
            message='중요한 공지사항입니다.'
        )
    )

Notification.objects.bulk_create(notifications)
```

#### 쿼리 최적화
```python
# select_related, prefetch_related 사용
notifications = Notification.objects.select_related(
    'user', 'task'
).prefetch_related(
    'task__assigned_to'
).filter(user=request.user)
```

---

## 📈 알림 통계 및 분석

### 알림 효과 측정

#### 읽음률 분석
```python
# 알림 유형별 읽음률
notification_stats = Notification.objects.values(
    'notification_type'
).annotate(
    total=Count('id'),
    read_count=Count('id', filter=Q(is_read=True))
).annotate(
    read_rate=F('read_count') * 100.0 / F('total')
)
```

#### 응답 시간 분석
```python
# 알림 생성부터 읽음까지의 시간
from django.db.models import Avg
from django.utils import timezone

response_times = Notification.objects.filter(
    is_read=True
).annotate(
    response_time=F('updated_at') - F('created_at')
).aggregate(
    avg_response_time=Avg('response_time')
)
```

### 사용자 행동 분석

#### 알림 선호도
```python
# 사용자별 알림 유형 선호도
user_preferences = Notification.objects.filter(
    user=user,
    is_read=True
).values('notification_type').annotate(
    count=Count('id')
).order_by('-count')
```

---

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 알림이 생성되지 않음
```python
# 체크 포인트
- 알림 생성 함수가 올바르게 호출되는지 확인
- 사용자 권한 및 조건 확인
- 중복 알림 방지 로직 확인
```

#### 2. 중복 알림 발생
```python
# 해결 방법
- 중복 체크 로직 강화
- 트랜잭션 사용으로 동시성 문제 해결
- 유니크 제약조건 추가 고려
```

#### 3. 성능 문제
```python
# 최적화 방법
- 벌크 연산 사용
- 인덱스 추가
- 오래된 알림 정리 작업
```

### 디버깅 도구

#### 로그 설정
```python
# settings.py
LOGGING = {
    'loggers': {
        'notifications': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### 테스트 명령어
```bash
# 알림 시스템 테스트
python manage.py shell
>>> from notifications.utils import *
>>> check_due_date_notifications()
>>> check_worklog_reminders()
```

---

## 📚 추가 자료

### 관련 문서
- [Django Signals 활용](https://docs.djangoproject.com/en/stable/topics/signals/)
- [Celery를 이용한 비동기 처리](https://docs.celeryproject.org/)
- [실시간 알림 구현 (WebSocket)](https://channels.readthedocs.io/)

### 확장 가능성
- **이메일 알림**: SMTP 설정으로 이메일 발송
- **SMS 알림**: 외부 API 연동
- **푸시 알림**: 모바일 앱 연동
- **Slack 연동**: 팀 채널로 알림 전송

---

**알림 시스템을 통해 더 효율적인 업무 협업을 경험하세요!** 🚀
