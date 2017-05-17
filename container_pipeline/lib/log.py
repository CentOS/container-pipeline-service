import logging.config

from container_pipeline.lib.settings import LOGGING_CONF


def load_logger():
    """
    This loads logging config
    """
    logging.config.dictConfig(LOGGING_CONF)
