import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_SECRET_KEY = '',
DEBUG = True
WEBSERVER_DEBUG = True

CLOUDFRONT_DOMAIN = None
CLOUDFRONT_ID = None
AWS_SECRET_ACCESS_KEY = ""
AWS_ACCESS_KEY_ID = ""
STORAGE_BUCKET_NAME = ''
S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % STORAGE_BUCKET_NAME

GOOGLE_ANALYTICS_TRACKING_ID = ''

EMAIL_HOST = ''
EMAIL_PORT = 26
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_TLS = True
EMAIL_FROM_EMAIL = ''

BROKER_URL = None

INSTAGRAM_USERNAME = ''
INSTAGRAM_PASSWORD = ''
INSTAGRAM_EMAIL = ''

BUFFER_CLIENT_ID = ''
BUFFER_SECRET_ID = ''
BUFFER_ACCESS_TOKEN = ''

DATABASE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


#Used by Discord bot
SQUID_BOT_CLIENT_ID = ""
SQUID_BOT_DEBUG_MODE = "true"
SQUID_BOT_EMAIL_PASSWORD = ""
SQUID_BOT_OWNER_ID = ""
SQUID_BOT_TOKEN = ""


CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'rest_framework',
    'api.apps.ApiConfig',
    'rest_framework_docs',
    'bot',
    'configurations',
    'djcelery',
    'embed_video',
    'jet.dashboard',
    'jet',
    'django.contrib.admin',
    'django_user_agents',
    'django_filters',
    'rest_framework.authtoken',
    'storages',
    'mptt',
    'tagging',
    'zinnia',
    'collectfast',
    'robots',
    'app',
    'sorl.thumbnail',
    'sorl_thumbnail_serializer',
    'ads_txt',
    # 'debug_toolbar',
    'silk',
    'mathfilters',
    'django_tables2',
    'bootstrap4',
    'django_extensions',
    'tz_detect',
]

API_RENDERER = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

GOOGLE_API_KEY = ''