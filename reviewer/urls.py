from django.urls import path
from .views import ReviewDashboardView, ReviewActionAPIView, ReviewDetailAPIView

urlpatterns = [
    path('', ReviewDashboardView.as_view(), name='review_dashboard'),
    path('api/action/', ReviewActionAPIView.as_view(), name='review_action_api'),
    path('api/history/<uuid:pk>/', ReviewDetailAPIView.as_view(), name='review_detail_api'),
]
