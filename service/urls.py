from django.urls import path
from . import views

urlpatterns = [
    path('request', views.service_request_type_list, name='service_request_type_list'),
    path('<str:code>', views.service_request_create, name='service_request_create'),
    path('lists/', views.service_request_list, name='service_request_list'),
    path('reception/', views.service_request_reception_list, name='service_request_reception_list'),
    path('reception/<int:pk>', views.service_request_reception_create, name='service_request_reception_create'),
    path('list/<int:pk>', views.service_request_detail, name='service_request_detail'),
    path('list/search/', views.service_request_list_search, name='service_request_search'),
    path('admin_approve_list/', views.service_admin_approve_list, name='service_admin_approve_list'),
    path('approve/<int:pk>/', views.service_request_approve, name='service_request_approve'),  # 접수승인 URL
    path('assign/<int:pk>/', views.service_request_assign, name='service_request_assign'),    # 담당자 변경 URL
    path('split/<int:pk>/', views.child_service_request_create, name='child_service_request_create'),  # SR 분할 처리 URL
    path('accept/<int:pk>/', views.service_request_accept, name='service_request_accept'),  # 분할SR 접수
    path('inspection/<int:pk>/', views.service_request_inspection, name='service_request_inspection'),  # 검수요청
    path('inspection_result/<uuid:token>/', views.service_request_inspection_result, name='service_request_inspection_result'),
    path('release/<int:pk>/', views.service_request_release, name='service_request_release'),  # 검수요청
    path('dataset/<str:dataset>/', views.dataset_data_list, name='dataset_data_list'),
    path('admin/dataset-status/', views.dataset_status_list, name='dataset_status_list'),
    path('admin/form-elements/', views.form_element_list, name='form_element_list'),
    path('admin/form-elements/create/', views.form_element_create, name='form_element_create'),
    path('admin/form-elements/<int:pk>/edit/', views.form_element_edit, name='form_element_edit'),
    path('admin/form-elements/<int:pk>/delete/', views.form_element_delete, name='form_element_delete'),
    path('admin/datasets/<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('admin/datasets/<int:pk>/delete/', views.dataset_delete, name='dataset_delete'),    path('release_approve/<int:pk>/', views.service_request_release_approve, name='service_request_release_approve'),  # 검수요청승인   
    path('complete/<int:pk>/', views.service_request_complete, name='service_request_complete'),  # 완료 처리
    path('report/', views.service_request_report, name='service_request_report'),
]
