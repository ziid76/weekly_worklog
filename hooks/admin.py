from django.contrib import admin
from django.utils.html import format_html
from .models import WebhookSource, WebhookEvent, Incident, IncidentEvent

@admin.register(WebhookSource)
class WebhookSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'source_key', 'is_active', 'created_at')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name', 'source_key')
    readonly_fields = ('source_key', 'created_at')

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('source', 'received_at', 'processed', 'external_uuid')
    list_filter = ('source', 'processed', 'received_at')
    search_fields = ('external_uuid',)
    readonly_fields = ('source', 'payload', 'headers', 'received_at', 'external_uuid')
    ordering = ('-received_at',)

class IncidentEventInline(admin.TabularInline):
    model = IncidentEvent
    extra = 0
    readonly_fields = ('created_at', 'raw_event')
    fields = ('event_type', 'message', 'user', 'created_at', 'raw_event')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_display', 'level_display', 'source', 'projectName', 'assignee', 'created_at')
    list_filter = ('status', 'level', 'source', 'created_at')
    search_fields = ('title', 'description', 'fingerprint', 'projectName', 'oname')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    inlines = [IncidentEventInline]
    
    def status_display(self, obj):
        colors = {
            'open': '#dc3545',        # Red
            'acknowledged': '#ffc107', # Yellow
            'resolved': '#28a745',     # Green
            'closed': '#6c757d'        # Gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    status_display.short_description = '상태'

    def level_display(self, obj):
        colors = {
            'info': '#17a2b8',       # Cyan
            'warning': '#ffc107',    # Yellow
            'critical': '#fd7e14',   # Orange
            'fatal': '#dc3545'       # Red
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_level_display()
        )
    level_display.short_description = '심각도'

@admin.register(IncidentEvent)
class IncidentEventAdmin(admin.ModelAdmin):
    list_display = ('incident', 'event_type', 'user', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('message', 'incident__title')
    readonly_fields = ('created_at', 'raw_event')
