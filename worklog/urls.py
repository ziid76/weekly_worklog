from django.urls import path
from .views import (
    WorklogListView, WorklogCreateView, WorklogUpdateView, 
    WorklogDeleteView, WorklogDetailView, upload_worklog_file, download_worklog_file,
    get_user_tasks_api, worklog_add_task, worklog_remove_task, worklog_update_task, copy_worklog_api,
    my_worklog_history
)

urlpatterns = [
    path('my-history/', my_worklog_history, name='my_worklog_history'),
    path('', WorklogListView.as_view(), name='worklog_list'),
    path('create/<int:year>/<int:week_number>/', WorklogCreateView.as_view(), name='worklog_create_for_week'),
    path('<int:pk>/', WorklogDetailView.as_view(), name='worklog_detail'),
    path('<int:pk>/update/', WorklogUpdateView.as_view(), name='worklog_update'),
    path('<int:pk>/delete/', WorklogDeleteView.as_view(), name='worklog_delete'),
    
    # 파일 관련
    path('<int:worklog_id>/upload/', upload_worklog_file, name='upload_worklog_file'),
    path('file/<int:file_id>/download/', download_worklog_file, name='download_worklog_file'),
    
    # Task 관련 - 모든 함수 이름 업데이트
    path('<int:worklog_id>/add-task/', worklog_add_task, name='add_task_to_worklog'),
    path('<int:worklog_id>/remove-task/<int:task_id>/', worklog_remove_task, name='remove_task_from_worklog'),
    path('<int:worklog_id>/update-task/<int:task_id>/', worklog_update_task, name='update_worklog_task'),
    
    # API 엔드포인트
    path('api/tasks/', get_user_tasks_api, name='get_user_tasks_api'),
    path('api/copy/<int:worklog_id>/', copy_worklog_api, name='copy_worklog_api'),
]