from django.contrib import admin

from .models import (
    ApprovalHistory,
    ApprovalToken,
    DrivingLogEntry,
    DrivingLogSheet,
    Executive,
)


@admin.register(Executive)
class ExecutiveAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name', 'email']
    ordering = ['display_order', 'name']
    fields = ['name', 'email', 'is_active', 'display_order']


class DrivingLogEntryInline(admin.TabularInline):
    model = DrivingLogEntry
    extra = 0
    fields = [
        'log_date', 'is_holiday', 'start_time', 'end_time',
        'cumulative_distance', 'vehicle_number', 'overtime_minutes',
    ]
    readonly_fields = ['overtime_minutes']


@admin.register(DrivingLogSheet)
class DrivingLogSheetAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author', 'period_start', 'period_end', 'status',
        'reviewer', 'total_overtime_display', 'submitted_at', 'reviewed_at',
    ]
    list_filter = ['status', 'period_start', 'reviewer']
    search_fields = ['author__username', 'author__email', 'title']
    date_hierarchy = 'period_start'
    autocomplete_fields = ['author', 'reviewer']
    readonly_fields = ['total_overtime_minutes', 'created_at', 'updated_at']
    inlines = [DrivingLogEntryInline]

    fieldsets = (
        ('기본 정보', {
            'fields': ('author', 'title', 'period_start', 'period_end', 'status'),
        }),
        ('결재', {
            'fields': ('reviewer', 'submitted_at', 'reviewed_at', 'review_comment'),
        }),
        ('집계 / 시간 정보', {
            'fields': ('total_overtime_minutes', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def total_overtime_display(self, obj):
        return obj.total_overtime_display
    total_overtime_display.short_description = '초과근무 합계'


@admin.register(DrivingLogEntry)
class DrivingLogEntryAdmin(admin.ModelAdmin):
    list_display = [
        'log_date', 'sheet', 'is_holiday', 'start_time', 'end_time',
        'cumulative_distance', 'vehicle_number', 'overtime_minutes',
    ]
    list_filter = ['is_holiday', 'log_date']
    search_fields = ['sheet__author__username', 'vehicle_number']
    date_hierarchy = 'log_date'


@admin.register(ApprovalToken)
class ApprovalTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'scope', 'sheet', 'executive', 'expires_at', 'used_at', 'created_at']
    list_filter = ['scope']
    search_fields = ['token', 'executive__display_name']
    readonly_fields = ['token', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'sheet', 'action', 'actor_user', 'actor_executive', 'ip_address']
    list_filter = ['action']
    search_fields = ['sheet__author__username', 'comment']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
