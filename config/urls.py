from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import dashboard, search
from django.contrib.auth import views as auth_views
from accounts.views import CustomLoginView
from accounts import sso_views

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('useraccounts/', include('accounts.urls')),
    
    # SSO 인증
    path('auth/sso/login/', sso_views.sso_login, name='sso_login'),
    path('auth/sso/callback/', sso_views.sso_callback, name='sso_callback'),
    path('auth/sso/logout/', sso_views.sso_logout, name='sso_logout'),
    path('auth/sso/status/', sso_views.sso_status, name='sso_status'),
    
    path('dashboard/', dashboard, name='dashboard'),
    path('search/', search, name='search'),
    path('worklog/', include('worklog.urls')),
    path('task/', include('task.urls')),
    path('reports/', include('reports.urls')),
    path('batch/', include('batch.urls', namespace='batch')),
    path('monitor/', include('monitor.urls')),
    path('service/', include('service.urls')),
    path("notifications/", include("notifications.urls")),
    path('assets/', include('assets.urls')),
    path('hooks/', include('hooks.urls')),
    path('', include('app.urls')),
    path('summernote/', include('django_summernote.urls')), 
]


# Media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
