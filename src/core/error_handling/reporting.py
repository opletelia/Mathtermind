import json
import os
import platform
import socket
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging.logger import get_app_logger
from .exceptions import MathtermindError


class ErrorContext:
    """
    Captures and stores the context of an error.

    This class collects information about the environment, system state,
    and other relevant data when an error occurs.
    """

    def __init__(
        self, error: Exception, additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error context.

        Args:
            error: The exception that occurred
            additional_data: Additional data to include in the context
        """
        self.timestamp = datetime.now().isoformat()
        self.error = error
        self.error_type = type(error).__name__
        self.error_message = str(error)
        self.traceback = traceback.format_exc()
        self.additional_data = additional_data or {}

        self.system_info = self._collect_system_info()

        self.app_state = self.additional_data.get("app_state", {})

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect information about the system."""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "user": os.environ.get("USER", "unknown"),
            "executable": sys.executable,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error context to a dictionary."""
        result = {
            "timestamp": self.timestamp,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "traceback": self.traceback,
            "system_info": self.system_info,
        }

        if isinstance(self.error, MathtermindError):
            result["error_details"] = self.error.to_dict()

        if self.additional_data:
            result["additional_data"] = self.additional_data

        if self.app_state:
            result["app_state"] = self.app_state

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert the error context to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ErrorReporter:
    """
    Reports errors to appropriate destinations.

    This class handles reporting errors to the logging system and optionally
    to external error tracking services.
    """

    def __init__(self):
        """Initialize the error reporter."""
        self.logger = get_app_logger()
        self.error_log_path = os.path.join("logs", "error_reports")
        os.makedirs(self.error_log_path, exist_ok=True)

    def report(
        self, error: Exception, additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Report an error.

        Args:
            error: The exception to report
            additional_data: Additional data to include in the report
        """
        context = ErrorContext(error, additional_data)

        self.logger.error(
            f"Error report: {context.error_type} - {context.error_message}",
            extra={"error_context": context.to_dict()},
        )

        self._save_error_report(context)

    def _save_error_report(self, context: ErrorContext) -> None:
        """
        Save the error report to a file.

        Args:
            context: The error context to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"error_{timestamp}_{context.error_type}.json"
        file_path = os.path.join(self.error_log_path, filename)

        try:
            with open(file_path, "w") as f:
                f.write(context.to_json())
            self.logger.debug(f"Error report saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save error report: {str(e)}")


error_reporter = ErrorReporter()


def report_error(error: Exception, **kwargs) -> None:
    """
    Report an error with additional context data.

    Args:
        error: The exception to report
        **kwargs: Additional data to include in the report
    """
    error_reporter.report(error, kwargs)


class ErrorReportingContext:
    """
    Context manager for error reporting.

    This context manager captures and reports any exceptions that occur
    within its context.
    """

    def __init__(
        self, context_name: str, additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error reporting context.

        Args:
            context_name: Name of the context (used for reporting)
            additional_data: Additional data to include in error reports
        """
        self.context_name = context_name
        self.additional_data = additional_data or {}
        self.additional_data["context_name"] = context_name

    def __enter__(self):
        """Enter the context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context and report any errors.

        Args:
            exc_type: Type of the exception (if any)
            exc_val: The exception instance (if any)
            exc_tb: The traceback (if any)

        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_val:
            report_error(exc_val, **self.additional_data)

            logger = get_app_logger()
            logger.info(f"Caught and reported error in context '{self.context_name}'")

            return False

        return True
