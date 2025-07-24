from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Task, Category, TaskComment, TaskFile
from monitor.models import OperationLog, OperationLogAttachment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'task_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    ordering = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; display: inline-block;"></div>',
            obj.color
        )
    color_display.short_description = '색상'
    
    def task_count(self, obj):
        count = obj.task_set.count()
        if count > 0:
            url = reverse('admin:task_task_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} 개</a>', url, count)
        return '0 개'
    task_count.short_description = '업무 수'

class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['author', 'content', 'created_at']

class TaskFileInline(admin.TabularInline):
    model = TaskFile
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']
    fields = ['file', 'original_name', 'uploaded_by', 'uploaded_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'status_display', 'priority_display', 
        'category', 'due_date_display', 'assigned_users', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'category', 'created_at', 
        'due_date', 'team'
    ]
    search_fields = ['title', 'description', 'author__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    filter_horizontal = ['assigned_to']
    inlines = [TaskCommentInline, TaskFileInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'description', 'author')
        }),
        ('상태 및 우선순위', {
            'fields': ('status', 'priority', 'category','progress')
        }),
        ('할당 및 팀', {
            'fields': ('assigned_to', 'team')
        }),
        ('일정', {
            'fields': ('due_date',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def status_display(self, obj):
        colors = {
            'todo': '#ffc107',
            'in_progress': '#17a2b8', 
            'done': '#28a745',
            'dropped': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    status_display.short_description = '상태'
    
    def priority_display(self, obj):
        colors = {
            'urgent': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_priority_display()
        )
    priority_display.short_description = '우선순위'
    
    def due_date_display(self, obj):
        if obj.due_date:
            if obj.is_overdue:
                return format_html(
                    '<span style="color: #dc3545; font-weight: bold;">{} (지연)</span>',
                    obj.due_date.strftime('%Y-%m-%d %H:%M')
                )
            return obj.due_date.strftime('%Y-%m-%d %H:%M')
        return '-'
    due_date_display.short_description = '마감일'
    
    def assigned_users(self, obj):
        users = obj.assigned_to.all()
        if users:
            return ', '.join([user.username for user in users])
        return '-'
    assigned_users.short_description = '담당자'
    
    actions = ['mark_as_todo', 'mark_as_in_progress', 'mark_as_done']
    
    def mark_as_todo(self, request, queryset):
        updated = queryset.update(status='todo')
        self.message_user(request, f'{updated}개 업무를 "예정업무"로 변경했습니다.')
    mark_as_todo.short_description = '선택된 업무를 예정업무로 변경'
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated}개 업무를 "진행중 업무"로 변경했습니다.')
    mark_as_in_progress.short_description = '선택된 업무를 진행중 업무로 변경'
    
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='done')
        self.message_user(request, f'{updated}개 업무를 "완료업무"로 변경했습니다.')
    mark_as_done.short_description = '선택된 업무를 완료업무로 변경'

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task_title', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'task__title', 'author__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def task_title(self, obj):
        url = reverse('admin:task_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_title.short_description = '업무'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '댓글 내용'

@admin.register(TaskFile)
class TaskFileAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'task_title', 'uploaded_by', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['original_name', 'task__title', 'uploaded_by__username']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def task_title(self, obj):
        url = reverse('admin:task_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_title.short_description = '업무'
    
    def file_size(self, obj):
        try:
            size = obj.file.size
            if size < 1024:
                return f'{size} B'
            elif size < 1024 * 1024:
                return f'{size / 1024:.1f} KB'
            else:
                return f'{size / (1024 * 1024):.1f} MB'
        except:
            return '-'
    file_size.short_description = '파일 크기'


class OperationLogAttachmentInline(admin.StackedInline):
    model = OperationLogAttachment
    extra = 0

@admin.register(OperationLog)
class OperationLog(admin.ModelAdmin):
    inlines = (OperationLogAttachmentInline,)
    list_display = ('date', 'duty_user', 'completed')
