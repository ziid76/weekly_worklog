from django.contrib import admin
from .models import CommonCode, ServiceRequest, ServiceRequestAttachment, ServiceInspection

# Register your models here.

@admin.register(CommonCode)
class CommonCode(admin.ModelAdmin):
    list_display = ('group', 'code', 'name')

class ServiceRequestAttachmentInline(admin.StackedInline):
    model = ServiceRequestAttachment
    extra = 0

@admin.register(ServiceRequest)
class ServiceRequest(admin.ModelAdmin):
    inlines = (ServiceRequestAttachmentInline,)
    list_display = ('req_type','req_system', 'assignee', 'status')


@admin.register(ServiceInspection)
class ServiceInspectionAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'inspector_name', 'created_at')
