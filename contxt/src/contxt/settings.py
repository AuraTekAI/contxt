
from pathlib import Path

import os
import json

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

env_file_path = BASE_DIR / '.env'
if not env_file_path.exists():
    raise ValueError(f"\n\n----> .env file does not exists. Please create .env file in this directory ({BASE_DIR}).\n\n")

environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=True)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
if DEBUG == 'True':
    DEBUG = True
else:
    DEBUG = False


# Application definition
INSTALLED_APPS = [
    # Pre installed apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # User defined apps
    "core",
    "accounts",
    "process_emails",
    "sms_app",

    # Third part apps
    "django_celery_beat",
    "rest_framework",
    "corsheaders",
    "drf_yasg",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "contxt.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "contxt.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

USE_SQLITE = env('USE_SQLITE')
if USE_SQLITE == 'True':
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER'),
            'PASSWORD': env('POSTGRES_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT')
        }
    }

CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL") + env("REDIS_DB"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

EMAILS_ENABLED = env('EMAILS_ENABLED')
if EMAILS_ENABLED == 'True' or EMAILS_ENABLED == 'true':
    EMAILS_ENABLED = True
else:
    EMAILS_ENABLED = False

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

ADMIN_EMAIL_ADDRESS = env('ADMIN_EMAIL_ADDRESS')
ADMIN_EMAIL_NAME = env('ADMIN_EMAIL_NAME')


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


PARENT_DIR = os.path.dirname(BASE_DIR)
LOG_DIR = os.path.join(PARENT_DIR, 'logs')

if not os.path.exists(LOG_DIR):
    print(f'logs directory not found. Please make sure that log directory exists at this path {LOG_DIR}')

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
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'formatter': 'verbose'
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'celery.log'),
            'formatter': 'verbose'
        },
        'login_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'login.log'),
            'formatter': 'verbose'
        },
        'pull_email_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'pull_email.log'),
            'formatter': 'verbose'
        },
        'push_email_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'push_email.log'),
            'formatter': 'verbose'
        },
        'mail_box_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'mail_box.log'),
            'formatter': 'verbose'
        },
        'accept_invite_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'accept_invite.log'),
            'formatter': 'verbose'
        },
        'send_sms_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'send_sms.log'),
            'formatter': 'verbose'
        },
        'sms_quota_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'sms_quota.log'),
            'formatter': 'verbose'
        },
        'sms_webhook_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'sms_webhook.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'login': {
            'handlers': ['console', 'login_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'pull_email': {
            'handlers': ['console', 'pull_email_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'push_email': {
            'handlers': ['console', 'push_email_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'mail_box': {
            'handlers': ['console', 'mail_box_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'accpet_invite': {
            'handlers': ['console', 'accept_invite_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'send_sms': {
            'handlers': ['console', 'send_sms_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'sms_quota': {
            'handlers': ['console', 'sms_quota_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'sms_webhook': {
            'handlers': ['console', 'sms_webhook_file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

AUTH_USER_MODEL = 'accounts.User'

SWAGGER_SETTINGS = {
'SECURITY_DEFINITIONS': {
 'Bearer':{
    'type':'apiKey',
    'name':'Authorization',
    'in':'header'
  }
 }
}

ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS').split(',')

SECRET_KEY = env("SECRET_KEY")

ENVIRONMENT = env("ENVIRONMENT")
TEST_MODE = env('TEST_MODE')
if TEST_MODE == 'True' or TEST_MODE == 'true':
    TEST_MODE = True
else:
    TEST_MODE = False


CELERY_ENABLED = env('CELERY_ENABLED')
if CELERY_ENABLED == 'True' or CELERY_ENABLED == 'true':
    CELERY_ENABLED = True
else:
    CELERY_ENABLED = False

BOT_TASK_INTERVAL_VALUE = env('BOT_TASK_INTERVAL_VALUE')
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

CELERY_TIMEZONE = env('CELERY_TIMEZONE')
TIME_ZONE = "UTC"


USE_ALTERNATE_LOGIN_DETAILS = env('USE_ALTERNATE_LOGIN_DETAILS')
if USE_ALTERNATE_LOGIN_DETAILS == 'True' or USE_ALTERNATE_LOGIN_DETAILS == 'true':
    USE_ALTERNATE_LOGIN_DETAILS = True
else:
    USE_ALTERNATE_LOGIN_DETAILS = False

ALTERNATE_USERNAME = env('ALTERNATE_USERNAME')
ALTERNATE_PASSWORD = env('ALTERNATE_PASSWORD')
USERNAME = env('USERNAME')
PASSWORD = env('PASSWORD')
LOGIN_REQUEST_HEADER = env('LOGIN_REQUEST_HEADER')
LOGIN_BUTTON_TEXT = env('LOGIN_BUTTON_TEXT')
LOGIN_PAGE = env('LOGIN_PAGE')
LOGIN_EMAIL_FIELD_ID = env('LOGIN_EMAIL_FIELD_ID')
LOGIN_PASSWORD_FIELD_ID = env('LOGIN_PASSWORD_FIELD_ID')
LOGIN_BUTTON_ID = env('LOGIN_BUTTON_ID')
SUPER_SECRET_INITIAL_USER_PASSWORD = env('SUPER_SECRET_INITIAL_USER_PASSWORD')

USE_PROXY = env('USE_PROXY')
if USE_PROXY == 'True' or USE_PROXY == 'true':
    USE_PROXY = True
else:
    USE_PROXY = False

PROXY_URL = env('PROXY_URL')

BASE_URL = env('BASE_URL')
INBOX_PAGE = env('INBOX_PAGE')
HTTPBIN_IP_URL_HTTP = env('HTTPBIN_IP_URL_HTTP')
HTTPBIN_IP_URL_HTTPS = env('HTTPBIN_IP_URL_HTTPS')
INBOX_URL = env('INBOX_URL')
SPLASH_URL = env('SPLASH_URL')
CONTACT_URL = env('CONTACT_URL')
REPLY_WEBHOOK_URL = env('REPLY_WEBHOOK_URL')
SMS_SEND_URL = env('SMS_SEND_URL')
SMS_STATUS_URL = env('SMS_STATUS_URL')
SMS_QUOTA_URL = env('SMS_QUOTA_URL')
UNREAD_MESSAGES_URL = env('UNREAD_MESSAGES_URL')

PULL_EMAIL_REQUEST_HEADERS = json.loads(env('PULL_EMAIL_REQUEST_HEADERS'))
COMPRESSED_VIEWSTATE_ID = env('COMPRESSED_VIEWSTATE_ID')
EMAIL_ROWS_CSS_SELECTOR = env('EMAIL_ROWS_CSS_SELECTOR')
FROM_ELEMENT_CSS_SELECTOR = env('FROM_ELEMENT_CSS_SELECTOR')
SUBJECT_ELEMENT_CSS_SELECTOR = env('SUBJECT_ELEMENT_CSS_SELECTOR')
DATE_ELEMENT_CSS_SELECTOR = env('DATE_ELEMENT_CSS_SELECTOR')
PULL_EMAIL_EVENTTARGET = env('PULL_EMAIL_EVENTTARGET')
ASYNCPOST = env('ASYNCPOST')
TOPSCRIPTMANAGER = env('TOPSCRIPTMANAGER')

HEADERS_FOR_PUSH_EMAIL_REQUEST = json.loads(env('HEADERS_FOR_PUSH_EMAIL_REQUEST'))
MAX_EMAIL_REPLY_RETRIES = int(env('MAX_EMAIL_REPLY_RETRIES'))
STATIC_COOKIES = json.loads(env('STATIC_COOKIES'))


USE_ALTERNATE_EMAIL = env('USE_ALTERNATE_EMAIL')
if USE_ALTERNATE_EMAIL == 'True' or USE_ALTERNATE_EMAIL == 'true':
    USE_ALTERNATE_EMAIL = True
else:
    USE_ALTERNATE_EMAIL = False

ALTERNATE_EMIALURL = env("ALTERNATE_EMIALURL")
ALTERNATE_EMAIL_USERNAME = env("ALTERNATE_EMAIL_USERNAME")
ALTERNATE_EMAIL_PASSWORD = env("ALTERNATE_EMAIL_PASSWORD")
EMAILURL = env("EMAILURL")
EMAIL_USERNAME = env('EMAIL_USERNAME')
EMAIL_PASSWORD = env('EMAIL_PASSWORD')
MAIL_SEARCH_DAYS_VALUE = int(env('MAIL_SEARCH_DAYS_VALUE'))
CONTXT_MAIL_SEARCH_STRING = env('CONTXT_MAIL_SEARCH_STRING')
CONTXT_MAIL_BROADER_SEARCH_STRING = env('CONTXT_MAIL_BROADER_SEARCH_STRING')
GMAIL_SEARCH_STRING = env('GMAIL_SEARCH_STRING')
GMAIL_BROADER_SEARCH_STRING = env('GMAIL_BROADER_SEARCH_STRING')
MAX_ACCEPT_INVITE_RETRIES = int(env('MAX_ACCEPT_INVITE_RETRIES'))
INVITATION_CODE_BOX_ID = env('INVITATION_CODE_BOX_ID')
INVITATION_CODE_GO_BUTTON_ID = env('INVITATION_CODE_GO_BUTTON_ID')
PERSON_IN_CUSTODY_INFORMATION_DIV_ID = env('PERSON_IN_CUSTODY_INFORMATION_DIV_ID')
INVITATION_ACCEPT_BUTTON_ID = env('INVITATION_ACCEPT_BUTTON_ID')
RECORD_NOT_FOUND_SPAN_ID = env('RECORD_NOT_FOUND_SPAN_ID')
HEADERS_FOR_ACCEPT_INVITE = json.loads(env('HEADERS_FOR_ACCEPT_INVITE'))

API_KEY = env('API_KEY')
TEST_TO_NUMBER = env('TEST_TO_NUMBER')
TEST_MESSAGE_BODY = env('TEST_MESSAGE_BODY')
TEST_KEY = env('TEST_KEY')
TEST_USER_ID = env('TEST_USER_ID')
MAX_SMS_RETRIES = int(env('MAX_SMS_RETRIES'))
SMS_RETRY_DELAY = int(env('SMS_RETRY_DELAY'))
