from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

class FirstLoginMiddleware:
    """첫 로그인 사용자를 패스워드 변경 페이지로 리다이렉트하는 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 로그인된 사용자이고, 첫 로그인인 경우
        if (not isinstance(request.user, AnonymousUser) and 
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            request.user.profile.is_first_login):
            
            # 이미 패스워드 변경 페이지에 있거나, 로그아웃 중이면 통과
            allowed_paths = [
                reverse('first_login_password_change'),
                reverse('logout'),
                '/accounts/logout/',
                '/admin/',  # 관리자 페이지는 예외
            ]
            
            if not any(request.path.startswith(path) for path in allowed_paths):
                return redirect('first_login_password_change')

        response = self.get_response(request)
        return response
