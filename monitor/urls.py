from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='monitor'),
    path('ops/logs/', views.operation_log_list, name='operation_log_list'),
    path('ops/logs/add', views.operation_log_add, name='operation_log_add'),
    path('ops/logs/<int:pk>/detail', views.operation_log_detail, name='operation_log_detail'),
    path('ops/logs/<int:pk>/complete', views.operation_log_complete, name='operation_log_complete'),
    path('ops/duty', views.operation_duty, name='operation_duty'),
    path('ops/duty/calendar', views.operation_calendar, name='operation_calendar'),
    path('ops/duty/get_data', views.get_table_data, name='get_duty_data'),
    path('ops/duty/save_data', views.save_table_data, name='save_duty_data'),
    path('ops/calendar/data', views.get_calendar_data, name='get_calendar_data'),
    path('ops/approve', views.operation_log_approval_list, name='operation_log_approval_list'),
    path('ops/approve/<int:pk>', views.operation_log_approve, name='operation_log_approve'),
    path('ops/subcategories/', views.get_subcategories, name='get_subcategories'),
]
