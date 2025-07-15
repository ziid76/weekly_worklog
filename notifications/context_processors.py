from .models import Notification

def notifications(request):
    """
    알림 관련 컨텍스트를 모든 템플릿에서 사용할 수 있도록 제공
    """
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
        recent_notifications = Notification.objects.filter(user=request.user)[:5]
        
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_notifications.count(),
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
