"""
Base settings to build other settings files upon.
"""

import logging
from pathlib import Path
from pythonjsonlogger import jsonlogger
from datetime import datetime
import environ
import sentry_sdk

# webook/
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "webook"

env = environ.Env()

ENV_FILE = BASE_DIR / ".env"
if Path(ENV_FILE).exists():
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ENV_FILE))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", "English"),
    ("nb-NO", "Norwegian"),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{str(BASE_DIR / 'webook.db')}",
    )
}


# sentry_sdk.init(
#     dsn=env.str("SENTRY_DSN", default=None),
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for tracing.
#     traces_sample_rate=1.0,
#     # Set profiles_sample_rate to 1.0 to profile 100%
#     # of sampled transactions.
#     # We recommend adjusting this value in production.
#     profiles_sample_rate=1.0,
# )

if env.str("DATABASE_HOST", default=None):
    DATABASES["default"]["HOST"] = env.str("DATABASE_HOST")
if env.str("DATABASE_ENGINE", default=None):
    DATABASES["default"]["ENGINE"] = env.str("DATABASE_ENGINE")
if env.str("DATABASE_NAME", default=None):
    DATABASES["default"]["NAME"] = env.str("DATABASE_NAME")
if env.str("DATABASE_USER", default=None):
    DATABASES["default"]["USER"] = env.str("DATABASE_USER")
if env.str("DATABASE_PASSWORD", default=None):
    DATABASES["default"]["PASSWORD"] = env.str("DATABASE_PASSWORD")
if env.str("DATABASE_PORT", default=None):
    DATABASES["default"]["PORT"] = env.str("DATABASE_PORT")

DATABASES["default"]["ATOMIC_REQUESTS"] = True

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
    "colorfield",
    "django_celery_results",
    "django_celery_beat",
    "haystack",
]

LOCAL_APPS = [
    "webook.users.apps.UsersConfig",
    # Your stuff: custom apps go here
    "webook.arrangement.apps.ArrangementConfig",
    "webook.crumbinator.apps.CrumbinatorConfig",
    "webook.screenshow.apps.ScreenshowConfig",
    "webook.api.apps.ApiConfig",
    "webook.onlinebooking.apps.OnlinebookingConfig",
    "webook.graph_integration.apps.GraphIntegrationConfig",
    "webook.celery_haystack.apps.CeleryHaystackConfig",
    "webook.tasks.apps.TaskConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "webook.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# To comply with AllAuth
USER_MODEL_USERNAME_FIELD = "email"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "users:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"


# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "webook.middleware.timezone_middleware.TimezoneMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "npm.finders.NpmFinder",
]

if env("USE_GCS_STATIC", default=False) and env("GS_BUCKET_NAME", default=None):
    GS_QUERYSTRING_AUTH = env.bool("GS_QUERYSTRING_AUTH", default=False)
    GS_STATIC_BUCKET_NAME = env("GS_STATIC_BUCKET_NAME", default=None)
    GS_UPLOADS_BUCKET_NAME = env("GS_UPLOADS_BUCKET_NAME", default=None)
    STATIC_URL = env("/static/", default="/static/")
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GS_UPLOADS_BUCKET_NAME,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GS_STATIC_BUCKET_NAME,
            }
        },
    }

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "webook.utils.context_processors.settings_context",
            ],
        },
    }
]

TEMPLATE_DIRS = (
    BASE_DIR / "templates",  # app-shared project templates (is this anti-pattern?)
    APPS_DIR / "onlinebooking/templates",  # app-specific templates
    APPS_DIR / "celery_haystack/templates",  # app-specific templates
)

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

CSRT_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost"])

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/2.2/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="webook@webook.no")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

USE_REDIS = env.bool("USE_REDIS", default=False)

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379")

# CACHING
if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL", default="redis://localhost:6379"),
            "KEY_PREFIX": env("REDIS_KEY_PREFIX", default="webook"),
        }
    }

    # UpdateCacheMiddleware should be first in the list
    # FetchFromCacheMiddleware should be last in the list
    # MIDDLEWARE.insert(0, "django.middleware.cache.UpdateCacheMiddleware")
    # MIDDLEWARE.append("django.middleware.cache.FetchFromCacheMiddleware")
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "",
        }
    }

CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
RESULT_BACKEND = env("RESULT_BACKEND", default="django-db")
# CELERY_CACHE_BACKEND = env("CELERY_CACHE_BACKEND", default="default")

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("Magnus", "magnus@wemade")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["component"] = getattr(record, "component", "unknown")
        log_record["service"] = getattr(record, "service", APP_TITLE)
        log_record["request_id"] = getattr(record, "request_id", None)
        log_record["trace_id"] = getattr(record, "trace_id", None)
        log_record["user_id"] = getattr(record, "user_id", None)
        log_record["timestamp"] = datetime.now().isoformat()
        log_record["environment"] = "development" if DEBUG else "production"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "[%(levelname)s] [%(module)s] %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

if env("LOG_TO_FILE", default=False):
    LOGGING["root"]["handlers"].append("file")
    LOGGING["handlers"]["file"] = {
        "level": "INFO",
        "class": "logging.FileHandler",
        "filename": env("LOG_FILE", default="webook.log"),
        "formatter": "json",
    }
    LOGGING["formatters"]["json"] = {
        "()": CustomJsonFormatter,
        "format": "%(timestamp)s %(levelname)s %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S.%fZ",
    }


# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", False)
ALLOW_SSO = env.bool("ALLOW_SSO", False)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "email"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = env.str("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "webook.users.adapters.AccountAdapter"
ACCOUNT_FORMS = {"signup": "webook.users.forms.UserCreationForm"}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "webook.users.adapters.MicrosoftPersonAccountAdapter"

SOCIALACCOUNT_EMAIL_VERIFICATION = False

SOCIALACCOUNT_PROVIDERS = {}
if ALLOW_SSO:
    SOCIALACCOUNT_PROVIDERS["microsoft"] = {
        "tenant": env("MICROSOFT_TENANT", default="common"),
        "APP": {
            "name": env("MICROSOFT_SOCIAL_NAME", default="WeBook"),
            "client_id": env("MICROSOFT_CLIENT_ID"),
            "secret": env("MICROSOFT_CLIENT_SECRET"),
            "sites": env("MICROSOFT_CLIENT_SITES"),
            "adapter": "webook.users.adapters.MicrosoftPersonAccountAdapter",
        },
    }

ALLOW_EMAIL_LOGIN = env("ALLOW_EMAIL_LOGIN", default=True)

# Your stuff...
# ------------------------------------------------------------------------------
APP_LOGO = env("APP_LOGO", default="static/images/wemade_logo.jpg")

APP_TITLE = env("APP_TITLE", default="WeBook")

# Remember to override this with a valid key if project is commercial.
FULLCALENDAR_LICENSE_KEY = env(
    "FULLCALENDAR_LICENSE_KEY", default="CC-Attribution-NonCommercial-NoDerivatives"
)

ASSET_SERVER_URL = env("ASSET_SERVER_URL", default="localhost/static")

# The default timezone that will be assigned to new users
USER_DEFAULT_TIMEZONE = env(
    "USER_DEFAULT_TIMEZONE",
    default=TIME_ZONE,
)
# HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

DISPLAY_SSO_ERROR_REASONING = env("DISPLAY_SSO_ERROR_REASONING", default=False)

JWT_TOKEN_LIFETIME_MINUTES = env("JWT_TOKEN_LIFETIME_MINUTES", default=20)

PDF_TMP_DIR = env("PDF_TMP_DIR", default="./webook/media/tmpfiles/")

URL_TO_ONLINE_BOOKING_APP = env(
    "URL_TO_ONLINE_BOOKING_APP", default="http://localhost:5000"
)

# if env("ELASTICSEARCH_URL", default=None):
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": env("ELASTICSEARCH_URL", default="http://localhost:9200/"),
        "INDEX_NAME": "haystack",
    }
}
HAYSTACK_SIGNAL_PROCESSOR = (
    "webook.celery_haystack.queued_signal_processor.QueuedSignalProcessor"
)

TASK_BACKEND = env(
    "TASK_BACKEND",
    default="local",
)

AZURE_TENANT_ID = env("AZURE_TENANT_ID", default=None)
AZURE_CLIENT_ID = env("AZURE_CLIENT_ID", default=None)
AZURE_CLIENT_SECRET = env("AZURE_CLIENT_SECRET", default=None)

# Alert shown to super users in header
ALERT_TEXT_SUPER_USER = env("ALERT_TEXT_SUPER_USER", default=None)

# Alert shown to all users in header
ALERT_TEXT_ALL_USERS = env("ALERT_TEXT_ALL_USERS", default=None)

ADMIN_ENABLED = env("ADMIN_ENABLED", default=False)
APP_BASE_URL = env("APP_BASE_URL", default="http://localhost:8000")

GOOGLE_PROJECT_ID = env("GOOGLE_PROJECT_ID", default=None)
GOOGLE_CLOUD_TASK_QUEUE_NAME = env(
    "GOOGLE_CLOUD_TASK_QUEUE_NAME", default="webook-queue"
)
GOOGLE_PROJECT_LOCATION = env("GOOGLE_PROJECT_LOCATION", default="europe-west1")
