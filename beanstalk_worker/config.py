import logging
import logging.config

LOGLEVEL = 'DEBUG'

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
        }
    ),
    loggers={
        'linter': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        },
        'build-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        },
        'delivery-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        },
        'scan-worker': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        },
        'dispatcher': {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        }
    },
)


def load_logger():
    logging.config.dictConfig(LOGGING_CONF)
