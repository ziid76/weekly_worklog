import json
import logging
from datetime import date, datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST

from django.views.generic import DeleteView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import ExecutiveForm
from .models import ApprovalHistory, ApprovalToken, DrivingLogEntry, DrivingLogSheet, Executive
from .overtime import format_minutes
from .permissions import (
    DRIVING_LOG_USER_GROUP,
    DrivingLogManagerRequiredMixin,
    DrivingLogUserRequiredMixin,
    is_driving_log_manager,
    is_driving_log_user,
)

logger = logging.getLogger(__name__)


def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def no_permission(request):
    """driving_log_users 그룹에 속하지 않은 사용자가 진입 시 안내 페이지."""
    return render(request, 'driving_log/no_permission.html', status=403)


class DrivingLogSheetListView(DrivingLogUserRequiredMixin, ListView):
    template_name = 'driving_log/driving_log_list.html'
    context_object_name = 'sheets'
    paginate_by = 20

    def get_queryset(self):
        return (
            DrivingLogSheet.objects
            .filter(author=self.request.user)
            .select_related('reviewer')
        )


class DrivingLogSheetCreateView(DrivingLogUserRequiredMixin, View):
    """[신규 작성] 클릭 시 빈 sheet 를 즉시 만들고 편집 화면으로 redirect.

    헤더에 별도 메타 입력 폼이 없으므로 생성 화면을 따로 두지 않는다.
    사용자가 임시저장 한 번 안 눌러도 목록에서 식별 가능하도록 작성일자 기반 기본 제목을 부여한다.
    """

    def get(self, request, *args, **kwargs):
        sheet = DrivingLogSheet.objects.create(
            author=request.user, status=DrivingLogSheet.STATUS_DRAFT,
        )
        sheet.title = f'{sheet.created_at:%Y-%m-%d} 운행일지'
        sheet.save(update_fields=['title'])
        return redirect('driving_log:driving_log_edit', pk=sheet.pk)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class DrivingLogSheetEditView(DrivingLogUserRequiredMixin, DetailView):
    """편집 화면. 메타 폼 없음. 14일 항목은 AJAX 로 저장."""

    model = DrivingLogSheet
    template_name = 'driving_log/driving_log_form.html'
    context_object_name = 'sheet'

    def get_queryset(self):
        return DrivingLogSheet.objects.filter(author=self.request.user)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # 반려/재기안종결/결재요청/승인 상태는 편집 불가 — 상세로 보낸다.
        # 반려 건은 상세에서 [재상신] 버튼으로만 진행. (편집 가능한 상태는 draft 만)
        if self.object.status != DrivingLogSheet.STATUS_DRAFT:
            return redirect('driving_log:driving_log_detail', pk=self.object.pk)
        ctx = self.get_context_data(object=self.object)
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'edit'
        ctx['MAX_ENTRIES'] = DrivingLogSheet.MAX_ENTRIES
        entries = list(self.object.entries.all().order_by('log_date'))
        ctx['entries_data'] = [
            {
                'id': e.id,
                'log_date': e.log_date.isoformat() if e.log_date else '',
                'is_holiday': e.is_holiday,
                'start_time': e.start_time.strftime('%H:%M') if e.start_time else '',
                'end_time': e.end_time.strftime('%H:%M') if e.end_time else '',
                'cumulative_distance': float(e.cumulative_distance) if e.cumulative_distance is not None else None,
                'vehicle_number': e.vehicle_number or '',
                'overtime_minutes': e.overtime_minutes or 0,
                'run_minutes': e.run_minutes or 0,
            }
            for e in entries
        ]
        ctx['total_overtime_display'] = format_minutes(self.object.total_overtime_minutes)
        ctx['total_run_display'] = format_minutes(self.object.total_run_minutes)
        return ctx


class DrivingLogSheetDeleteView(DrivingLogUserRequiredMixin, DeleteView):
    model = DrivingLogSheet
    template_name = 'driving_log/driving_log_confirm_delete.html'
    success_url = reverse_lazy('driving_log:driving_log_list')

    def get_queryset(self):
        # 반려 건은 더 이상 편집/삭제 모두 차단(재상신 워크플로로만 진행). draft 만 삭제 가능.
        return DrivingLogSheet.objects.filter(
            author=self.request.user,
            status=DrivingLogSheet.STATUS_DRAFT,
        )


class DrivingLogSheetDetailView(DrivingLogUserRequiredMixin, DetailView):
    model = DrivingLogSheet
    template_name = 'driving_log/driving_log_detail.html'
    context_object_name = 'sheet'

    def get_queryset(self):
        return DrivingLogSheet.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entries'] = self.object.entries.all().order_by('log_date')
        ctx['total_overtime_display'] = format_minutes(self.object.total_overtime_minutes)
        ctx['total_run_display'] = format_minutes(self.object.total_run_minutes)
        return ctx


def _parse_time(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%H:%M').time()
    except ValueError:
        return None


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


@require_POST
@login_required
@user_passes_test(is_driving_log_user)
def save_sheet_api(request, pk):
    """임시저장 / 편집 저장 AJAX 엔드포인트.

    payload 예시:
    {
      "title": "...",
      "entries": [
        {"log_date":"2026-05-01","is_holiday":false,"start_time":"09:00","end_time":"18:00",
         "cumulative_distance":120.5,"vehicle_number":"서울 12가 1234"},
        ...
      ]
    }
    """
    sheet = get_object_or_404(DrivingLogSheet, pk=pk, author=request.user)
    if sheet.status != DrivingLogSheet.STATUS_DRAFT:
        return JsonResponse(
            {'success': False, 'error': '임시저장 상태가 아닌 운행일지는 수정할 수 없습니다.'},
            status=400,
        )

    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    entries_data = payload.get('entries', []) or []
    if len(entries_data) > DrivingLogSheet.MAX_ENTRIES:
        return JsonResponse(
            {'success': False, 'error': f'최대 {DrivingLogSheet.MAX_ENTRIES}일까지 작성 가능합니다.'},
            status=400,
        )

    # 단순 구현: 기존 entries 전체 삭제 후 재생성. 동시편집 가능성이 낮은 1인용 양식이므로 OK.
    sheet.entries.all().delete()

    saved_dates = []
    for ed in entries_data:
        log_date = _parse_date(ed.get('log_date'))
        if log_date is None:
            continue  # 일자 없는 행은 스킵

        DrivingLogEntry.objects.create(
            sheet=sheet,
            log_date=log_date,
            is_holiday=bool(ed.get('is_holiday')),
            start_time=_parse_time(ed.get('start_time')),
            end_time=_parse_time(ed.get('end_time')),
            cumulative_distance=ed.get('cumulative_distance') or None,
            vehicle_number=(ed.get('vehicle_number') or '').strip(),
        )
        saved_dates.append(log_date)

    if saved_dates:
        sheet.period_start = min(saved_dates)
        sheet.period_end = max(saved_dates)
    else:
        sheet.period_start = None
        sheet.period_end = None

    # 합계 메모리 동기화: Entry.save 가 DB 의 sheet 합계를 갱신했지만 메모리상의 sheet 객체는
    # 갱신되지 않으므로, sheet.save() 가 옛 값으로 덮어쓰지 않도록 직접 재계산. (초과근무 + 운행시간)
    agg = sheet.entries.aggregate(
        ot=Sum('overtime_minutes'),
        run=Sum('run_minutes'),
    )
    sheet.total_overtime_minutes = agg['ot'] or 0
    sheet.total_run_minutes = agg['run'] or 0

    # 제목: 사용자 입력 우선, 비워두면 일자 범위로 자동 생성
    user_title = (payload.get('title') or '').strip()
    if user_title:
        sheet.title = user_title
    elif sheet.period_start and sheet.period_end:
        if sheet.period_start == sheet.period_end:
            sheet.title = f'{sheet.period_start:%Y-%m-%d} 운행일지'
        else:
            sheet.title = f'{sheet.period_start:%Y-%m-%d} ~ {sheet.period_end:%Y-%m-%d} 운행일지'
    else:
        sheet.title = f'{sheet.created_at:%Y-%m-%d} 운행일지'
    sheet.save()
    sheet.refresh_from_db()

    return JsonResponse({
        'success': True,
        'total_overtime_minutes': sheet.total_overtime_minutes,
        'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
        'total_run_minutes': sheet.total_run_minutes,
        'total_run_display': format_minutes(sheet.total_run_minutes),
        'period_start': sheet.period_start.isoformat() if sheet.period_start else None,
        'period_end': sheet.period_end.isoformat() if sheet.period_end else None,
        'entries': [
            {
                'id': e.id,
                'log_date': e.log_date.isoformat(),
                'is_holiday': e.is_holiday,
                'overtime_minutes': e.overtime_minutes,
                'run_minutes': e.run_minutes,
            }
            for e in sheet.entries.all().order_by('log_date')
        ],
    })


@require_GET
@login_required
@user_passes_test(is_driving_log_user)
def executives_api(request):
    """결재요청 모달에서 표시할 수행임원 목록."""
    qs = (
        Executive.objects.filter(is_active=True)
        .order_by('display_order', 'name')
    )
    return JsonResponse({
        'success': True,
        'executives': [
            {'id': e.id, 'name': e.name, 'email': e.email}
            for e in qs
        ],
    })


@require_POST
@login_required
@user_passes_test(is_driving_log_user)
def submit_sheet_api(request, pk):
    """결재요청. sheet 상태를 submitted 로 전이하고 메일 발송."""
    sheet = get_object_or_404(DrivingLogSheet, pk=pk, author=request.user)
    if sheet.status != DrivingLogSheet.STATUS_DRAFT:
        return JsonResponse(
            {'success': False, 'error': '임시저장 상태가 아닌 운행일지는 결재요청할 수 없습니다.'},
            status=400,
        )
    if sheet.entries.count() == 0:
        return JsonResponse(
            {'success': False, 'error': '운행 내역을 1건 이상 입력해주세요.'},
            status=400,
        )

    # 휴일여부 외 모든 필드 필수 — 클라이언트 검증을 우회한 요청 차단
    for idx, e in enumerate(sheet.entries.all().order_by('log_date'), start=1):
        missing = []
        if not e.log_date:           missing.append('일자')
        if not e.start_time:         missing.append('운행 시작')
        if not e.end_time:           missing.append('운행 종료')
        if e.cumulative_distance is None: missing.append('누적거리')
        if not e.vehicle_number:     missing.append('차량번호')
        if missing:
            return JsonResponse(
                {'success': False,
                 'error': f'{idx}번째 행의 필수 항목이 누락되었습니다: {", ".join(missing)}'},
                status=400,
            )

    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    executive_id = payload.get('executive_id')
    if not executive_id:
        return JsonResponse(
            {'success': False, 'error': '수행임원을 선택해주세요.'},
            status=400,
        )

    try:
        executive = Executive.objects.get(pk=executive_id, is_active=True)
    except Executive.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': '유효하지 않은 수행임원입니다.'},
            status=400,
        )

    sheet.reviewer = executive
    sheet.status = DrivingLogSheet.STATUS_SUBMITTED
    sheet.submitted_at = timezone.now()
    sheet.review_comment = ''  # 재제출인 경우 이전 반려 코멘트 초기화
    sheet.reviewed_at = None
    sheet.save()

    ApprovalHistory.objects.create(
        sheet=sheet,
        actor_user=request.user,
        action=ApprovalHistory.ACTION_REQUESTED,
        ip_address=_client_ip(request),
    )

    mail_warning = None
    try:
        from mailing.mailer import send_driving_log_request_mail
        send_driving_log_request_mail(sheet)
    except Exception as e:
        # 메일 실패는 결재요청 자체를 막지 않음. 사용자에게 경고만 전달.
        logger.warning(f"결재요청 메일 발송 실패: sheet={sheet.id}, error={e}")
        mail_warning = '메일 발송에 실패했습니다. 관리자에게 문의해주세요.'

    return JsonResponse({
        'success': True,
        'redirect_url': reverse('driving_log:driving_log_detail', args=[sheet.pk]),
        'mail_warning': mail_warning,
    })


@require_POST
@login_required
@user_passes_test(is_driving_log_user)
def resubmit_sheet_api(request, pk):
    """반려된 운행일지를 재상신용 신규 draft 로 복제하고 원본을 종결한다.

    동작:
      1. 원본은 status=rejected, resubmitted_to is None 이어야 한다 (방어).
      2. 트랜잭션 내에서:
         - 새 sheet 를 draft 로 생성 (title 에 '(재상신) ' 접두, reviewer/메타 복제).
         - 원본 entries 를 새 sheet 로 복제.
         - 원본 sheet.status = rejected_resubmitted, resubmitted_to = 새 sheet 로 종결 마킹.
         - ApprovalHistory.ACTION_RESUBMITTED 기록.
      3. 새 sheet 의 편집 URL 반환 (클라이언트가 redirect).
    """
    sheet = get_object_or_404(DrivingLogSheet, pk=pk, author=request.user)
    if sheet.status != DrivingLogSheet.STATUS_REJECTED:
        return JsonResponse(
            {'success': False, 'error': '반려된 운행일지에서만 재상신할 수 있습니다.'},
            status=400,
        )
    if sheet.resubmitted_to_id is not None:
        return JsonResponse(
            {'success': False, 'error': '이미 재상신된 운행일지입니다.'},
            status=400,
        )

    base_title = sheet.title or ''
    if not base_title.startswith('(재상신)'):
        new_title = f'(재상신) {base_title}'.strip()
    else:
        new_title = base_title

    with transaction.atomic():
        # 한 번 더 select_for_update 로 동시 클릭 방어
        locked = (
            DrivingLogSheet.objects
            .select_for_update()
            .get(pk=sheet.pk)
        )
        if locked.status != DrivingLogSheet.STATUS_REJECTED or locked.resubmitted_to_id is not None:
            return JsonResponse(
                {'success': False, 'error': '이미 재상신된 운행일지입니다.'},
                status=400,
            )

        new_sheet = DrivingLogSheet.objects.create(
            author=locked.author,
            title=new_title,
            period_start=locked.period_start,
            period_end=locked.period_end,
            status=DrivingLogSheet.STATUS_DRAFT,
            reviewer=locked.reviewer,
        )
        # entries 복제 (save() 가 overtime 재계산 + sheet 합계 갱신을 해 줌)
        for e in locked.entries.all().order_by('log_date'):
            DrivingLogEntry.objects.create(
                sheet=new_sheet,
                log_date=e.log_date,
                is_holiday=e.is_holiday,
                start_time=e.start_time,
                end_time=e.end_time,
                cumulative_distance=e.cumulative_distance,
                vehicle_number=e.vehicle_number,
            )

        locked.status = DrivingLogSheet.STATUS_REJECTED_RESUBMITTED
        locked.resubmitted_to = new_sheet
        locked.save(update_fields=['status', 'resubmitted_to', 'updated_at'])

        ApprovalHistory.objects.create(
            sheet=locked,
            actor_user=request.user,
            action=ApprovalHistory.ACTION_RESUBMITTED,
            ip_address=_client_ip(request),
            comment=f'재상신 → sheet #{new_sheet.id}',
        )

    return JsonResponse({
        'success': True,
        'new_sheet_id': new_sheet.id,
        'redirect_url': reverse('driving_log:driving_log_edit', args=[new_sheet.pk]),
    })


@require_POST
@login_required
@user_passes_test(is_driving_log_user)
def resend_request_mail_api(request, pk):
    """결재요청 메일 재발송.

    토큰이 만료되었거나 임원이 메일을 놓친 경우를 대비해, status=submitted 인 sheet 에 대해
    기존 활성 토큰을 무효화하고 새 토큰 + 새 메일을 발송한다. status/reviewer 는 그대로 유지.
    """
    sheet = get_object_or_404(DrivingLogSheet, pk=pk, author=request.user)
    if sheet.status != DrivingLogSheet.STATUS_SUBMITTED:
        return JsonResponse(
            {'success': False, 'error': '결재요청 중인 운행일지만 재발송할 수 있습니다.'},
            status=400,
        )
    if not sheet.reviewer or not sheet.reviewer.is_active:
        return JsonResponse(
            {'success': False, 'error': '결재선 임원이 비활성 상태입니다. 관리자에게 문의해주세요.'},
            status=400,
        )

    with transaction.atomic():
        # 이메일에 남아있는 이전 승인/반려 링크가 사용되지 않도록 즉시 만료시킨다.
        ApprovalToken.objects.filter(
            sheet=sheet,
            scope=ApprovalToken.SCOPE_APPROVE_REJECT,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).update(expires_at=timezone.now())

        ApprovalHistory.objects.create(
            sheet=sheet,
            actor_user=request.user,
            action=ApprovalHistory.ACTION_REQUESTED,
            comment='메일 재발송',
            ip_address=_client_ip(request),
        )

    mail_warning = None
    try:
        from mailing.mailer import send_driving_log_request_mail
        send_driving_log_request_mail(sheet)
    except Exception as e:
        logger.warning(f"결재요청 메일 재발송 실패: sheet={sheet.id}, error={e}")
        mail_warning = '메일 발송에 실패했습니다. 관리자에게 문의해주세요.'

    return JsonResponse({'success': True, 'mail_warning': mail_warning})


# ---------------------------------------------------------------------------
# 이메일 토큰 진입 (수행임원용, 로그인 불필요)
# ---------------------------------------------------------------------------

def _fetch_token(token_uuid, expected_scope):
    """토큰 조회 + 유효성 검사. 실패시 (None, reason) 반환.

    reason: 'not_found' | 'expired' | 'used' | 'wrong_scope' | 'mismatch'
    """
    try:
        tok = (
            ApprovalToken.objects
            .select_related('executive', 'sheet', 'sheet__author', 'sheet__reviewer')
            .get(token=token_uuid)
        )
    except ApprovalToken.DoesNotExist:
        return None, 'not_found'

    if tok.scope != expected_scope:
        return None, 'wrong_scope'
    if timezone.now() >= tok.expires_at:
        return None, 'expired'
    if tok.scope == ApprovalToken.SCOPE_APPROVE_REJECT and tok.used_at is not None:
        return None, 'used'
    # 방어 2차: approve_reject 는 sheet.reviewer 와 token.executive 가 일치해야 한다.
    if tok.scope == ApprovalToken.SCOPE_APPROVE_REJECT:
        if not tok.sheet or tok.sheet.reviewer_id != tok.executive_id:
            return None, 'mismatch'
    return tok, None


def _render_token_invalid(request, reason, scope=None):
    return render(
        request,
        'driving_log/token_invalid.html',
        {'reason': reason, 'scope': scope},
        status=410 if reason in ('expired', 'used') else 404,
    )


def approve_via_email(request, token):
    """이메일의 [✓ 승인] 진입. GET: 확인 페이지, POST: 승인 처리."""
    tok, err = _fetch_token(token, ApprovalToken.SCOPE_APPROVE_REJECT)
    if err:
        return _render_token_invalid(request, err, scope=ApprovalToken.SCOPE_APPROVE_REJECT)

    sheet = tok.sheet
    if request.method == 'POST':
        # 이미 처리된 sheet 인 경우(다른 토큰/관리자 강제변경 등) 방어
        if sheet.status != DrivingLogSheet.STATUS_SUBMITTED:
            return _render_token_invalid(request, 'used')

        comment = (request.POST.get('comment') or '').strip()
        with transaction.atomic():
            tok_locked = (
                ApprovalToken.objects
                .select_for_update()
                .get(pk=tok.pk)
            )
            if tok_locked.used_at is not None:
                return _render_token_invalid(request, 'used')
            tok_locked.used_at = timezone.now()
            tok_locked.save(update_fields=['used_at'])

            sheet.status = DrivingLogSheet.STATUS_APPROVED
            sheet.reviewed_at = timezone.now()
            sheet.review_comment = comment
            sheet.save(update_fields=['status', 'reviewed_at', 'review_comment'])

            ApprovalHistory.objects.create(
                sheet=sheet,
                actor_executive=tok.executive,
                action=ApprovalHistory.ACTION_APPROVED,
                comment=comment,
                ip_address=_client_ip(request),
            )

        return render(request, 'driving_log/approve_page.html', {
            'sheet': sheet,
            'executive': tok.executive,
            'entries': sheet.entries.all().order_by('log_date'),
            'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
            'total_run_display': format_minutes(sheet.total_run_minutes),
            'done': True,
            'comment': comment,
        })

    # GET: 확인 페이지
    return render(request, 'driving_log/approve_page.html', {
        'sheet': sheet,
        'executive': tok.executive,
        'entries': sheet.entries.all().order_by('log_date'),
        'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
        'total_run_display': format_minutes(sheet.total_run_minutes),
        'done': False,
    })


def reject_via_email(request, token):
    """이메일의 [✕ 반려] 진입. 반려사유 필수."""
    tok, err = _fetch_token(token, ApprovalToken.SCOPE_APPROVE_REJECT)
    if err:
        return _render_token_invalid(request, err, scope=ApprovalToken.SCOPE_APPROVE_REJECT)

    sheet = tok.sheet
    error_message = None
    comment_value = ''

    if request.method == 'POST':
        if sheet.status != DrivingLogSheet.STATUS_SUBMITTED:
            return _render_token_invalid(request, 'used')

        comment_value = (request.POST.get('comment') or '').strip()
        if not comment_value:
            error_message = '반려 사유를 입력해주세요.'
        else:
            with transaction.atomic():
                tok_locked = (
                    ApprovalToken.objects
                    .select_for_update()
                    .get(pk=tok.pk)
                )
                if tok_locked.used_at is not None:
                    return _render_token_invalid(request, 'used')
                tok_locked.used_at = timezone.now()
                tok_locked.save(update_fields=['used_at'])

                sheet.status = DrivingLogSheet.STATUS_REJECTED
                sheet.reviewed_at = timezone.now()
                sheet.review_comment = comment_value
                sheet.save(update_fields=['status', 'reviewed_at', 'review_comment'])

                ApprovalHistory.objects.create(
                    sheet=sheet,
                    actor_executive=tok.executive,
                    action=ApprovalHistory.ACTION_REJECTED,
                    comment=comment_value,
                    ip_address=_client_ip(request),
                )

            return render(request, 'driving_log/reject_page.html', {
                'sheet': sheet,
                'executive': tok.executive,
                'entries': sheet.entries.all().order_by('log_date'),
                'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
                'total_run_display': format_minutes(sheet.total_run_minutes),
                'done': True,
                'comment': comment_value,
            })

    # GET 또는 사유 누락 POST
    return render(request, 'driving_log/reject_page.html', {
        'sheet': sheet,
        'executive': tok.executive,
        'entries': sheet.entries.all().order_by('log_date'),
        'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
        'total_run_display': format_minutes(sheet.total_run_minutes),
        'done': False,
        'error_message': error_message,
        'comment': comment_value,
    })


def history_via_email(request, token):
    """이메일의 [📋 이력 조회] 진입. 만료 전까지 다회 조회 가능."""
    tok, err = _fetch_token(token, ApprovalToken.SCOPE_HISTORY_VIEW)
    if err:
        return _render_token_invalid(request, err, scope=ApprovalToken.SCOPE_HISTORY_VIEW)

    executive = tok.executive
    sheets = (
        DrivingLogSheet.objects
        .filter(
            reviewer=executive,
            status__in=[
                DrivingLogSheet.STATUS_APPROVED,
                DrivingLogSheet.STATUS_REJECTED,
                DrivingLogSheet.STATUS_REJECTED_RESUBMITTED,
            ],
        )
        .select_related('author')
        .order_by('-reviewed_at')[:100]
    )

    ApprovalHistory.objects.create(
        sheet=None,
        actor_executive=executive,
        action=ApprovalHistory.ACTION_VIEWED_HISTORY,
        ip_address=_client_ip(request),
    )

    return render(request, 'driving_log/history_page.html', {
        'executive': executive,
        'sheets': sheets,
        'expires_at': tok.expires_at,
        'token': token,
    })


def history_sheet_detail_via_email(request, token, sheet_pk):
    """history scope 토큰으로 결재 이력에 포함된 운행일지 1건의 상세를 read-only 로 조회한다.

    - 동일 토큰 만료 전까지 다회 조회 가능.
    - sheet.reviewer 와 token.executive 가 일치할 때만 접근 허용 (다른 임원의 결재 건은 차단).
    """
    tok, err = _fetch_token(token, ApprovalToken.SCOPE_HISTORY_VIEW)
    if err:
        return _render_token_invalid(request, err, scope=ApprovalToken.SCOPE_HISTORY_VIEW)

    sheet = get_object_or_404(
        DrivingLogSheet.objects.select_related('author', 'reviewer'),
        pk=sheet_pk,
    )
    if sheet.reviewer_id != tok.executive_id:
        return _render_token_invalid(request, 'mismatch', scope=ApprovalToken.SCOPE_HISTORY_VIEW)
    if sheet.status not in (
        DrivingLogSheet.STATUS_APPROVED,
        DrivingLogSheet.STATUS_REJECTED,
        DrivingLogSheet.STATUS_REJECTED_RESUBMITTED,
    ):
        return _render_token_invalid(request, 'mismatch', scope=ApprovalToken.SCOPE_HISTORY_VIEW)

    return render(request, 'driving_log/history_sheet_detail.html', {
        'sheet': sheet,
        'executive': tok.executive,
        'entries': sheet.entries.all().order_by('log_date'),
        'total_overtime_display': format_minutes(sheet.total_overtime_minutes),
        'total_run_display': format_minutes(sheet.total_run_minutes),
        'token': token,
    })


# ---------------------------------------------------------------------------
# 지원팀 관리자 화면 (P5) — 전체 운행일지 조회/필터/CSV 내보내기.
# 강제 상태변경은 본 화면에서 제공하지 않으며, Django admin 으로 처리한다.
# ---------------------------------------------------------------------------

_ADMIN_VISIBLE_STATUSES = (
    DrivingLogSheet.STATUS_SUBMITTED,
    DrivingLogSheet.STATUS_APPROVED,
    DrivingLogSheet.STATUS_REJECTED,
    DrivingLogSheet.STATUS_REJECTED_RESUBMITTED,
)
# 지원팀이 보아야 하는 상태 — 임시저장(draft) 은 운전기사 손에 있는 것이므로 제외.


def _admin_status_choices():
    """관리자 필터 UI 에 노출할 상태 선택지 (draft 제외)."""
    return [
        (value, label)
        for value, label in DrivingLogSheet.STATUS_CHOICES
        if value in _ADMIN_VISIBLE_STATUSES
    ]


def _apply_admin_filters(qs, request):
    """관리자 목록/CSV 공통 필터.

    기본 동작: 항상 임시저장(draft) 제외 — 관리자는 결재중/완료 건만 본다.

    쿼리스트링:
      q          — sheet.title 부분일치 (LIKE)
      author     — User id (driving_log_users 그룹 멤버 중 선택)
      reviewer   — Executive id
      status     — DrivingLogSheet.STATUS_* (다중 선택 가능, getlist). draft 는 무시.
      drive_from — 운행일(entries.log_date) 범위 내에 항목 1건이라도 있으면 매칭
      drive_to   — 운행일 범위 끝 (drive_from 과 짝). 둘 중 하나만 있어도 동작.
    """
    # 항상 draft 제외
    qs = qs.exclude(status=DrivingLogSheet.STATUS_DRAFT)

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(title__icontains=q)

    author_id = request.GET.get('author')
    if author_id:
        qs = qs.filter(author_id=author_id)

    reviewer_id = request.GET.get('reviewer')
    if reviewer_id:
        qs = qs.filter(reviewer_id=reviewer_id)

    statuses = [s for s in request.GET.getlist('status') if s in _ADMIN_VISIBLE_STATUSES]
    if statuses:
        qs = qs.filter(status__in=statuses)

    # 운행일(entry.log_date) 범위: 항목 중 1건이라도 범위에 들면 해당 sheet 노출.
    # entries 조인이라 distinct() 필수.
    drive_from = _parse_date(request.GET.get('drive_from'))
    drive_to = _parse_date(request.GET.get('drive_to'))
    if drive_from or drive_to:
        entry_filter = Q()
        if drive_from:
            entry_filter &= Q(entries__log_date__gte=drive_from)
        if drive_to:
            entry_filter &= Q(entries__log_date__lte=drive_to)
        qs = qs.filter(entry_filter).distinct()

    return qs


class DrivingLogAdminListView(DrivingLogManagerRequiredMixin, ListView):
    """지원팀 관리자용 전체 운행일지 목록.

    상단 필터바(기간/운전기사/수행임원/상태) + 페이지네이션 + CSV 내보내기.
    상세는 read-only(DrivingLogAdminDetailView), 강제 변경은 Django admin.

    권한: driving_log_managers 그룹 또는 슈퍼유저 (is_staff 사용 안 함).
    """
    template_name = 'driving_log/admin_sheet_list.html'
    context_object_name = 'sheets'
    paginate_by = 30

    def get_queryset(self):
        qs = (
            DrivingLogSheet.objects
            .select_related('author', 'author__profile', 'reviewer')
            .annotate(entry_count=Count('entries', distinct=True))
        )
        qs = _apply_admin_filters(qs, self.request)
        # 최근 결재요청 우선. draft 는 _apply_admin_filters 에서 이미 제외됨.
        return qs.order_by(
            '-submitted_at', '-created_at',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['executives'] = (
            Executive.objects
            .filter(is_active=True)
            .order_by('display_order', 'name')
        )
        # 운전기사 드롭다운: driving_log_users 그룹 멤버만 (매니저/슈퍼유저 제외).
        # 한국명(profile) 기준 정렬, profile 없으면 username 으로 fallback 정렬됨.
        ctx['drivers'] = (
            User.objects
            .filter(groups__name=DRIVING_LOG_USER_GROUP)
            .select_related('profile')
            .distinct()
            .order_by('profile__last_name_ko', 'profile__first_name_ko', 'username')
        )
        ctx['status_choices'] = _admin_status_choices()
        ctx['filter'] = {
            'q': self.request.GET.get('q', ''),
            'author': self.request.GET.get('author', ''),
            'reviewer': self.request.GET.get('reviewer', ''),
            'statuses': self.request.GET.getlist('status'),
            'drive_from': self.request.GET.get('drive_from', ''),
            'drive_to': self.request.GET.get('drive_to', ''),
        }
        # 페이지네이션 링크에 필터 유지
        qd = self.request.GET.copy()
        qd.pop('page', None)
        ctx['querystring'] = qd.urlencode()
        return ctx


class DrivingLogAdminDetailView(DrivingLogManagerRequiredMixin, DetailView):
    """관리자용 read-only 상세 + 결재 이력 타임라인.

    권한: driving_log_managers 그룹 또는 슈퍼유저.
    """
    model = DrivingLogSheet
    template_name = 'driving_log/admin_sheet_detail.html'
    context_object_name = 'sheet'

    def get_queryset(self):
        return DrivingLogSheet.objects.select_related('author', 'reviewer')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entries'] = self.object.entries.all().order_by('log_date')
        ctx['total_overtime_display'] = format_minutes(self.object.total_overtime_minutes)
        ctx['total_run_display'] = format_minutes(self.object.total_run_minutes)
        ctx['history'] = (
            self.object.history
            .select_related('actor_user', 'actor_executive')
            .order_by('-created_at')
        )
        return ctx


@login_required
@user_passes_test(is_driving_log_manager)
def driving_log_admin_csv_export(request):
    """관리자 목록과 동일 필터 적용 후 CSV 다운로드.

    Excel 호환을 위해 UTF-8 BOM 추가 (worklog.WorklogAdmin.export_to_csv 패턴).
    권한: driving_log_managers 그룹 또는 슈퍼유저.
    """
    import csv
    from urllib.parse import quote

    qs = (
        DrivingLogSheet.objects
        .select_related('author', 'author__profile', 'reviewer')
        .annotate(entry_count=Count('entries', distinct=True))
    )
    qs = _apply_admin_filters(qs, request).order_by('-submitted_at', '-created_at')

    filename = f'driving_logs_{timezone.now():%Y%m%d_%H%M}.csv'
    encoded = quote(filename.encode('utf-8'))
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded}'
    response.write('﻿')  # Excel UTF-8 BOM

    writer = csv.writer(response)
    writer.writerow([
        'ID', '요청자', '결재자', '제목',
        '운행기간', '건수',
        '운행시간(분)', '운행시간(표시)',
        '초과근무(분)', '초과근무(표시)',
        '상태', '결재요청일', '결재완료일', '결재 의견',
    ])
    for s in qs.iterator():
        # 운전기사 표시명: profile.get_korean_name → user.last_name+first_name → username
        author_name = s.author.username if s.author_id else ''
        if s.author_id and hasattr(s.author, 'profile'):
            try:
                author_name = s.author.profile.get_korean_name
            except Exception:
                pass
        # 운행기간: 화면과 동일하게 'yy.mm.dd ~ yy.mm.dd' 한 컬럼으로
        if s.period_start and s.period_end:
            period_str = f"{s.period_start:%y.%m.%d} ~ {s.period_end:%y.%m.%d}"
        elif s.period_start:
            period_str = f"{s.period_start:%y.%m.%d}"
        elif s.period_end:
            period_str = f"{s.period_end:%y.%m.%d}"
        else:
            period_str = ''
        writer.writerow([
            s.id,
            author_name,
            s.reviewer.name if s.reviewer_id else '',
            s.title or '',
            period_str,
            s.entry_count,
            s.total_run_minutes or 0,
            format_minutes(s.total_run_minutes),
            s.total_overtime_minutes or 0,
            format_minutes(s.total_overtime_minutes),
            s.get_status_display(),
            s.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if s.submitted_at else '',
            s.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if s.reviewed_at else '',
            (s.review_comment or '').replace('\n', ' ').replace('\r', ' '),
        ])
    return response


# ---------------------------------------------------------------------------
# 임원 관리 (수행임원 마스터 CRUD) — 지원팀 관리자(driving_log_managers) 전용.
# 기존 Django admin 의 Executive 입력을 프로그램단으로 옮긴 화면.
# ---------------------------------------------------------------------------

class ExecutiveListView(DrivingLogManagerRequiredMixin, ListView):
    """수행임원 목록. 활성/비활성 모두 표시(편집 위해).

    권한: driving_log_managers 그룹 또는 슈퍼유저 (is_staff 사용 안 함).
    """
    model = Executive
    template_name = 'driving_log/executive_list.html'
    context_object_name = 'executives'

    def get_queryset(self):
        # Meta.ordering(display_order, name) 을 그대로 사용.
        return Executive.objects.all()


class ExecutiveCreateView(DrivingLogManagerRequiredMixin, CreateView):
    """수행임원 신규 등록."""
    model = Executive
    form_class = ExecutiveForm
    template_name = 'driving_log/executive_form.html'
    success_url = reverse_lazy('driving_log:executive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'create'
        return ctx


class ExecutiveUpdateView(DrivingLogManagerRequiredMixin, UpdateView):
    """수행임원 수정."""
    model = Executive
    form_class = ExecutiveForm
    template_name = 'driving_log/executive_form.html'
    success_url = reverse_lazy('driving_log:executive_list')
    context_object_name = 'executive'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'edit'
        return ctx


class ExecutiveDeleteView(DrivingLogManagerRequiredMixin, DeleteView):
    """수행임원 삭제.

    결재선(DrivingLogSheet.reviewer)에 사용된 임원은 on_delete=PROTECT 라
    하드 삭제가 불가하다. 이 경우 삭제를 막고 [비활성화] 를 안내한다.
    (비활성 임원은 결재요청 모달 목록에서 제외되므로 사실상 은퇴 처리와 동일.)
    """
    model = Executive
    template_name = 'driving_log/executive_confirm_delete.html'
    success_url = reverse_lazy('driving_log:executive_list')
    context_object_name = 'executive'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['review_sheet_count'] = self.object.review_sheets.count()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.review_sheets.exists():
            # 결재 이력이 있는 임원은 삭제 차단 — 확인 페이지를 차단 안내와 함께 재렌더.
            ctx = self.get_context_data(object=self.object)
            return self.render_to_response(ctx)
        return super().post(request, *args, **kwargs)
