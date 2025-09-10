from .base import *

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# En dev, si quieres API libre:
# CORS_ALLOW_ALL_ORIGINS = True

# DB local por compose (si defines DATABASE_URL en .env, pisa esto)
# DATABASES = {"default": env.db("DATABASE_URL")}
