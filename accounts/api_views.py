from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class RecipientListAPIView(View):
    """
    Web Monitor의 '외부 API 대상자 가져오기' 기능과 연동되는 외부 시스템 API
    규격에 맞춰 사용자 목록을 반환합니다.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # 1. 인증 방식: Bearer Token (Authorization Header)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Unauthorized', 'message': 'Bearer Token is missing or invalid'}, 
                status=401
            )
        
        token = auth_header.split(' ')[1]
        if token != settings.INTERNAL_API_TOKEN:
            return JsonResponse(
                {'error': 'Unauthorized', 'message': 'Invalid Bearer Token'}, 
                status=401
            )

        try:
            # 2. 데이터 조회
            # 활성 상태이며 이메일이 있는 사용자만 필터링 (권장사항 반영)
            users = User.objects.filter(is_active=True).exclude(email='').select_related('profile')
            
            # 3. 데이터 구조 생성 (name, email 필수, email 중복 제거)
            recipient_list = []
            seen_emails = set()
            
            for user in users:
                if not user.email or user.email in seen_emails:
                    continue
                
                display_name = user.profile.display_name if hasattr(user, 'profile') else user.username
                recipient_list.append({
                    'name': display_name.strip(),
                    'email': user.email
                })
                seen_emails.add(user.email)

            # 4. 응답 데이터 반환 (JSON 리스트 형식)
            return JsonResponse(recipient_list, safe=False, json_dumps_params={'ensure_ascii': False})

        except Exception as e:
            # 5. 예외 처리 (500 Internal Server Error)
            return JsonResponse(
                {'error': 'Internal Server Error', 'message': str(e)}, 
                status=500
            )
