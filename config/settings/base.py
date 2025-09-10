from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(
    DEBUG=(bool, False),
)

# Carga .env si existe (en servidores puedes no tenerlo y usar envs del sistema)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY", default="unsafe-dev-key")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "whitenoise.runserver_nostatic",
    # "rest_framework",
    # "corsheaders",
]
LOCAL_APPS = [
    "apps.documentos",
    "apps.usuarios",
    "apps.empresas",
    "apps.panel",
    "apps.sitio",
    "apps.proveedores",
    "apps.integraciones",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "usuarios.Usuario"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# DB (cada ambiente lo define con DATABASE_URL; por defecto SQLite)
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Auth
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

# i18n
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# Static & media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise (sirve estáticos en prod)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Límites de subida razonables
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS/CSRF (ajusta por ambiente)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Email (por defecto consola; en prod usar SMTP/SES vía env)
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

# Integraciones (Google/Dropbox) — TODAS por env
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI", default="")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

DROPBOX_APP_KEY = env("DROPBOX_APP_KEY", default="")
DROPBOX_APP_SECRET = env("DROPBOX_APP_SECRET", default="")
DROPBOX_REDIRECT_URI = env("DROPBOX_REDIRECT_URI", default="")
DROPBOX_SCOPES = ["files.metadata.read", "files.content.read", "files.content.write", "sharing.read", "sharing.write"]

# Celery / Redis
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_TIME_LIMIT = 60 * 5
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 4
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=1)
