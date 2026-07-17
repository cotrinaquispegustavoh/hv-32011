import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

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
    'apps.documents'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates', # Aquí está el base.html global
            
            # Rutas de Clean Architecture para cada app
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        # Usamos el backend de Redis, pero configurado para correr localmente en memoria
        "BACKEND": "channels.layers.InMemoryChannelLayer" 
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es-pe'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'staticfiles']
STATIC_ROOT = BASE_DIR / 'static_root'

# Media files (Uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# --- SEGURIDAD DE SESIONES ---
# Cierra la sesión automáticamente cuando el usuario cierra el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True 

# Tiempo máximo de inactividad (30 minutos = 1800 segundos)
SESSION_COOKIE_AGE = 1800 

# Renueva los 30 minutos cada vez que el usuario hace clic en algo
SESSION_SAVE_EVERY_REQUEST = True