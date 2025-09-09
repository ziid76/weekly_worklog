from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def mark_notification_read(request, notification_id):
    """알림을 읽음으로 표시하고 관련 task로 이동"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # 알림을 읽음으로 표시
    notification.is_read = True
    notification.save()
    
    # task가 연결되어 있으면 task 상세 페이지로 이동
    if notification.task:
        return redirect('task_detail', pk=notification.task.id)
    else:
        # task가 없으면 대시보드로 이동
        return redirect('dashboard')

@login_required
def mark_all_notifications_read(request):
    """모든 알림을 읽음으로 표시"""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
