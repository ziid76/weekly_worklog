# ITMS-SSO 연동 단계별 가이드

## 개요
이 문서는 itms.samchully.co.kr 웹서비스를 SSO 시스템과 실제로 연동하는 단계별 가이드입니다.

---

## 📋 사전 준비사항

### 필요한 정보
- **ITMS 도메인**: itms.samchully.co.kr
- **ITMS 프로젝트 경로**: D:\16.Dev\gemini
- **SSO 서버 URL**: http://localhost:8000 (개발) 또는 실제 SSO 도메인
- **연동 방식**: OAuth2 Authorization Code Flow with PKCE

---

## 🔧 Phase 1: SSO 시스템 설정 (현재 프로젝트)

### Step 1.1: SSO 서버 시작
```bash
# SSO 프로젝트 디렉토리에서
cd D:\16.Dev\SSO
python manage.py runserver 8000
```

### Step 1.2: 관리자 계정으로 로그인
```bash
# 브라우저에서
http://localhost:8000/admin/

# 관리자 계정이 없다면 생성
python manage.py createsuperuser
```

### Step 1.3: ServiceProvider 등록
Django Admin에서 다음 정보로 ServiceProvider 생성:

**기본 정보:**
- Name: `ITMS`
- Display Name: `삼천리 ITMS 시스템`
- Description: `삼천리 IT 관리 시스템`
- Client ID: `itms-client-id` (자동 생성 또는 수동 입력)
- Client Secret: (자동 생성 - 복사해두기!)

**OAuth2 설정:**
- Redirect URIs: 
  ```json
  [
    "http://itms.samchully.co.kr/auth/sso/callback/",
    "http://localhost:8001/auth/sso/callback/"
  ]
  ```
- Allowed Scopes:
  ```json
  ["openid", "profile", "email", "read", "write"]
  ```
- Token Endpoint Auth Method: `client_secret_post`

**SSO Portal 메타데이터:**
- Service URL: `http://itms.samchully.co.kr`
- Icon URL: (선택사항) ITMS 로고 URL
- Category: (선택사항) 카테고리 선택
- Is Visible: ✅ 체크
- Is Active: ✅ 체크

**저장 후 Client Secret 복사!** (다시 볼 수 없습니다)

### Step 1.4: 테스트 사용자 생성 및 권한 부여
```bash
# Django shell에서
python manage.py shell
```

```python
from authentication.models import User, ServiceProvider, UserServiceAccess
from django.utils import timezone

# 1. 테스트 사용자 생성
user = User.objects.create_user(
    username='testuser',
    email='testuser@samchully.co.kr',
    password='Test1234!',
    first_name='테스트',
    last_name='사용자'
)

# 2. ITMS ServiceProvider 가져오기
itms_service = ServiceProvider.objects.get(client_id='itms-client-id')

# 3. 사용자에게 ITMS 접근 권한 부여
access = UserServiceAccess.objects.create(
    user=user,
    service=itms_service,
    is_active=True,
    granted_by=None  # 또는 관리자 User 객체
)

print(f"✅ 사용자 {user.email}에게 ITMS 접근 권한 부여 완료")
```

또는 Django Admin에서:
1. `User Service Access` 메뉴 선택
2. "Add User Service Access" 클릭
3. User: testuser@samchully.co.kr 선택
4. Service: ITMS 선택
5. Is Active: ✅ 체크
6. Save

---

## 🔧 Phase 2: ITMS 시스템 설정 (D:\16.Dev\gemini)

### Step 2.1: 필요한 패키지 설치
```bash
cd D:\16.Dev\gemini
pip install requests PyJWT cryptography
```

### Step 2.2: 환경 변수 설정
`.env` 파일 생성 또는 수정:

```env
# SSO 설정
SSO_SERVER_URL=http://localhost:8000
SSO_CLIENT_ID=itms-client-id
SSO_CLIENT_SECRET=<Step 1.3에서 복사한 Client Secret>
SSO_REDIRECT_URI=http://localhost:8001/auth/sso/callback/
SSO_SCOPES=openid profile email read write

# ITMS 서버 설정
ITMS_SERVER_PORT=8001
```

### Step 2.3: Django Settings 수정
`settings.py`에 추가:

```python
from decouple import config

# SSO 설정
SSO_SERVER_URL = config('SSO_SERVER_URL', default='http://localhost:8000')
SSO_CLIENT_ID = config('SSO_CLIENT_ID')
SSO_CLIENT_SECRET = config('SSO_CLIENT_SECRET')
SSO_REDIRECT_URI = config('SSO_REDIRECT_URI')
SSO_SCOPES = config('SSO_SCOPES', default='openid profile email').split()

# SSO 엔드포인트
SSO_AUTHORIZATION_URL = f'{SSO_SERVER_URL}/oauth/authorize/'
SSO_TOKEN_URL = f'{SSO_SERVER_URL}/oauth/token/'
SSO_USERINFO_URL = f'{SSO_SERVER_URL}/oauth/userinfo/'
SSO_LOGOUT_URL = f'{SSO_SERVER_URL}/auth/logout/'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'authentication.backends.SSOAuthenticationBackend',  # SSO 백엔드 추가
    'django.contrib.auth.backends.ModelBackend',  # 기본 백엔드 유지
]

# Session 설정
SESSION_COOKIE_AGE = 86400  # 24시간
SESSION_SAVE_EVERY_REQUEST = True
```

### Step 2.4: SSO Authentication Backend 생성
`authentication/backends.py` 파일 생성:

```python
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
```

### Step 2.5: SSO Views 생성
`authentication/sso_views.py` 파일 생성:

```python
"""
SSO Integration Views
SSO 시스템과의 연동을 위한 뷰
"""
import secrets
import hashlib
import base64
import requests
from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)


def generate_pkce_pair():
    """
    PKCE code_verifier와 code_challenge 생성
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
    """
    # PKCE 생성
    code_verifier, code_challenge = generate_pkce_pair()
    
    # 세션에 저장
    request.session['sso_code_verifier'] = code_verifier
    request.session['sso_state'] = secrets.token_urlsafe(32)
    
    # SSO 인증 URL 생성
    params = {
        'client_id': settings.SSO_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.SSO_REDIRECT_URI,
        'scope': ' '.join(settings.SSO_SCOPES),
        'state': request.session['sso_state'],
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    from urllib.parse import urlencode
    auth_url = f"{settings.SSO_AUTHORIZATION_URL}?{urlencode(params)}"
    
    logger.info(f"Redirecting to SSO: {auth_url}")
    return redirect(auth_url)


@csrf_exempt
def sso_callback(request):
    """
    SSO 콜백 처리 - 인증 코드를 받아서 토큰 교환
    """
    # 에러 체크
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"SSO error: {error} - {error_description}")
        return JsonResponse({
            'error': error,
            'error_description': error_description
        }, status=400)
    
    # 인증 코드 및 state 확인
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code or not state:
        return JsonResponse({'error': 'Missing code or state'}, status=400)
    
    # State 검증
    session_state = request.session.get('sso_state')
    if state != session_state:
        logger.error("State mismatch")
        return JsonResponse({'error': 'Invalid state'}, status=400)
    
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
        response = requests.post(
            settings.SSO_TOKEN_URL,
            data=token_data,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            return JsonResponse({
                'error': 'Token exchange failed',
                'details': response.text
            }, status=400)
        
        tokens = response.json()
        access_token = tokens.get('access_token')
        
        # 사용자 인증
        from django.contrib.auth import authenticate
        user = authenticate(request, sso_token=access_token)
        
        if user:
            login(request, user)
            
            # 토큰을 세션에 저장 (선택사항)
            request.session['sso_access_token'] = access_token
            request.session['sso_refresh_token'] = tokens.get('refresh_token')
            
            logger.info(f"User {user.email} logged in via SSO")
            
            # 메인 페이지로 리다이렉트
            return redirect('/')
        else:
            return JsonResponse({'error': 'Authentication failed'}, status=401)
            
    except Exception as e:
        logger.error(f"SSO callback error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def sso_logout(request):
    """
    SSO 로그아웃 - 로컬 세션 종료 및 SSO 서버 로그아웃
    """
    # SSO 토큰 가져오기
    access_token = request.session.get('sso_access_token')
    
    # 로컬 로그아웃
    logout(request)
    
    # SSO 서버 로그아웃 (선택사항)
    if access_token:
        try:
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
    """
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'user': request.user.email if request.user.is_authenticated else None,
        'has_sso_token': 'sso_access_token' in request.session,
    })
```

### Step 2.6: URL 설정
`urls.py`에 추가:

```python
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
```

### Step 2.7: 로그인 페이지 수정
기존 로그인 템플릿에 SSO 로그인 버튼 추가:

```html
<!-- templates/login.html 또는 해당 로그인 템플릿 -->
<div class="login-container">
    <h2>로그인</h2>
    
    <!-- 기존 로그인 폼 -->
    <form method="post">
        {% csrf_token %}
        <!-- ... 기존 폼 필드 ... -->
        <button type="submit">로그인</button>
    </form>
    
    <div class="divider">또는</div>
    
    <!-- SSO 로그인 버튼 추가 -->
    <a href="{% url 'sso_login' %}" class="btn btn-sso">
        🔐 SSO로 로그인
    </a>
</div>

<style>
.btn-sso {
    display: block;
    width: 100%;
    padding: 12px;
    background: #4CAF50;
    color: white;
    text-align: center;
    text-decoration: none;
    border-radius: 4px;
    margin-top: 10px;
}

.btn-sso:hover {
    background: #45a049;
}

.divider {
    text-align: center;
    margin: 20px 0;
    color: #666;
}
</style>
```

---

## 🧪 Phase 3: 연동 테스트

### Step 3.1: 서버 시작
```bash
# Terminal 1: SSO 서버
cd D:\16.Dev\SSO
python manage.py runserver 8000

# Terminal 2: ITMS 서버
cd D:\16.Dev\gemini
python manage.py runserver 8001
```

### Step 3.2: 기본 연결 테스트
```bash
# SSO 서버 상태 확인
curl http://localhost:8000/api/health/

# ITMS 서버 상태 확인
curl http://localhost:8001/
```

### Step 3.3: SSO 로그인 플로우 테스트

1. **ITMS 로그인 페이지 접속**
   ```
   http://localhost:8001/login/
   ```

2. **"SSO로 로그인" 버튼 클릭**
   - SSO 서버로 리다이렉트됨
   - URL: `http://localhost:8000/oauth/authorize/?client_id=...`

3. **SSO 로그인**
   - Email: `testuser@samchully.co.kr`
   - Password: `Test1234!`

4. **권한 승인**
   - 요청된 권한 확인
   - "승인" 버튼 클릭

5. **ITMS로 리다이렉트**
   - URL: `http://localhost:8001/auth/sso/callback/?code=...&state=...`
   - 자동으로 ITMS 메인 페이지로 이동

6. **로그인 확인**
   ```
   http://localhost:8001/auth/sso/status/
   ```
   
   응답 예시:
   ```json
   {
     "authenticated": true,
     "user": "testuser@samchully.co.kr",
     "has_sso_token": true
   }
   ```

### Step 3.4: 로그아웃 테스트
```
http://localhost:8001/auth/sso/logout/
```

---

## 🐛 문제 해결

### 문제 1: "Invalid redirect_uri"
**원인**: ServiceProvider의 redirect_uris에 콜백 URL이 등록되지 않음

**해결**:
```python
# Django shell에서
from authentication.models import ServiceProvider

itms = ServiceProvider.objects.get(client_id='itms-client-id')
itms.redirect_uris = [
    "http://itms.samchully.co.kr/auth/sso/callback/",
    "http://localhost:8001/auth/sso/callback/"
]
itms.save()
```

### 문제 2: "Access denied"
**원인**: 사용자에게 ITMS 접근 권한이 없음

**해결**:
```python
from authentication.models import User, ServiceProvider, UserServiceAccess

user = User.objects.get(email='testuser@samchully.co.kr')
itms = ServiceProvider.objects.get(client_id='itms-client-id')

UserServiceAccess.objects.create(
    user=user,
    service=itms,
    is_active=True
)
```

### 문제 3: "Token exchange failed"
**원인**: Client Secret이 잘못되었거나 PKCE 검증 실패

**해결**:
1. `.env` 파일의 `SSO_CLIENT_SECRET` 확인
2. ServiceProvider의 Client Secret과 일치하는지 확인
3. PKCE code_verifier가 세션에 제대로 저장되었는지 확인

### 문제 4: CORS 에러
**원인**: SSO 서버에서 ITMS 도메인을 허용하지 않음

**해결** (SSO settings.py):
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",
    "http://itms.samchully.co.kr",
]
```

---

## 📊 연동 확인 체크리스트

### SSO 시스템
- [ ] SSO 서버 실행 중 (포트 8000)
- [ ] ServiceProvider 등록 완료
- [ ] Client ID/Secret 생성 완료
- [ ] Redirect URIs 설정 완료
- [ ] 테스트 사용자 생성 완료
- [ ] UserServiceAccess 권한 부여 완료

### ITMS 시스템
- [ ] 필요한 패키지 설치 완료
- [ ] .env 파일 설정 완료
- [ ] settings.py SSO 설정 추가 완료
- [ ] SSOAuthenticationBackend 생성 완료
- [ ] SSO views 생성 완료
- [ ] URL 패턴 추가 완료
- [ ] 로그인 페이지에 SSO 버튼 추가 완료
- [ ] ITMS 서버 실행 중 (포트 8001)

### 기능 테스트
- [ ] SSO 로그인 플로우 정상 작동
- [ ] 사용자 정보 동기화 확인
- [ ] 세션 유지 확인
- [ ] 로그아웃 정상 작동
- [ ] 권한 없는 사용자 접근 차단 확인

---

## 🚀 다음 단계

연동이 완료되면:

1. **프로덕션 배포 준비**
   - HTTPS 설정
   - 실제 도메인 설정
   - 보안 강화 (SECRET_KEY, Client Secret 관리)

2. **추가 기능 구현**
   - 자동 로그인 (Remember Me)
   - 토큰 갱신 (Refresh Token)
   - 사용자 프로필 동기화
   - 권한 기반 접근 제어

3. **모니터링 설정**
   - 로그인 실패 추적
   - 성능 모니터링
   - 에러 알림

---

## 📞 지원

문제가 발생하면:
1. 로그 확인: `logs/sso_service.log` (SSO), ITMS 로그
2. Django shell에서 데이터 확인
3. 브라우저 개발자 도구 네트워크 탭 확인
4. 이 가이드의 문제 해결 섹션 참조
