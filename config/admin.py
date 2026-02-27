from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html

class CustomAdminSite(AdminSite):
    site_header = 'ITMS 관리자'
    site_title = 'ITMS Admin'
    index_title = 'ITMS 관리 대시보드'
    
    def index(self, request, extra_context=None):
        """
        관리자 메인 페이지에 추가 정보 표시
        """
        extra_context = extra_context or {}
        
        # 각 모델의 통계 정보 추가
        from task.models import Task, Category
        from worklog.models import Worklog
        from teams.models import Team
        from notifications.models import Notification
        from django.contrib.auth.models import User
        
        stats = {
            'users_count': User.objects.count(),
            'tasks_count': Task.objects.count(),
            'categories_count': Category.objects.count(),
            'worklogs_count': Worklog.objects.count(),
            'teams_count': Team.objects.count(),
            'notifications_count': Notification.objects.count(),
            'pending_tasks': Task.objects.filter(status='todo').count(),
            'in_progress_tasks': Task.objects.filter(status='in_progress').count(),
            'completed_tasks': Task.objects.filter(status='done').count(),
            'unread_notifications': Notification.objects.filter(is_read=False).count(),
        }
        
        extra_context['stats'] = stats
        return super().index(request, extra_context)

# 커스텀 admin 사이트 인스턴스 생성
admin_site = CustomAdminSite(name='custom_admin')

# Django의 기본 admin 사이트 설정 변경
admin.site.site_header = 'ITMS 관리자'
admin.site.site_title = 'ITMS Admin'
admin.site.index_title = 'ITMS 관리 대시보드'
