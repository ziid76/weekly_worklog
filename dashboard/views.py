from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from task.models import Task, Category
from worklog.models import Worklog
from notifications.models import Notification

@login_required
def dashboard(request):
    """대시보드 메인 페이지"""
    user = request.user
    
    # 업무 통계
    total_tasks = Task.objects.filter(author=user).count()
    todo_tasks = Task.objects.filter(author=user, status='todo').count()
    in_progress_tasks = Task.objects.filter(author=user, status='in_progress').count()
    done_tasks = Task.objects.filter(author=user, status='done').count()
    
    # 마감일 임박 업무 (3일 이내)
    upcoming_deadline = timezone.now() + timedelta(days=3)
    urgent_tasks = Task.objects.filter(
        author=user,
        due_date__lte=upcoming_deadline,
        due_date__gte=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')
    
    # 연체된 업무
    overdue_tasks = Task.objects.filter(
        author=user,
        due_date__lt=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')

    # 최근 업무
    recent_tasks = Task.objects.filter(author=user)[:5]
    print(recent_tasks)
    

    # 최근 워크로그
    recent_worklogs = Worklog.objects.filter(author=user)[:5]
    
    # 읽지 않은 알림
    unread_notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    
    # 우선순위별 업무 통계
    priority_stats = Task.objects.filter(author=user).values('priority').annotate(count=Count('id'))
    
    # 카테고리별 업무 통계
    category_stats = Task.objects.filter(author=user).values('category__name', 'category__color').annotate(count=Count('id'))
    
    context = {
        'total_tasks': total_tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'urgent_tasks': urgent_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'recent_worklogs': recent_worklogs,
        'unread_notifications': unread_notifications,
        'priority_stats': priority_stats,
        'category_stats': category_stats,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def search(request):
    """통합 검색 기능"""
    query = request.GET.get('q', '')
    results = {
        'tasks': [],
        'worklogs': [],
        'query': query
    }
    
    if query:
        # 업무 검색
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            author=request.user
        )
        
        # 워크로그 검색
        results['worklogs'] = Worklog.objects.filter(
            Q(this_week_work__icontains=query) | Q(next_week_plan__icontains=query),
            author=request.user
        )
    
    return render(request, 'dashboard/search_results.html', results)
