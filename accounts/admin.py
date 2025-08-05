from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '사용자 프로필'
    fields = ('last_name_ko', 'first_name_ko', 'position', 'phone', 'is_first_login', 'password_changed_at')
    readonly_fields = ('password_changed_at',)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_korean_name', 'get_is_first_login', 'get_password_changed_at')
    list_filter = UserAdmin.list_filter + ('profile__is_first_login',)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)
    
    def get_korean_name(self, obj):
        try:
            return obj.profile.get_korean_name if hasattr(obj, 'profile') else '-'
        except:
            return '-'
    get_korean_name.short_description = '한글명'
    
    def get_is_first_login(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return '예' if obj.profile.is_first_login else '아니오'
            return '-'
        except:
            return '-'
    get_is_first_login.short_description = '첫 로그인'
    get_is_first_login.boolean = True
    
    def get_password_changed_at(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.password_changed_at:
                return obj.profile.password_changed_at.strftime('%Y-%m-%d %H:%M')
            return '-'
        except:
            return '-'
    get_password_changed_at.short_description = '패스워드 변경일'

# 기존 User admin을 해제하고 새로운 admin 등록
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_korean_name', 'primary_team_display', 'position', 'is_first_login', 'password_changed_at', 'created_at']
    list_filter = ['position', 'is_first_login', 'created_at']
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
        ('보안 정보', {
            'fields': ('is_first_login', 'password_changed_at')
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
