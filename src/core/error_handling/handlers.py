import functools
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from ..logging.logger import get_app_logger, get_module_logger
from .exceptions import (
    AuthenticationError,
    DatabaseError,
    MathtermindError,
    SecurityError,
    ServiceError,
    UIError,
    ValidationError,
)

F = TypeVar("F", bound=Callable[..., Any])


class ErrorHandler:
    """
    Base class for error handlers.

    This class provides common functionality for all error handlers.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.

        Args:
            logger: Logger to use for logging errors
        """
        self.logger = logger or get_app_logger()

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Any:
        """
        Handle an error.

        Args:
            error: The exception to handle
            context: Additional context information about when/where the error occurred

        Returns:
            An appropriate response or raises an exception
        """
        context = context or {}

        if isinstance(error, MathtermindError):
            self.logger.error(
                f"Error occurred: {error}",
                extra={"error_details": error.to_dict(), "context": context},
            )
        else:
            self.logger.error(
                f"Unexpected error occurred: {str(error)}",
                extra={"error_type": type(error).__name__, "context": context},
            )
            self.logger.debug(traceback.format_exc())

        raise error


class ServiceErrorHandler(ErrorHandler):
    """Error handler for service layer errors."""

    def handle_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle a service layer error.

        Args:
            error: The exception to handle
            context: Additional context information

        Returns:
            A dictionary with error information
        """
        context = context or {}
        service_name = context.get("service_name", "unknown_service")

        super().handle_error(error, context)

        if isinstance(error, MathtermindError):
            return error.to_dict()
        else:
            wrapped_error = ServiceError(
                message=f"An unexpected error occurred in service {service_name}: {str(error)}",
                service=service_name,
                details={
                    "original_error": str(error),
                    "error_type": type(error).__name__,
                },
            )
            return wrapped_error.to_dict()


class UIErrorHandler(ErrorHandler):
    """Error handler for UI layer errors."""

    def handle_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle a UI layer error.

        Args:
            error: The exception to handle
            context: Additional context information

        Returns:
            A dictionary with error information suitable for displaying to the user
        """
        context = context or {}
        component = context.get("component", "unknown_component")

        super().handle_error(error, context)

        if isinstance(error, ValidationError):
            return {
                "message": error.message,
                "field_errors": error.details.get("field_errors", {}),
            }
        elif isinstance(error, MathtermindError):
            return {"message": error.message, "error_code": error.error_code}
        else:
            return {
                "message": "An unexpected error occurred. Please try again later.",
                "error_code": "UNKNOWN_ERROR",
            }


class DatabaseErrorHandler(ErrorHandler):
    """Error handler for database layer errors."""

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Handle a database layer error.

        Args:
            error: The exception to handle
            context: Additional context information

        Raises:
            DatabaseError: Always raises a more specific database error
        """
        context = context or {}
        operation = context.get("operation", "unknown_operation")

        self.logger.error(
            f"Database error during {operation}: {str(error)}",
            extra={"error_type": type(error).__name__, "context": context},
        )
        self.logger.debug(traceback.format_exc())

        if not isinstance(error, DatabaseError):
            raise DatabaseError(
                message=f"Database error during {operation}: {str(error)}",
                details={"original_error": str(error), "operation": operation},
            ) from error

        raise


class SecurityErrorHandler(ErrorHandler):
    """Error handler for security-related errors."""

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Handle a security-related error.

        Args:
            error: The exception to handle
            context: Additional context information

        Raises:
            SecurityError or AuthenticationError: Always raises a more specific security error
        """
        context = context or {}
        operation = context.get("operation", "unknown_operation")

        self.logger.error(
            f"Security error during {operation}: {str(error)}",
            extra={"error_type": type(error).__name__, "context": context},
        )
        self.logger.debug(traceback.format_exc())

        if isinstance(error, (SecurityError, AuthenticationError)):
            raise

        raise SecurityError(
            message=f"Security error during {operation}: {str(error)}",
            operation=operation,
            details={"original_error": str(error)},
        ) from error


def handle_service_errors(
    service_name: Optional[str] = None,
    error_map: Optional[Dict[Type[Exception], Callable[[Exception], Any]]] = None,
):
    """
    Decorator to handle service layer errors.

    Args:
        service_name: Name of the service (used for logging)
        error_map: Mapping from exception types to handler functions

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_name = f"mathtermind.services.{service_name or func.__module__}"
            logger = get_module_logger(logger_name)

            error_handler = ServiceErrorHandler(logger)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_map:
                    for exception_type, handler in error_map.items():
                        if isinstance(e, exception_type):
                            return handler(e)

                return error_handler.handle_error(
                    e,
                    {
                        "service_name": service_name or func.__module__,
                        "function": func.__name__,
                    },
                )

        return wrapper

    return decorator


def handle_ui_errors(component: Optional[str] = None, show_error_dialog: bool = True):
    """
    Decorator to handle UI layer errors.

    Args:
        component: Name of the UI component (used for logging)
        show_error_dialog: Whether to show an error dialog to the user

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_name = f"mathtermind.ui.{component or func.__module__}"
            logger = get_module_logger(logger_name)

            error_handler = UIErrorHandler(logger)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = error_handler.handle_error(
                    e,
                    {
                        "component": component or func.__module__,
                        "function": func.__name__,
                    },
                )

                if show_error_dialog:
                    try:
                        from PyQt5.QtWidgets import QMessageBox

                        QMessageBox.critical(
                            None,
                            "Error",
                            error_info.get("message", "An unexpected error occurred."),
                        )
                    except ImportError:
                        logger.warning(
                            "Could not show error dialog: PyQt5 not available"
                        )

                return None

        return wrapper

    return decorator


def handle_db_errors(
    operation: Optional[str] = None, retry_count: int = 0, retry_delay: float = 1.0
):
    """
    Decorator to handle database layer errors.

    Args:
        operation: Description of the database operation (used for logging)
        retry_count: Number of times to retry the operation on failure
        retry_delay: Delay in seconds between retries

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_module_logger("mathtermind.db")
            error_handler = DatabaseErrorHandler(logger)

            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retry_count:
                        error_handler.handle_error(
                            e,
                            {
                                "operation": operation or func.__name__,
                                "function": func.__name__,
                            },
                        )

                    logger.warning(
                        f"Database operation failed, retrying ({attempt+1}/{retry_count+1}): {str(e)}"
                    )

                    if attempt < retry_count:
                        import time

                        time.sleep(retry_delay)

        return wrapper

    return decorator


def handle_security_errors(
    operation: Optional[str] = None, service_name: Optional[str] = None
):
    """
    Decorator to handle security-related errors.

    Args:
        operation: Name of the security operation (used for logging)
        service_name: Name of the service (used for logging)

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_name = f"mathtermind.security.{service_name or func.__module__}"
            logger = get_module_logger(logger_name)

            error_handler = SecurityErrorHandler(logger)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e,
                    {
                        "operation": operation or func.__name__,
                        "service_name": service_name,
                    },
                )

        return wrapper

    return decorator


def with_error_boundary(name: str, fallback_value: Any = None):
    """
    Create an error boundary around a function.

    Similar to React's error boundaries, this prevents errors in one component
    from crashing the entire application.

    Args:
        name: Name of the boundary (used for logging)
        fallback_value: Value to return if an error occurs

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_app_logger()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in boundary '{name}': {str(e)}",
                    extra={"error_type": type(e).__name__, "boundary": name},
                )
                logger.debug(traceback.format_exc())

                return fallback_value

        return wrapper

    return decorator
