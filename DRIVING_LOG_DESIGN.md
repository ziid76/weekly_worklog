# 운행일지(Driving Log) 신규 앱 상세 설계서

> 작성일: 2026-05-19 (최초)
> 최종 갱신: 2026-05-29 (P5.x 시리즈 종료, P7 — 운행시간 캐시 컬럼 신설 + 전 화면 노출)
> 작성자 검토 대상: chsong@samchully.co.kr
> 대상 프로젝트: WEEKLY_WORKLOG-MAIN (Django 5.1 기반 ITMS)
> 본 문서는 **실제 구현 코드와 일치하도록 갱신된 현행 설계서**입니다. 신규 변경 사항은 본 문서를 함께 갱신하여 코드-설계 일치를 유지합니다.

---

## 0. 설계 원칙

1. **기존 소스 최소 침습 (영향 없음 보장)**: 기존 앱(`worklog`, `accounts`, `teams`, `reports` 등)의 **모델·뷰·URL·기존 함수 시그니처는 일체 수정하지 않는다.** 신규 앱 `driving_log/`를 추가하고, 변경이 필요한 경우는 **공통 성격이 강한 부분**(예: 이메일 발송 모듈, 공통 이메일 베이스 템플릿)에 한해 **추가만 하고 기존 동작은 보존한다.**
2. **기존 패턴 답습**: 모델/뷰/URL/템플릿 구조는 [worklog/](worklog/) 앱을 그대로 따른다 (CBV ListView/CreateView/UpdateView + AJAX FBV, 템플릿은 [templates/basic.html](templates/basic.html) 상속).
3. **UI 통일성**: [design.md](design.md) 의 컬러팔레트·컴포넌트·상태배지를 그대로 사용한다 (Primary `#0077C8`, `rounded-[2rem]`, Material Symbols, Manrope).
4. **인증 통일**: 기존 SSO ([accounts.backends.SSOAuthenticationBackend](accounts/backends.py)) 와 `LoginRequiredMixin` 을 그대로 사용한다. 앱 단위 접근권한은 §9 참고.
5. **이메일 발송 공통화 + 그룹웨어 SMTP 별도 사용**: 이메일 발송은 공통 성격 모듈이므로 **신규 mailer 함수를 [mailing/mailer.py](mailing/mailer.py) 에 추가**한다 (driving_log 앱 내부에 가두지 않음). 기존 함수 `send_review_notification` 은 변경하지 않는다. **단, 운행일지 결재 메일은 기존 AWS SES 백엔드를 우회하고 그룹웨어 SMTP(`GROUPWARE_SMTP_*`)를 발송 시점에 `get_connection()` 으로 주입한다** — 임원 메일이 사내 그룹웨어 도메인이므로 외부 SES 발송 시 스팸 처리되는 문제를 회피하기 위함. 공통 이메일 베이스 템플릿은 **본 단계에선 생성하지 않았다** (필요시 추후 추가).
6. **모바일 우선**: 운전자 입력 화면은 모바일 폭(<640px)을 기본 레이아웃으로, 데스크톱은 sm: 분기로 확장한다.
7. **운전 전용 사용자 격리**: 운전기사만을 위한 별도 User 가 ITMS 의 다른 화면(주간보고, 업무 등)에 접근하지 못하도록 **미들웨어·로그인 분기·사이드바 분기** 3중 격리를 둔다. 자세한 정의는 §9.4 참고.

---

## 1. 사용자 역할 매트릭스

### 1.1 역할 정의

| 역할 | 식별 방법 | 가능한 행위 |
| --- | --- | --- |
| **운전자(Driver)** | Django Group **`driving_log_users`** 에 속한 User | 본인 운행일지 작성/임시저장/제출, 본인 목록 조회, 결재요청 |
| **지원팀 관리자(Manager)** ★ 2026-05-29 신규 | Django Group **`driving_log_managers`** 에 속한 User (또는 슈퍼유저) | 전체 운행일지 목록/필터/CSV/상세/이력 타임라인 조회. 운전자 화면(`/driving-log/`) 도 접근 가능 (본인이 운전기사를 겸할 수 있음). 강제 상태변경은 Django admin 으로 위임. |
| **운행일지 전용 사용자(Driving-only)** | `driving_log_users` 또는 `driving_log_managers` 그룹**만** 가진 User (다른 ITMS 그룹 미소속, `is_staff=False`, `is_superuser=False`) | 운전자/매니저와 동일 행위. 로그인 직후 `/driving-log/` 로 라우팅되고 그 외 URL 접근 시 강제 리다이렉트. 사이드바도 운행일지 (+ 매니저면 운행일지 관리) 만 노출. ([driving_log/permissions.py](driving_log/permissions.py) `is_driving_log_only_user` — 그룹 집합이 `{users, managers}` 의 부분집합인지로 판정) |
| **수행임원(Executive)** | `driving_log.Executive` 테이블에 등록된 마스터 데이터 (시스템 User 와 무관) | 이메일 링크로 승인/반려, 과거 이력 조회 (휘발성 URL) |

> ★ **2026-05-29 권한 모델 재정렬** (P5.1): 기존 `is_driving_log_admin` 가 `is_staff` 기반이어서 기존 ITMS 의 IT 스태프가 자동으로 운행일지 관리에 노출되는 문제를 발견. **신규 그룹 `driving_log_managers` 도입**하고 모든 매니저 판정을 이 그룹 멤버십(+슈퍼유저) 으로 전환. `is_staff` 의존을 매니저 판정에서 제거. 격리 미들웨어도 매니저 그룹을 포함하도록 확장.

### 1.2 권한 관리 방식 선택 근거

기존 프로젝트 조사 결과:
- **앱 단위 권한 시스템이 부재**한다. 일반 사용자 앱([worklog/views.py](worklog/views.py), [task/views.py](task/views.py))은 `LoginRequiredMixin` 만 사용해 로그인한 모든 User 에게 열려 있고, 관리자 보호는 [accounts/views.py:28-30](accounts/views.py#L28-L30) 의 `is_staff_or_superuser()` 헬퍼 + `@user_passes_test()` 데코레이터로 처리한다.
- Django `Group` 모델은 [accounts/views.py](accounts/views.py) 에 import 만 되어 있고 권한 분기에는 사용되지 않는다.
- `accounts.UserProfile.team_role` 은 'member/leader/admin' 값을 가지지만 권한 체크가 아닌 표시·정렬 용도다.

따라서 본 앱에서는 **Django 기본 `Group` 모델**을 활용한다 (외부 의존성 추가 없음, 기존 인프라 활용, Django admin 의 User > Groups 화면에서 멤버십 관리 가능):

- 그룹명:
  - **`driving_log_users`** — 운행일지 작성 권한 (운전기사)
  - **`driving_log_managers`** ★ 2026-05-29 신규 — 운행일지 관리(전체 조회/CSV) 권한 (지원팀 관리자)
- 그룹 멤버십은 Django admin 의 `auth > Users > {유저} > Groups` 화면에서 지원팀 관리자가 직접 추가/제거
- 그룹은 **[driving_log/apps.py](driving_log/apps.py) 의 `post_migrate` signal** 로 자동 생성된다 (수동 셋업 불필요). 데이터 마이그레이션 파일을 만들지 않고 signal 로 처리.
- 운전자 뷰는 `LoginRequiredMixin + UserPassesTestMixin`(`is_driving_log_user`: users 또는 managers 그룹 또는 슈퍼유저) 으로 보호
- 관리자 뷰는 `DrivingLogManagerRequiredMixin`(`is_driving_log_manager`: managers 그룹 또는 슈퍼유저) 으로 보호 — **`is_staff` 는 사용하지 않는다**
- 권한 없는 User 가 접근시 `templates/driving_log/no_permission.html` 안내 페이지로 라우팅 (관리자에게 권한 요청 안내)

> **결정사항**: "수행임원"은 `driving_log` 앱 **내부의 독립 마스터 모델** `Executive` 로 관리한다 (이름 + 수신 이메일 + 활성여부 + 표시순서). **시스템 User 와 FK 로 연결하지 않는다** — 수행임원은 시스템 로그인 사용자가 아니라 외부 결재선이며, 이메일 토큰으로만 접근한다. 기존 `accounts.UserProfile` 은 건드리지 않는다.

---

## 2. 데이터 모델

### 2.1 ERD 요약

```
User (Django 기본, 수정 안 함)
 └─┬── DrivingLogSheet (운행일지 1건 = 결재 단위, 최대 14일 묶음)
   │    - status: draft / submitted / approved / rejected / rejected_resubmitted
   │    - reviewer (Executive FK)
   │    - resubmitted_to (self OneToOne, nullable)
   │         반려 → 재상신 시 원본이 새 sheet 을 가리키며, 새 sheet 에서는
   │         resubmitted_from reverse 로 원본을 참조한다.
   │    - 결재 요청 일시, 결재 처리 일시, 반려 사유
   │
   └── DrivingLogEntry (운행일지 1행 = 1일치)
        - sheet FK
        - log_date, is_holiday
        - start_time, end_time
        - cumulative_distance, vehicle_number
        - overtime_minutes (저장 시점 계산)

Executive (수행임원 마스터, User 와 무관한 독립 데이터)
 - name (예: "홍길동 상무")
 - email (결재 메일 수신처)
 - is_active
 - display_order

ApprovalToken (이메일용 휘발성 토큰)
 - sheet FK
 - executive FK
 - token (UUID, unique)
 - action_scope: 'approve_reject' | 'history_view'
 - expires_at (scope 별로 TTL 다름 — §7.3 참고)
 - used_at (단발성 사용)

ApprovalHistory (감사 로그)
 - sheet FK
 - actor (User FK, nullable)
 - action: requested / approved / rejected / resubmitted / viewed_history
 - comment
 - created_at
```

### 2.2 모델 상세 (`driving_log/models.py`)

```python
class Executive(models.Model):
    """수행임원 마스터.

    시스템 사용자(User) 와 무관한 독립 마스터 데이터. 외부 결재선이며
    이메일 토큰으로만 접근하므로 Django User 와 연결하지 않는다.
    """
    name = models.CharField("이름", max_length=50)               # 예: "홍길동 상무"
    email = models.EmailField("수신 이메일")                       # 결재 알림 수신처
    is_active = models.BooleanField("활성", default=True)
    display_order = models.IntegerField("표시 순서", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "수행임원"


class DrivingLogSheet(models.Model):
    """운행일지 1건. 최대 14일치 Entry 를 묶어 한 번에 결재."""
    STATUS = (
        ('draft', '임시저장'),
        ('submitted', '결재요청'),
        ('approved', '승인'),
        ('rejected', '반려'),
        ('rejected_resubmitted', '반려(재기안)'),   # 재상신 후 종결된 원본 문서
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driving_sheets')
    title = models.CharField("제목", max_length=200, blank=True)  # 자동: "2026-05-01 ~ 2026-05-14 운행일지"
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')

    reviewer = models.ForeignKey(Executive, on_delete=models.PROTECT,
                                  null=True, blank=True, related_name='review_sheets')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)

    # 반려 → 재상신 시 원본이 새 sheet 을 가리킨다. 새 sheet 에서는 `resubmitted_from` reverse 로 원본 접근.
    resubmitted_to = models.OneToOneField(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resubmitted_from',
    )

    total_overtime_minutes = models.IntegerField(default=0)  # 캐시: Entry 저장시 갱신
    total_run_minutes = models.IntegerField(default=0)       # ★ 2026-05-29 신규: 운행시간(분) 합계 캐시
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start', '-created_at']


class DrivingLogEntry(models.Model):
    """운행일지 1행 = 1일치."""
    sheet = models.ForeignKey(DrivingLogSheet, on_delete=models.CASCADE, related_name='entries')
    log_date = models.DateField()
    is_holiday = models.BooleanField(default=False)        # 토/일 자동, 공휴일 수동
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    cumulative_distance = models.DecimalField(max_digits=8, decimal_places=1,
                                              null=True, blank=True)  # km 단위
    vehicle_number = models.CharField(max_length=20, blank=True)
    overtime_minutes = models.IntegerField(default=0)      # 저장시 계산값 캐시
    run_minutes = models.IntegerField(default=0)           # ★ 2026-05-29 신규: 운행시간(분) = end - start 캐시

    class Meta:
        ordering = ['log_date']
        unique_together = ('sheet', 'log_date')


class ApprovalToken(models.Model):
    """이메일 본문의 승인/반려/이력조회 버튼용 휘발성 UUID."""
    SCOPES = (
        ('approve_reject', '승인/반려'),
        ('history_view', '이력조회'),
    )
    sheet = models.ForeignKey(DrivingLogSheet, on_delete=models.CASCADE,
                              related_name='tokens', null=True, blank=True)
    # history_view 의 경우 sheet 가 null 이고 executive 만 필요
    executive = models.ForeignKey(Executive, on_delete=models.CASCADE, related_name='tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scope = models.CharField(max_length=20, choices=SCOPES)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)  # 'approve_reject' 는 1회용
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.expires_at and (
            self.scope == 'history_view' or self.used_at is None
        )


class ApprovalHistory(models.Model):
    """결재 감사 로그. 누가 언제 무엇을 했는지 기록."""
    ACTIONS = (
        ('requested', '결재요청'),
        ('approved', '승인'),
        ('rejected', '반려'),
        ('resubmitted', '재상신'),
        ('viewed_history', '이력조회'),
    )
    sheet = models.ForeignKey(DrivingLogSheet, on_delete=models.CASCADE, related_name='history')
    actor_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actor_executive = models.ForeignKey(Executive, on_delete=models.SET_NULL,
                                         null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    comment = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

---

## 3. 상태 머신

```
[draft] --임시저장--> [draft]
[draft] --결재요청(reviewer 지정)--> [submitted] --이메일 발송--> Executive
[submitted] --이메일 승인 클릭--> [approved]   (감사로그 + 토큰 used_at)
[submitted] --이메일 반려 클릭--> [rejected]   (반려사유 입력 후)
[rejected] --운전자 [재상신] 클릭--> [rejected_resubmitted] (원본 종결)
                                  └→ + 신규 [draft] 생성 (entries 복제, title 에 "(재상신) " 접두)
[rejected_resubmitted] --종결--> (편집/삭제/재상신 모두 불가)
[approved] --변경 불가--> (관리자 강제변경만 가능)
```

> **2026-05-28 변경**: 기존의 `rejected → draft` 전이 (운전자 재편집) 는 폐기되었다. 반려 건은 본문 수정 가능성과 결재 이력 추적성을 모두 보전하기 위해 **편집/삭제 모두 차단**하고, `[재상신]` 버튼을 통해서만 **신규 sheet 으로 복제 + 원본을 `rejected_resubmitted` 로 종결**하는 워크플로로 변경됨. 재상신 상세 흐름은 §6.8 참고.

전이 권한:

| 전이 | 주체 |
|---|---|
| draft ↔ draft | author 본인 |
| draft → submitted | author 본인 |
| submitted → approved/rejected | reviewer Executive (이메일 토큰 경유) |
| rejected → rejected_resubmitted (+ 신규 draft 생성) | author 본인 ([재상신] 1회용) |
| 모든 강제 변경 | Support Admin (Django admin) |

---

## 4. 초과근무 계산 로직

### 4.1 규칙 (요구사항 그대로)

- **평일(월~금) + 휴일 아님**: 09:00~18:00 **제외 시간**이 초과근무
  - 예: 08:00~19:00 운행 → 1h(아침) + 1h(저녁) = **120분 초과근무**
  - 예: 09:00~18:00 운행 → 0분
  - 예: 13:00~14:00 운행 → 0분
- **토/일** (자동 휴일) **또는** **사용자 수동 휴일 체크**: 운행 **전체 시간**이 초과근무
  - 예: 07:00~17:00 운행 → 600분

### 4.2 의사코드

```python
def calc_overtime_minutes(entry):
    if not entry.start_time or not entry.end_time:
        return 0
    s = datetime.combine(entry.log_date, entry.start_time)
    e = datetime.combine(entry.log_date, entry.end_time)
    if e <= s:
        return 0  # 자정 넘어가는 운행은 별도 정책 필요 (4.3 참고)
    total_min = int((e - s).total_seconds() // 60)

    weekday = entry.log_date.weekday()  # 0=월 ... 5=토 6=일
    is_weekend = weekday >= 5
    if is_weekend or entry.is_holiday:
        return total_min

    # 평일 정규근무 구간 09:00~18:00 와의 겹침
    work_s = datetime.combine(entry.log_date, time(9, 0))
    work_e = datetime.combine(entry.log_date, time(18, 0))
    overlap_s = max(s, work_s)
    overlap_e = min(e, work_e)
    overlap_min = max(0, int((overlap_e - overlap_s).total_seconds() // 60))
    return total_min - overlap_min
```

### 4.3 미해결 정책 — 구현 전 확인 필요

- 자정을 넘기는 운행 (예: 22:00 시작, 다음날 02:00 종료) — 본 설계서는 **end <= start 이면 0분 처리**로 가정. 필요시 `end_date` 필드 추가 검토.
- 분 단위 표시 vs 시간:분 표시 — 모델은 `int(분)` 으로 저장하고, 화면 표시는 `f"{m//60}h {m%60}m"` 으로 변환.

### 4.4 저장 시점

- `DrivingLogEntry.save()` 에서 `overtime_minutes` 와 `run_minutes` 둘 다 계산 후 저장
- 같은 save() 의 마지막에 부모 `DrivingLogSheet.total_overtime_minutes` / `total_run_minutes` 를 한 쿼리로 합계 재계산 (헬퍼 `_refresh_sheet_totals(sheet_id)`)

### 4.5 운행시간 계산 (★ 2026-05-29 신규)

```python
def calc_run_minutes(log_date, start_time, end_time):
    """운행 시간(분) = end - start 단순 차감.

    자정 넘는 운행은 일자 2건 분리 운용 정책이라 e>s 가정.
    e <= s 면 0분.
    """
    if log_date is None or start_time is None or end_time is None:
        return 0
    s = datetime.combine(log_date, start_time)
    e = datetime.combine(log_date, end_time)
    if e <= s:
        return 0
    return int((e - s).total_seconds() // 60)
```

- 초과근무와 같이 `DrivingLogEntry.save()` 안에서 계산되어 `run_minutes` 에 캐시.
- 합계는 `DrivingLogSheet.total_run_minutes` 에 캐시 (Entry 변경 시 자동 갱신).
- 화면 표시: `DrivingLogSheet.total_run_display` property (`"NN시간 MM분"`).
- 편집 화면의 JS 도 같은 단순 차감 로직 (`calcRun(row)`) — 행 입력 즉시 미리보기, 저장 시 서버 계산값으로 덮어씀.

---

## 5. URL 구조

[worklog/urls.py](worklog/urls.py) 의 명명 규칙(snake_case 이름, kebab-case 경로) 을 그대로 따른다. `app_name = 'driving_log'` 로 네임스페이싱한다 ([driving_log/urls.py:5](driving_log/urls.py#L5)).

```python
# config/urls.py 에 1줄 추가 (구현됨)
path('driving-log/', include('driving_log.urls')),

# driving_log/urls.py
app_name = 'driving_log'

urlpatterns = [
    # 운전자
    path('',                          DrivingLogSheetListView.as_view(),   name='driving_log_list'),
    path('create/',                   DrivingLogSheetCreateView.as_view(), name='driving_log_create'),
    path('<int:pk>/',                 DrivingLogSheetDetailView.as_view(), name='driving_log_detail'),
    path('<int:pk>/edit/',            DrivingLogSheetEditView.as_view(),   name='driving_log_edit'),
    path('<int:pk>/delete/',          DrivingLogSheetDeleteView.as_view(), name='driving_log_delete'),

    # AJAX
    path('api/sheet/<int:pk>/save/',     save_sheet_api,     name='driving_log_save_api'),       # 임시저장+편집
    path('api/sheet/<int:pk>/submit/',   submit_sheet_api,   name='driving_log_submit_api'),     # 결재요청 (reviewer 포함)
    path('api/sheet/<int:pk>/resubmit/', resubmit_sheet_api, name='driving_log_resubmit_api'),   # 반려 → 재상신 복제 (★ 2026-05-28 추가)
    path('api/sheet/<int:pk>/resend/',   resend_request_mail_api, name='driving_log_resend_api'),# 결재요청 메일 재발송 (★ 2026-05-28 추가)
    path('api/executives/',              executives_api,     name='driving_log_executives_api'),

    # 이메일 토큰 진입 (로그인 불필요, 토큰 자체가 인증)
    path('approve/<uuid:token>/',     approve_via_email, name='driving_log_approve_email'),
    path('reject/<uuid:token>/',      reject_via_email,  name='driving_log_reject_email'),
    path('history/<uuid:token>/',     history_via_email, name='driving_log_history_email'),
    # ★ 2026-05-28 추가: history scope 토큰으로 sheet 1건의 read-only 상세 조회
    path('history/<uuid:token>/sheet/<int:sheet_pk>/',
         history_sheet_detail_via_email,
         name='driving_log_history_sheet_detail_email'),

    # 안내 페이지
    path('no-permission/', no_permission, name='no_permission'),

    # 관리자 (P5 — 2026-05-29 구현 완료)
    path('admin/sheets/',                DrivingLogAdminListView.as_view(),   name='admin_sheet_list'),
    path('admin/sheets/export/',         driving_log_admin_csv_export,        name='admin_sheet_csv'),
    path('admin/sheets/<int:pk>/',       DrivingLogAdminDetailView.as_view(), name='admin_sheet_detail'),
]
```

> **관리자 화면 (P5)** (★ 2026-05-29 구현 완료): `admin/sheets/` 커스텀 페이지를 두어 지원팀 관리자가 운행일지를 부서/기간/임원/상태별로 조회·CSV 다운로드 할 수 있다. 강제 상태변경 등 destructive 한 운영성 변경은 본 화면에서 제공하지 않고 Django admin (`/admin/driving_log/drivinglogsheet/`) 으로 일임한다 — 상세 페이지 하단의 [Django admin 에서 강제 변경] 링크가 직접 진입을 돕는다. 자세한 화면 구성은 §6.5 참고.

---

## 6. 화면 와이어프레임

### 6.1 [목록] `/driving-log/` (운전자)

```
┌─────────────────────────────────────────────┐
│ 운행일지                       [+ 신규 작성] │
│ ─────────────────────────────────────────── │
│ ┌──────────────────────────────────────┐    │
│ │ 2026-05-01 ~ 2026-05-14              │    │
│ │ [임시저장] · 7건 · 초과 320분         │    │
│ │ 작성: 2026-05-15                     │    │
│ └──────────────────────────────────────┘    │
│ ┌──────────────────────────────────────┐    │
│ │ 2026-04-15 ~ 2026-04-28              │    │
│ │ [승인] · 14건 · 초과 1,250분         │    │
│ │ 결재: 홍길동 상무 (2026-04-30)        │    │
│ └──────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```
- 카드: `bg-white rounded-[2rem] border border-slate-200 p-6 hover:shadow-xl`
- 상태배지: design.md §5.3 상태배지 그대로 (draft=amber, submitted=blue, approved=emerald, rejected=rose)

### 6.2 [편집] `/driving-log/<pk>/edit/` — **핵심 화면**, 모바일 우선

데스크톱: 14행 테이블.
모바일(<640px): 각 행이 카드 1장으로 펼쳐짐 (Tailwind `flex-col sm:table-row`).

```
모바일 (1행 = 1카드)              데스크톱 (테이블)
┌──────────────────────────┐    ┌────┬──────┬──────┬──────┬────┬──────┬──────┐
│ 일자: [2026-05-01  📅]    │    │일자│휴일  │시작  │종료  │거리│차량  │초과  │
│ 휴일여부: ☑ (자동: 토)    │    ├────┼──────┼──────┼──────┼────┼──────┼──────┤
│ 시작: [09:00] 종료:[18:00]│    │5/1 │ ☑(토)│ 09:00│ 18:00│120 │1234  │ 540m│
│ 거리: [120.5] km          │    │5/2 │ ☐    │ 08:00│ 19:00│ 80 │1234  │ 120m│
│ 차량: [서울 12가 1234]    │    │... 12 more rows ...                       │
│ 초과근무: 540분 (자동)    │    ├────┴──────┴──────┴──────┴────┴──────┴──────┤
│                          │    │ 합계 초과근무: 12h 30m (750분)             │
│ [➕ 행 추가] [🗑 삭제]    │    └─────────────────────────────────────────────┘
└──────────────────────────┘
```

화면 하단 고정 액션바 (모바일은 sticky bottom):
```
[임시저장]  [결재요청 →]
```

**핵심 인터랙션**:
- 일자 변경시 즉시 토/일 판정해 `is_holiday` 자동 체크 (JS, 사용자가 다시 끌 수 있음)
- 시작/종료 시간 또는 휴일 토글 변경시 즉시 초과근무 계산 (클라이언트 측, 서버 저장시 재검증)
- **휴일 체크박스 이벤트 처리 주의** (★ 2026-05-28 race condition fix): 휴일 체크박스의 `change` 핸들러는 일반 input 루프에서 **분리**해서 등록해야 한다. 같은 루프에 두면 `recalcRow → autoHoliday` 가 사용자의 `userTouched` 플래그 셋팅보다 먼저 실행되어, 평일에 휴일을 체크해도 곧바로 체크가 풀려버리는 race 가 발생한다. 휴일 체크박스 핸들러 안에서 **`userTouched='1'` 셋팅을 먼저 한 뒤** `markDirty()`/`recalcRow()` 를 호출하는 순서가 정답이다.
- **행 추가 시 차량번호 자동 복사** (★ 2026-05-28 추가): [+ 행 추가] 버튼은 직전 행의 `vehicle_number` 를 초기값으로 채운 새 행을 만든다 (`lastVehicleNumber()` 헬퍼). 같은 차량으로 며칠씩 운행하는 일반적 패턴에서 입력 수고를 줄이기 위함.
- 14일 초과 추가 시도시 토스트로 차단: "한 운행일지에는 최대 14일까지 작성할 수 있습니다."
- 임시저장: 5초 디바운스 자동저장 + 명시적 [임시저장] 버튼 (둘 다 `save_sheet_api` 호출)

### 6.3 [결재요청 모달] — 2단계 (★ 2026-05-28 변경)

발송 직전 사용자가 "누구에게 / 무엇을" 보내는지 한 번 더 확인할 수 있도록 모달을 **2단계**로 구성한다.

```
Step 1: 임원 선택                     Step 2: 최종 확인
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│  결재요청               [✕]      │   │  결재요청               [✕]      │
│ ─────────────────────────────── │   │ ─────────────────────────────── │
│  수행임원 선택                   │   │  아래 내용으로 결재요청을 발송  │
│  ┌─────────────────────────┐    │   │  합니다. 내용을 확인해주세요.   │
│  │ 홍길동 상무 — h@…  ▾    │    │   │ ┌───────────────────────────┐   │
│  └─────────────────────────┘    │   │ │ 제목: 2026-05-01 ~ ...    │   │
│  ※ 선택한 임원의 이메일로        │   │ │ 수행임원: 홍길동 상무      │   │
│    결재 요청 메일이 발송됩니다.  │ → │ │           h@samchully...   │   │
│    승인/반려 링크는 3일 유효.   │   │ │ 운행 기간: 2026-05-01 ~ … │   │
│                                 │   │ │ 운행 건수: 7건             │   │
│         [취소]      [다음 →]     │   │ │ 합계 초과근무: 12h 30m     │   │
└─────────────────────────────────┘   │ └───────────────────────────┘   │
                                      │  ※ 발송 후에는 임원의 결재     │
                                      │    전까지 수정할 수 없습니다.  │
                                      │                                 │
                                      │      [← 이전]  [결재요청 보내기]│
                                      └─────────────────────────────────┘
```

- 임원 목록은 `GET /driving-log/api/executives/` 로 조회 (Executive.is_active=True 만)
- 임원 옵션의 `data-name` / `data-email` 속성에 표시명/이메일을 함께 담아 Step2 의 확인 카드에서 즉시 표시
- 운행 기간 / 건수 / 합계 OT 는 현재 화면 상의 행 데이터로부터 클라이언트가 즉석 재계산해 표시 (서버 라운드트립 없음)

**재상신 sheet 의 결재요청** (§6.8 참고):
- 새 sheet 의 `reviewer` 가 원본과 동일하게 미리 결정되어 있으므로, **Step1 (임원 선택) 을 건너뛰고 곧장 Step2 (최종 확인) 로 진입**한다.
- 분기 신호는 form template 의 root 요소에 부여된 `data-is-resubmit / data-fixed-exec-id / data-fixed-exec-name / data-fixed-exec-email` 4개 속성. JS 의 `openApprovalModal()` 에서 `IS_RESUBMIT && FIXED_EXEC_ID` 일 때 hidden `<select>` 에 옵션을 미리 채우고 `showStep2()` 호출.
- 재상신 모드에서는 Step2 의 [← 이전] 버튼이 의미 없으므로 숨김.

### 6.4 [이메일 → 결재] 진입 페이지

이메일의 [승인] 버튼 → `/driving-log/approve/<uuid>/`
- 토큰 유효성 검증
- 토큰 유효시: 운행일지 요약 + 코멘트 입력란 + [최종 승인] 버튼
- [최종 승인] 클릭시 즉시 처리 후 결과 페이지

이메일의 [반려] 버튼 → `/driving-log/reject/<uuid>/`
- 같은 페이지지만 **반려사유 필수입력**

> **모바일 UI** (★ 2026-05-28 보완): approve/reject 페이지 모두 운행 내역 영역이 **모바일은 카드 리스트(`md:hidden`) / 데스크톱은 가로 테이블(`hidden md:block`)** 로 분기된다. 기존엔 데스크톱 가로 테이블 하나만 있어 모바일에서 좌우 잘림이 발생했음.

이메일의 [승인이력 조회] 버튼 → `/driving-log/history/<uuid>/`
- scope=`history_view` 토큰. 1시간 동안 여러번 조회 가능 (used_at 기록 X)
- 해당 Executive 가 결재한 과거 운행일지 목록 (모바일 카드 / 데스크톱 테이블 분기)

> **결재이력 상세 진입** (★ 2026-05-28 추가): history 페이지의 sheet 카드/행은 클릭 가능하며 `/driving-log/history/<token>/sheet/<sheet_pk>/` (view: `history_sheet_detail_via_email`) 로 이동한다. 동일 history scope 토큰의 만료 전까지 다회 read-only 조회 가능. 보안상 `sheet.reviewer == token.executive` 일치 검증을 거치고, 일치하지 않으면 `mismatch` 안내 페이지 (404). approve_page 와 유사한 헤더 + 운행 내역 카드/테이블 + 결재 의견/반려 사유 박스로 구성.

> **토큰 만료 안내 분기** (★ 2026-05-28 갱신): `templates/driving_log/token_invalid.html` 의 `reason='expired'` 안내는 **scope 별로 다른 문구**를 출력한다.
> - 공통 제목: "링크가 만료되었습니다."
> - `approve_reject`: "유효기간이 지나 결재가 만료되었습니다. / 원 요청자의 재기안이 필요합니다." (운전기사가 detail 의 [메일 재발송] 으로 직접 처리 가능 — §7.5 참고)
> - `history_view`: "결재 이력 조회 유효기간이 지났습니다."
> 분기를 위해 `_render_token_invalid(request, reason, scope)` 헬퍼가 scope 도 컨텍스트로 전달한다.

### 6.5 [관리자 목록 / 상세] `/driving-log/admin/sheets/` ★ 2026-05-29 구현 완료

지원팀 관리자(`is_staff` 또는 `superuser`)가 전체 운행일지를 부서/기간/임원/상태별로 조회하고 CSV 로 내보내는 화면. 강제 상태변경은 본 화면에서 제공하지 않고 Django admin 으로 위임한다.

#### 6.5.1 목록 화면 [`admin_sheet_list.html`](templates/driving_log/admin_sheet_list.html) ★ 2026-05-29 (3차) 운영 피드백 반영

**조회 정책**: 임시저장(`draft`) 은 운전기사 손에 있는 단계라 지원팀이 볼 필요가 없으므로 **항상 제외**한다 (`_apply_admin_filters` 가 unconditionally `.exclude(status=STATUS_DRAFT)`). 상태 필터 옵션 UI 에서도 draft 는 노출되지 않는다.

상단 **필터바** (★ 2026-05-29 4차 단순화):
- **제목 검색** (`q`): `sheet.title` 부분일치 (`title__icontains`). 운전기사명 검색은 별도 드롭다운으로 분리.
- **운전기사** (`author`, 드롭다운): `driving_log_users` 그룹 멤버만 옵션으로 노출 (매니저/슈퍼유저는 제외). 표시명은 `profile.get_korean_name`, 정렬은 한국명 기준.
- **수행임원** (`reviewer`, 드롭다운): `Executive.is_active=True` 만.
- **운행일** (`drive_from` / `drive_to`): **운행일지의 실제 운행 항목(`entries.log_date`)** 범위. 항목 1건이라도 범위에 포함되면 해당 sheet 노출. (예: sheet 의 entries = `[05-03, 05-08]` 이고 필터 = `05-05 ~ 05-15` 이면 `05-08` 매칭 → sheet 표시.) entries 조인이므로 `qs.distinct()` 필수.
- **상태** (`status`, getlist 다중선택): submitted / approved / rejected / rejected_resubmitted. (draft 는 의도적으로 제외.)
- [초기화] / [조회] 버튼. 페이지네이션 링크에 필터 쿼리스트링이 유지됨 (`querystring` 컨텍스트 변수).

> **이전 버전과의 차이** (2026-05-29 4차): 3차에서 도입했던 결재요청일/결재완료일 일자 필터 4개 (`submitted_from/to`, `reviewed_from/to`) 는 **상단이 너무 복잡하다는 운영자 피드백**으로 모두 제거. 일자 필터는 운행일 1쌍만 유지. 검색어는 운전기사명/제목 LIKE 혼합 → **제목 단독 LIKE** 로 좁힘. 운전기사 검색은 드롭다운으로 분리해서 오타 가능성과 부분 매칭 모호함 제거.

**테이블 컬럼** (데스크톱) / **카드** (모바일) (★ 2026-05-29 5차 컬럼 정리):
| ID | 요청자 | 결재자 | 제목 | 운행기간 | 건수 | 초과근무 | 상태 | 결재요청일 | 결재완료일 |

- **요청자** (구 "운전기사"): `sheet.author.profile.get_korean_name` (한국식: `last_name_ko + first_name_ko` → `user.last_name + first_name` → username 순서로 fallback). select_related 에 `author__profile` 추가하여 N+1 회피.
- **결재자** (구 "수행임원"): `sheet.reviewer.name`.
- **제목**: 결재자 우측. 길면 `max-w-xs truncate` 로 잘림. 빈 값은 "(제목 없음)".
- **건수**: `Count('entries', distinct=True)` 어노테이션 (`entry_count`) — entries 조인된 상태에서도 정확.
- **운행기간** / **결재요청일** / **결재완료일** 모두 `y.m.d` 또는 `y.m.d H:i` 형식 (예: `26.05.01 ~ 26.05.14`, `26.05.15 09:30`) — 컬럼 폭 절약.
- 행 클릭 시 상세 페이지로 이동 (`cursor-pointer` + hover). 별도 [상세] 컬럼은 없음.
- 정렬: `('-submitted_at', '-created_at')` — 최근 결재요청 우선.
- 페이지당 30건 (`paginate_by = 30`).

**CSV 내보내기 버튼** 은 **조회결과 영역 상단** (필터바 바깥, 결과 카운트 행 우측) 에 위치 — 필터를 조작하는 영역과 데이터를 보는 영역을 시각적으로 분리. 현재 필터 쿼리스트링을 그대로 들고 `admin/sheets/export/` 로 GET.

페이지 상단 설명 문구는 제거 (요건 #9) — 제목만 노출.

#### 6.5.2 상세 화면 [`admin_sheet_detail.html`](templates/driving_log/admin_sheet_detail.html)

운전자용 `driving_log_detail.html` 의 read-only 변형 + **결재 이력 타임라인** 추가.

- 헤더: `#ID` · 제목 · 운전기사 (한국명 `profile.get_korean_name` + email) · 운행 기간 · 작성일자 · 상태 뱃지
- 승인/반려 강조 박스 (운전자 detail 과 동일 패턴, [[feedback-driving-log-css-owned-by-user]] 외부 컨테이너 정책 동일 적용)
- 운행 내역 (데스크톱 테이블 / 모바일 카드 분기)
- 결재선 박스 (이름/이메일/요청·처리 일시)
- **결재 이력 타임라인**: `ApprovalHistory` 를 시간 역순으로, action 별 색상 뱃지 + actor (사용자 한국명 / 임원) + IP + comment 박스
- 하단 액션: [목록] 만. **Django admin 직링크는 제거** (★ 2026-05-29 3차) — 지원팀은 데이터를 수정하는 조직이 아니다 (요건 #7). 강제 변경이 필요할 경우 슈퍼유저가 직접 Django admin URL 로 진입한다.

#### 6.5.3 CSV 내보내기 (`driving_log_admin_csv_export`)

- 목록과 동일한 `_apply_admin_filters(qs, request)` 헬퍼로 필터 공유 (중복 제거). 결과적으로 draft 제외 + 운행일/결재요청일/결재완료일 범위 + 검색어/임원/상태 필터 모두 동일하게 적용.
- 컬럼 (★ 2026-05-29 6차 갱신: 운행시작일/운행종료일 → **운행기간 단일 컬럼** 으로 통합, 화면과 동일한 `yy.mm.dd ~ yy.mm.dd` 형식): `ID, 요청자, 결재자, 제목, 운행기간, 건수, 초과근무(분), 초과근무(표시), 상태, 결재요청일, 결재완료일, 결재 의견`
- 운전기사 컬럼은 `profile.get_korean_name` 값 (한국명). profile 이 없는 fallback 케이스는 username.
- Excel UTF-8 호환을 위해 BOM(`﻿`) 선두 출력 — [worklog.WorklogAdmin.export_to_csv](worklog/admin.py#L71-L100) 패턴.
- 파일명: `driving_logs_YYYYMMDD_HHMM.csv` (URL-encoded RFC 5987 `filename*=UTF-8''…`).
- `qs.iterator()` 사용 — 대량 다운로드 시 메모리 절약.

#### 6.5.4 권한 / 접근 경로 (★ 2026-05-29 권한 모델 재정렬 반영)

- [DrivingLogManagerRequiredMixin](driving_log/permissions.py) (`driving_log_managers` 그룹 또는 슈퍼유저) 로 보호. 일반 사용자는 `no_permission.html` (HTTP 403).
- **`is_staff` 는 의도적으로 사용하지 않는다** — 기존 ITMS 의 IT 스태프가 의도치 않게 운행일지 관리 화면에 노출되는 것을 막기 위함.
- 사이드바 진입점: [templates/basic.html](templates/basic.html) 에서 `{% if is_driving_log_manager %}` 로 분기. 일반 ITMS 사용자 블록과 격리(driving-only) 블록 양쪽 모두에서 동일 가드로 노출.
- 격리(driving-only) 사용자가 매니저 그룹도 함께 가진 경우(매니저 전용 사용자) 사이드바에 [운행일지] + [운행일지 관리] 두 메뉴가 함께 노출되며, 미들웨어는 `/driving-log/` prefix 만 허용하므로 다른 ITMS 화면에는 접근할 수 없다.

### 6.6 [편집 / 삭제 차단 정책] — 구현 반영 (★ 2026-05-28 갱신)

설계 단계에서 명시되지 않았던 상태별 진입 제한이 구현되어 있다. **2026-05-28 변경**: 반려(`rejected`) 상태는 더 이상 편집/삭제 모두 불가하다 — 본문을 직접 고치는 대신 §6.8 의 [재상신] 워크플로로만 진행한다.

| 작업 | 허용 상태 | 차단 시 동작 |
|---|---|---|
| 편집 진입 (`/edit/`) | `draft` 만 | 그 외 모든 상태는 detail 페이지로 redirect (`status != STATUS_DRAFT` 한 줄로 통일) |
| 삭제 (`/delete/`) | `draft` 만 | 그 외는 queryset 단계에서 404 |
| 임시저장 API (`save_sheet_api`) | `draft` 만 | 400 응답 "임시저장 상태가 아닌 운행일지는 수정할 수 없습니다." |
| 결재요청 API (`submit_sheet_api`) | `draft` 만 | 400 응답 "임시저장 상태가 아닌 운행일지는 결재요청할 수 없습니다." **추가로 모든 필수필드(일자/시작/종료/누적거리/차량번호) 검증 후 누락 시 행 번호와 함께 에러 메시지 반환** |
| 재상신 API (`resubmit_sheet_api`) | `rejected` 만, `resubmitted_to is None` | 400 응답 "반려된 운행일지에서만 재상신할 수 있습니다." / "이미 재상신된 운행일지입니다." (select_for_update 로 동시클릭 1회만 통과) |
| 메일 재발송 API (`resend_request_mail_api`) | `submitted` 만, `reviewer.is_active=True` | 400 응답. 활성 토큰 일괄 만료 + 새 토큰/메일 (§7.5) |

### 6.7 [신규 작성 흐름] — 구현 반영

설계 단계의 "신규 작성" 클릭 동작은 본 구현에서 다음과 같이 단순화되었다:

- 별도 작성 폼 화면 / 모달 없음 (`driving_log/forms.py` 는 비어 있음)
- [+ 신규 작성] 클릭 시 [DrivingLogSheetCreateView](driving_log/views.py#L50-L66) 가 **즉시 빈 sheet 를 DB에 생성하고 편집 화면으로 redirect**
- 기본 제목은 `"YYYY-MM-DD 운행일지"` (생성일자 기준), 이후 편집 시 일자 범위가 채워지면 자동으로 `"YYYY-MM-DD ~ YYYY-MM-DD 운행일지"` 로 갱신
- `period_start` / `period_end` 는 사용자가 직접 입력하지 않고, `save_sheet_api` 가 entries 의 `log_date` 최소/최대값으로 자동 계산

### 6.8 [재상신 흐름] ★ 2026-05-28 신규

반려된 운행일지를 운전자가 다시 결재 받기 위한 워크플로. **원본을 수정하는 게 아니라 신규 sheet 으로 복제**해서 추적성을 보전한다.

```
[반려 상세 화면]                               [재상신용 신규 sheet 편집 화면]
┌────────────────────────────┐                ┌──────────────────────────────┐
│ 2026-05-01 ~ 05-07 운행일지 │                │ (재상신) 2026-05-01 ~ ... 운행 │
│ [반려]                      │                │ [임시저장 / 결재요청]          │
│ ▣ 반려되었습니다             │                │  ※ 운행 내역은 원본과 동일하게 │
│   사유: 누적거리 표기 오류   │     POST       │     이미 채워져 있다           │
│   처리자: 홍길동 상무        │  resubmit_     │                              │
│                            │ ─ sheet_api ─→ │ [+ 행 추가] / 일자/차량 수정… │
│ [목록]   [재상신 →]         │                │                              │
└────────────────────────────┘                │ [결재요청] 누르면 → step2 직행 │
                                              │  (Step1 임원 선택 스킵)        │
                                              └──────────────────────────────┘
                                                          ↓
[원본 sheet]                                    [새 sheet (결재요청 완료)]
status = rejected_resubmitted                   status = submitted
resubmitted_to = (새 sheet)                     reviewer = 원본과 동일
편집/삭제/재상신 모두 차단                       (정상 결재 흐름으로 진입)
```

**[재상신] 버튼 표시 조건**: `status == 'rejected'` AND `resubmitted_to is None` (한 원본에서 1회만 가능).

**버튼 클릭 시 백엔드 처리** (`resubmit_sheet_api`, `transaction.atomic()` + `select_for_update()` 내부):
1. 새 `DrivingLogSheet` 를 `draft` 로 생성 — title 은 `(재상신) {원본 title}` (이미 prefix 있으면 중복 안 함), `reviewer` 는 원본과 동일, `period_start/end` 도 복제.
2. 원본의 모든 `DrivingLogEntry` 를 새 sheet 으로 복제 (`DrivingLogEntry.save()` 가 OT 자동 재계산 + sheet 합계 갱신).
3. 원본의 `status = rejected_resubmitted`, `resubmitted_to = 새 sheet` 저장.
4. `ApprovalHistory.ACTION_RESUBMITTED` 기록 (원본 sheet 에, comment 에 `재상신 → sheet #{new_id}`).
5. 새 sheet 의 편집 URL 을 응답 → 클라이언트가 `window.location.href` 로 이동.

**상세 화면의 반려 안내 박스** (`rejected` + `rejected_resubmitted` 공통):
- `bg-rose-50 border-2 border-rose-200` 강조 박스
- 반려 사유 / 처리자 / 처리일시 / (재상신된 경우) 재상신 문서로의 이동 링크

**확인 다이얼로그**: 버튼 클릭 시 `confirm()` 으로 "원본은 [반려(재기안)] 상태로 종결되며 더 이상 편집/삭제할 수 없습니다. 계속하시겠습니까?" 한 번 더 묻는다 — destructive 까진 아니지만 1회용이라 사용자가 의도치 않게 누르는 걸 막기 위함.

### 6.9 [detail 화면 UX 정비] ★ 2026-05-28 추가

상태별로 결재 결과의 시각 표현을 통일하고, 모바일 잘림·중복 표시를 정리.

- **승인/반려 강조 박스 위치 통일**: `status=approved` 와 `status=rejected/rejected_resubmitted` 모두 헤더 직후 상단에 동일 패턴의 박스 (`bg-{color}-50 border-2 border-{color}-200 rounded-[2rem] p-6 md:p-8`). 박스 안에 흰색 카드로 `review_comment` 강조. 색만 emerald ↔ rose 차이.
- **결재선 박스 정리**: 라벨 "결재" → "결재선" 으로 명확화. 박스 안 `review_comment` 표시는 제거 (위 강조 박스로 일원화, 중복 회피).
- **임원 이메일 mailto 링크 제거**: detail 화면의 결재선 박스에서 `<a href="mailto:...">` → `<span>` 으로 변경. 모바일에서 의도치 않게 메일 앱이 열리는 것 방지.
- **헤더 제목 폰트 인라인 강제**: `style="font-size: 1.15rem;"` 로 직접 지정 — Tailwind `text-2xl md:text-3xl` 류 임의값이 일부 환경에서 누락되는 사례 회피.
- **헤더 메타 두 줄 분리**: `작성일자 ... · 운행 ...` 한 줄 → `작성일자` / `운행` 별도 `<p>` 두 개로 분리. 좁은 모바일에서 어색한 위치 줄바꿈 해소.
- **운행 내역 모바일 카드: grid-cols-2 → flex-col stack**: 시간/거리/차량을 각각 한 줄씩 `min-w-0 + truncate`. 누적거리 6~7자리(예: 122,458 km)에서 viewport 잘림 해소.
- **viewport 잘림 안전장치**: 외부 컨테이너에 `style="overflow-x: hidden;"` + `min-w-0` 추가. 어떤 자식이 부모를 넘어가도 시각적 잘림이 viewport 밖으로 노출되지 않음.
- **모바일 fixed 액션바 가림 방지 spacer**: 액션바 바로 위에 `<div class="md:hidden" style="height: 1.5rem;" aria-hidden="true">` 명시적 spacer. Tailwind `pb-*` 큰 값이 빌드에 누락되는 사례 회피 위해 인라인 style.

> **CSS 작성 원칙**: 임의값 / negative margin 류 Tailwind 클래스가 안정적으로 빌드되지 않는 환경이라, 시각 미세 조정은 **인라인 `style`** 또는 **`{% block extra_css %}` 의 `<style>`** 로 직접 명시한다. driving_log 페이지(list/form/detail)의 외부 컨테이너 패딩은 운영 사용자가 직접 조정하는 영역이므로 변경 시 명확한 요청이 있을 때만 손댄다.

### 6.10 [신규 작성 / 편집] 화면 UX (★ 2026-05-28 추가)

- **행 추가 버튼 위치**: 운행 내역 카드 헤더 우측 → **행 리스트 마지막 아래**. 모바일에선 `w-full` 가로 가득 (`md:w-auto` 데스크톱은 기존 자동 너비). 새 행을 여러 번 추가하는 모바일 사용자가 화면 위아래로 왕복하지 않아도 됨.
- **차량번호 자동 복사 (P4.1 유지)**: [+ 행 추가] 시 직전 행의 `vehicle_number` 를 새 행에 미리 채움 (`lastVehicleNumber()` 헬퍼).
- **휴일 체크박스 race fix (P4.1 유지)**: 휴일 체크박스의 `change` 핸들러를 일반 input 루프에서 분리, `userTouched='1'` 셋팅을 먼저 → 그 다음 `markDirty()/recalcRow()`.

### 6.11 [삭제 확인 화면] (★ 2026-05-28 갱신)

기존 `{{ period_start }} ~ {{ period_end }} 운행일지를 영구 삭제합니다.` 문구는 period 가 비어 있는 sheet(아직 일자 미입력) 에서 "~~운행일지" 처럼 빈 자리로 표시되는 버그가 있었다. **`sheet.title` 을 그대로 사용**하도록 변경 (모델/뷰에서 항상 자동 채워짐). 강조(`font-bold text-slate-700`) + `<br>` 줄바꿈 적용.

---

## 7. 이메일 발송 / 휘발성 토큰

### 7.1 발송 트리거

`submit_sheet_api` 호출시 ([driving_log/views.py:274-350](driving_log/views.py#L274-L350)):
1. **필수필드 검증**: 모든 entry 의 일자/시작/종료/누적거리/차량번호가 채워졌는지 확인. 누락 시 행 번호와 함께 400 반환.
2. `DrivingLogSheet.status` 를 `submitted` 로 전이 + `submitted_at`, `reviewer` 기록
3. `ApprovalHistory(action='requested')` 기록 (요청자 IP 포함)
4. `mailing.mailer.send_driving_log_request_mail(sheet)` 호출 — 이 함수 안에서 토큰 2개 생성 후 메일 발송
5. 메일 발송 실패는 결재요청 자체를 막지 않음. 사용자에게 `mail_warning` 만 전달 ([driving_log/views.py:338-344](driving_log/views.py#L338-L344))

토큰은 메일 발송 함수 내부에서 생성된다:
- scope=`approve_reject` (단발성, **72시간 = 3일**) — 승인/반려 한 토큰을 공유, 둘 중 하나가 사용되면 다른 쪽도 자동 무효화
- scope=`history_view` (만료 전까지 다회 조회 가능, **1시간**)

### 7.2 이메일 템플릿 ([templates/emails/driving_log_request.html](templates/emails/driving_log_request.html))

기존 [templates/emails/review_notification.html](templates/emails/review_notification.html) 의 헤더/푸터/색감을 그대로 따라간다.

본문 구성:
- **제목** (★ 2026-05-28 추가): `sheet.title` 을 헤더 직하단에 굵게 노출. 메일 제목줄에는 `[운행일지 결재요청] {요청자} {기간}` 식의 시스템 포맷이 들어가므로, 본문 상단에는 운전기사가 직접 입력한 제목을 표시해 임원이 어떤 운행 건인지 즉시 구분할 수 있게 한다.
- 요청자/기간/일수/합계 초과근무
- 14일 운행 내역 요약 테이블
- 액션 버튼 3개:
  - `[✓ 승인]` → `{site_url}/driving-log/approve/{token}/`
  - `[✕ 반려]` → `{site_url}/driving-log/reject/{token}/`
  - `[📋 승인이력 조회]` → `{site_url}/driving-log/history/{history_token}/`

> 공통 베이스 템플릿 `templates/emails/base_email.html` 은 본 단계에선 생성하지 않았다. `driving_log_request.html` 은 `review_notification.html` 스타일을 복제해서 독립적으로 작성됨.

### 7.3 토큰 보안 및 만료 정책

- **토큰 값**: `UUIDField(default=uuid.uuid4)` — 122비트 엔트로피, 충돌·추측 불가
- **만료 시각**: 생성 시점에 계산되어 `ApprovalToken.expires_at` 에 저장
- **TTL (설정값)** ([mailing/mailer.py:84-85](mailing/mailer.py#L84-L85)):
  - 승인/반려 토큰: `settings.DRIVING_LOG_APPROVE_TTL_HOURS` (기본 **360시간 = 15일**) ★ 2026-05-29 (5차) 72h → 360h 로 확장
  - 이력조회 토큰: `settings.DRIVING_LOG_HISTORY_TTL_HOURS` (기본 **1시간**)
  - 두 변수 모두 `config/settings.py` 에 명시되어 있지 않으면 `getattr` 의 기본값이 사용됨. 운영 중 조정 필요 시 settings 에 추가.
  > **설계 변경 사유**: 초기 설계는 둘 다 1시간 → 임원 부재 대응 위해 승인/반려를 3일(72h) → 다시 **15일(360h)** 로 확장 (2026-05-29). 임원이 장기 출장/휴가 중에도 결재할 수 있도록 충분한 여유 확보. 이력조회는 보안상 1시간 짧게 유지. TTL 이 만료된 건은 기사가 detail 의 [메일 재발송] 으로 직접 새 토큰 발급 가능 (§7.5).
- **단발성/다회 사용**:
  - 승인/반려 토큰: **1회 사용** (`used_at` 기록 후 무효 — `transaction.atomic` + `select_for_update` 로 동시 클릭 방어, [driving_log/views.py:406-415](driving_log/views.py#L406-L415))
  - 이력 조회 토큰: 만료 전까지 다회 조회 가능
- **방어 2차**: 승인/반려 토큰은 `token.executive_id == sheet.reviewer_id` 일치 확인 ([driving_log/views.py:378-380](driving_log/views.py#L378-L380))
- **검증 실패 사유 5종** ([driving_log/views.py:357-381](driving_log/views.py#L357-L381) `_fetch_token`):
  - `not_found` (404), `wrong_scope` (404), `mismatch` (404)
  - `expired` (410), `used` (410)
  - 사유는 `templates/driving_log/token_invalid.html` 에 전달되어 사용자에게 안내
- 모든 토큰 사용은 `ApprovalHistory` 에 `ip_address` 와 함께 기록

### 7.4 발송 함수 구조 ([mailing/mailer.py:55-158](mailing/mailer.py#L55-L158))

> **위치 변경**: 설계 단계의 `driving_log/mailers.py` 가 아닌 `mailing/mailer.py` 안에 함수 추가됨 (§0.5 원칙 반영).

```python
# mailing/mailer.py
def send_driving_log_request_mail(sheet):
    """운행일지 결재 요청 메일 발송.

    수행임원의 이메일로 결재 링크가 포함된 HTML 메일을 보낸다.
    승인/반려 토큰은 3일(72시간), 이력조회 토큰은 1시간 유효.

    기존 AWS SES 백엔드(EMAIL_BACKEND)는 그대로 두고, 본 함수만 그룹웨어 SMTP 서버
    (GROUPWARE_SMTP_*)로 발송한다. 발신자는 운전기사 본인 이메일(sheet.author.email).
    """
    from driving_log.models import ApprovalToken  # 앱 초기화 순서 안전한 lazy import

    executive = sheet.reviewer
    # ... reviewer / to_email / from_email 검증, 누락 시 발송 스킵

    approve_ttl_hours = getattr(settings, 'DRIVING_LOG_APPROVE_TTL_HOURS', 72)
    history_ttl_hours = getattr(settings, 'DRIVING_LOG_HISTORY_TTL_HOURS', 1)
    approve_token = ApprovalToken.objects.create(
        sheet=sheet, executive=executive,
        scope=ApprovalToken.SCOPE_APPROVE_REJECT,
        expires_at=timezone.now() + timedelta(hours=approve_ttl_hours),
    )
    history_token = ApprovalToken.objects.create(
        sheet=None, executive=executive,
        scope=ApprovalToken.SCOPE_HISTORY_VIEW,
        expires_at=timezone.now() + timedelta(hours=history_ttl_hours),
    )

    # 기존 EMAIL_BACKEND(AWS SES) 우회 — 이 발송 건만 그룹웨어 SMTP 사용
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=settings.GROUPWARE_SMTP_HOST,
        port=settings.GROUPWARE_SMTP_PORT,
        use_tls=bool(settings.GROUPWARE_SMTP_USE_TLS),
        username=settings.GROUPWARE_SMTP_USERNAME or '',
        password=settings.GROUPWARE_SMTP_PASSWORD or '',
        timeout=30,
    )
    msg = EmailMessage(
        subject=f"[운행일지 결재요청] {author_name} {period_label}",
        body=html_message,
        from_email=sheet.author.email,   # 운전기사 본인 이메일에서 발송
        to=[executive.email],
        connection=connection,
    )
    msg.content_subtype = "html"
    msg.send()
```

**핵심 설계 결정**:
1. **발신자가 운전기사 본인 이메일**: 임원이 받아봤을 때 "누가 결재 요청을 보냈는지" 가 발신자란에 즉시 보이도록. `sheet.author.email` 이 비어 있으면 발송 스킵 + 경고 로그.
2. **그룹웨어 SMTP 별도 사용**: 기존 ITMS 의 알림 메일(`send_review_notification`)은 AWS SES (`EMAIL_BACKEND`) 로 계속 발송됨. 운행일지 결재 메일만 사내 그룹웨어 SMTP 우회.
3. **메일 실패가 결재요청을 막지 않음**: 메일 발송이 실패해도 sheet 의 `submitted` 상태 전이는 유효. 운전기사에게 경고 메시지만 표시.

### 7.5 메일 재발송 (★ 2026-05-28 추가)

임원이 결재요청 메일을 놓치고 토큰 TTL(72h)이 지나면, 토큰 만료된 submitted sheet 은 임원도 더 이상 처리할 수 없고 기사도 편집/삭제 불가라 dead state 였다. 이를 기사가 직접 풀 수 있도록 **메일 재발송 기능**을 도입.

- **엔드포인트**: `POST /driving-log/api/sheet/<int:pk>/resend/` (`resend_request_mail_api`)
- **노출 위치**: `status=submitted` 인 sheet 의 detail 액션바에 [메일 재발송] 버튼 ([재상신] 자리와 동일 패턴)
- **동작** (`transaction.atomic()` 내부):
  1. 동일 sheet 의 활성 승인/반려 토큰(`scope=approve_reject, used_at IS NULL, expires_at>now()`) 을 모두 `expires_at=now()` 로 즉시 만료시킨다 — 이메일에 남아있던 이전 링크가 더 이상 사용되지 않도록 무효화.
  2. `ApprovalHistory.objects.create(action=ACTION_REQUESTED, comment='메일 재발송', ...)` 로 이력 기록 (별도 action 추가하지 않고 기존 `requested` 재사용).
  3. `send_driving_log_request_mail(sheet)` 를 그대로 호출 → 새 approve_reject + history_view 토큰 발급 + 새 메일 발송.
- **status/reviewer 는 그대로 유지**. 결재선/내용 변경이 필요한 경우엔 [재상신] 이 아니라 admin 강제 처리 또는 임원이 반려한 뒤 [재상신] 으로 다시 진행하는 흐름.
- **방어**: `status != submitted` 이면 400. `reviewer.is_active == False` 이면 400 (비활성 임원 사용 차단).
- **클라이언트 UX**: 버튼 클릭 시 `confirm()` 으로 "이메일에 남아있던 이전 승인/반려 링크는 즉시 무효화됩니다. 계속하시겠습니까?" 한 번 더 확인.

---

## 8. 기존 프로젝트와의 통합 지점 (변경 최소화)

### 8.1 기존 파일 변경 (모두 **추가만**, 기존 동작 보존) — 구현 반영

| 파일 | 변경 내용 | 변경 성격 |
|---|---|---|
| [config/settings.py](config/settings.py) | ① `INSTALLED_APPS` 에 `'driving_log'` 추가 ② `MIDDLEWARE` 에 `driving_log.middleware.DrivingOnlyRedirectMiddleware` 추가 ③ `TEMPLATES.context_processors` 에 `driving_log.context_processors.driving_only_flag` 추가 ④ `GROUPWARE_SMTP_*` 5개 환경변수 추가 (`.env` 빈 값 fallback 패턴) | 추가 |
| [config/urls.py](config/urls.py) | `path('driving-log/', include('driving_log.urls'))` 1줄 추가 | 추가 |
| [mailing/mailer.py](mailing/mailer.py) | 신규 함수 `send_driving_log_request_mail()` 추가. 기존 함수 시그니처 변경 금지. | 추가 |
| [accounts/views.py](accounts/views.py) | `CustomLoginView.get_success_url()` 에 운전 전용 사용자 분기 추가 — 로그인 성공 후 `/driving-log/` 로 직진 ([accounts/views.py:25-31](accounts/views.py#L25-L31)). `is_first_login` 체크 다음, 기존 super() 호출 이전에 삽입되어 기존 흐름 영향 없음. | 추가 |
| [templates/basic.html](templates/basic.html) | ① 사이드바에 `{% if is_driving_only_user %}` 분기 추가 — 운전 전용은 운행일지 메뉴만 노출 ② (★ 2026-05-29) 일반 사용자 블록 내 `{% if user.is_staff or user.is_superuser %}` 분기로 **운행일지 관리** 메뉴 1개 추가 — 일반 사용자에게는 노출되지 않음. | 추가 |

> **사이드바 메뉴 추가**: 본래 설계 §8.1 에서는 `basic.html` 수정을 P6(옵션)으로 미루기로 했으나, **운전 전용 사용자 격리** 기능을 위해 P3 단계에서 함께 반영되었다. 일반 사용자의 사이드바는 100% 동일하게 유지된다.

### 8.2 신규 생성 파일 — 구현 반영

```
driving_log/                          # 신규 앱
├── __init__.py
├── apps.py                           # post_migrate signal 로 driving_log_users 그룹 자동 생성
├── admin.py                          # Executive / Sheet / Entry / Token / History 모두 등록
├── models.py
├── views.py
├── urls.py
├── forms.py                          # 현재 비어 있음 (헤더 메타 폼 없음 — 주석만 존재)
├── permissions.py                    # is_driving_log_user / is_driving_log_admin / is_driving_log_only_user
│                                     # + DrivingLogUserRequiredMixin / DrivingLogAdminRequiredMixin
├── middleware.py                     # ★ 신규 추가: DrivingOnlyRedirectMiddleware
├── context_processors.py             # ★ 신규 추가: driving_only_flag (basic.html 분기용)
├── overtime.py                       # 초과근무 계산 헬퍼 (calc_overtime_minutes, format_minutes)
├── migrations/
│   └── 0001_initial.py               # 개발 단계 — 모델 변경 시 0001 을 직접 갱신하고 DB 를 재생성한다 (마이그레이션 누적 회피)
└── tests.py

# driving_log_users 그룹 자동 생성은 driving_log/apps.py 의 post_migrate signal 로 처리

templates/driving_log/                # 신규 템플릿 폴더
├── driving_log_list.html
├── driving_log_form.html
├── driving_log_detail.html
├── driving_log_confirm_delete.html   # ★ 추가됨 (DeleteView 의 confirm 페이지)
├── approve_page.html                 # 2026-05-28: 모바일 카드 / 데스크톱 테이블 분기 적용
├── reject_page.html                  # 2026-05-28: 모바일 카드 / 데스크톱 테이블 분기 적용
├── history_page.html                 # 2026-05-28: 카드/행 → 상세(history_sheet_detail) 링크
├── history_sheet_detail.html         # ★ 2026-05-28: history scope 토큰 기반 read-only 상세
├── token_invalid.html                # 2026-05-28: scope 별 만료 안내 분기
├── no_permission.html
├── _status_badge.html                # ★ 2026-05-29: 상태 뱃지 공통 partial (admin 화면에서 include)
├── admin_sheet_list.html             # ★ 2026-05-29: 지원팀 관리자 목록 (필터 + 페이지네이션 + CSV)
└── admin_sheet_detail.html           # ★ 2026-05-29: 지원팀 관리자 read-only 상세 + 결재 이력 타임라인

templates/emails/
└── driving_log_request.html          # 결재요청 메일
# base_email.html — 현재 미생성 (필요 시 추후 추가)
```

> mailer 는 `driving_log/mailers.py` 가 아닌 **[mailing/mailer.py](mailing/mailer.py) 내부에 신규 함수로 추가**한다 (피드백 #0 반영). 이메일 발송은 공통 성격이 강하므로 mailing 앱에 집중시킨다.

### 8.3 환경변수 (`.env`) — 신규 추가

운행일지 결재 메일은 그룹웨어 SMTP 를 별도로 사용하므로 아래 5개 환경변수가 추가되었다 ([config/settings.py:142-148](config/settings.py#L142-L148)). 빈 값(`KEY=`) 으로 두면 코드의 fallback 값이 적용된다:

| 환경변수 | 기본값 (fallback) | 용도 |
|---|---|---|
| `GROUPWARE_SMTP_HOST` | `'192.9.200.145'` | 그룹웨어 SMTP 서버 |
| `GROUPWARE_SMTP_PORT` | `587` | SMTP 포트 |
| `GROUPWARE_SMTP_USE_TLS` | `0` (False) | TLS 사용 여부 (0/1) |
| `GROUPWARE_SMTP_USERNAME` | `''` | 인증 ID (필요 시) |
| `GROUPWARE_SMTP_PASSWORD` | `''` | 인증 PW (필요 시) |

추가로 토큰 TTL 을 조정하려면 다음 두 변수를 `settings.py` 에 추가:
- `DRIVING_LOG_APPROVE_TTL_HOURS` (기본 72)
- `DRIVING_LOG_HISTORY_TTL_HOURS` (기본 1)

---

## 9. 권한 / 데이터 격리

### 9.1 운전자 뷰 (driving_log_users 또는 driving_log_managers 그룹 필요)

```python
# driving_log/permissions.py — 구현 반영 (★ 2026-05-29 권한 모델 재정렬)
DRIVING_LOG_USER_GROUP = 'driving_log_users'
DRIVING_LOG_MANAGER_GROUP = 'driving_log_managers'   # ★ 신규


def is_driving_log_user(user):
    """운행일지(본인 목록/작성) 접근 권한.

    driving_log_users 또는 driving_log_managers 그룹 소속, 또는 슈퍼유저.
    매니저도 동일 접근을 허용 — 매니저 본인이 운전기사를 겸할 수 있고, 그렇지 않더라도
    본인 목록이 비어 있을 뿐 접근 자체는 막지 않는다 (요건 §1).
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=[DRIVING_LOG_USER_GROUP, DRIVING_LOG_MANAGER_GROUP],
    ).exists()
```

- 모든 운전자 뷰: `DrivingLogUserRequiredMixin` 적용
- 본인 데이터만 노출: `queryset = DrivingLogSheet.objects.filter(author=self.request.user)`
- AJAX 엔드포인트도 동일 데코레이터(`@login_required` + `@user_passes_test(is_driving_log_user)`) 적용

### 9.2 관리자 뷰 — `DrivingLogManagerRequiredMixin` ★ 2026-05-29 권한 모델 재정렬

```python
def is_driving_log_manager(user):
    """운행일지 관리(전체 조회/CSV) 접근 권한.

    driving_log_managers 그룹 소속 또는 슈퍼유저.
    `is_staff` 는 의도적으로 사용하지 않는다 — 기존 ITMS 의 IT 스태프(IT 운영자 등)
    가 운행일지 관리 화면에 자동 노출되지 않도록 격리한다.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=DRIVING_LOG_MANAGER_GROUP).exists()


class DrivingLogManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False
    def test_func(self):
        return is_driving_log_manager(self.request.user)
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return render(self.request, 'driving_log/no_permission.html', status=403)
```

- [DrivingLogAdminListView](driving_log/views.py) / [DrivingLogAdminDetailView](driving_log/views.py) 가 본 Mixin 적용. CSV FBV(`driving_log_admin_csv_export`) 는 `@user_passes_test(is_driving_log_manager)` 적용.
- 기존 `is_driving_log_admin` 와 `DrivingLogAdminRequiredMixin` 은 **제거됨**. `is_staff` 기반 판정은 모두 폐지.
- 매니저는 운전자 뷰도 접근 가능 (§9.1 — `is_driving_log_user` 가 매니저 그룹도 통과시킴).

### 9.3 수행임원 (Executive) — 이메일 토큰 진입

- 토큰 뷰는 로그인 **불필요** — 토큰 자체가 인증
- `ApprovalToken.is_valid()` 검증 실패시 즉시 `token_invalid.html` 페이지
- 임원이 자신에게 할당되지 않은 sheet 의 토큰을 추측해도 UUID(122비트) 충돌이 사실상 불가능 (방어 1차)
- 추가 방어: 토큰의 `executive_id` 와 `sheet.reviewer_id` 일치 확인 (방어 2차)
- Executive 는 시스템 User 와 무관한 외부 결재선 데이터다 — 시스템에 로그인하지 않으며, 본인이 운행일지를 작성하려면 별도 User 계정으로 `driving_log_users` 그룹에 가입해야 한다 (Executive 등록과 무관)

### 9.4 운행일지 전용 사용자 격리 (★ 신규 — 설계서 최초 갱신 시 추가, 2026-05-29 매니저 포함으로 확장)

운행일지 전용 User(전속 운전기사 또는 매니저 전용) 는 ITMS 의 다른 화면(주간보고, 업무 등)을 사용할 필요가 없다. 다음 **3중 격리**로 분리한다.

#### 9.4.1 식별: `is_driving_log_only_user` ([driving_log/permissions.py](driving_log/permissions.py))

```python
def is_driving_log_only_user(user):
    """운행일지 전용 사용자 — 다른 ITMS 메뉴 접근 차단(미들웨어 리다이렉트) 대상.

    그룹이 `{driving_log_users, driving_log_managers}` 의 부분집합일 때만 격리.
    다른 그룹(예: 기존 IT 사용자) 을 함께 가진 사용자는 일반 ITMS 사용자로 통과.

    슈퍼유저 / is_staff 는 절대 격리 대상이 아니다 — 기존 ITMS 도 사용하기 때문.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return False
    group_names = set(user.groups.values_list('name', flat=True))
    if not group_names:
        return False
    return group_names.issubset({DRIVING_LOG_USER_GROUP, DRIVING_LOG_MANAGER_GROUP})
```

판정 기준 (★ 2026-05-29 확장): **그룹 집합이 `{users, managers}` 의 부분집합** + **is_staff/superuser 가 아닐 것** + 그룹 1개 이상. 매니저 전용 사용자도 격리 대상이며, 사이드바에는 [운행일지] + [운행일지 관리] 두 메뉴가 노출된다 (§9.4.4).

#### 9.4.2 미들웨어: `DrivingOnlyRedirectMiddleware` ([driving_log/middleware.py](driving_log/middleware.py))

운전 전용 사용자가 허용 prefix 외의 URL 에 접근하면 `/driving-log/` 로 강제 리다이렉트한다.

허용 prefix:
```
/driving-log/    /admin/    /accounts/    /useraccounts/
/auth/           /logout/   /static/      /media/        /summernote/
```

판정에서 `False` 가 나오는 사용자(슈퍼유저/스태프/기존 ITMS 사용자) 는 미들웨어를 그대로 통과하므로 **기존 동작에 영향이 없다**. 등록은 `MIDDLEWARE` 의 `AuthenticationMiddleware` + `FirstLoginMiddleware` 뒤에 위치 ([config/settings.py:80](config/settings.py#L80)).

#### 9.4.3 로그인 분기 ([accounts/views.py:25-31](accounts/views.py#L25-L31))

`CustomLoginView.get_success_url()` 에서 로그인 직후 운전 전용 사용자는 `/driving-log/` 로 직진. `is_first_login` 체크 직후, `super().get_success_url()` 직전에 위치.

#### 9.4.4 사이드바 분기 ([templates/basic.html](templates/basic.html) + `driving_only_flag` context processor)

`{% if is_driving_only_user %}` 블록으로 사이드바를 분기 (★ 2026-05-29 매니저 분기 추가):
- 격리 사용자 (전용 운전기사 또는 전용 매니저):
  - [운행일지] 메뉴 (항상)
  - [운행일지 관리] 메뉴 (`{% if is_driving_log_manager %}` 일 때만)
- 그 외 (일반 ITMS 사용자 + 슈퍼유저): 기존 ITMS 사이드바 그대로 + AI Assistant 뒤에 `{% if is_driving_log_manager %}` 일 때 [운행일지 관리] 1줄 추가

context processor (`driving_log.context_processors.driving_only_flag`) 가 자동 주입하는 변수 ([config/settings.py:100](config/settings.py#L100)):
- `is_driving_only_user` — 격리 대상 여부
- `is_driving_log_manager` — 매니저(그룹 또는 슈퍼유저) 여부

---

## 10. 단계별 구현 로드맵 — 진행 상황 반영 (2026-05-28)

| Phase | 산출물 | 상태 | 비고 |
|---|---|---|---|
| **P1** | 신규 앱 스캐폴드 + 모델 + 마이그레이션 + Django admin 등록 + 권한 Mixin | ✅ **완료** | `driving_log_users` 그룹 자동 생성 (`apps.py` post_migrate signal). |
| **P2** | 운전자 목록/편집 화면 + 14일 입력 + 초과근무 계산 + 임시저장 | ✅ **완료** | 모바일 폭 입력 정상 동작. |
| **P3** | 결재요청 모달 + 임원 선택 + 메일 함수 추가 + **사이드바 분기 + 운전 전용 사용자 격리** | ✅ **완료** | 그룹웨어 SMTP 백엔드 도입. |
| **P4** | 이메일 진입 페이지 (승인/반려/이력조회) + 토큰 만료 처리 | ✅ **완료** | 승인/반려 토큰은 72시간(3일), 이력조회는 1시간으로 운영. |
| **P4.1** | 운영 피드백 8건 일괄 반영 — 토큰 만료 안내 분기, 모바일 UI 보완, 메일 본문 제목, 차량번호 자동복사, 결재요청 2단계 모달, **반려→재상신 워크플로**, 휴일 체크 race fix, 결재이력 상세 진입 | ✅ **완료 (2026-05-28)** | 본 문서 갱신과 함께 반영. 개발 단계라 0001_initial 만 갱신하고 DB 재생성으로 적용 (마이그레이션 누적 없음). |
| **P4.2** | 추가 피드백 — **메일 재발송 기능**, detail UX 정비(승인/반려 박스 위치 통일, 결재선 정리, mailto 제거), 헤더 폰트/줄바꿈, 운행내역 모바일 stack, viewport 잘림 안전장치, 행 추가 위치 변경, 토큰 만료 문구 개정, 삭제 확인 문구 title 사용 | ✅ **완료 (2026-05-28)** | 마이그레이션 변경 없음. 모든 추가 변경은 템플릿/뷰/URL 만. |
| **P5** | 관리자 목록/상세 + 필터 + CSV 내보내기 + 결재 이력 타임라인 + 사이드바 진입점 | ✅ **완료 (2026-05-29)** | `DrivingLogAdminListView` / `DrivingLogAdminDetailView` / `driving_log_admin_csv_export` 신설. 강제 상태변경은 Django admin 으로 위임 (상세 화면 하단 직링크). 마이그레이션 변경 없음. |
| **P5.1** | 권한 모델 재정렬 — 신규 그룹 `driving_log_managers` 도입, `is_staff` 의존 제거, 격리 미들웨어가 매니저 포함 | ✅ **완료 (2026-05-29)** | 기존 IT 스태프가 운행일지 관리 화면에 자동 노출되던 문제 해결. `is_driving_log_admin` / `DrivingLogAdminRequiredMixin` 폐기, `is_driving_log_manager` / `DrivingLogManagerRequiredMixin` 로 대체. apps.py 의 post_migrate signal 이 신규 그룹도 자동 생성. |
| **P5.2** | 관리자 목록/CSV 운영 피드백 11건 — 일자 필터 6개로 명확화(결재요청일/결재완료일/운행일 × from-to), draft 항상 제외, 운전기사 한국명 표시, 컬럼명 갱신(운행기간/건수/결재요청일/결재완료일), 제목 컬럼 신규 추가, CSV 버튼 위치 이동, 페이지 설명 문구 제거, 상세의 Django admin 직링크 제거 | ✅ **완료 (2026-05-29)** | 운행일 필터는 entries 조인(distinct) — sheet 의 작성기간이 아니라 실제 운행일 항목 매칭. 모델/마이그레이션 변경 0건. |
| **P6** | 테스트 작성 (사이드바 메뉴는 P3 로 이동) | ⏳ **미착수** | `python manage.py test driving_log` 미작성. |
| **P7** | **운행시간 캐시 컬럼 신설 + 전 화면 노출** | ✅ **완료 (2026-05-29)** | `DrivingLogEntry.run_minutes` / `DrivingLogSheet.total_run_minutes` 추가 (Entry.save() 자동 계산·합계 갱신). `calc_run_minutes` 헬퍼 (overtime.py). 모든 화면(편집/운전자 상세/매니저 상세/임원 결재·반려·이력 상세/이메일 본문/CSV) 에 행별 + 합계 노출. 마이그레이션: 0001_initial 직접 갱신 + dev DB 재생성 (개발 정책). |

각 Phase 는 독립 PR 로 분리 가능. 현재 MVP + 결재 + 재상신 + 메일 재발송 + **관리자 화면** 흐름은 P1~P5 로 완성된 상태이며, 운영 가능. P6 (테스트) 는 향후 우선순위에 따라 진행.

---

## 11. 테스트 시나리오 (수동 QA)

1. 운전자 A: 6일치 작성 (월~토) → 임시저장 → 목록에 draft 카드
2. 토요일 자동 휴일 체크 확인, 운행 8시간 → 480분 초과
3. 평일 08:00~19:00 → 120분 초과 (정규시간 외 1h+1h)
4. 14일 추가 시도 → 15번째 추가 차단 토스트
5. 결재요청 → 임원 선택 → 메일 수신
6. 메일의 [승인] 클릭 → 상태 approved, 운전자 목록에 emerald 배지
7. 같은 토큰 재클릭 → "이미 사용된 토큰" 페이지
8. 1시간 후 토큰 만료 확인
9. 이력조회 링크로 과거 결재내역 조회 (다회)
10. 관리자: 전체 운전자 조회 + 기간 필터 + CSV 내보내기

---

## 12. 미해결 / 후속 결정 필요 항목

- [x] ~~**자정 넘는 운행 처리 정책**~~ — 2026-05-29 결정: 추가 컬럼 없이 현행 0분 처리 유지. 자정 넘는 운행은 운전자가 **일자 2건으로 분리 입력**하도록 운용 가이드.
- [x] ~~임시저장 자동저장 주기~~ — 명시적 [임시저장] 버튼 방식으로 단순화됨. 자동저장 미구현.
- [x] ~~**동시에 여러 sheet 진행 가능 여부**~~ — 결정: 제약 없음 (운전자가 여러 미결 sheet 보유 가능). 현행 유지.
- [x] ~~**동일 운전자가 동일 일자를 여러 sheet 에 작성하는 것 허용?**~~ — 2026-05-29 결정: **허용** (운전자 단위 unique 제약 추가하지 않음).
- [x] ~~사이드바 메뉴 추가~~ — P3 에서 [templates/basic.html](templates/basic.html) 분기로 반영 완료.
- [ ] **운행일지 첨부파일 필요 여부** — 현재 미포함. 운영 중 명시적 요청 발생 시 worklog 의 `WorklogFile` 패턴으로 추가 (보류).
- [x] ~~**반려 후 재제출시 이전 결재이력 표시 정책**~~ — 2026-05-28 해결: 원본 sheet 은 `rejected_resubmitted` 로 종결되어 list/detail 에 그대로 남고, 새 sheet 으로 `resubmitted_to` FK 가 연결됨. 운전자 detail 에서 양방향 추적 가능, 임원도 결재이력 페이지에서 두 문서 모두 확인.
- [x] ~~**승인/반려 토큰 TTL 적정성**~~ — 2026-05-29 결정: **15일(360h)** 로 확장 (기존 72h). 임원 장기 부재(출장/휴가) 대응. 만료 시 기사가 detail 의 [메일 재발송] 으로 직접 풀 수 있음.
- [x] ~~**P5 (관리자 커스텀 페이지)**~~ — 2026-05-29 완료. `admin/sheets/` 목록+필터+CSV+상세+이력 타임라인. 강제 변경은 Django admin 위임.
- [x] ~~**관리자 목록의 운행시간(합) 컬럼**~~ — 2026-05-29 결정: 추가하지 않음. CSV 다운로드로 별도 분석 가능하므로 화면 컬럼 노출은 불필요.

---

## 13. 검토 이력

**최초 설계 검토 완료 (2026-05-19)**: 본 설계서 §1~§11 검토 후 P1~P4 구현 진행됨.

**현행화 갱신 이력**:

| 일자 | 갱신 항목 | 사유 |
|---|---|---|
| 2026-05-27 | §0, §1, §5~§10, §12 전반 현행화 | 구현 코드와 설계서 정합성 확보. 운영 중 발생한 설계 변경(토큰 TTL, 그룹웨어 SMTP, 운전 전용 사용자 격리 등) 일괄 반영. |
| 2026-05-28 | §2 (status `rejected_resubmitted` + `resubmitted_to` 필드 + `ACTION_RESUBMITTED`), §3 상태 머신, §5 URL (resubmit / history_sheet_detail), §6.2 (휴일 체크 race fix, 차량번호 자동복사), §6.3 (결재요청 모달 2단계 + 재상신 분기), §6.4 (모바일 UI 보완, history 상세 진입, token_invalid scope 별 안내), §6.6 (편집/삭제 정책 — `draft` 만 허용), **§6.8 신규 (재상신 흐름)**, §7.2 (메일 본문에 sheet.title 노출), §8.2 (history_sheet_detail.html 추가, 마이그레이션 0001 직접 갱신), §10 P4.1, §12 (재제출 정책 해결) | 운영 피드백 8건 일괄 반영. 반려 건 처리 방식이 "운전자 재편집(rejected → draft)" 에서 "복제 재상신(rejected → rejected_resubmitted + 신규 draft 생성)" 으로 전환된 것이 가장 큰 구조 변경. |
| 2026-05-28 (2차) | §5 URL (`resend_request_mail_api`), §6.6 차단 정책 표 (resend 행 추가), **§6.9 신규 (detail 화면 UX 정비)**, **§6.10 신규 (form 화면 UX)**, **§6.11 신규 (삭제 확인 화면)**, §6.4 token 만료 문구 갱신, **§7.5 신규 (메일 재발송)**, §10 P4.2 추가 | 운영 사용자 테스트 중 발견된 추가 이슈 반영. 가장 큰 추가는 토큰 만료 시 기사가 직접 재발송할 수 있는 **메일 재발송** 기능. 그 외 detail/form/삭제확인 화면의 시각 통일 + 모바일 잘림·중복 표시 정리. driving_log 페이지의 외부 컨테이너 패딩은 운영 사용자가 직접 조정하는 영역이라 본 문서에서는 권장값을 명시하지 않는다. |
| 2026-05-29 | §5 URL (admin 3개 경로 active 처리), **§6.5 전면 재작성 (관리자 목록/상세/CSV 구현)**, §8.1 basic.html 변경 추가, §8.2 신규 파일 3종(`admin_sheet_list.html` / `admin_sheet_detail.html` / `_status_badge.html`) 추가, §9.2 Mixin 사용처 명시, §10 P5 ✅, §12 (P5 항목 종결 + 운행시간 컬럼 미해결 신규) | **P5 (지원팀 관리자 화면) 구현 완료**. 신규 뷰 3개 — `DrivingLogAdminListView`(필터/페이지네이션 30건), `DrivingLogAdminDetailView`(read-only + 결재 이력 타임라인), `driving_log_admin_csv_export`(공통 필터 헬퍼 `_apply_admin_filters` 로 목록과 일관). 강제 상태변경은 본 화면에서 제공하지 않고 상세 화면 하단의 직링크를 통해 Django admin 으로 위임. 사이드바 진입점은 `is_staff/superuser` 분기로 일반 사용자에게 노출되지 않음. 마이그레이션 변경 없음. |
| 2026-05-29 (7차) | **P7 — 운행시간 모델 캐시 + 전 화면 노출**. §2 (Entry.run_minutes / Sheet.total_run_minutes 추가), §4.4 (Entry.save 가 두 필드 자동 계산), **§4.5 신규 (calc_run_minutes 헬퍼)**, §10 (P7 행 추가), §6.5.3 CSV 컬럼 추가, 모든 운행 내역 표시 화면에 운행시간 컬럼/합계 추가, 마이그레이션 0001_initial 직접 갱신 + dev DB 재생성 | 그동안 초과근무만 관리되고 운행시간(end-start)은 관리되지 않던 갭 해결. 자정 넘는 운행은 일자 2건 분리 정책이라 단순 차감으로 충분. 영향 받은 템플릿: driving_log_form / driving_log_detail / admin_sheet_detail / approve_page / reject_page / history_sheet_detail / emails/driving_log_request. CSV 에도 `운행시간(분)` / `운행시간(표시)` 2컬럼 추가. |
| 2026-05-29 (6차) | §6.5.3 CSV 컬럼: 운행시작일/운행종료일 → **운행기간 단일 컬럼** (yy.mm.dd ~ yy.mm.dd 형식) 통합 | 화면 목록과 CSV 의 운행기간 표시 형식 일치. |
| 2026-05-29 (5차) | §6.5.1 컬럼 헤더(운전기사→**요청자**, 수행임원→**결재자**) + [상세] 컬럼 제거, 일자 표시 포맷 `Y-m-d (H:i)` → `y.m.d (H:i)`, §6.5.3 CSV 컬럼명 동기화, **§7.3 승인/반려 토큰 TTL 72h → 360h(15일) 확장**, §12 정책 결정 항목 다수 종결(자정 운행/중복 sheet/운행시간 컬럼/TTL) | 운영 정책 결정 일괄 반영. 자정 운행은 일자 2건 분리 입력으로 운용. 임원 장기 부재 대응을 위해 TTL 대폭 확장(72h→360h). 컬럼명을 "운전기사/수행임원" → "**요청자/결재자**" 로 결재 워크플로 용어와 통일. y.m.d 포맷으로 컬럼 폭 절약. 모델/마이그레이션 변경 0건. |
| 2026-05-29 (4차) | §6.5.1 필터바 단순화 — 결재요청일/결재완료일 일자필드 4개 제거, 검색어 → 제목 LIKE 단독, 운전기사 드롭다운 신규 | 3차에서 도입한 일자 필드 6개가 UI 가 너무 복잡하다는 피드백. 일자는 **운행일 1쌍만** 유지. 운전기사는 `driving_log_users` 그룹 멤버만 드롭다운 옵션으로. 모델/마이그레이션 변경 0건. |
| 2026-05-29 (3차) | **§6.5.1 목록 화면 전면 재작성** (필터 6개 일자필드로 재구성, draft 항상 제외, 컬럼명 갱신, 제목 컬럼 신규, 운전기사 한국명 표시, CSV 버튼 위치 이동), §6.5.2 (Django admin 직링크 제거), §6.5.3 CSV 컬럼 갱신 | 운영자 피드백 11건 일괄 반영. **핵심 변경**: ① 일자 필터를 의미별로 명확화 (결재요청일/결재완료일/운행일 각 from-to). 특히 운행일은 sheet 의 작성기간이 아니라 entries 의 실제 운행일에 매칭 (distinct join). ② draft 는 운전기사 손에 있는 단계라 관리자 화면에서 항상 제외 (상태 옵션 UI 에서도 숨김). ③ 지원팀은 데이터 수정 조직이 아니므로 강제변경 진입점(상세의 Django admin 직링크) 완전 제거. ④ 운전기사 ID(username) → 한국명(`profile.get_korean_name`) 표시. 모델/마이그레이션 변경 0건. |
| 2026-05-29 (2차) | §1.1 역할 매트릭스 (`driving_log_managers` 그룹 신규 행 추가), §1.2 그룹 운용, §6.5.4 권한, **§9.1/§9.2 전면 재작성 (`is_driving_log_manager` / `DrivingLogManagerRequiredMixin` 도입, `is_driving_log_admin` 폐기)**, §9.4 격리 정의 확장, §9.4.4 사이드바 분기, §10 **P5.1 행 추가** | **P5.1 권한 모델 재정렬**. 운영자 피드백: 기존 `is_staff` 기반 매니저 판정이 기존 ITMS 의 IT 스태프(=IT 운영자) 에게 운행일지 관리 화면을 자동 노출시키는 문제. 해결: 신규 그룹 `driving_log_managers` 도입 후 모든 매니저 판정(뷰 보호 / 사이드바 / context processor) 을 그룹 멤버십(+슈퍼유저) 으로 전환. `is_staff` 의존을 매니저 판정에서 완전 제거. 격리 함수 `is_driving_log_only_user` 는 그룹 집합 `⊆ {users, managers}` 로 확장하여 매니저 전용 사용자도 격리. apps.py 의 post_migrate signal 이 매니저 그룹도 자동 생성. 모델/마이그레이션 변경 없음. |

향후 코드 변경 시 본 설계서를 함께 갱신하여 **항상 코드와 일치하는 단일 소스 오브 트루스(SSOT) 로 유지**한다.
