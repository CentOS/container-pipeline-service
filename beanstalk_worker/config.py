import logging
import logging.config
import os

LOG_LEVEL = 'DEBUG'

LOG_PATH = '/srv/pipeline-logs/cccp.log'

LOGGING_CONF = dict(
    version=1,
    level=LOG_LEVEL,
    formatters=dict(
        bare={
            "format": '[%(asctime)s] %(name)s p%(process)s %(lineno)d %(levelname)s - %(message)s'
        },
    ),
    handlers=dict(
        console={
            "class": "logging.StreamHandler",
            "formatter": "bare",
            "level": LOG_LEVEL,
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


class DynamicFileHandler:

    def __init__(self, logger, log_path, level='DEBUG'):
        """Initialize dynamic file handler"""
        self.logger = logger
        self.h = logging.FileHandler(log_path)
        self.h.setLevel(getattr(logging, level))
        self.h.setFormatter(LOGGING_CONF['formatters']['base']['formatter'])
        self.logger.addHandler(self.h)

    def remove(self):
        """Remove handler from logger"""
        self.logger.removeHandler(self.h)

    def clean(self):
        """Clean associated log file"""
        try:
            os.remove(self.h.baseFilename)
        except OSError as e:
            self.logger.error('Error during cleaning log file: %s' % e)
