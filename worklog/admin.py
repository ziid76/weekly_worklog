from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Worklog, WorklogFile, WorklogTask

class WorklogTaskInline(admin.TabularInline):
    model = WorklogTask
    extra = 0
    fields = ('task', 'status', 'progress', 'time_spent', 'notes')
    readonly_fields = ('created_at', 'updated_at')

class WorklogFileInline(admin.TabularInline):
    model = WorklogFile
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']
    fields = ['file', 'original_name', 'uploaded_by', 'uploaded_at']

@admin.register(Worklog)
class WorklogAdmin(admin.ModelAdmin):
    list_display = [
        'week_display', 'author', 'month_week_display', 'display_order',
        'content_preview', 'task_count', 'file_count', 'created_at'
    ]
    list_filter = ['year', 'week_number', 'created_at', 'author']
    search_fields = ['this_week_work', 'next_week_plan', 'author__username']
    ordering = ['-year', '-week_number']
    date_hierarchy = 'created_at'
    inlines = [WorklogTaskInline, WorklogFileInline]
    
    fieldsets = (
        ('기간 정보', {
            'fields': ('year', 'week_number', 'author')
        }),
        ('워크로그 내용', {
            'fields': ('this_week_work', 'next_week_plan', 'display_order')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def week_display(self, obj):
        return f'{obj.year}년 {obj.week_number}주차'
    week_display.short_description = '주차'
    week_display.admin_order_field = 'year'
    
    def month_week_display(self, obj):
        return obj.month_week_display
    month_week_display.short_description = '월별 주차'
    
    def content_preview(self, obj):
        content = obj.this_week_work or obj.next_week_plan or ''
        # HTML 태그 제거
        import re
        content = re.sub('<[^<]+?>', '', content)
        preview = content[:100] + '...' if len(content) > 100 else content
        return preview
    content_preview.short_description = '내용 미리보기'
    
    def task_count(self, obj):
        count = obj.worklog_tasks.count()
        if count > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{} 개</span>',
                count
            )
        return '0 개'
    task_count.short_description = '연결된 업무'
    
    def file_count(self, obj):
        count = obj.files.count()
        if count > 0:
            return format_html(
                '<span style="color: #007cba; font-weight: bold;">{} 개</span>',
                count
            )
        return '0 개'
    file_count.short_description = '첨부파일'
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from urllib.parse import quote
        
        response = HttpResponse(content_type='text/csv')
        filename = 'worklogs.csv'
        encoded_filename = quote(filename.encode('utf-8'))
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        response.write('\ufeff')  # UTF-8 BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow([
            '연도', '주차', '월별주차', '작성자', '이번주수행업무', '다음주계획', '연결된업무수', '작성일'
        ])
        
        for worklog in queryset:
            writer.writerow([
                worklog.year,
                worklog.week_number,
                worklog.month_week_display,
                worklog.author.username,
                worklog.this_week_work,
                worklog.next_week_plan,
                worklog.worklog_tasks.count(),
                worklog.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        self.message_user(request, f'{queryset.count()}개 워크로그를 CSV로 내보냈습니다.')
        return response
    export_to_csv.short_description = '선택된 워크로그를 CSV로 내보내기'

@admin.register(WorklogTask)
class WorklogTaskAdmin(admin.ModelAdmin):
    list_display = [
        'worklog_display', 'task_display', 'status', 'progress_display', 
        'time_spent', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'worklog__year', 'worklog__week_number', 'task__priority']
    search_fields = ['task__title', 'worklog__author__username', 'notes']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('worklog', 'task')
        }),
        ('진행 상황', {
            'fields': ('status', 'progress', 'time_spent')
        }),
        ('추가 정보', {
            'fields': ('notes',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def worklog_display(self, obj):
        url = reverse('admin:worklog_worklog_change', args=[obj.worklog.id])
        return format_html(
            '<a href="{}">{} - {}년 {}주차</a>', 
            url, obj.worklog.author.username, obj.worklog.year, obj.worklog.week_number
        )
    worklog_display.short_description = '워크로그'
    
    def task_display(self, obj):
        url = reverse('admin:task_task_change', args=[obj.task.id])
        priority_colors = {
            'urgent': '#dc3545',
            'high': '#fd7e14', 
            'medium': '#0dcaf0',
            'low': '#198754'
        }
        color = priority_colors.get(obj.task.priority, '#6c757d')
        return format_html(
            '<a href="{}" style="color: {}; font-weight: bold;">[{}] {}</a>', 
            url, color, obj.task.get_priority_display(), obj.task.title
        )
    task_display.short_description = '업무'
    
    def progress_display(self, obj):
        if obj.progress > 0:
            color = '#28a745' if obj.progress >= 100 else '#ffc107' if obj.progress >= 50 else '#17a2b8'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color, obj.progress
            )
        return '0%'
    progress_display.short_description = '진행률'

@admin.register(WorklogFile)
class WorklogFileAdmin(admin.ModelAdmin):
    list_display = [
        'original_name', 'worklog_display', 'uploaded_by', 
        'file_size', 'uploaded_at'
    ]
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['original_name', 'worklog__author__username']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def worklog_display(self, obj):
        url = reverse('admin:worklog_worklog_change', args=[obj.worklog.id])
        return format_html(
            '<a href="{}">{} - {}년 {}주차</a>', 
            url, obj.worklog.author.username, obj.worklog.year, obj.worklog.week_number
        )
    worklog_display.short_description = '워크로그'
    
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
