from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '사용자 프로필'
    fields = ('last_name_ko', 'first_name_ko', 'position', 'phone')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

# 기존 User admin을 해제하고 새로운 admin 등록
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_korean_name', 'primary_team_display', 'position', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['user__username', 'last_name_ko', 'first_name_ko']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user',)
        }),
        ('한국식 이름', {
            'fields': ('last_name_ko', 'first_name_ko')
        }),
        ('추가 정보', {
            'fields': ('position', 'phone')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_korean_name(self, obj):
        try:
            return obj.get_korean_name
        except:
            return '-'
    display_korean_name.short_description = '한국식 이름'
    
    def primary_team_display(self, obj):
        try:
            return obj.primary_team.name if obj.primary_team else '미배정'
        except:
            return '미배정'
    primary_team_display.short_description = '주요 팀'
