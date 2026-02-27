from django.urls import path
from . import views

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('api/user-tasks/', views.get_user_tasks_api, name='get_user_tasks_api'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('<int:task_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:task_id>/upload/', views.upload_file, name='upload_file'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    path('comment/file/<int:comment_id>/download/', views.download_comment_file, name='download_comment_file'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('<int:task_id>/status/', views.task_status_update, name='task_status_update'),
    path('board/partial/<int:pk>/', views.task_board_detail_partial, name='task_board_detail_partial'),
    path('planner/', views.TaskPlannerView.as_view(), name='task_planner'),
    path('planner/roadmap/', views.TaskRoadmapView.as_view(), name='task_roadmap'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
]
