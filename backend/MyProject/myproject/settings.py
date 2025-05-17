import base64
import os
from cryptography.fernet import Fernet
from pathlib import Path
from django.core.management.utils import get_random_secret_key
import sys
from datetime import timedelta

SERVER_IP = ""  # Enter server IP before running

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security-critical settings with NO DEFAULTS
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise Exception("SECRET_KEY environment variable is required in production")

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise Exception("ENCRYPTION_KEY environment variable is required in production")
ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

# Production security
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# Always apply security headers, with stricter settings in production
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_BROWSER_XSS_FILTER = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database with SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': '5432', 
        # Add SSL for production database connections
        'OPTIONS': {
            'sslmode': 'require',
        } if not DEBUG else {},
        # Add connection pooling and timeout settings
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',
        } if not DEBUG else {'connect_timeout': 10},
    }
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'graphene_django',
    'rest_framework',
    'channels',
    'myapp',
    'payments',
    'rest_framework_simplejwt.token_blacklist',
    'ratelimit',
]

SIMULATED_PAYMENT = {
    'SUCCESS_RATE': 1.0,
    'CURRENCY': 'INR',
    'ENCRYPTION_ENABLED': True,
}

# Middleware
MIDDLEWARE = [
    'ratelimit.middleware.RatelimitMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# FOR DEVELOPMENT, ONLY WORKS FOR SINGLE WORKER, NEED REDIS FOR PRODUCTION FOR MULTIPLE WORKERS
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer",
#     },
# }

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],  # Tuple format (host, port)
        },
    },
}

# CORS & CSRF Protection - Only allow specific origins
CORS_ALLOWED_ORIGINS = [
    f"https://{SERVER_IP}",
    # "http://localhost:8080",  # Development only
]

ALLOWED_HOSTS = [
    f'{SERVER_IP}',  # Production server
    'backend',        # Container name
    'backend.local',  # Docker network alias
    # 'localhost',      # Local development
]

CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    f"https://{SERVER_IP}",
    # "http://localhost:8080",  # Development only
]

# Cookie & Session Settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Need to access in JS for AJAX requests
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour

# Proxy Configuration
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'", f"wss://{SERVER_IP}")

# Rest of the configuration
ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'
ASGI_APPLICATION = 'myproject.asgi.application'

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

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
            ],
        },
    },
]

# Media Handling with restricted file types
MEDIA_ROOT = '/var/www/media'
MEDIA_URL = '/media/'
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# Define allowed file extensions
ALLOWED_UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx', '.csv']

# REST Framework with enhanced security
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'myapp.authentication.CookiesJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '120/minute',
        'forgot_password': '3/hour'
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ] if not DEBUG else [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_SECURE": not DEBUG,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SAMESITE": "Strict",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
}

# Rate limiting configuration
RATELIMIT_VIEW = 'myapp.views.ratelimited_error'
RATELIMIT_KEY_FUNCTION = 'django_ratelimit.utils.get_client_ip'
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Disable email if credentials aren't available
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'json',
            'mode': 'a',
        },
        'security': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/security.log'),
            'formatter': 'json',
            'mode': 'a'
        },
    },
    'loggers': {
        'django': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True,
        },
        'channels': {
                    'handlers': ['console'],
                    'level': 'DEBUG',
                    'propagate': False,
                },
        'myapp.consumers': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
