"""
Django settings for container_pipeline project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'p$q(l91m+24-swq&#!x0qa$8!oumsw7(()e#klgz7rpspel+qh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'tracking',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'container_pipeline.urls'

WSGI_APPLICATION = 'container_pipeline.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'DEBUG'
LOG_PATH = os.environ.get('LOG_PATH') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'cccp_file': {
            'format': '[%(asctime)s %(name)s %(levelname)s] %(message)s',
        },
        'cccp_stream': {
            'format': '[%(asctime)s %(name)s %(levelname)s] %(message)s',
        },
    },
    'handlers': {
        'log_to_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_PATH, 'cccp.log'),
            'mode': 'a+',
            'formatter': 'cccp_file',
        },
        'log_to_stream': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'cccp_stream',
        },
    },
    'loggers': {
        'cccp': {
            'handlers': ['log_to_file', 'log_to_stream', ],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'tracking': {
            'handlers': ['log_to_file', 'log_to_stream', ],
            'level': LOG_LEVEL,
            'propagate': False,
        }
    },
}

# tracking
REGISTRY_ENDPOINT = ('registry.centos.org', 'https://registry.centos.org')
JENKINS_ENDPOINT = 'http://127.0.0.1:8080/'
JENKINS_USERNAME = ''
JENKINS_PASSWORD = ''
JENKINS_CLI = '/opt/jenkins-cli.jar'
CONTAINER_BUILD_TRIGGER_DELAY = 10
UPSTREAM_PACKAGE_CACHE = os.path.join(BASE_DIR, 'tracking/data')
