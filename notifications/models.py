from django.db import models
from django.contrib.auth.models import User
from task.models import Task

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('task_due', '업무 마감일 임박'),
        ('task_overdue', '업무 마감일 초과'),
        ('task_assigned', '업무 할당'),
        ('comment_added', '댓글 추가'),
        ('worklog_reminder', '워크로그 작성 알림'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField("알림 유형", max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField("제목", max_length=200)
    message = models.TextField("메시지")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField("읽음 여부", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.title}'
