from .base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ROOT_DIR / "db.sqlite3",
    }
}

ALLOWED_HOSTS = ['localhost', '0.0.0.0', '127.0.0.1']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]