import logging
import time
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from worklog.models import Worklog
from reports.models import ReportReview
from app.services.report_review import review_last_4_weeks

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate review reports for users who have current week worklogs but no existing review'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='ISO year to process')
        parser.add_argument('--week', type=int, help='ISO week number to process')

    def handle(self, *args, **options):
        """
        오늘이 포함된 주차의 워크로그가 있지만 리뷰 리포트가 없는 사용자들을 찾아
        AI 리뷰를 일괄 생성합니다.
        """
        if options.get('year') and options.get('week'):
            current_year = options['year']
            current_week = options['week']
            try:
                target_monday = date.fromisocalendar(current_year, current_week, 1)
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid --year/--week combination."))
                return
        else:
            target_monday = date.today()
            current_year, current_week, _ = target_monday.isocalendar()
        
        self.stdout.write(f"현재 주차: {current_year}년 {current_week}주차")
        
        # 현재 주차에 워크로그가 있는 사용자들 조회
        users_with_worklog = User.objects.filter(
            worklogs__year=current_year,
            worklogs__week_number=current_week
        ).distinct()
        
        if not users_with_worklog.exists():
            self.stdout.write(self.style.WARNING("현재 주차에 워크로그를 작성한 사용자가 없습니다."))
            return
        
        self.stdout.write(f"현재 주차 워크로그 작성자: {users_with_worklog.count()}명")
        
        # 이미 리뷰가 있는 사용자들 제외
        users_without_review = users_with_worklog.exclude(
            report_reviews__year=current_year,
            report_reviews__week_number=current_week
        )
        
        if not users_without_review.exists():
            self.stdout.write(self.style.SUCCESS("모든 사용자의 리뷰가 이미 생성되어 있습니다."))
            return
        
        self.stdout.write(f"리뷰 생성 대상: {users_without_review.count()}명")
        self.stdout.write("-" * 50)
        
        success_count = 0
        fail_count = 0
        
        for user in users_without_review:
            try:
                self.stdout.write(f"🔄 {user.username}님의 리뷰를 생성 중...")
                
                # AI 리뷰 생성 (이 함수가 자동으로 DB에 저장함)
                review_result = review_last_4_weeks(user, as_of=target_monday)
                
                if review_result.get('error'):
                    self.stdout.write(self.style.WARNING(f"⚠️  {user.username}님 리뷰 생성 중 오류: {review_result['error']}"))
                    fail_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f"✅ {user.username}님의 리뷰가 성공적으로 생성되었습니다."))
                    success_count += 1
                
                # 과도한 API 요청 방지를 위한 지연 (3초)
                if user != users_without_review.last():
                    time.sleep(3)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {user.username}님 리뷰 생성 실패: {e}"))
                logger.error(f"Failed to generate review for user {user.id}: {e}", exc_info=True)
                fail_count += 1
        
        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ 성공: {success_count}건"))
        if fail_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠️  실패: {fail_count}건"))
        self.stdout.write(f"📊 총 처리: {success_count + fail_count}건")
        
        if success_count > 0:
            self.stdout.write("\n💡 생성된 리뷰를 이메일로 발송하려면 다음 명령어를 실행하세요:")
            self.stdout.write("python manage.py send_review_notifications")
