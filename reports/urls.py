from django.urls import path
from . import views

urlpatterns = [
    # 개인별 주간업무 이력
    path('personal-history/', views.personal_report_history, name='personal_report_history'),

    # 기존 주간 리포트
    path('', views.WeeklyReportListView.as_view(), name='weekly_report_list'),
    path('create/', views.generate_weekly_report, name='weekly_report_create'),
    path('generate/', views.generate_weekly_report, name='generate_weekly_report'),
    path('weekly/<int:id>/', views.weekly_report_detail, name='weekly_report_detail'),
    path('weekly/<int:report_id>/personal-comments/', views.add_personal_comment, name='add_personal_comment'),
    path('weekly/<int:id>/excel/', views.export_weekly_report_excel, name='export_weekly_report_excel'),
    path('weekly/<int:id>/pptx/', views.export_weekly_report_pptx, name='export_weekly_report_pptx'),
    path('confirm-closing/', views.confirm_closing_api, name='confirm_closing_api'),
    path('team-summary/', views.team_worklog_summary, name='team_worklog_summary'),
    path('popup/<int:year>/<int:week_number>/', views.worklog_summary_popup, name='worklog_summary_popup'),
]
