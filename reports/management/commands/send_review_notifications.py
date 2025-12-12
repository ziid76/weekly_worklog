import logging
from django.core.management.base import BaseCommand
from reports.models import ReportReview
from mailing.mailer import send_review_notification

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends pending AI review result notifications to users via email.'

    def handle(self, *args, **options):
        """
        알림 발송이 필요한 AI 리뷰를 조회하여 이메일을 발송하고,
        발송 완료 상태를 업데이트합니다.
        """
        pending_reviews = ReportReview.objects.filter(notification_sent=False)
        
        if not pending_reviews.exists():
            self.stdout.write(self.style.SUCCESS("발송할 리뷰 알림이 없습니다."))
            return

        self.stdout.write(f"총 {pending_reviews.count()}개의 리뷰 알림을 발송합니다.")
        
        success_count = 0
        fail_count = 0

        for review in pending_reviews:
            try:
                # 이메일 발송 함수 호출
                send_review_notification(review)
                
                # 발송 성공 시, 플래그 업데이트
                review.notification_sent = True
                review.save(update_fields=['notification_sent'])
                
                self.stdout.write(self.style.SUCCESS(f"✅ {review.user.username}님에게 리뷰 알림을 성공적으로 발송했습니다. (리뷰 ID: {review.id})"))
                success_count += 1
            
            except Exception as e:
                # 메일러에서 발생한 예외 처리
                self.stderr.write(self.style.ERROR(f"❌ {review.user.username}님에게 리뷰 알림 발송 중 오류가 발생했습니다. (리뷰 ID: {review.id})"))
                logger.error(f"Failed to send notification for review {review.id}: {e}", exc_info=True)
                fail_count += 1

        self.stdout.write("-" * 30)
        self.stdout.write(self.style.SUCCESS(f"총 {success_count}건의 알림을 성공적으로 발송했습니다."))
        if fail_count > 0:
            self.stdout.write(self.style.WARNING(f"총 {fail_count}건의 알림이 발송에 실패했습니다. 로그를 확인해주세요."))
        self.stdout.write("-" * 30)
