from django.urls import path
from . import views

urlpatterns = [
    # 기존 주간 리포트
    path('', views.WeeklyReportListView.as_view(), name='weekly_report_list'),
    path('create/', views.generate_weekly_report, name='weekly_report_create'),
    path('generate/', views.generate_weekly_report, name='generate_weekly_report'),
    path('weekly/<int:year>/<int:week_number>/', views.weekly_report_detail, name='weekly_report_detail'),
    path('confirm-closing/', views.confirm_closing_api, name='confirm_closing_api'),
    path('team-summary/', views.team_worklog_summary, name='team_worklog_summary'),
    path('popup/<int:year>/<int:week_number>/', views.worklog_summary_popup, name='worklog_summary_popup'),
]
