from django.urls import path
from . import views

urlpatterns = [
    
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/remove-avatar/', views.remove_avatar, name='remove_avatar'),
    path('first-login-password-change/', views.first_login_password_change, name='first_login_password_change'),
    
    # 사용자 관리 (관리자 전용)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/teams/', views.user_team_manage, name='user_team_manage'),
    
    # AJAX 엔드포인트
    path('ajax/team/create/', views.team_create_ajax, name='team_create_ajax'),
    path('ajax/users/search/', views.user_search_ajax, name='user_search_ajax'),
]
