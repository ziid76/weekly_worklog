from django.utils import timezone
from datetime import timedelta
from .models import Notification
from task.models import Task
from django.contrib.auth.models import User

def create_notification(user, notification_type, title, message, task=None):
    """
    알림 생성 헬퍼 함수
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        task=task
    )

def notify_task_assigned(task, assigned_users, assigner):
    """
    업무 할당 알림
    """
    for user in assigned_users:
        if user != assigner:
            create_notification(
                user=user,
                notification_type='task_assigned',
                title='새 업무가 할당되었습니다',
                message=f'"{task.title}" 업무가 {assigner.get_full_name() or assigner.username}님에 의해 할당되었습니다.',
                task=task
            )

def notify_comment_added(task, comment_author):
    """
    댓글 추가 알림
    """
    # 업무 작성자에게 알림
    if task.author != comment_author:
        create_notification(
            user=task.author,
            notification_type='comment_added',
            title='새 댓글이 추가되었습니다',
            message=f'"{task.title}" 업무에 {comment_author.get_full_name() or comment_author.username}님이 댓글을 추가했습니다.',
            task=task
        )
    
    # 담당자들에게 알림 (작성자와 댓글 작성자 제외)
    for assigned_user in task.assigned_to.all():
        if assigned_user != comment_author and assigned_user != task.author:
            create_notification(
                user=assigned_user,
                notification_type='comment_added',
                title='새 댓글이 추가되었습니다',
                message=f'담당하고 있는 "{task.title}" 업무에 새 댓글이 추가되었습니다.',
                task=task
            )

def notify_task_status_changed(task, old_status, new_status, changer):
    """
    업무 상태 변경 알림
    """
    status_messages = {
        'todo': '대기',
        'in_progress': '진행중',
        'done': '완료',
        'dropped': '중단'
    }
    
    # 업무 작성자에게 알림 (상태 변경자가 아닌 경우)
    if task.author != changer:
        create_notification(
            user=task.author,
            notification_type='task_assigned',  # 기존 타입 활용
            title='업무 상태가 변경되었습니다',
            message=f'"{task.title}" 업무가 "{status_messages.get(old_status, old_status)}"에서 "{status_messages.get(new_status, new_status)}"로 변경되었습니다.',
            task=task
        )
    
    # 담당자들에게 알림
    for assigned_user in task.assigned_to.all():
        if assigned_user != changer:
            create_notification(
                user=assigned_user,
                notification_type='task_assigned',
                title='담당 업무 상태가 변경되었습니다',
                message=f'담당하고 있는 "{task.title}" 업무가 "{status_messages.get(new_status, new_status)}" 상태로 변경되었습니다.',
                task=task
            )

def check_due_date_notifications():
    """
    마감일 임박 및 초과 업무 알림 체크
    (이 함수는 주기적으로 실행되어야 함 - 예: 매일 오전 9시)
    """
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    three_days_later = now + timedelta(days=3)
    
    # 마감일 임박 알림 (1일 전, 3일 전)
    upcoming_tasks = Task.objects.filter(
        due_date__gte=now,
        due_date__lte=three_days_later,
        status__in=['todo', 'in_progress']
    )
    
    for task in upcoming_tasks:
        days_left = (task.due_date - now).days
        
        # 중복 알림 방지를 위해 오늘 이미 알림을 보냈는지 확인
        today_notifications = Notification.objects.filter(
            task=task,
            notification_type='task_due',
            created_at__date=now.date()
        )
        
        if not today_notifications.exists():
            # 업무 작성자에게 알림
            create_notification(
                user=task.author,
                notification_type='task_due',
                title=f'업무 마감일이 {days_left}일 남았습니다',
                message=f'"{task.title}" 업무의 마감일이 {days_left}일 남았습니다. ({task.due_date.strftime("%Y-%m-%d %H:%M")})',
                task=task
            )
            
            # 담당자들에게 알림
            for assigned_user in task.assigned_to.all():
                create_notification(
                    user=assigned_user,
                    notification_type='task_due',
                    title=f'담당 업무 마감일이 {days_left}일 남았습니다',
                    message=f'담당하고 있는 "{task.title}" 업무의 마감일이 {days_left}일 남았습니다.',
                    task=task
                )
    
    # 마감일 초과 알림
    overdue_tasks = Task.objects.filter(
        due_date__lt=now,
        status__in=['todo', 'in_progress']
    )
    
    for task in overdue_tasks:
        days_overdue = (now - task.due_date).days
        
        # 중복 알림 방지
        today_overdue_notifications = Notification.objects.filter(
            task=task,
            notification_type='task_overdue',
            created_at__date=now.date()
        )
        
        if not today_overdue_notifications.exists():
            # 업무 작성자에게 알림
            create_notification(
                user=task.author,
                notification_type='task_overdue',
                title=f'업무 마감일이 {days_overdue}일 지났습니다',
                message=f'"{task.title}" 업무의 마감일이 {days_overdue}일 지났습니다. 빠른 처리가 필요합니다.',
                task=task
            )
            
            # 담당자들에게 알림
            for assigned_user in task.assigned_to.all():
                create_notification(
                    user=assigned_user,
                    notification_type='task_overdue',
                    title=f'담당 업무 마감일이 {days_overdue}일 지났습니다',
                    message=f'담당하고 있는 "{task.title}" 업무의 마감일이 지났습니다. 긴급 처리가 필요합니다.',
                    task=task
                )

def check_worklog_reminders():
    """
    워크로그 작성 알림 체크
    (매주 금요일 오후에 실행)
    """
    from worklog.models import Worklog
    import datetime
    
    # 현재 주차 정보
    today = datetime.date.today()
    year, week_number, _ = today.isocalendar()
    
    # 이번 주 워크로그를 작성하지 않은 사용자들 찾기
    users_with_worklog = Worklog.objects.filter(
        year=year,
        week_number=week_number
    ).values_list('author', flat=True)
    
    users_without_worklog = User.objects.filter(
        is_active=True
    ).exclude(id__in=users_with_worklog)
    
    for user in users_without_worklog:
        # 이미 이번 주 워크로그 알림을 받았는지 확인
        existing_reminder = Notification.objects.filter(
            user=user,
            notification_type='worklog_reminder',
            created_at__week=week_number,
            created_at__year=year
        )
        
        if not existing_reminder.exists():
            create_notification(
                user=user,
                notification_type='worklog_reminder',
                title='워크로그 작성 알림',
                message=f'{year}년 {week_number}주차 워크로그를 아직 작성하지 않으셨습니다. 이번 주 업무 내용을 기록해주세요.'
            )

def mark_notifications_as_read(user, notification_ids=None):
    """
    알림을 읽음으로 표시
    """
    queryset = Notification.objects.filter(user=user, is_read=False)
    
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    
    return queryset.update(is_read=True)

def get_unread_notifications_count(user):
    """
    읽지 않은 알림 개수 반환
    """
    return Notification.objects.filter(user=user, is_read=False).count()

def get_recent_notifications(user, limit=10):
    """
    최근 알림 목록 반환
    """
    return Notification.objects.filter(user=user).order_by('-created_at')[:limit]
