"""
Django settings for config project.
"""

from pathlib import Path
import os
import django  # 👈 para ubicar los templates nativos de forms

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-=g+wgz+d6t+u60f(ar0$!#o#-$m=(nwcv)!_df5oz^gyuee*e0'
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# -------------------------------------------------------------------
# APPS
# -------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    # "rest_framework",
    # "corsheaders",
    # "storages",
]

LOCAL_APPS = [
    "apps.documentos",
    "apps.usuarios.apps.UsuariosConfig",  # 👈 usa AppConfig (carga signals)
    "apps.empresas",
    "apps.panel",
    "apps.sitio",
    "apps.proveedores",
    "apps.integraciones",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
AUTH_USER_MODEL = "usuarios.Usuario"

# -------------------------------------------------------------------
# AUTHENTICATION & LOGIN
# -------------------------------------------------------------------
LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "panel:dashboard"
LOGOUT_REDIRECT_URL = "usuarios:login"

AUTHENTICATION_BACKENDS = [
    "apps.usuarios.backends.EmailRutOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",  # respaldo
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# -------------------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------------------
# 👇 Hace que los widgets de formularios BUSQUEN también en /templates del proyecto
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
DJANGO_FORMS_TEMPLATES = Path(django.__file__).resolve().parent / "forms" / "templates"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",          # /templates de tu proyecto
            DJANGO_FORMS_TEMPLATES,          # templates nativos de django/forms
        ],
        "APP_DIRS": True,                    # /templates dentro de cada app instalada
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# -------------------------------------------------------------------
# DATABASE
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# (opcional) límites razonables de subida en dev
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# -------------------------------------------------------------------
# DEFAULTS
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# Integraciones (dev)
# -------------------------------------------------------------------
GOOGLE_CLIENT_ID = "823310417562-k5gtt54p653j47tjidrnq3utt7gdjvmr.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:8000/integraciones/google/callback/"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

DROPBOX_APP_KEY = "uz0n2oqo1e2vwcw"
DROPBOX_APP_SECRET = "bywi3h7axhxtwm6"
DROPBOX_REDIRECT_URI = "http://localhost:8000/integraciones/dropbox/callback/"
DROPBOX_SCOPES = ["files.metadata.read", "files.content.read", "files.content.write", "sharing.read", "sharing.write"]

# -------------------------------------------------------------------
# EMAIL (dev)
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "sgidtchile@gmail.com"
EMAIL_HOST_PASSWORD = "nmoofucdchipkwal"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# -------------------------------------------------------------------
# Celery / Redis (dev)
# -------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_TASK_ALWAYS_EAGER = True  # para pruebas locales sin worker
CELERY_TASK_TIME_LIMIT = 60 * 5
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 4
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "1"))
