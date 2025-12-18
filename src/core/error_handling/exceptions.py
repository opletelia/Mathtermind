from typing import Any, Dict, List, Optional


class MathtermindError(Exception):
    """Base exception class for all Mathtermind exceptions."""

    def __init__(
        self,
        message: str = "An error occurred in Mathtermind",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        error_str = self.message
        if self.error_code:
            error_str = f"[{self.error_code}] {error_str}"
        if self.details:
            error_str = f"{error_str} - Details: {self.details}"
        return error_str

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary representation."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class DatabaseError(MathtermindError):
    """Base exception for database-related errors."""

    def __init__(self, message: str = "A database error occurred", **kwargs):
        if "error_code" not in kwargs:
            kwargs["error_code"] = "DB_ERROR"
        super().__init__(message, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Exception raised when a database connection cannot be established."""

    def __init__(self, message: str = "Could not connect to the database", **kwargs):
        kwargs["error_code"] = "DB_CONNECTION_ERROR"
        super().__init__(message, **kwargs)


class QueryError(DatabaseError):
    """Exception raised when a database query fails."""

    def __init__(
        self,
        message: str = "Database query failed",
        query: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if query:
            details["query"] = query
        kwargs["details"] = details
        kwargs["error_code"] = "DB_QUERY_ERROR"
        super().__init__(message, **kwargs)


class MigrationError(DatabaseError):
    """Exception raised when a database migration fails."""

    def __init__(self, message: str = "Database migration failed", **kwargs):
        kwargs["error_code"] = "DB_MIGRATION_ERROR"
        super().__init__(message, **kwargs)


class AuthenticationError(MathtermindError):
    """Base exception for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        if "error_code" not in kwargs:
            kwargs["error_code"] = "AUTH_ERROR"
        super().__init__(message, **kwargs)


class LoginError(AuthenticationError):
    """Exception raised when a login attempt fails."""

    def __init__(self, message: str = "Login failed", **kwargs):
        kwargs["error_code"] = "AUTH_LOGIN_ERROR"
        super().__init__(message, **kwargs)


class PermissionError(AuthenticationError):
    """Exception raised when a user doesn't have permission for an action."""

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        kwargs["details"] = details
        kwargs["error_code"] = "AUTH_PERMISSION_ERROR"
        super().__init__(message, **kwargs)


class AuthorizationError(AuthenticationError):
    """Exception raised when there's an error with role-based authorization."""

    def __init__(
        self,
        message: str = "Authorization failed",
        role: Optional[str] = None,
        permission: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if role:
            details["role"] = role
        if permission:
            details["permission"] = permission
        kwargs["details"] = details
        kwargs["error_code"] = "AUTH_AUTHORIZATION_ERROR"
        super().__init__(message, **kwargs)


class TokenError(AuthenticationError):
    """Exception raised when there's an issue with an authentication token."""

    def __init__(self, message: str = "Invalid or expired token", **kwargs):
        kwargs["error_code"] = "AUTH_TOKEN_ERROR"
        super().__init__(message, **kwargs)


# Service Exceptions
class ServiceError(MathtermindError):
    """Base exception for service-related errors."""

    def __init__(
        self,
        message: str = "Service operation failed",
        service: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if service:
            details["service"] = service
        kwargs["details"] = details
        if "error_code" not in kwargs:
            kwargs["error_code"] = "SERVICE_ERROR"
        super().__init__(message, **kwargs)


class ValidationError(ServiceError):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if field_errors:
            details["field_errors"] = field_errors
        kwargs["details"] = details
        kwargs["error_code"] = "VALIDATION_ERROR"
        super().__init__(message, **kwargs)


class ResourceNotFoundError(ServiceError):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        kwargs["details"] = details
        kwargs["error_code"] = "RESOURCE_NOT_FOUND"
        super().__init__(message, **kwargs)


class DependencyError(ServiceError):
    """Exception raised when a service dependency is missing or invalid."""

    def __init__(
        self,
        message: str = "Service dependency error",
        dependency: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if dependency:
            details["dependency"] = dependency
        kwargs["details"] = details
        kwargs["error_code"] = "DEPENDENCY_ERROR"
        super().__init__(message, **kwargs)


class BusinessLogicError(ServiceError):
    """Exception raised when a business logic rule or constraint is violated."""

    def __init__(
        self,
        message: str = "Business logic constraint violated",
        constraint: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if constraint:
            details["constraint"] = constraint
        kwargs["details"] = details
        kwargs["error_code"] = "BUSINESS_LOGIC_ERROR"
        super().__init__(message, **kwargs)


class UIError(MathtermindError):
    """Base exception for UI-related errors."""

    def __init__(self, message: str = "UI operation failed", **kwargs):
        super().__init__(message, error_code="UI_ERROR", **kwargs)


class RenderError(UIError):
    """Exception raised when UI rendering fails."""

    def __init__(
        self,
        message: str = "Failed to render UI component",
        component: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if component:
            details["component"] = component
        kwargs["details"] = details
        super().__init__(message, error_code="UI_RENDER_ERROR", **kwargs)


class InputError(UIError):
    """Exception raised when there's an error with user input."""

    def __init__(
        self, message: str = "Invalid user input", field: Optional[str] = None, **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        kwargs["details"] = details
        super().__init__(message, error_code="UI_INPUT_ERROR", **kwargs)


class FileSystemError(MathtermindError):
    """Base exception for file system-related errors."""

    def __init__(
        self,
        message: str = "File system operation failed",
        file_path: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if file_path:
            details["file_path"] = file_path
        kwargs["details"] = details
        super().__init__(message, error_code="FS_ERROR", **kwargs)


class FileNotFoundError(FileSystemError):
    """Exception raised when a file is not found."""

    def __init__(self, message: str = "File not found", **kwargs):
        super().__init__(message, error_code="FS_FILE_NOT_FOUND", **kwargs)


class AccessDeniedError(FileSystemError):
    """Exception raised when access to a file is denied."""

    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="FS_ACCESS_DENIED", **kwargs)


class ConfigurationError(MathtermindError):
    """Exception raised when there's an error in the application configuration."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        kwargs["details"] = details
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class ContentError(MathtermindError):
    """Base exception for content-related errors."""

    def __init__(
        self,
        message: str = "Content error",
        content_id: Optional[str] = None,
        content_type: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if content_id:
            details["content_id"] = content_id
        if content_type:
            details["content_type"] = content_type
        kwargs["details"] = details
        error_code = kwargs.pop("error_code", "CONTENT_ERROR")
        super().__init__(message, error_code=error_code, **kwargs)


class ContentNotFoundError(ContentError):
    """Exception raised when requested content is not found."""

    def __init__(self, message: str = "Content not found", **kwargs):
        super().__init__(message, error_code="CONTENT_NOT_FOUND", **kwargs)


class ContentFormatError(ContentError):
    """Exception raised when content has an invalid format."""

    def __init__(self, message: str = "Invalid content format", **kwargs):
        super().__init__(message, error_code="CONTENT_FORMAT_ERROR", **kwargs)


class ContentValidationError(ContentError):
    """Exception raised when content validation fails."""

    def __init__(
        self,
        message: str = "Content validation failed",
        content_type: Optional[str] = None,
        content_id: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if validation_errors:
            details["validation_errors"] = validation_errors
        if content_type:
            details["content_type"] = content_type
        if content_id:
            details["content_id"] = content_id
        kwargs["details"] = details
        error_code = kwargs.pop("error_code", "CONTENT_VALIDATION_ERROR")
        self.validation_errors = validation_errors or []
        self.content_type = content_type
        self.content_id = content_id
        super().__init__(
            message,
            content_id=content_id,
            content_type=content_type,
            error_code=error_code,
            **kwargs,
        )


class SecurityError(MathtermindError):
    """Base exception for security-related errors."""

    def __init__(
        self,
        message: str = "Security operation failed",
        operation: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        kwargs["details"] = details

        if "error_code" not in kwargs:
            kwargs["error_code"] = "SECURITY_ERROR"
        super().__init__(message, **kwargs)


class StorageError(SecurityError):
    """Exception raised when secure storage operations fail."""

    def __init__(self, message: str = "Secure storage operation failed", **kwargs):
        kwargs["error_code"] = "STORAGE_ERROR"
        super().__init__(message, **kwargs)


class SessionError(SecurityError):
    """Exception raised when session operations fail."""

    def __init__(self, message: str = "Session operation failed", **kwargs):
        kwargs["error_code"] = "SESSION_ERROR"
        super().__init__(message, **kwargs)
