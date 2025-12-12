from django.urls import path
from . import views

app_name = 'batch'

urlpatterns = [
    path('', views.batch_operations, name='operations'),
    path('send-review-notifications/', views.send_review_notifications, name='send_review_notifications'),
    path('generate-missing-reviews/', views.generate_missing_reviews, name='generate_missing_reviews'),
    path('check-monitor-notifications/', views.check_monitor_notifications, name='check_monitor_notifications'),
]
