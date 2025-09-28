from django.core.management.base import BaseCommand
from notifications.utils import check_due_date_notifications, check_worklog_reminders, check_monitor_reminders


class Command(BaseCommand):
    help = 'crontab 등록한 알림 발송 프로그램'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['due_date', 'worklog', 'monitor', 'all'],
            default='all',
            help='실행할 알림 타입 (due_date, worklog, monitor, all)'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        
        if notification_type in ['due_date', 'all']:
            self.stdout.write('마감일 알림 체크 중...')
            try:
                check_due_date_notifications()
                self.stdout.write(
                    self.style.SUCCESS('마감일 알림 체크 완료')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'마감일 알림 체크 실패: {e}')
                )
        
        if notification_type in ['worklog', 'all']:
            self.stdout.write('워크로그 알림 체크 중...')
            try:
                check_worklog_reminders()
                self.stdout.write(
                    self.style.SUCCESS('워크로그 알림 체크 완료')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'워크로그 알림 체크 실패: {e}')
                )

        if notification_type in ['monitor', 'all']:
            self.stdout.write('모니터링 알림 체크 중...')
            try:
                check_monitor_reminders()
                self.stdout.write(
                    self.style.SUCCESS('모니터링 알림 체크 완료')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'모니터링 알림 체크 실패: {e}')
                )