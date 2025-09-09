from django.db.models import Q
from .models import Task

def task_count(request):
    """현재 사용자의 진행중 업무 수를 반환하는 컨텍스트 프로세서"""
    if request.user.is_authenticated:
        in_progress_tasks_count = Task.objects.filter(
            Q(author=request.user) | Q(assigned_to=request.user),
            status='in_progress'
        ).distinct().count()
        
        return {
            'in_progress_tasks_count': in_progress_tasks_count
        }
    return {
        'in_progress_tasks_count': 0
    }
