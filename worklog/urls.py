from django.urls import path
from .views import (
    WorklogListView, WorklogCreateView, WorklogUpdateView, 
    WorklogDeleteView, WorklogDetailView, upload_worklog_file, download_worklog_file,
    copy_worklog_api, my_worklog_history, writing_guide
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
    
    # API 엔드포인트
    path('api/copy/<int:worklog_id>/', copy_worklog_api, name='copy_worklog_api'),
    path('api/writing_guide/', writing_guide, name='writing_guide'),
]