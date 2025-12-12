from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('systems/', views.SystemListView.as_view(), name='system_list'),
    path('systems/create/', views.SystemCreateView.as_view(), name='system_create'),
    path('systems/<int:pk>/', views.SystemDetailView.as_view(), name='system_detail'),
    path('systems/<int:pk>/edit/', views.SystemUpdateView.as_view(), name='system_edit'),
    path('systems/<int:pk>/history/add/', views.SystemHistoryCreateView.as_view(), name='system_history_add'),
    path('systems/search/', views.SystemSearchView.as_view(), name='system_search'),
    
    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/create/', views.ContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.ContractUpdateView.as_view(), name='contract_edit'),
    path('contracts/<int:pk>/search-related/', views.ContractSearchView.as_view(), name='contract_search_related'),
    path('contracts/<int:pk>/add-related/', views.AddRelatedContractView.as_view(), name='contract_add_related'),
    path('contracts/<int:pk>/remove-related/', views.RemoveRelatedContractView.as_view(), name='contract_remove_related'),
    path('contracts/<int:pk>/history/add/', views.ContractHistoryCreateView.as_view(), name='contract_history_add'),
    path('contracts/<int:pk>/attachments/<int:attachment_id>/delete/', views.ContractAttachmentDeleteView.as_view(), name='contract_attachment_delete'),

    path('hardwares/', views.HardwareListView.as_view(), name='hardware_list'),
    path('hardwares/create/', views.HardwareCreateView.as_view(), name='hardware_create'),
    path('hardwares/<int:pk>/', views.HardwareDetailView.as_view(), name='hardware_detail'),
    path('hardwares/<int:pk>/edit/', views.HardwareUpdateView.as_view(), name='hardware_edit'),
    path('hardwares/<int:pk>/history/add/', views.HardwareHistoryCreateView.as_view(), name='hardware_history_add'),
    
    path('softwares/', views.SoftwareListView.as_view(), name='software_list'),
    path('softwares/create/', views.SoftwareCreateView.as_view(), name='software_create'),
    path('softwares/<int:pk>/', views.SoftwareDetailView.as_view(), name='software_detail'),
    path('softwares/<int:pk>/edit/', views.SoftwareUpdateView.as_view(), name='software_edit'),
    path('softwares/<int:pk>/history/add/', views.SoftwareHistoryCreateView.as_view(), name='software_history_add'),
    
    path('inspections/create/', views.RegularInspectionCreateView.as_view(), name='inspection_create'),
]
