import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'orbit-dev-only-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','orbit_app']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware']
ROOT_URLCONF = 'orbit.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','orbit_app.context_processors.orbit_context']}}]
WSGI_APPLICATION = 'orbit.wsgi.application'
db_url = os.getenv('DATABASE_URL', '')
if db_url.startswith('postgres'):
    import urllib.parse
    p=urllib.parse.urlparse(db_url); DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':p.path[1:],'USER':p.username,'PASSWORD':p.password,'HOST':p.hostname,'PORT':p.port or 5432}}
else: DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE='fr-fr'; TIME_ZONE=os.getenv('TIME_ZONE','Africa/Casablanca'); USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; STATIC_ROOT=BASE_DIR/'staticfiles'; STATICFILES_DIRS=[BASE_DIR/'static']; MEDIA_ROOT=BASE_DIR/'media'; MEDIA_URL='media/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'; LOGIN_URL='/connexion/'; LOGIN_REDIRECT_URL='/'; LOGOUT_REDIRECT_URL='/connexion/'
EMAIL_BACKEND=os.getenv('EMAIL_BACKEND','django.core.mail.backends.console.EmailBackend'); DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL','noreply@orbit.local')
