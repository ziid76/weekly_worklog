from django.contrib import admin
from .models import CommonCode, ServiceRequest, ServiceRequestAttachment, ServiceInspection, ServiceRequestFormData, FormElement, Dataset

# Register your models here.

@admin.register(CommonCode)
class CommonCode(admin.ModelAdmin):
    list_display = ('group', 'code', 'name', 'category','separator', 'display_order', 'dataset', 'active')

class ServiceRequestAttachmentInline(admin.StackedInline):
    model = ServiceRequestAttachment
    extra = 0

class ServiceRequestFormDataInline(admin.TabularInline):
    model = ServiceRequestFormData
    extra = 0

@admin.register(ServiceRequest)
class ServiceRequest(admin.ModelAdmin):
    inlines = (ServiceRequestAttachmentInline, ServiceRequestFormDataInline)
    list_display = ('req_type','req_system', 'assignee', 'status')


@admin.register(ServiceInspection)
class ServiceInspectionAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'inspector_name', 'created_at')

@admin.register(ServiceRequestFormData)
class ServiceRequestFormDataAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'dataset', 'field_key', 'field_value')
    list_filter = ('dataset', 'field_key')
    search_fields = ('service_request__req_title', 'field_key', 'field_value')


class FormElementInline(admin.TabularInline):
    model = FormElement
    extra = 1
    fields = ('element_name', 'element_code', 'element_type', 'is_required', 'order', 'placeholder', 'active')
    ordering = ('order',)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'active', 'created_at')
    list_filter = ('active',)
    search_fields = ('name', 'code')
    ordering = ('code',)
    inlines = [FormElementInline]


@admin.register(FormElement)
class FormElementAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'element_name', 'element_code', 'element_type', 'is_required', 'order', 'active')
    list_filter = ('dataset', 'element_type', 'is_required', 'active')
    search_fields = ('dataset__name', 'dataset__code', 'element_name', 'element_code')
    ordering = ('dataset', 'order', 'element_name')
    list_editable = ('order', 'active', 'is_required')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('dataset', 'element_name', 'element_code')
        }),
        ('폼 설정', {
            'fields': ('element_type', 'placeholder', 'is_required', 'order', 'active')
        }),
    )
