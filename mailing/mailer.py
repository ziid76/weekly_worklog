from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
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
