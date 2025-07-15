# URL 참조 오류 수정 완료

## 수정된 오류들

### 1. NoReverseMatch 오류 해결
- **오류**: `Reverse for 'weekly_report_create' not found`
- **해결**: reports/urls.py에 `weekly_report_create` URL 패턴 추가

### 2. 잘못된 URL 이름 수정
- **task_edit** → **task_update** (task/templates/task/task_list.html)
- **task_add_comment** → **add_comment** (task/templates/task/task_detail.html)
- **task_update_status** → **task_status_update** (task/templates/task/task_detail.html)

### 3. 존재하지 않는 뷰 제거
- task/urls.py에서 `CategoryUpdateView`, `CategoryDeleteView` 제거 (뷰가 존재하지 않음)

## 현재 유효한 URL 패턴들

### Task 앱 (task/)
```python
urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('<int:task_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:task_id>/upload/', views.upload_file, name='upload_file'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    path('<int:task_id>/status/', views.task_status_update, name='task_status_update'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
]
```

### Worklog 앱 (worklog/)
```python
urlpatterns = [
    path('', WorklogListView.as_view(), name='worklog_list'),
    path('create/', WorklogCreateView.as_view(), name='worklog_create'),
    path('<int:pk>/', WorklogDetailView.as_view(), name='worklog_detail'),
    path('<int:pk>/update/', WorklogUpdateView.as_view(), name='worklog_update'),
    path('<int:pk>/delete/', WorklogDeleteView.as_view(), name='worklog_delete'),
    path('<int:worklog_id>/upload/', upload_worklog_file, name='upload_worklog_file'),
    path('file/<int:file_id>/download/', download_worklog_file, name='download_worklog_file'),
    path('api/tasks/', get_user_tasks, name='get_user_tasks'),
    path('api/add-task/', add_task_to_worklog, name='add_task_to_worklog'),
]
```

### Reports 앱 (reports/)
```python
urlpatterns = [
    path('', views.WeeklyReportListView.as_view(), name='weekly_report_list'),
    path('create/', views.generate_weekly_report, name='weekly_report_create'),
    path('generate/', views.generate_weekly_report, name='generate_weekly_report'),
    path('<int:year>/<int:week_number>/', views.weekly_report_detail, name='weekly_report_detail'),
    path('team-summary/', views.team_worklog_summary, name='team_worklog_summary'),
]
```

### Accounts 앱 (accounts/)
```python
urlpatterns = [
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
```

### 메인 URL (config/urls.py)
```python
urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', dashboard, name='dashboard'),
    path('search/', search, name='search'),
    path('worklog/', include('worklog.urls')),
    path('task/', include('task.urls')),
    path('reports/', include('reports.urls')),
]
```

## 템플릿에서 사용하는 URL 참조

### 대시보드 (dashboard.html)
- `{% url 'task_create' %}` ✅
- `{% url 'task_list' %}` ✅
- `{% url 'worklog_create' %}` ✅
- `{% url 'weekly_report_create' %}` ✅

### 업무 목록 (task_list.html)
- `{% url 'task_create' %}` ✅
- `{% url 'task_detail' task.pk %}` ✅
- `{% url 'task_update' task.pk %}` ✅
- `{% url 'task_delete' task.pk %}` ✅

### 업무 상세 (task_detail.html)
- `{% url 'task_list' %}` ✅
- `{% url 'task_update' task.pk %}` ✅
- `{% url 'task_delete' task.pk %}` ✅
- `{% url 'add_comment' task.pk %}` ✅
- `{% url 'task_status_update' task.pk %}` ✅

### 워크로그 목록 (worklog_list.html)
- `{% url 'worklog_create' %}` ✅
- `{% url 'worklog_detail' worklog.pk %}` ✅
- `{% url 'worklog_update' worklog.pk %}` ✅
- `{% url 'worklog_delete' worklog.pk %}` ✅

### 베이스 템플릿 (base.html)
- `{% url 'dashboard' %}` ✅
- `{% url 'task_list' %}` ✅
- `{% url 'worklog_list' %}` ✅
- `{% url 'weekly_report_list' %}` ✅
- `{% url 'category_list' %}` ✅
- `{% url 'profile_edit' %}` ✅
- `{% url 'password_change' %}` ✅
- `{% url 'logout' %}` ✅
- `{% url 'login' %}` ✅

## 검증 완료
- `python3 manage.py check` 통과 ✅
- 모든 URL 패턴 정상 작동 ✅
- 템플릿 참조 오류 해결 ✅

## 주의사항
1. 새로운 뷰를 추가할 때는 반드시 urls.py에 패턴을 추가해야 함
2. 템플릿에서 URL 이름을 사용할 때는 정확한 이름을 사용해야 함
3. URL 이름을 변경할 때는 모든 템플릿에서 참조를 업데이트해야 함
4. `python3 manage.py check` 명령으로 정기적으로 검증 필요
