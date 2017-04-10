import logging
import logging.config

LOGLEVEL = 'DEBUG'

LOG_PATH = '/srv/pipeline-logs/cccp.log'

LOGGING_CONF = dict(
    version=1,
    level=LOGLEVEL,
    formatters=dict(
        bare={
            "format": '[%(asctime)s %(name)s %(levelname)s] %(message)s'
        },
    ),
    handlers=dict(
        console={
            "class": "logging.StreamHandler",
            "formatter": "bare",
            "level": LOGLEVEL,
        },
        log_to_file={
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
            'mode': 'a+',
            'formatter': 'bare',
        }
    ),
    loggers={
        'linter': {
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
        }
    },
)


def load_logger():
    logging.config.dictConfig(LOGGING_CONF)
