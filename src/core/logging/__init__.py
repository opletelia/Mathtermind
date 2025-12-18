import logging

from .config import configure_logging, enable_debug_mode, update_log_levels
from .logger import (get_app_logger, get_db_logger, get_module_logger,
                     get_service_logger, get_ui_logger, logger_manager)

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def setup(environment=None):
    """
    Set up the logging system with default configuration.

    Args:
        environment: The application environment (development, testing, production)
    """
    configure_logging(environment)


def get_logger(name):
    """
    Get a logger for a module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        A configured logger instance
    """
    return get_module_logger(name)


def set_level(level, logger_name=None):
    """
    Set the logging level for a logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Name of the logger (None for all loggers)
    """
    if logger_name is None:
        update_log_levels(
            {
                "mathtermind": {"console": level, "file": level},
                "mathtermind.db": {"console": level, "file": level},
                "mathtermind.ui": {"console": level, "file": level},
            }
        )
    else:
        update_log_levels({logger_name: {"console": level, "file": level}})


def debug_mode():
    """Enable debug mode for all loggers."""
    enable_debug_mode()
