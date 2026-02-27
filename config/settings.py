from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/


# .env에서 환경변수 가져오기
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = int(os.environ.get('DEBUG', 1))

if os.environ.get('DJANGO_ALLOWED_HOSTS'):
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(',')
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'itms.samchully.co.kr']


CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://itms.samchully.co.kr"
).split(",")

SITE_URL ="https://itms.samchully.co.kr"

#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "30"))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'app',
    'accounts',
    'worklog',
    'task',
    'teams',
    'notifications',
    'dashboard',
    'reports',
    'monitor',
    'service',
    'mailing',
    'batch',
    'django_summernote',  # 임시 비활성화
    'django_ses',
    'templates',
    'assets',
    'hooks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'common.middleware.ThreadLocalUserMiddleware',  # Thread Local User Middleware
    'accounts.middleware.FirstLoginMiddleware',  # 첫 로그인 체크 미들웨어
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications',
                'common.context_processors.service_request_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# SSO 설정
SSO_SERVER_URL = os.environ.get('SSO_SERVER_URL', 'http://localhost:8000')
SSO_CLIENT_ID = os.environ.get('SSO_CLIENT_ID', '')
SSO_CLIENT_SECRET = os.environ.get('SSO_CLIENT_SECRET', '')
SSO_REDIRECT_URI = os.environ.get('SSO_REDIRECT_URI', 'http://localhost:8001/auth/sso/callback/')
SSO_SCOPES = os.environ.get('SSO_SCOPES', 'openid profile email').split()

# SSO 엔드포인트
SSO_AUTHORIZATION_URL = f'{SSO_SERVER_URL}/oauth/authorize/'
SSO_TOKEN_URL = f'{SSO_SERVER_URL}/oauth/token/'
SSO_USERINFO_URL = f'{SSO_SERVER_URL}/oauth/userinfo/'
SSO_LOGOUT_URL = f'{SSO_SERVER_URL}/auth/logout/'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.SSOAuthenticationBackend',  # SSO 백엔드 추가
    'django.contrib.auth.backends.ModelBackend',  # 기본 백엔드 유지
]

# Session 설정
SESSION_COOKIE_AGE = 86400  # 24시간
SESSION_SAVE_EVERY_REQUEST = True


# Email Settings for AWS SES
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION_NAME', 'ap-northeast-2')
AWS_SES_ACCESS_KEY_ID = os.environ.get('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.environ.get('AWS_SES_SECRET_ACCESS_KEY')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'gemini@example.com')


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases



DATABASES = {
    'default': {
        'ENGINE': os.environ.get("SQL_ENGINE", 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('SQL_DATABASE', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.environ.get('SQL_USER', 'user'),
        'PASSWORD': os.environ.get('SQL_PASSWORD', 'password'),
        'HOST': os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get("SQL_PORT", '5432'),
    }


}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'  # nginx와 공유하는 경로로 지정
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']
# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' if DEBUG else '/app/media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Summernote 설정
SUMMERNOTE_CONFIG = {
    'iframe': True,
    'summernote': {
        'airMode': False,
        'width': '100%',
        'height': '400',
        'lang': 'ko-KR',
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'underline', 'clear']],
            ['fontname', ['fontname']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['table', ['table']],
            ['insert', ['link', 'picture', 'video']],
            ['view', ['fullscreen', 'codeview', 'help']],
        ],
    },
    'disable_attachment': False,
    'attachment_require_authentication': True,
}


# 로그 디렉토리 설정
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_general': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'general.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_batch': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'batch.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file_general', 'file_error'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_general', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'batch': {
            'handlers': ['console', 'file_batch', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# [ITMS] settings.py 최하단에 추가
SESSION_COOKIE_NAME = 'itms_sessionid'   # SSO와 겹치지 않게 고유 이름 사용
CSRF_COOKIE_NAME = 'itms_csrftoken'
# 로컬(http) 테스트 환경용 설정
SESSION_COOKIE_SECURE = False   # https가 아니므로 False여야 함
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_DOMAIN = None    # localhost인 경우 비워두거나 None