from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.utils import check_due_date_notifications, check_worklog_reminders

class Command(BaseCommand):
    help = '마감일 임박/초과 업무 및 워크로그 작성 알림을 체크합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['due_dates', 'worklog', 'all'],
            default='all',
            help='체크할 알림 유형을 지정합니다'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        
        self.stdout.write(
            self.style.SUCCESS(f'알림 체크를 시작합니다... (유형: {notification_type})')
        )
        
        try:
            if notification_type in ['due_dates', 'all']:
                self.stdout.write('마감일 관련 알림을 체크하는 중...')
                check_due_date_notifications()
                self.stdout.write(
                    self.style.SUCCESS('✅ 마감일 관련 알림 체크 완료')
                )
            
            if notification_type in ['worklog', 'all']:
                self.stdout.write('워크로그 작성 알림을 체크하는 중...')
                check_worklog_reminders()
                self.stdout.write(
                    self.style.SUCCESS('✅ 워크로그 작성 알림 체크 완료')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'🎉 모든 알림 체크가 완료되었습니다! ({timezone.now()})')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 알림 체크 중 오류가 발생했습니다: {str(e)}')
            )
            raise e
