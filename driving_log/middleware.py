from django.shortcuts import redirect


# 운전 전용 사용자도 진입 가능한 URL prefix. 이 외의 모든 경로는 /driving-log/ 로 리다이렉트된다.
ALLOWED_PREFIXES_FOR_DRIVING_ONLY = (
    '/driving-log/',
    '/admin/',           # 안전망 — 운전 전용은 보통 is_staff=False 라 admin 진입 안되지만 차단은 admin 측에 위임
    '/accounts/',        # 로그인/로그아웃 등 인증 화면
    '/useraccounts/',    # 프로필 편집 등
    '/auth/',            # SSO
    '/logout/',
    '/static/',
    '/media/',
    '/summernote/',
)


class DrivingOnlyRedirectMiddleware:
    """운전 전용 사용자가 운행일지 외의 경로에 접근하면 /driving-log/ 로 리다이렉트.

    is_driving_log_only_user 로 판정되지 않는 사용자(슈퍼유저/스태프/기존 ITMS 사용자)는
    이 미들웨어를 완전히 통과하므로 기존 동작에 영향이 없다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # import 를 호출 시점에 하여 앱 초기화 순서 문제를 회피
        from .permissions import is_driving_log_only_user

        user = getattr(request, 'user', None)
        if user is not None and is_driving_log_only_user(user):
            path = request.path
            if not path.startswith(ALLOWED_PREFIXES_FOR_DRIVING_ONLY):
                return redirect('/driving-log/')

        return self.get_response(request)
