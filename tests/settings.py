import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True
SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
	'django.contrib.contenttypes',
	'django.contrib.auth',
	'rest_framework',
	'rest_framework.authtoken',
	'drf_spectacular',
	'django_filters',
	'eremaea',
]

MIDDLEWARE = [
	'django.middleware.http.ConditionalGetMiddleware',
]

TEMPLATES = [{
	'BACKEND': 'django.template.backends.django.DjangoTemplates',
	'APP_DIRS': True,
	'OPTIONS': {'debug': True,},
	},
]

REST_FRAMEWORK = {
	'DEFAULT_RENDERER_CLASSES': (
		'rest_framework.renderers.JSONRenderer',
	),
	'DEFAULT_PARSER_CLASSES': (
		'rest_framework.parsers.JSONParser',
	),
	'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': 'test.sqlite3',
	}
}
FILE_UPLOAD_HANDLERS = [
	'django.core.files.uploadhandler.MemoryFileUploadHandler',
	'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
STORAGES = {
	'default': {
		'BACKEND': 'django.core.files.storage.InMemoryStorage'
	},
}
MEDIA_URL = 'http://media.example.com/'
# STATIC_URL is required for LiveServerTestCase
STATIC_URL = 'http://static.example.com/'
MIDDLEWARE_CLASSES = []
ROOT_URLCONF = 'tests.urls'
TIME_ZONE = 'UTC'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
