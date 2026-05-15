import datetime
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from common.message_views import send_kakao_message
from task.models import Task

from .models import Notification

logger = logging.getLogger(__name__)


def create_notification(user, notification_type, title, message, task=None):
    """알림 생성 헬퍼 함수."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        task=task,
    )


def _display_name(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "display_name", None) or user.username


def _task_url(task):
    return f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/task/{task.id}/"


def _send_kakao_box_message(user, header_text, text, button_text, button_url):
    if not getattr(user, "email", None):
        return False

    try:
        return send_kakao_message(
            email=user.email,
            text=text,
            header_text=header_text,
            message_type="box",
            button_text=button_text,
            button_url=button_url,
        )
    except Exception:
        logger.exception("카카오워크 알림 전송 실패: user=%s", user.id)
        return False


def notify_task_assigned(task, assigned_users, assigner):
    """업무 할당 알림 생성 및 카카오워크 발송."""
    for user in assigned_users:
        if user == assigner:
            continue

        create_notification(
            user=user,
            notification_type="task_assigned",
            title="새 업무가 할당되었습니다.",
            message=f'"{task.title}" 업무가 {_display_name(assigner)}님에 의해 할당되었습니다.',
            task=task,
        )

        kakao_message = (
            f"제목: {task.title}\n"
            f"할당자: {_display_name(assigner)}\n"
            f"우선순위: {task.get_priority_display()}"
        )
        _send_kakao_box_message(user, "업무 담당자로 지정되었어요.", kakao_message, "업무 확인하기", _task_url(task))


def notify_task_unassigned(task, removed_users, actor):
    """업무 담당자 해제 알림 생성 및 카카오워크 발송."""
    for user in removed_users:
        if user == actor:
            continue

        create_notification(
            user=user,
            notification_type="task_assigned",
            title="업무 담당자에서 해제되었습니다.",
            message=f'"{task.title}" 업무에서 {_display_name(actor)}님이 담당자를 해제했습니다.',
            task=task,
        )

        kakao_message = (
            f"제목: {task.title}\n"
            f"처리자: {_display_name(actor)}"
        )
        _send_kakao_box_message(user, "담당자에서 해제되었어요.", kakao_message, "업무 확인하기", _task_url(task))


def notify_task_assignment_changes(task, previous_assigned_users, current_assigned_users, actor):
    """담당자 추가/삭제 차이를 계산해 알림 처리."""
    previous_users = {user.id: user for user in previous_assigned_users}
    current_users = {user.id: user for user in current_assigned_users}

    added_users = [user for user_id, user in current_users.items() if user_id not in previous_users]
    removed_users = [user for user_id, user in previous_users.items() if user_id not in current_users]

    if added_users:
        notify_task_assigned(task, added_users, actor)

    if removed_users:
        notify_task_unassigned(task, removed_users, actor)


def notify_comment_added(task, comment_author, comment):
    """댓글 추가 알림 생성 및 카카오워크 발송."""
    kakao_message = (
        f"업무명: {task.title}\n"
        f"작성자: {_display_name(comment_author)}\n\n"
        f"작성내용:\n"
        f"{comment}"
    )

    if task.author != comment_author:
        create_notification(
            user=task.author,
            notification_type="comment_added",
            title="업무 댓글이 추가되었습니다.",
            message=f'"{task.title}" 업무에 {_display_name(comment_author)}님이 댓글을 추가했습니다.',
            task=task,
        )
        _send_kakao_box_message(task.author, "새 댓글이 등록되었어요.", kakao_message, "댓글 확인하기", _task_url(task))

    for assigned_user in task.assigned_to.all():
        if assigned_user == comment_author or assigned_user == task.author:
            continue

        create_notification(
            user=assigned_user,
            notification_type="comment_added",
            title="업무 댓글이 추가되었습니다.",
            message=f'담당 중인 "{task.title}" 업무에 새 댓글이 추가되었습니다.',
            task=task,
        )
        _send_kakao_box_message(assigned_user, "새 댓글이 등록되었어요.", kakao_message, "댓글 확인하기", _task_url(task))


def notify_task_status_changed(task, old_status, new_status, changer):
    """업무 상태 변경 알림 생성 및 카카오워크 발송."""
    status_messages = {
        "todo": "대기",
        "in_progress": "진행중",
        "done": "완료",
        "dropped": "중단",
    }
    status_change_text = (
        f"{status_messages.get(old_status, old_status)} -> "
        f"{status_messages.get(new_status, new_status)}"
    )
    kakao_message = (
        f"제목: {task.title}\n"
        f"변경자: {_display_name(changer)}\n"
        f"상태: {status_change_text}"
    )

    if task.author != changer:
        create_notification(
            user=task.author,
            notification_type="task_assigned",
            title="업무 상태가 변경되었습니다.",
            message=f'"{task.title}" 업무가 "{status_change_text}" 상태로 변경되었습니다.',
            task=task,
        )
        _send_kakao_box_message(task.author, "업무 상태가 변경되었어요.", kakao_message, "업무 확인하기", _task_url(task))

    for assigned_user in task.assigned_to.all():
        if assigned_user == changer or assigned_user == task.author:
            continue

        create_notification(
            user=assigned_user,
            notification_type="task_assigned",
            title="담당 업무 상태가 변경되었습니다.",
            message=f'담당 중인 "{task.title}" 업무가 "{status_change_text}" 상태로 변경되었습니다.',
            task=task,
        )
        _send_kakao_box_message(assigned_user, "업무 상태가 변경되었어요.", kakao_message, "업무 확인하기", _task_url(task))


def check_due_date_notifications():
    """마감일 임박 및 초과 업무 알림 체크."""
    today = timezone.localdate()
    three_days_later = today + timedelta(days=3)

    upcoming_tasks = Task.objects.filter(
        due_date__gte=today,
        due_date__lte=three_days_later,
        status__in=["todo", "in_progress"],
    )

    for task in upcoming_tasks:
        if not task.due_date:
            continue

        days_left = (task.due_date - today).days
        today_notifications = Notification.objects.filter(
            task=task,
            notification_type="task_due",
            created_at__date=today,
        )

        if not today_notifications.exists() and days_left <= 3:
            create_notification(
                user=task.author,
                notification_type="task_due",
                title=f"업무 마감일이 {days_left}일 남았습니다.",
                message=f'"{task.title}" 업무의 마감일이 {days_left}일 남았습니다. ({task.due_date:%Y-%m-%d})',
                task=task,
            )

            for assigned_user in task.assigned_to.all():
                create_notification(
                    user=assigned_user,
                    notification_type="task_due",
                    title=f"담당 업무 마감일이 {days_left}일 남았습니다.",
                    message=f'담당 중인 "{task.title}" 업무의 마감일이 {days_left}일 남았습니다.',
                    task=task,
                )

    overdue_tasks = Task.objects.filter(
        due_date__lt=today,
        status__in=["todo", "in_progress"],
    )

    for task in overdue_tasks:
        if not task.due_date:
            continue

        days_overdue = (today - task.due_date).days
        today_overdue_notifications = Notification.objects.filter(
            task=task,
            notification_type="task_overdue",
            created_at__date=today,
        )

        if not today_overdue_notifications.exists():
            create_notification(
                user=task.author,
                notification_type="task_overdue",
                title=f"업무 마감일이 {days_overdue}일 지났습니다.",
                message=f'"{task.title}" 업무의 마감일이 {days_overdue}일 지났습니다. 빠른 처리가 필요합니다.',
                task=task,
            )

            for assigned_user in task.assigned_to.all():
                create_notification(
                    user=assigned_user,
                    notification_type="task_overdue",
                    title=f"담당 업무 마감일이 {days_overdue}일 지났습니다.",
                    message=f'담당 중인 "{task.title}" 업무의 마감일이 지났습니다. 빠른 처리가 필요합니다.',
                    task=task,
                )


def check_worklog_reminders():
    """워크로그 작성 알림 체크."""
    from worklog.models import Worklog

    today = datetime.date.today()
    year, week_number, _ = today.isocalendar()

    users_with_worklog = Worklog.objects.filter(
        year=year,
        week_number=week_number,
    ).values_list("author", flat=True)

    users_without_worklog = User.objects.filter(is_active=True).exclude(id__in=users_with_worklog)

    for user in users_without_worklog:
        existing_reminder = Notification.objects.filter(
            user=user,
            notification_type="worklog_reminder",
            created_at__week=week_number,
            created_at__year=year,
        )

        if not existing_reminder.exists():
            create_notification(
                user=user,
                notification_type="worklog_reminder",
                title="주간보고 작성 알림",
                message="금주 주간보고를 아직 작성하지 않았습니다. 이번 주 업무 내용을 기록해주세요.",
            )


def check_monitor_reminders():
    """시스템 점검일지 미작성 카카오워크 알림."""
    from monitor.models import OperationLog

    today = timezone.localdate()
    start_date = today - timedelta(days=30)
    end_date = today - timedelta(days=1)
    qs = (
        OperationLog.objects.filter(completed=False, date__range=(start_date, end_date))
        .select_related("duty_user", "duty_user__profile")
        .order_by("-date", "-created_at")
    )

    for row in qs:
        if not row.duty_user or not row.duty_user.email:
            continue

        task_url = (
            f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}"
            f"/monitor/ops/logs/{row.id}/detail"
        )
        kakao_message = (
            f"점검일자: {row.date:%Y-%m-%d}\n"
            f"담당자: {_display_name(row.duty_user)}"
        )
        _send_kakao_box_message(
            row.duty_user,
            "점검일지 작성 필요",
            kakao_message,
            "점검일지 바로가기",
            task_url,
        )


def mark_notifications_as_read(user, notification_ids=None):
    """알림을 읽음으로 표시."""
    queryset = Notification.objects.filter(user=user, is_read=False)

    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)

    return queryset.update(is_read=True)


def get_unread_notifications_count(user):
    """읽지 않은 알림 개수 반환."""
    return Notification.objects.filter(user=user, is_read=False).count()


def get_recent_notifications(user, limit=10):
    """최근 알림 목록 반환."""
    return Notification.objects.filter(user=user).order_by("-created_at")[:limit]
