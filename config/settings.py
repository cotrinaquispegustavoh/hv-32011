import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False) # Por defecto en producción será False
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Dominios permitidos
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Intranet HV - Local Apps
    'apps.core',
    'apps.users',
    'apps.academics',
    'apps.warehouse',
    'apps.discipline',
    'apps.portfolio',
    'apps.assignments',
    'apps.documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'apps.users.interfaces.middlewares.ForcePasswordChangeMiddleware',
    'apps.users.interfaces.middlewares.RoleGuardMiddleware',
    'apps.users.interfaces.middlewares.NoCacheAuthenticatedMiddleware',
    'apps.core.interfaces.middlewares.CurrentUserMiddleware',
    'apps.users.interfaces.middlewares.HtmxLoginRedirectMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'apps' / 'users' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'core' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'academics' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'warehouse' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'discipline' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'portfolio' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'assignments' / 'interfaces' / 'templates',
            BASE_DIR / 'apps' / 'documents' / 'interfaces' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.notifications_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# --- CONFIGURACIÓN DE WEBSOCKETS ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer" 
    },
}

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS Y MULTIMEDIA ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

# --- SEGURIDAD DE SESIONES ---
SESSION_EXPIRE_AT_BROWSER_CLOSE = True 
SESSION_COOKIE_AGE = 1800 
SESSION_SAVE_EVERY_REQUEST = True

# --- SEGURIDAD EN PRODUCCIÓN (HTTPS) ---
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False
    
    # CORRECCIÓN: Le decimos a Django que confíe en el dominio de Render para los formularios
    CSRF_TRUSTED_ORIGINS = ['https://intranet-hv.onrender.com']