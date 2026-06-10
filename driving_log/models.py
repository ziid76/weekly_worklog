import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Executive(models.Model):
    """수행임원 마스터.

    시스템 사용자(User)와 무관한 별도의 결재선 마스터 데이터.
    """
    name = models.CharField('이름', max_length=50)
    email = models.EmailField('수신 이메일')
    is_active = models.BooleanField('활성', default=True)
    display_order = models.IntegerField('표시 순서', default=0)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = '수행임원'
        verbose_name_plural = '수행임원'

    def __str__(self):
        return self.name


class DrivingLogSheet(models.Model):
    """운행일지 1건. 최대 14일치 Entry 를 묶어 한 번에 결재한다."""

    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_REJECTED_RESUBMITTED = 'rejected_resubmitted'  # 반려 후 재상신되어 종결된 원본 문서
    STATUS_CHOICES = (
        (STATUS_DRAFT, '임시저장'),
        (STATUS_SUBMITTED, '결재요청'),
        (STATUS_APPROVED, '승인'),
        (STATUS_REJECTED, '반려'),
        (STATUS_REJECTED_RESUBMITTED, '반려(재기안)'),
    )

    MAX_ENTRIES = 14

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='driving_sheets',
        verbose_name='작성자',
    )
    title = models.CharField('제목', max_length=200, blank=True)
    period_start = models.DateField('시작일', null=True, blank=True)
    period_end = models.DateField('종료일', null=True, blank=True)
    status = models.CharField(
        '상태', max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT,
    )

    reviewer = models.ForeignKey(
        Executive, on_delete=models.PROTECT,
        null=True, blank=True, related_name='review_sheets',
        verbose_name='수행임원',
    )
    submitted_at = models.DateTimeField('결재요청 일시', null=True, blank=True)
    reviewed_at = models.DateTimeField('결재처리 일시', null=True, blank=True)
    review_comment = models.TextField('결재 의견', blank=True)

    # 반려 → 재상신 시 원본이 새 문서를 참조한다. 새 문서에서는 reverse(`resubmitted_from`)로 원본 확인.
    resubmitted_to = models.OneToOneField(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resubmitted_from',
        verbose_name='재상신 문서',
    )

    total_overtime_minutes = models.IntegerField('초과근무 합계(분)', default=0)
    total_run_minutes = models.IntegerField('운행시간 합계(분)', default=0)
    created_at = models.DateTimeField('작성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']
        verbose_name = '운행일지'
        verbose_name_plural = '운행일지'

    def __str__(self):
        if self.period_start and self.period_end:
            return f'{self.author.username} {self.period_start} ~ {self.period_end}'
        return f'{self.author.username} 운행일지 #{self.pk}'

    @property
    def total_overtime_display(self):
        m = self.total_overtime_minutes or 0
        return f'{m // 60}시간 {m % 60}분'

    @property
    def total_run_display(self):
        m = self.total_run_minutes or 0
        return f'{m // 60}시간 {m % 60}분'


class DrivingLogEntry(models.Model):
    """운행일지 1행 = 1일치."""

    sheet = models.ForeignKey(
        DrivingLogSheet, on_delete=models.CASCADE, related_name='entries',
        verbose_name='운행일지',
    )
    log_date = models.DateField('일자')
    is_holiday = models.BooleanField(
        '휴일여부', default=False,
        help_text='토/일은 자동 체크, 국가공휴일은 사용자가 직접 체크합니다.',
    )
    start_time = models.TimeField('운행 시작', null=True, blank=True)
    end_time = models.TimeField('운행 종료', null=True, blank=True)
    cumulative_distance = models.DecimalField(
        '누적 주행거리(km)', max_digits=8, decimal_places=1,
        null=True, blank=True,
    )
    vehicle_number = models.CharField('차량번호', max_length=20, blank=True)
    overtime_minutes = models.IntegerField('초과근무(분)', default=0)
    run_minutes = models.IntegerField('운행시간(분)', default=0)

    class Meta:
        ordering = ['log_date', 'id']
        verbose_name = '운행일지 항목'
        verbose_name_plural = '운행일지 항목'

    def __str__(self):
        return f'{self.sheet_id} / {self.log_date}'

    @property
    def run_display(self):
        m = self.run_minutes or 0
        return f'{m // 60}시간 {m % 60}분'

    @property
    def overtime_display(self):
        m = self.overtime_minutes or 0
        return f'{m // 60}시간 {m % 60}분'

    def save(self, *args, **kwargs):
        from .overtime import calc_overtime_minutes, calc_run_minutes
        self.overtime_minutes = calc_overtime_minutes(
            self.log_date, self.start_time, self.end_time, self.is_holiday,
        )
        self.run_minutes = calc_run_minutes(
            self.log_date, self.start_time, self.end_time,
        )
        super().save(*args, **kwargs)
        if self.sheet_id:
            _refresh_sheet_totals(self.sheet_id)

    def delete(self, *args, **kwargs):
        sheet_id = self.sheet_id
        super().delete(*args, **kwargs)
        if sheet_id:
            _refresh_sheet_totals(sheet_id)


def _refresh_sheet_totals(sheet_id):
    """Entry 변경 후 부모 Sheet 의 합계(초과근무+운행시간)를 한 쿼리로 갱신."""
    agg = DrivingLogEntry.objects.filter(sheet_id=sheet_id).aggregate(
        ot=models.Sum('overtime_minutes'),
        run=models.Sum('run_minutes'),
    )
    DrivingLogSheet.objects.filter(pk=sheet_id).update(
        total_overtime_minutes=agg['ot'] or 0,
        total_run_minutes=agg['run'] or 0,
    )


class ApprovalToken(models.Model):
    """이메일 본문의 승인/반려/이력조회 버튼용 휘발성 UUID 토큰.

    - approve_reject: 단발성. used_at 이 기록되면 더 이상 사용 불가.
    - history_view: 만료 전까지 다회 조회 가능.
    """

    SCOPE_APPROVE_REJECT = 'approve_reject'
    SCOPE_HISTORY_VIEW = 'history_view'
    SCOPE_CHOICES = (
        (SCOPE_APPROVE_REJECT, '승인/반려'),
        (SCOPE_HISTORY_VIEW, '이력조회'),
    )

    sheet = models.ForeignKey(
        DrivingLogSheet, on_delete=models.CASCADE, related_name='tokens',
        null=True, blank=True, verbose_name='운행일지',
    )
    executive = models.ForeignKey(
        Executive, on_delete=models.CASCADE, related_name='tokens',
        verbose_name='수행임원',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scope = models.CharField('용도', max_length=20, choices=SCOPE_CHOICES)
    expires_at = models.DateTimeField('만료 일시')
    used_at = models.DateTimeField('사용 일시', null=True, blank=True)
    created_at = models.DateTimeField('생성 일시', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '결재 토큰'
        verbose_name_plural = '결재 토큰'

    def __str__(self):
        return f'{self.scope}/{self.token}'

    def is_valid(self):
        if timezone.now() >= self.expires_at:
            return False
        if self.scope == self.SCOPE_APPROVE_REJECT and self.used_at is not None:
            return False
        return True


class ApprovalHistory(models.Model):
    """결재 감사 로그. 누가 언제 무엇을 했는지 기록한다."""

    ACTION_REQUESTED = 'requested'
    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_RESUBMITTED = 'resubmitted'
    ACTION_VIEWED_HISTORY = 'viewed_history'
    ACTION_CHOICES = (
        (ACTION_REQUESTED, '결재요청'),
        (ACTION_APPROVED, '승인'),
        (ACTION_REJECTED, '반려'),
        (ACTION_RESUBMITTED, '재상신'),
        (ACTION_VIEWED_HISTORY, '이력조회'),
    )

    sheet = models.ForeignKey(
        DrivingLogSheet, on_delete=models.CASCADE, related_name='history',
        null=True, blank=True, verbose_name='운행일지',
    )
    actor_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='행위자(사용자)',
    )
    actor_executive = models.ForeignKey(
        Executive, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='행위자(수행임원)',
    )
    action = models.CharField('동작', max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField('코멘트', blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    created_at = models.DateTimeField('일시', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '결재 이력'
        verbose_name_plural = '결재 이력'

    def __str__(self):
        return f'{self.action} @ {self.created_at:%Y-%m-%d %H:%M}'
