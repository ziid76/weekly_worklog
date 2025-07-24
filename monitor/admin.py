from django.contrib import admin
from .models import (
    LogCategory, LogSubcategory, OperationLog, 
    LogEntry, SubcategoryEntry, OperationLogAttachment
)


class LogSubcategoryInline(admin.TabularInline):
    model = LogSubcategory
    extra = 1


@admin.register(LogCategory)
class LogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('order', 'name')
    inlines = [LogSubcategoryInline]


@admin.register(LogSubcategory)
class LogSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'code', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('category', 'order', 'name')


class SubcategoryEntryInline(admin.TabularInline):
    model = SubcategoryEntry
    extra = 0


class LogEntryInline(admin.TabularInline):
    model = LogEntry
    extra = 0
    show_change_link = True


class OperationLogAttachmentInline(admin.TabularInline):
    model = OperationLogAttachment
    extra = 0


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'duty_user', 'completed', 'approved')
    list_filter = ('completed', 'approved', 'date')
    search_fields = ('date', 'duty_user__username')
    date_hierarchy = 'date'
    inlines = [LogEntryInline, OperationLogAttachmentInline]


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('operation_log', 'category', 'is_checked', 'checked_by', 'checked_at')
    list_filter = ('category', 'is_checked')
    search_fields = ('operation_log__date', 'category__name')
    inlines = [SubcategoryEntryInline]


@admin.register(SubcategoryEntry)
class SubcategoryEntryAdmin(admin.ModelAdmin):
    list_display = ('log_entry', 'subcategory', 'is_checked')
    list_filter = ('subcategory', 'is_checked')
    search_fields = ('log_entry__operation_log__date', 'subcategory__name')
