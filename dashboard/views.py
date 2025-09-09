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
    
    # 업무 통계 (작성한 업무 + 할당받은 업무)
    user_tasks = Q(author=user) | Q(assigned_to=user)
    total_tasks = Task.objects.filter(user_tasks).distinct().count()
    todo_tasks = Task.objects.filter(user_tasks, status='todo').distinct().count()
    in_progress_tasks = Task.objects.filter(user_tasks, status='in_progress').distinct().count()
    done_tasks = Task.objects.filter(user_tasks, status='done').distinct().count()
    
    # 우선순위별 업무 통계
    urgent_tasks = Task.objects.filter(user_tasks, priority='urgent').distinct().count()
    high_tasks = Task.objects.filter(user_tasks, priority='high').distinct().count()
    medium_tasks = Task.objects.filter(user_tasks, priority='medium').distinct().count()
    low_tasks = Task.objects.filter(user_tasks, priority='low').distinct().count()
    
    # 마감일 임박 업무 (3일 이내)
    upcoming_deadline = timezone.now() + timedelta(days=3)
    week_before = timezone.now() + timedelta(days=-7)
    urgent_deadline_tasks = Task.objects.filter(
        user_tasks,
        due_date__lte=upcoming_deadline,
        due_date__gte=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).distinct().order_by('due_date')

    new_tasks = Task.objects.filter(
        user_tasks,
        created_at__gte=week_before
    ).distinct().order_by('due_date')

    newly_start_tasks = Task.objects.filter(
        user_tasks,
        created_at__gte=week_before,
        status='in_progress'
    ).distinct().order_by('due_date')
    
    # 연체된 업무
    overdue_tasks = Task.objects.filter(
        user_tasks,
        due_date__lt=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).distinct().order_by('due_date')

    # 최근 업무
    recent_tasks = Task.objects.filter(user_tasks).distinct()[:5]
   
    # 최근 워크로그
    recent_worklogs = Worklog.objects.filter(author=user)[:5]
    
    # 최근 알림 (최근 활동으로 표시)
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    
    # 읽지 않은 알림
    unread_notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    
    # 카테고리별 업무 통계
    category_stats = Task.objects.filter(user_tasks).distinct().values('category__name', 'category__color').annotate(count=Count('id'))
    
    context = {
        'total_tasks': total_tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'urgent_tasks': urgent_tasks,
        'high_tasks': high_tasks,
        'medium_tasks': medium_tasks,
        'low_tasks': low_tasks,
        'urgent_deadline_tasks': urgent_deadline_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'recent_worklogs': recent_worklogs,
        'recent_notifications': recent_notifications,
        'unread_notifications': unread_notifications,
        'category_stats': category_stats,
        'new_tasks':new_tasks,
        'newly_start_tasks':newly_start_tasks,
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
        # 업무 검색 (작성한 업무 + 할당받은 업무)
        user_tasks = Q(author=request.user) | Q(assigned_to=request.user)
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            user_tasks
        ).distinct()
        
        # 워크로그 검색
        results['worklogs'] = Worklog.objects.filter(
            Q(this_week_work__icontains=query) | Q(next_week_plan__icontains=query),
            author=request.user
        )
    
    return render(request, 'dashboard/search_results.html', results)
