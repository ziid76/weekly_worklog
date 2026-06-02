from django.urls import path

from . import views

app_name = 'driving_log'

urlpatterns = [
    # 운전자 화면
    path('', views.DrivingLogSheetListView.as_view(), name='driving_log_list'),
    path('create/', views.DrivingLogSheetCreateView.as_view(), name='driving_log_create'),
    path('<int:pk>/', views.DrivingLogSheetDetailView.as_view(), name='driving_log_detail'),
    path('<int:pk>/edit/', views.DrivingLogSheetEditView.as_view(), name='driving_log_edit'),
    path('<int:pk>/delete/', views.DrivingLogSheetDeleteView.as_view(), name='driving_log_delete'),

    # AJAX
    path('api/sheet/<int:pk>/save/', views.save_sheet_api, name='driving_log_save_api'),
    path('api/sheet/<int:pk>/submit/', views.submit_sheet_api, name='driving_log_submit_api'),
    path('api/sheet/<int:pk>/resubmit/', views.resubmit_sheet_api, name='driving_log_resubmit_api'),
    path('api/sheet/<int:pk>/resend/',   views.resend_request_mail_api, name='driving_log_resend_api'),
    path('api/executives/', views.executives_api, name='driving_log_executives_api'),

    # 이메일 토큰 진입 (로그인 불필요, 토큰 자체가 인증)
    path('approve/<uuid:token>/', views.approve_via_email, name='driving_log_approve_email'),
    path('reject/<uuid:token>/',  views.reject_via_email,  name='driving_log_reject_email'),
    path('history/<uuid:token>/', views.history_via_email, name='driving_log_history_email'),
    path('history/<uuid:token>/sheet/<int:sheet_pk>/',
         views.history_sheet_detail_via_email,
         name='driving_log_history_sheet_detail_email'),

    # 안내 페이지
    path('no-permission/', views.no_permission, name='no_permission'),

    # 지원팀 관리자 화면 (P5) — is_staff/superuser. 강제 변경은 Django admin 으로.
    path('admin/sheets/',
         views.DrivingLogAdminListView.as_view(),
         name='admin_sheet_list'),
    path('admin/sheets/export/',
         views.driving_log_admin_csv_export,
         name='admin_sheet_csv'),
    path('admin/sheets/<int:pk>/',
         views.DrivingLogAdminDetailView.as_view(),
         name='admin_sheet_detail'),
]
