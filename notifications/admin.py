from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'notification_type_display', 'task_link',
        'is_read_display', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at', 'user'
    ]
    search_fields = ['title', 'message', 'user__username', 'task__title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('관련 업무', {
            'fields': ('task',)
        }),
        ('상태', {
            'fields': ('is_read',)
        }),
        ('시간 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def notification_type_display(self, obj):
        colors = {
            'task_due': '#ffc107',
            'task_overdue': '#dc3545',
            'task_assigned': '#17a2b8',
            'comment_added': '#28a745',
            'worklog_reminder': '#6f42c1'
        }
        color = colors.get(obj.notification_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_notification_type_display()
        )
    notification_type_display.short_description = '알림 유형'
    
    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:task_task_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.title)
        return '-'
    task_link.short_description = '관련 업무'
    
    def is_read_display(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">●</span> 읽음'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">●</span> 읽지 않음'
            )
    is_read_display.short_description = '읽음 상태'
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_read_notifications']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated}개 알림을 읽음으로 표시했습니다.')
    mark_as_read.short_description = '선택된 알림을 읽음으로 표시'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated}개 알림을 읽지 않음으로 표시했습니다.')
    mark_as_unread.short_description = '선택된 알림을 읽지 않음으로 표시'
    
    def delete_read_notifications(self, request, queryset):
        read_notifications = queryset.filter(is_read=True)
        count = read_notifications.count()
        read_notifications.delete()
        self.message_user(request, f'{count}개 읽은 알림을 삭제했습니다.')
    delete_read_notifications.short_description = '읽은 알림만 삭제'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # 관리자가 아닌 경우 자신의 알림만 볼 수 있도록 제한
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs
