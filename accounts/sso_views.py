"""
SSO Integration Views for ITMS
ITMS 프로젝트의 authentication/sso_views.py 파일로 복사하세요.

사용법:
1. 이 파일을 authentication/sso_views.py로 복사
2. urls.py에 URL 패턴 추가 (아래 참조)
"""
import secrets
import hashlib
import base64
import requests
import logging
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)


def generate_pkce_pair():
    """
    PKCE code_verifier와 code_challenge 생성
    
    Returns:
        tuple: (code_verifier, code_challenge)
    """
    # code_verifier: 43-128자의 랜덤 문자열
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    
    # code_challenge: code_verifier의 SHA256 해시
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge


def sso_login(request):
    """
    SSO 로그인 시작 - SSO 서버로 리다이렉트
    
    Flow:
    1. PKCE 파라미터 생성
    2. State 생성 (CSRF 방지)
    3. 세션에 저장
    4. SSO 인증 URL로 리다이렉트
    """
    try:
        # PKCE 생성
        code_verifier, code_challenge = generate_pkce_pair()
        
        # State 생성 (CSRF 방지)
        state = secrets.token_urlsafe(32)
        
        # 세션에 저장
        request.session['sso_code_verifier'] = code_verifier
        request.session['sso_state'] = state
        
        # 리다이렉트 URL 저장 (로그인 후 돌아갈 페이지)
        next_url = request.GET.get('next', '/')
        request.session['sso_next_url'] = next_url
        
        # SSO 인증 URL 생성
        params = {
            'client_id': settings.SSO_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': settings.SSO_REDIRECT_URI,
            'scope': ' '.join(settings.SSO_SCOPES),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        
        auth_url = f"{settings.SSO_AUTHORIZATION_URL}?{urlencode(params)}"
        
        logger.info(f"Redirecting to SSO login: {auth_url}")
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"SSO login error: {e}")
        return JsonResponse({
            'error': 'SSO login failed',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def sso_callback(request):
    """
    SSO 콜백 처리 - 인증 코드를 받아서 토큰 교환
    
    Flow:
    1. 에러 체크
    2. State 검증
    3. 인증 코드로 토큰 교환
    4. 사용자 인증
    5. 로그인 처리
    6. 원래 페이지로 리다이렉트
    """
    # 에러 체크
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"SSO callback error: {error} - {error_description}")
        return JsonResponse({
            'error': error,
            'error_description': error_description
        }, status=400)
    
    # 인증 코드 및 state 확인
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code or not state:
        logger.error("Missing code or state in callback")
        return JsonResponse({
            'error': 'Missing parameters',
            'message': 'Code or state parameter is missing'
        }, status=400)
    
    # State 검증 (CSRF 방지)
    session_state = request.session.get('sso_state')
    if state != session_state:
        logger.error(f"State mismatch: {state} != {session_state}")
        return JsonResponse({
            'error': 'Invalid state',
            'message': 'State parameter does not match'
        }, status=400)
    
    # 토큰 교환
    code_verifier = request.session.get('sso_code_verifier')
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.SSO_REDIRECT_URI,
        'client_id': settings.SSO_CLIENT_ID,
        'client_secret': settings.SSO_CLIENT_SECRET,
        'code_verifier': code_verifier,
    }
    
    try:
        logger.info("Exchanging authorization code for tokens")
        response = requests.post(
            settings.SSO_TOKEN_URL,
            data=token_data,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return JsonResponse({
                'error': 'Token exchange failed',
                'details': response.text
            }, status=400)
        
        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        if not access_token:
            logger.error("No access token in response")
            return JsonResponse({
                'error': 'No access token',
                'message': 'Access token not found in response'
            }, status=400)
        
        # 사용자 인증
        logger.info("Authenticating user with SSO token")
        user = authenticate(request, sso_token=access_token)
        
        if user:
            # 로그인 처리
            login(request, user)
            
            # 토큰을 세션에 저장
            request.session['sso_access_token'] = access_token
            if refresh_token:
                request.session['sso_refresh_token'] = refresh_token
            
            # 세션 정리
            request.session.pop('sso_code_verifier', None)
            request.session.pop('sso_state', None)
            
            logger.info(f"User {user.email} logged in via SSO")
            
            # 원래 페이지로 리다이렉트
            next_url = request.session.pop('sso_next_url', '/')
            return redirect(next_url)
        else:
            logger.error("User authentication failed")
            return JsonResponse({
                'error': 'Authentication failed',
                'message': 'Could not authenticate user with SSO token'
            }, status=401)
            
    except requests.RequestException as e:
        logger.error(f"SSO request error: {e}")
        return JsonResponse({
            'error': 'Request failed',
            'message': str(e)
        }, status=500)
    except Exception as e:
        logger.error(f"SSO callback error: {e}")
        return JsonResponse({
            'error': 'Internal error',
            'message': str(e)
        }, status=500)


@login_required
def sso_logout(request):
    """
    SSO 로그아웃 - 로컬 세션 종료 및 SSO 서버 로그아웃
    
    Flow:
    1. SSO 토큰 가져오기
    2. 로컬 로그아웃
    3. SSO 서버에 로그아웃 요청 (선택사항)
    4. 로그인 페이지로 리다이렉트
    """
    # SSO 토큰 가져오기
    access_token = request.session.get('sso_access_token')
    
    # 로컬 로그아웃
    logout(request)
    
    # SSO 서버 로그아웃 (선택사항)
    if access_token:
        try:
            logger.info("Logging out from SSO server")
            requests.post(
                settings.SSO_LOGOUT_URL,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=5
            )
        except Exception as e:
            logger.error(f"SSO logout error: {e}")
    
    return redirect('/login/')


def sso_status(request):
    """
    SSO 연동 상태 확인 (디버깅용)
    
    Returns:
        JSON response with authentication status
    """
    status_data = {
        'authenticated': request.user.is_authenticated,
        'user': None,
        'has_sso_token': 'sso_access_token' in request.session,
        'session_keys': list(request.session.keys()) if request.user.is_authenticated else []
    }
    
    if request.user.is_authenticated:
        status_data['user'] = {
            'email': request.user.email,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
    
    return JsonResponse(status_data)


"""
URLs.py에 추가할 내용:

from django.urls import path
from authentication import sso_views

urlpatterns = [
    # ... 기존 URL 패턴 ...
    
    # SSO 인증
    path('auth/sso/login/', sso_views.sso_login, name='sso_login'),
    path('auth/sso/callback/', sso_views.sso_callback, name='sso_callback'),
    path('auth/sso/logout/', sso_views.sso_logout, name='sso_logout'),
    path('auth/sso/status/', sso_views.sso_status, name='sso_status'),
]
"""
