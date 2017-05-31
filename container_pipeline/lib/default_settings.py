"""
This module contains the default config parameters for the container
pipeline service. However, other modules don't consume this module
directly, but container_pipeline.lib.settings.py which extends this module
and provides a layer of abstraction around config loading.
"""
import os

LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'DEBUG'

LOG_PATH = '/srv/pipeline-logs/cccp.log'
SERVICE_LOGFILE = "service_debug.log"

LOGGING_CONF = dict(
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
