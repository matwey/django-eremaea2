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
	'inmemorystorage',
	'eremaea',
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
DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'
MEDIA_URL = 'http://media.example.com/'
# STATIC_URL is required for LiveServerTestCase
STATIC_URL = 'http://static.example.com/'
MIDDLEWARE_CLASSES = []
ROOT_URLCONF = 'tests.urls'
TIME_ZONE = 'UTC'
