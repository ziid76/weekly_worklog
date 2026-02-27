"""
SSO Authentication Backend
SSO 시스템과 연동하여 사용자 인증을 처리합니다.
"""
import requests
import jwt
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SSOAuthenticationBackend(BaseBackend):
    """
    SSO 시스템을 통한 사용자 인증 백엔드
    """
    
    def authenticate(self, request, sso_token=None, **kwargs):
        """
        SSO 토큰을 사용하여 사용자 인증
        """
        if not sso_token:
            return None
        
        try:
            # SSO 서버에서 사용자 정보 가져오기
            headers = {
                'Authorization': f'Bearer {sso_token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(
                settings.SSO_USERINFO_URL,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"SSO userinfo failed: {response.status_code}")
                return None
            
            user_data = response.json()
            
            # 사용자 정보로 로컬 사용자 생성 또는 업데이트
            user = self.get_or_create_user(user_data)
            
            return user
            
        except Exception as e:
            logger.error(f"SSO authentication error: {e}")
            return None
    
    def get_or_create_user(self, user_data):
        """
        SSO 사용자 정보로 로컬 사용자 생성 또는 업데이트
        """
        email = user_data.get('email')
        if not email:
            return None
        
        # 사용자 조회 또는 생성
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': user_data.get('username', email.split('@')[0]),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'is_active': True,
            }
        )
        
        # 기존 사용자 정보 업데이트
        if not created:
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        return user
    
    def get_user(self, user_id):
        """
        사용자 ID로 사용자 객체 반환
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
