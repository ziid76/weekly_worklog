from django.urls import path
from . import views

app_name = 'hooks'

urlpatterns = [
    # API
    path('whatap/<uuid:source_key>/', views.webhook_receive, name='whatap_webhook'),
    path('receive/<uuid:source_key>/', views.webhook_receive, name='generic_webhook'),
    
    # UI
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/<int:pk>/', views.incident_detail, name='incident_detail'),
    path('sources/', views.source_list, name='source_list'),
    path('sources/create/', views.source_create, name='source_create'),
]
