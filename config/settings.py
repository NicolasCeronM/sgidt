# =====================================================================
# IMPORTS Y BASE
# =====================================================================
from pathlib import Path
import os
from datetime import timedelta
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================
# CONFIGURACIÓN GENERAL
# =====================================================================
DEBUG = True
SECRET_KEY = 'django-insecure-=g+wgz+d6t+u60f(ar0$!#o#-$m=(nwcv)!_df5oz^gyuee*e0'
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.18.119", "sgidt.onrender.com"]

# Confianza CSRF (dominios desde donde se permiten POST)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:53376",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# =====================================================================
# APPS
# =====================================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.documentos",
    "apps.usuarios",
    "apps.empresas",
    "apps.panel",
    "apps.sitio",
    "apps.proveedores",
    "apps.integraciones",
    "apps.sii",
    "apps.correo",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "usuarios.Usuario"

# =====================================================================
# AUTENTICACIÓN
# =====================================================================
LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "panel:dashboard"
LOGOUT_REDIRECT_URL = "usuarios:login"

AUTHENTICATION_BACKENDS = [
    "apps.usuarios.backends.EmailRutOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================================
# MIDDLEWARE
# =====================================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.usuarios.middleware.ActiveSessionMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# =====================================================================
# REST FRAMEWORK / JWT
# =====================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "50/hour",
        "user": "200/hour",
        "login": "10/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =====================================================================
# CORS
# =====================================================================
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]

# Métodos y headers comunes (incluye Authorization para Bearer)
from corsheaders.defaults import default_headers, default_methods

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]

CORS_ALLOW_METHODS = list(default_methods)  # GET, POST, PUT, PATCH, DELETE, OPTIONS
CORS_ALLOW_CREDENTIALS = False  # Para JWT normalmente no se requieren cookies
# =====================================================================
# TEMPLATES
# =====================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'apps.documentos.context_processors.alertas_counter',
            ],
        },
    },
]

# =====================================================================
# BASE DE DATOS
# =====================================================================
DATABASES = {
   "default": {
       "ENGINE": "django.db.backends.postgresql",
       "NAME": "sgidt",
       "USER": "sgidt_user",
       "PASSWORD": "admin123",
       "HOST": "db",
       "PORT": "5432",
   }
}

# =====================================================================
# INTERNACIONALIZACIÓN
# =====================================================================
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# =====================================================================
# STATIC & MEDIA
# =====================================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# =====================================================================
# DEFAULT FIELD
# =====================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================================
# INTEGRACIONES EXTERNAS
# =====================================================================
# --- Google OAuth ---
GOOGLE_CLIENT_ID = "823310417562-k5gtt54p653j47tjidrnq3utt7gdjvmr.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:8000/integraciones/google/callback/"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# --- Dropbox OAuth ---
DROPBOX_APP_KEY = "uz0n2oqo1e2vwcw"
DROPBOX_APP_SECRET = "bywi3h7axhxtwm6"
DROPBOX_REDIRECT_URI = "http://localhost:8000/integraciones/dropbox/callback/"
DROPBOX_SCOPES = ["files.metadata.read", "files.content.read", "files.content.write", "sharing.read", "sharing.write"]

# =====================================================================
# EMAIL
# =====================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "sgidtchile@gmail.com"
EMAIL_HOST_PASSWORD = "nmoofucdchipkwal"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================================
# CELERY / REDIS
# =====================================================================
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"

# En modo desarrollo: True (ejecuta las tareas sin worker)
CELERY_TASK_ALWAYS_EAGER = False

# Límites y concurrencia
CELERY_TASK_TIME_LIMIT = 60 * 5
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 4
CELERY_WORKER_CONCURRENCY = 1

# Tareas periódicas


# =====================================================================
# CONFIGURACIÓN SII
# =====================================================================
SII_USE_MOCK = True        # En desarrollo
SII_TIMEOUT = 15
SII_BASE_URL = "https://api.sii.cl"   # placeholder para el real

# =====================================================================
# Chatbot AI
# =====================================================================