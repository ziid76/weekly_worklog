from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Team, TeamMembership

class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'created_by', 'member_count', 'leader_count', 
        'task_count', 'created_at'
    ]
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description', 'created_by__username']
    ordering = ['name']
    date_hierarchy = 'created_at'
    inlines = [TeamMembershipInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('시간 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def member_count(self, obj):
        count = obj.members.count()
        if count > 0:
            url = reverse('admin:teams_teammembership_changelist') + f'?team__id__exact={obj.id}'
            return format_html('<a href="{}">{} 명</a>', url, count)
        return '0 명'
    member_count.short_description = '멤버 수'
    
    def leader_count(self, obj):
        count = obj.teammembership_set.filter(role='leader').count()
        if count > 0:
            return format_html(
                '<span style="color: #007cba; font-weight: bold;">{} 명</span>',
                count
            )
        return '0 명'
    leader_count.short_description = '팀장 수'
    
    def task_count(self, obj):
        count = obj.task_set.count()
        if count > 0:
            url = reverse('admin:task_task_changelist') + f'?team__id__exact={obj.id}'
            return format_html('<a href="{}">{} 개</a>', url, count)
        return '0 개'
    task_count.short_description = '팀 업무 수'

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'team', 'role_display', 'joined_at', 
        'user_task_count'
    ]
    list_filter = ['role', 'joined_at', 'team']
    search_fields = ['user__username', 'team__name']
    ordering = ['-joined_at']
    date_hierarchy = 'joined_at'
    
    def role_display(self, obj):
        colors = {
            'admin': '#dc3545',
            'leader': '#fd7e14',
            'member': '#28a745'
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_role_display()
        )
    role_display.short_description = '역할'
    
    def user_task_count(self, obj):
        count = obj.user.tasks.filter(team=obj.team).count()
        if count > 0:
            url = reverse('admin:task_task_changelist') + f'?author__id__exact={obj.user.id}&team__id__exact={obj.team.id}'
            return format_html('<a href="{}">{} 개</a>', url, count)
        return '0 개'
    user_task_count.short_description = '팀 내 업무 수'
    
    actions = ['promote_to_leader', 'demote_to_member']
    
    def promote_to_leader(self, request, queryset):
        updated = queryset.update(role='leader')
        self.message_user(request, f'{updated}명을 팀장으로 승진시켰습니다.')
    promote_to_leader.short_description = '선택된 멤버를 팀장으로 승진'
    
    def demote_to_member(self, request, queryset):
        updated = queryset.update(role='member')
        self.message_user(request, f'{updated}명을 일반 멤버로 변경했습니다.')
    demote_to_member.short_description = '선택된 멤버를 일반 멤버로 변경'
