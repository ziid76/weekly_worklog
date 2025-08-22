from django.urls import path
from . import views

urlpatterns = [
    path('request', views.service_request_type_list, name='service_request_type_list'),
    path('<str:code>', views.service_request_create, name='service_request_create'),
    path('lists/', views.service_request_list, name='service_request_list'),
    path('list/<int:pk>', views.service_request_detail, name='service_request_detail'),
    path('list/search/', views.service_request_list_search, name='service_request_search'),
    path('admin_request_list/', views.service_admin_request_list, name='service_admin_request_list'),
    path('admin_release_list/', views.service_admin_release_list, name='service_admin_release_list'),
    path('approve/<int:pk>/', views.service_request_approve, name='service_request_approve'),  # 접수승인 URL
    path('assign/<int:pk>/', views.service_request_assign, name='service_request_assign'),    # 담당자 변경 URL
    path('split/<int:pk>/', views.child_service_request_create, name='child_service_request_create'),  # SR 분할 처리 URL
    path('accept/<int:pk>/', views.service_request_accept, name='service_request_accept'),  # 분할SR 접수
    path('inspection/<int:pk>/', views.service_request_inspection, name='service_request_inspection'),  # 검수요청
    path('inspection_result/<uuid:token>/', views.service_request_inspection_result, name='service_request_inspection_result'),
    path('release/<int:pk>/', views.service_request_release, name='service_request_release'),  # 검수요청
    path('release_approve/<int:pk>/', views.service_request_release_approve, name='service_request_release_approve'),  # 검수요청승인   
    path('complete/<int:pk>/', views.service_request_complete, name='service_request_complete'),  # 완료 처리
    path('report/', views.service_request_report, name='service_request_report'),
]