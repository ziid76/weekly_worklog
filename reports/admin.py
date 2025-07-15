from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import WeeklyReport, WeeklyReportComment

class WeeklyReportCommentInline(admin.TabularInline):
    model = WeeklyReportComment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['author', 'content', 'created_at']

@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = [
        'week_display', 'month_week_display', 'title', 'created_by', 
        'comment_count', 'created_at'
    ]
    list_filter = ['year', 'created_at', 'created_by']
    search_fields = ['title', 'created_by__username']
    ordering = ['-year', '-week_number']
    date_hierarchy = 'created_at'
    inlines = [WeeklyReportCommentInline]
    
    fieldsets = (
        ('기간 정보', {
            'fields': ('year', 'week_number')
        }),
        ('리포트 정보', {
            'fields': ('title', 'created_by', 'editable')
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
    
    def comment_count(self, obj):
        count = obj.comments.count()
        if count > 0:
            url = reverse('admin:reports_weeklyreportcomment_changelist') + f'?report__id__exact={obj.id}'
            return format_html('<a href="{}">{} 개</a>', url, count)
        return '0 개'
    comment_count.short_description = '댓글 수'
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weekly_reports.csv"'
        response.write('\ufeff')  # UTF-8 BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow([
            '연도', '주차', '월별주차', '제목', '작성자', '댓글수', '작성일', '수정일'
        ])
        
        for report in queryset:
            writer.writerow([
                report.year,
                report.week_number,
                report.month_week_display,
                report.title,
                report.created_by.username,
                report.comments.count(),
                report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                report.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        self.message_user(request, f'{queryset.count()}개 주간 리포트를 CSV로 내보냈습니다.')
        return response
    export_to_csv.short_description = '선택된 리포트를 CSV로 내보내기'

@admin.register(WeeklyReportComment)
class WeeklyReportCommentAdmin(admin.ModelAdmin):
    list_display = [
        'report_display', 'author', 'content_preview', 'created_at'
    ]
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'report__title', 'author__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def report_display(self, obj):
        url = reverse('admin:reports_weeklyreport_change', args=[obj.report.id])
        return format_html(
            '<a href="{}">{} - {}년 {}주차</a>', 
            url, obj.report.title, obj.report.year, obj.report.week_number
        )
    report_display.short_description = '리포트'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '댓글 내용'
