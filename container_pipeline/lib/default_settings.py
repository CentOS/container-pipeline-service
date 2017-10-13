"""
This module contains the default config parameters for the container
pipeline service. However, other modules don't consume this module
directly, but container_pipeline.lib.settings.py which extends this module
and provides a layer of abstraction around config loading.
"""
import os

LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'DEBUG'
LOG_PATH = '/srv/pipeline-logs/cccp.log'
SERVICE_LOGFILE = "service_debug_log.txt"

# Django specific configuration
DEBUG = True
TIME_ZONE = 'UTC'
USE_TZ = True
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SECRET_KEY = 'xxxxxxxxxxxxxx'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'container_pipeline',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'container_pipeline.wsgi.application'

STATIC_URL = '/static/'
ROOT_URLCONF = 'container_pipeline.urls'

ALLOWED_HOSTS = ['127.0.0.1']

LOGS_URL_BASE = "https://registry.centos.org/pipeline-logs/"
LOGS_DIR = LOGS_DIR_BASE = "/srv/pipeline-logs/"

LOGGING = dict(
    version=1,
    level=LOG_LEVEL,
    formatters=dict(
        bare={
            "format": ('[%(asctime)s] %(name)s p%(process)s %(lineno)d '
                       '%(levelname)s - %(message)s')
        },
    ),
    handlers=dict(
        console={
            "class": "logging.StreamHandler",
            "formatter": "bare",
            "level": LOG_LEVEL,
        },
        log_to_file={
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
            'mode': 'a+',
            'formatter': 'bare',
        }
    ),
    loggers={
        'dockerfile-linter': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'build-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'test-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'delivery-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'scan-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'dispatcher': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'mail-service': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"],
        },
        'console': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"]

        },
        'tracking': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"]

        },
        'jenkins': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", "log_to_file"]

        },
        'cccp-index-reader': {
            "level": "DEBUG",
            "propogate": False,
            "handlers": ["console", "log_to_file"]
        }
    },
)

BEANSTALKD_HOST = os.environ.get('BEANSTALKD_HOST') or '127.0.0.1'
BEANSTALKD_PORT = int(os.environ.get('BEANSTALKD_PORT') or '11300')
OPENSHIFT_ENDPOINT = os.environ.get('OPENSHIFT_ENDPOINT') or \
    'https://localhost:8443'
OPENSHIFT_USER = os.environ.get('OPENSHIFT_USER') or 'test-admin'
OPENSHIFT_PASSWORD = os.environ.get('OPENSHIFT_PASSWORD') or 'admin'
OC_CONFIG = os.environ.get('OC_CONFIG') or \
    '/opt/cccp-service/client/node.kubeconfig'
OC_CERT = os.environ.get('OC_CERT') or '/opt/cccp-service/client/ca.crt'

SCANNERS_OUTPUT = {
        "registry.centos.org/pipeline-images/pipeline-scanner": [
            "image_scan_results.json"
        ],
        "registry.centos.org/pipeline-images/misc-package-updates": [
            "image_scan_results.json"
        ],
        "registry.centos.org/pipeline-images/scanner-rpm-verify": [
            "RPMVerify.json"
        ],
        "registry.centos.org/pipeline-images/container-capabilities-scanner": [
            "container_capabilities_scanner_results.json"
        ]
}
SCANNERS_RESULTFILE = {
        "registry.centos.org/pipeline-images/pipeline-scanner": [
            "pipeline_scanner_results.json"],
        "registry.centos.org/pipeline-images/misc-package-updates": [
            "misc_package_updates_scanner_results.json"],
        "registry.centos.org/pipeline-images/scanner-rpm-verify": [
            "RPMVerify_scanner_results.json"],
        "registry.centos.org/pipeline-images/container-capabilities-scanner": [
            "container-capabilities-results.json"
        ]

}
SCANNERS_STATUS_FILE = "scanners_status.json"

LINTER_RESULT_FILE = "linter_results.txt"
LINTER_STATUS_FILE = "linter_status.json"

# tracking
REGISTRY_ENDPOINT = ('registry.centos.org', 'https://registry.centos.org')
JENKINS_ENDPOINT = 'http://127.0.0.1:8080/'
JENKINS_USERNAME = ''
JENKINS_PASSWORD = ''
JENKINS_CLI = '/opt/jenkins-cli.jar'
CONTAINER_BUILD_TRIGGER_DELAY = 10
UPSTREAM_PACKAGE_CACHE = os.path.join(BASE_DIR, 'tracking/data')
BEANSTALK_SERVER = 'localhost'

# Build worker
BUILD_RETRY_DELAY = os.environ.get('BUILD_RETRY_DELAY') or 120  # in seconds
