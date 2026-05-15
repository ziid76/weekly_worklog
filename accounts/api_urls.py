from django.urls import path
from .api_views import RecipientListAPIView

app_name = 'accounts_api'

urlpatterns = [
    path('users', RecipientListAPIView.as_view(), name='recipient_list'),
]
