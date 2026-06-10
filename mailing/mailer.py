from datetime import timedelta

from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from reports.models import ReportReview
from .text_formatter import format_review_content
import logging

logger = logging.getLogger(__name__)

def send_review_notification(review: ReportReview):
    """AI 리뷰 결과를 사용자에게 이메일로 발송합니다."""
    user = review.user
    subject = f"📊 [{user.profile.display_name}님] {review.year}년 {review.week_number}주차 주간보고서 AI 리뷰 결과"

    if not user.email:
        logger.warning(f"User {user.username} (ID: {user.id}) has no email address. Skipping notification for review {review.id}.")
        return

    # 리뷰 내용을 가독성 있게 포맷팅
    formatted_review = format_review_content(review.review_content)
    
    context = {
        'review': formatted_review,
        'user': user,
        'year': review.year,
        'week_number': review.week_number,
        'site_url': settings.SITE_URL,
    }

    # 이메일 본문을 HTML 템플릿으로 렌더링
    html_message = render_to_string('emails/review_notification.html', context)
    
    # 이메일 발송
    try:
        msg = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.content_subtype = "html"
        msg.send()
        
        logger.info(f"Successfully sent review notification email to {user.email} for review {review.id}.")
    except Exception as e:
        logger.error(f"Failed to send email to {user.email} for review {review.id}. Error: {e}", exc_info=True)
        # 예외를 다시 발생시켜 호출한 쪽(관리 명령어)에서 처리하도록 함
        raise


def send_driving_log_request_mail(sheet):
    """운행일지 결재 요청 메일 발송.

    수행임원의 이메일로 결재 링크가 포함된 HTML 메일을 보낸다.
    승인/반려 토큰·이력조회 토큰 모두 30일(720시간) 유효.

    기존 AWS SES 백엔드(EMAIL_BACKEND)는 그대로 두고, 본 함수만 그룹웨어 SMTP 서버
    (GROUPWARE_SMTP_*)로 발송한다. 발신자는 운전기사 본인 이메일(sheet.author.email).
    """
    # driving_log 앱의 모델은 호출 시점에 lazy import (앱 초기화 순서 안전)
    from driving_log.models import ApprovalToken

    executive = sheet.reviewer
    if not executive:
        logger.warning(f"DrivingLogSheet {sheet.id}: reviewer 미지정으로 메일 발송 스킵")
        return

    to_email = executive.email
    if not to_email:
        logger.warning(f"Executive {executive.id}: 수신 이메일 없음 — 메일 발송 스킵")
        return

    from_email = sheet.author.email
    if not from_email:
        logger.warning(
            f"운전기사 {sheet.author.id}({sheet.author.username}): 발신 이메일 없음 — 메일 발송 스킵"
        )
        return

    approve_ttl_hours = getattr(settings, 'DRIVING_LOG_APPROVE_TTL_HOURS', 720)  # 기본 30일(720h)
    history_ttl_hours = getattr(settings, 'DRIVING_LOG_HISTORY_TTL_HOURS', 720)  # 기본 30일(720h)
    now = timezone.now()
    approve_expires_at = now + timedelta(hours=approve_ttl_hours)
    history_expires_at = now + timedelta(hours=history_ttl_hours)

    approve_token = ApprovalToken.objects.create(
        sheet=sheet, executive=executive,
        scope=ApprovalToken.SCOPE_APPROVE_REJECT,
        expires_at=approve_expires_at,
    )
    history_token = ApprovalToken.objects.create(
        sheet=None, executive=executive,
        scope=ApprovalToken.SCOPE_HISTORY_VIEW,
        expires_at=history_expires_at,
    )

    base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    ctx = {
        'sheet': sheet,
        'executive': executive,
        'author': sheet.author,
        'entries': sheet.entries.all().order_by('log_date'),
        'approve_url': f'{base_url}/driving-log/approve/{approve_token.token}/',
        'reject_url':  f'{base_url}/driving-log/reject/{approve_token.token}/',
        'history_url': f'{base_url}/driving-log/history/{history_token.token}/',
        'site_url': base_url,
        'approve_expires_at': approve_expires_at,
        'history_expires_at': history_expires_at,
    }

    author_name = (
        sheet.author.profile.display_name
        if hasattr(sheet.author, 'profile')
        else sheet.author.username
    )
    period_label = ''
    if sheet.period_start and sheet.period_end:
        period_label = f' {sheet.period_start:%Y-%m-%d} ~ {sheet.period_end:%Y-%m-%d}'
    subject = f"[운행일지 결재요청] {author_name}{period_label}"

    html_message = render_to_string('emails/driving_log_request.html', ctx)

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

    try:
        msg = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=from_email,
            to=[to_email],
            connection=connection,
        )
        msg.content_subtype = "html"
        msg.send()
        logger.info(
            f"운행일지 결재요청 메일 발송 완료: sheet={sheet.id}, from={from_email}, "
            f"to={to_email}, executive={executive.id}"
        )
    except Exception as e:
        logger.error(
            f"운행일지 결재요청 메일 발송 실패: sheet={sheet.id}, from={from_email}, "
            f"to={to_email}. Error: {e}",
            exc_info=True,
        )
        raise
