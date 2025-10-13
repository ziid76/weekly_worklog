"""Application URL configuration."""

from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    path("me/review", views.review_me, name="review_me"),
    path("manual/user", views.user_manual, name="user_manual"),
    path("manual/developer", views.developer_manual, name="developer_manual"),
]
