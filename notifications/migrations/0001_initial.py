# Generated by Django 4.2.11 on 2025-07-07 06:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('task', '0002_category_task_assigned_to_task_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('task_due', '업무 마감일 임박'), ('task_overdue', '업무 마감일 초과'), ('task_assigned', '업무 할당'), ('comment_added', '댓글 추가'), ('worklog_reminder', '워크로그 작성 알림')], max_length=20, verbose_name='알림 유형')),
                ('title', models.CharField(max_length=200, verbose_name='제목')),
                ('message', models.TextField(verbose_name='메시지')),
                ('is_read', models.BooleanField(default=False, verbose_name='읽음 여부')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.task')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
