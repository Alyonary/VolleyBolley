import os
from datetime import timedelta
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR_OUT = Path(__file__).resolve().parents[2]

ENV_PATH = BASE_DIR_OUT / 'infra' / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', get_random_secret_key())

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

if not ALLOWED_HOSTS:
    raise ValueError(
        'Failed to get ALLOWED_HOSTS from the file ".env". '
        'Check the path to the file ".env"'
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'social_django',
    'django_celery_beat',
    'apps.users.apps.UsersConfig',
    'apps.api.apps.ApiConfig',
    'apps.players.apps.PlayersConfig',
    'apps.courts.apps.CourtsConfig',
    'apps.event.apps.EventConfig',
    'apps.core.apps.CoreConfig',
    'apps.locations.apps.LocationsConfig',
    'apps.notifications.apps.NotificationsConfig',
    'phonenumber_field',
    'django_filters',
    'drf_yasg',
]

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    'https://api.volleybolley.app',
    'https://www.api.volleybolley.app',
]
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.api.middlewares.OAuthResponseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'volleybolley.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates',],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'volleybolley.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'volleybolley_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend']
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'SHOW_REFRESH_TOKEN': False,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

SOCIAL_AUTH_URL_NAMESPACE = 'api:social'
SOCIAL_AUTH_RAISE_EXCEPTIONS = True if DEBUG else False
SOCIAL_AUTH_LOG_REDIRECTS = True
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_CLEAN_USERNAMES = False

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'apps.players.pipeline.create_player',
    'apps.api.pipeline.generate_json_response',
    'apps.api.pipeline.raise_oauth_success',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', ''
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'access_type': 'online'}
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = (
    'https://api.volleybolley.app/api/social-auth/complete/google-oauth2/'
)

FIREBASE_SERVICE_ACCOUNT = {
    'type': os.getenv('FIREBASE_TYPE', 'service_account'),
    'project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
    'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
    'private_key': os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
    'client_email': os.getenv('FIREBASE_CLIENT_EMAIL', ''),
    'client_id': os.getenv('FIREBASE_CLIENT_ID', ''),
    'auth_uri': os.getenv(
        'FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'
    ),
    'token_uri': os.getenv(
        'FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'
    ),
    'auth_provider_x509_cert_url': os.getenv(
        'FIREBASE_AUTH_PROVIDER_CERT_URL',
        'https://www.googleapis.com/oauth2/v1/certs'
    ),
    'client_x509_cert_url': os.getenv('FIREBASE_CLIENT_CERT_URL', ''),
    'universe_domain': os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com'),
}


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

TEMPLATES_DIRS = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIRS],
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

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'
AUTO_CREATE_DEFAULT_SUPERUSER = os.getenv(
    'AUTO_CREATE_DEFAULT_SUPERUSER', False
)
MANY_SUPERUSERS = os.getenv('MANY_SUPERUSERS', False)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
            'level': 'DEBUG',
            'encoding': 'utf-8',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': 'errors.log',
            'formatter': 'verbose',
            'level': 'ERROR',
            'encoding': 'utf-8',
        },
        'notifications_file': {
            'class': 'logging.FileHandler',
            'filename': 'notifications.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'rest_framework': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'social_core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'allauth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'oauthlib': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'requests_oauthlib': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'apps.api': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.api.views': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # 'root': {
        #     'handlers': ['console'],
        #     'level': 'INFO',
        # },
    },
}

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', 'redis_pass')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Configuration Options
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 1500  # 25 minutes

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter token in format: '
                           '**Bearer <your_access_token>**\n\n'
                           'You can obtain the token through authentication'
                           ' endpoints:\n'
                           '- Authenticate via Google (id_token)\n'
                           '- Authenticate via Google (firebase id_token)\n'
                           '- Authenticate via Facebook (firebase id_token)\n'
                           '- Authenticate via phone number '
                           '(firebase id_token)\n\n'
                           'Response will include JSON with access_token, '
                           'refresh_token and player data.'
        },
        'JWT': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter token in format: '
                           '**JWT <your_access_token>**\n\n'
                           'You can obtain the token through authentication'
                           ' endpoints:\n'
                           '- Authenticate via Google (id_token)\n'
                           '- Authenticate via Google (firebase id_token)\n'
                           '- Authenticate via Facebook (firebase id_token)\n'
                           '- Authenticate via phone number '
                           '(firebase id_token)\n\n'
                           'Response will include JSON with access_token, '
                           'refresh_token and player data.'
        }
    },
    'USE_SESSION_AUTH': False,

    # Settings for Authorize button
    'SECURITY_REQUIREMENTS': [
        {'Bearer': []},
        {'JWT': []}
    ],

    # UI customization
    'DEEP_LINKING': True,
    'PERSIST_AUTH': True,
    'REFETCH_SCHEMA_ON_LOGGED_OUT': False,

    # Token descriptions
    'TOKEN_DESCRIPTION': f'''
    ### Token Information:

    - **Access Token Lifetime**: {SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']}
    - **Refresh Token Lifetime**: {SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']}
    - **Supported prefixes**: Bearer, JWT
    - **Algorithm**: {SIMPLE_JWT['ALGORITHM']}

    Use refresh_token through the appropriate endpoint to refresh your token.
    '''
}
