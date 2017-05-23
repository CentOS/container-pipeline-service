import logging.config
import os

from container_pipeline.lib.settings import LOGGING_CONF


def load_logger():
    """
    This loads logging config
    """
    logging.config.dictConfig(LOGGING_CONF)


class DynamicFileHandler:
    """
    This creates dynamic logging file handlers to store debug logs
    for a project's build in container index
    """

    def __init__(self, logger, log_path, level='DEBUG'):
        """Initialize dynamic file handler"""
        self.logger = logger
        self.h = logging.FileHandler(log_path)
        self.h.setLevel(getattr(logging, level))
        self.h.setFormatter(
            logging.Formatter(LOGGING_CONF['formatters']['bare']['format']))
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
