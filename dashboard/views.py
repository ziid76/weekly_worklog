from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from task.models import Task
from worklog.models import Worklog
from notifications.models import Notification

from monitor.models import OperationLog
from service.models import ServiceRequest

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
    
    # --- Monitor App Data ---
    # 1. 미처리 내역 (로그인한 사용자에게 할당된 완료되지 않은 점검일지)
    # Note: OperationLog model has 'duty_user' and 'completed' fields.
    monitor_pending_logs = OperationLog.objects.filter(
        duty_user=user,
        completed=False,
        date__lte=timezone.now().date()
    ).order_by('date')

    # 2. 향후 시스템점검일지 일정 (오늘 이후의 일정)
    monitor_upcoming_logs = OperationLog.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')[:5]

    # --- Service Request (SR) Data ---
    # 1. SR 접수 대상 (Status 'A': 요청접수)
    sr_receipt_target_count = ServiceRequest.objects.filter(status='A').count()

    # 2. 현재 처리진행 중인 SR 건수 (Status 'P': 처리중)
    sr_in_progress_count = ServiceRequest.objects.filter(status='P').count()

    # --- Average Lead Time Calculation ---
    # Calculate average lead time for completed operation logs
    # Lead time = completed_at - (date + 17:00)
    # Deadline is 5:00 PM on the operation log date
    
    avg_lead_time_hours = None
    avg_lead_time_days = None
    avg_lead_time_remaining_hours = None
    lead_time_status = None  # 'good' or 'attention'
    
    completed_logs = OperationLog.objects.filter(
        completed=True,
        completed_at__isnull=False
    )
    
    if completed_logs.exists():
        total_seconds = 0
        count = 0
        
        for log in completed_logs:
            # Create deadline: operation date at 5:00 PM (17:00)
            deadline = datetime.combine(log.date, datetime.min.time().replace(hour=17, minute=0))
            deadline = timezone.make_aware(deadline)
            
            # Calculate lead time (can be negative if completed before deadline)
            lead_time = (log.completed_at - deadline).total_seconds()
            total_seconds += lead_time
            count += 1
        
        # Calculate average in hours
        avg_lead_time_seconds = total_seconds / count
        avg_lead_time_hours = avg_lead_time_seconds / 3600
        
        # Convert to days and hours
        avg_lead_time_days = int(avg_lead_time_hours // 24)
        avg_lead_time_remaining_hours = int(avg_lead_time_hours % 24)
        
        # Determine status based on 24-hour threshold
        if avg_lead_time_hours <= 24:
            lead_time_status = 'good'
        else:
            lead_time_status = 'attention'

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
        # Monitor Data
        'monitor_pending_logs': monitor_pending_logs,
        'monitor_upcoming_logs': monitor_upcoming_logs,
        # SR Data
        'sr_receipt_target_count': sr_receipt_target_count,
        'sr_in_progress_count': sr_in_progress_count,
        'avg_lead_time_hours': avg_lead_time_hours,
        'avg_lead_time_days': avg_lead_time_days,
        'avg_lead_time_remaining_hours': avg_lead_time_remaining_hours,
        'lead_time_status': lead_time_status,
        'today': timezone.now().date(),
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
