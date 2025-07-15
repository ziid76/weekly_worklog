from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Category(models.Model):
    name = models.CharField("카테고리명", max_length=100)
    color = models.CharField("색상", max_length=7, default="#007bff")  # hex color
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = (
        ('todo', '예정업무'),
        ('in_progress', '진행중 업무'),
        ('done', '완료업무'),
        ('dropped', 'Drop'),
    )

    PRIORITY_CHOICES = (
        ('low', '낮음'),
        ('medium', '보통'),
        ('high', '높음'),
        ('urgent', '긴급'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField("업무명", max_length=200)
    description = models.TextField("업무 설명", blank=True)
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField("우선순위", max_length=20, choices=PRIORITY_CHOICES, default='medium')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="카테고리")
    due_date = models.DateField("마감일", null=True, blank=True)
    progress = models.IntegerField("진척율", null=True, blank=True)
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="팀")
    assigned_to = models.ManyToManyField(User, blank=True, related_name='assigned_tasks', verbose_name="담당자")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        """마감일이 지났는지 확인"""
        if self.due_date and self.status != 'done':
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_until_due(self):
        """마감일까지 남은 일수"""
        if self.due_date:
            delta = self.due_date - timezone.now().date()
            return delta.days
        return None

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField("댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'

class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')
    file = models.FileField("파일", upload_to='task_files/')
    original_name = models.CharField("원본 파일명", max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.original_name