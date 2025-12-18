import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union

DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DETAILED_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
)
SIMPLE_LOG_FORMAT = "%(levelname)-8s | %(message)s"

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "mathtermind.log"


class LoggerManager:
    """
    Manages loggers for the Mathtermind application.

    This class provides methods to create and configure loggers for different
    components with appropriate handlers and formatters.
    """

    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for LoggerManager."""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance

    def __init__(
        self, log_dir: str = DEFAULT_LOG_DIR, log_file: str = DEFAULT_LOG_FILE
    ):
        """
        Initialize the LoggerManager.

        Args:
            log_dir: Directory to store log files
            log_file: Name of the main log file
        """
        if self._initialized:
            return

        self.log_dir = log_dir
        self.log_file = log_file
        self.log_path = os.path.join(log_dir, log_file)

        os.makedirs(log_dir, exist_ok=True)

        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)

        self._initialized = True

    def get_logger(
        self,
        name: str,
        console_level: int = DEFAULT_CONSOLE_LEVEL,
        file_level: int = DEFAULT_FILE_LEVEL,
        console_format: str = DEFAULT_LOG_FORMAT,
        file_format: str = DETAILED_LOG_FORMAT,
        enable_console: bool = True,
        enable_file: bool = True,
        add_component_file: bool = False,
    ) -> logging.Logger:
        """
        Get or create a logger with the specified configuration.

        Args:
            name: Name of the logger, typically the module name
            console_level: Logging level for console output
            file_level: Logging level for file output
            console_format: Format string for console logs
            file_format: Format string for file logs
            enable_console: Whether to enable console logging
            enable_file: Whether to enable file logging
            add_component_file: Whether to create a separate log file for this component

        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(console_level)
            console_formatter = logging.Formatter(console_format)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        if enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_path, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_handler.setLevel(file_level)
            file_formatter = logging.Formatter(file_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        if add_component_file:
            component_log_path = os.path.join(self.log_dir, f"{name}.log")
            component_handler = logging.handlers.RotatingFileHandler(
                component_log_path, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            component_handler.setLevel(file_level)
            component_formatter = logging.Formatter(file_format)
            component_handler.setFormatter(component_formatter)
            logger.addHandler(component_handler)

        self._loggers[name] = logger
        return logger

    def set_global_level(self, level: int) -> None:
        """
        Set the logging level for all loggers.

        Args:
            level: Logging level to set
        """
        for logger in self._loggers.values():
            logger.setLevel(level)

    def add_error_file_handler(self, logger_name: str) -> None:
        """
        Add a handler that writes only ERROR and above messages to an errors log file.

        Args:
            logger_name: Name of the logger to add the handler to
        """
        if logger_name not in self._loggers:
            raise ValueError(f"Logger '{logger_name}' not found")

        logger = self._loggers[logger_name]
        error_log_path = os.path.join(self.log_dir, "errors.log")

        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(DETAILED_LOG_FORMAT)
        error_handler.setFormatter(error_formatter)

        logger.addHandler(error_handler)

    def add_daily_rotating_handler(
        self, logger_name: str, filename: str = None
    ) -> None:
        """
        Add a time-rotating handler that creates a new log file every day.

        Args:
            logger_name: Name of the logger to add the handler to
            filename: Name of the log file, defaults to {logger_name}_daily.log
        """
        if logger_name not in self._loggers:
            raise ValueError(f"Logger '{logger_name}' not found")

        logger = self._loggers[logger_name]
        if filename is None:
            filename = f"{logger_name}_daily.log"

        log_path = os.path.join(self.log_dir, filename)

        handler = logging.handlers.TimedRotatingFileHandler(
            log_path, when="midnight", interval=1, backupCount=30
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
        handler.suffix = "%Y-%m-%d"

        logger.addHandler(handler)


logger_manager = LoggerManager()


def get_app_logger():
    """Get the main application logger."""
    return logger_manager.get_logger("mathtermind")


def get_db_logger():
    """Get the database logger."""
    return logger_manager.get_logger("mathtermind.db", add_component_file=True)


def get_ui_logger():
    """Get the UI logger."""
    return logger_manager.get_logger("mathtermind.ui", add_component_file=True)


def get_service_logger(service_name: str):
    """Get a logger for a specific service."""
    return logger_manager.get_logger(f"mathtermind.services.{service_name}")


def get_module_logger(module_name: str):
    """Get a logger for a specific module."""
    return logger_manager.get_logger(module_name)
