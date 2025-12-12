from django.contrib import admin
from .models import (
    System, Contract, Hardware, Software,
    AssetHistory, RegularInspection, RegularInspectionAttachment,
    ContractAttachment
)

@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager', 'status', 'launch_date')
    list_filter = ('status',)
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('name', 'contract_type', 'contractor', 'start_date', 'end_date', 'amount')
    list_filter = ('contract_type', 'start_date', 'end_date')
    search_fields = ('name', 'contractor')
    ordering = ('-start_date',)

@admin.register(Hardware)
class HardwareAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'manufacturer', 'status', 'purchase_date')
    list_filter = ('status', 'manufacturer')
    search_fields = ('name', 'model_name', 'serial_number')
    ordering = ('name',)

@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'manufacturer', 'license_type', 'status')
    list_filter = ('status', 'license_type')
    search_fields = ('name', 'manufacturer')
    ordering = ('name',)

@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ('get_asset_display', 'asset_type', 'action', 'user', 'created_at')
    list_filter = ('asset_type', 'action', 'created_at')
    search_fields = ('comment',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def get_asset_display(self, obj):
        """Display the asset name"""
        return obj.get_asset_name()
    get_asset_display.short_description = '자산'
    
    def has_add_permission(self, request):
        """Prevent manual creation through admin"""
        return False

@admin.register(RegularInspection)
class RegularInspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_month', 'system', 'contract', 'inspection_date', 'created_at')
    list_filter = ('inspection_month', 'inspection_date', 'created_at')
    search_fields = ('system__name', 'contract__name', 'result')
    ordering = ('-inspection_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(RegularInspectionAttachment)
class RegularInspectionAttachmentAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'filename', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'inspection__system__name')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)

@admin.register(ContractAttachment)
class ContractAttachmentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'filename', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'contract__name')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)
