import functools
import logging
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import (Any, Callable, Dict, Generic, List, Optional, Set, Tuple,
                    Type, TypeVar, Union)

from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.db import get_db
from src.db.models import Base

T = TypeVar("T", bound=Base)


class ServiceError(Exception):
    """Base exception for service errors."""

    pass


class EntityNotFoundError(ServiceError):
    """Raised when an entity is not found."""

    pass


class ValidationError(ServiceError):
    """Raised when validation fails."""

    pass


class DatabaseError(ServiceError):
    """Raised when a database operation fails."""

    pass


class ConcurrencyError(ServiceError):
    """Raised when a concurrency violation occurs."""

    pass


class BaseService(Generic[T]):
    """Base service class for business logic operations.

    This class defines the standard operations and patterns to be used by all
    service implementations. It is generic over the model type and provides:

    - Enhanced error handling with specific exception types
    - Transaction management utilities
    - Caching for frequently accessed data
    """

    def __init__(self, repository=None, test_mode=False):
        """Initialize the service with a repository.

        Args:
            repository: The repository to use for database operations.
            test_mode: If True, exceptions will be re-raised for testing purposes.
        """
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = next(get_db())
        self.test_mode = test_mode

        self._cache = {}
        self._cache_ttl = {}
        self._default_ttl = timedelta(minutes=5)
        self._max_cache_size = 100

    @contextmanager
    def transaction(self):
        """Context manager for transaction management.

        Manages a database transaction, committing on success and
        rolling back on exception.

        Yields:
            The database session.

        Raises:
            DatabaseError: If a database operation fails.
        """
        try:
            yield self.db
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed: {str(e)}")
            if isinstance(e, IntegrityError):
                raise DatabaseError(f"Integrity constraint violated: {str(e)}") from e
            elif isinstance(e, DataError):
                raise DatabaseError(f"Invalid data format: {str(e)}") from e
            else:
                raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed due to non-database error: {str(e)}")
            raise

    def execute_in_transaction(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function within a transaction.

        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of the function.

        Raises:
            DatabaseError: If a database operation fails.
        """
        with self.transaction():
            return func(*args, **kwargs)

    def batch_operation(
        self, items: List[Any], operation: Callable[[Any], None], batch_size: int = 100
    ) -> None:
        """Execute an operation on items in batches.

        Args:
            items: The items to process.
            operation: The operation to execute on each item.
            batch_size: The size of each batch.

        Raises:
            DatabaseError: If a database operation fails.
        """
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            try:
                with self.transaction():
                    for item in batch:
                        try:
                            operation(item)
                        except Exception as e:
                            self.logger.error(f"Error processing item {item}: {str(e)}")
            except Exception as e:
                self.logger.error(f"Batch operation failed: {str(e)}")

    def cache(self, key: str, ttl: Optional[timedelta] = None) -> Callable:
        """Decorator for caching method results.

        Args:
            key: The base key to use for caching.
            ttl: The time-to-live for cached values.

        Returns:
            A decorator function.
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                cache_key = f"{key}:{hash(str(args) + str(sorted(kwargs.items())))}"

                if cache_key in self._cache:
                    expiry_time = self._cache_ttl.get(cache_key)
                    if expiry_time is None or expiry_time > time.time():
                        self.logger.debug(f"Cache hit for key: {cache_key}")
                        return self._cache[cache_key]

                result = func(*args, **kwargs)

                self._cache[cache_key] = result
                if ttl is not None:
                    self._cache_ttl[cache_key] = time.time() + ttl.total_seconds()
                else:
                    self._cache_ttl[cache_key] = (
                        time.time() + self._default_ttl.total_seconds()
                    )

                self._manage_cache_size()

                return result

            return wrapper

        return decorator

    def invalidate_cache(self, key_prefix: Optional[str] = None) -> None:
        """Invalidate cache entries.

        Args:
            key_prefix: Prefix of keys to invalidate. If None, all entries are invalidated.
        """
        if key_prefix is None:
            self._cache.clear()
            self._cache_ttl.clear()
            self.logger.debug("Cache fully invalidated")
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                self._cache.pop(k, None)
                self._cache_ttl.pop(k, None)
            self.logger.debug(f"Cache invalidated for prefix: {key_prefix}")

    def _manage_cache_size(self) -> None:
        """Manage cache size by removing oldest entries when needed."""
        if len(self._cache) <= self._max_cache_size:
            return

        ordered_keys = sorted(self._cache_ttl.items(), key=lambda x: x[1])
        keys_to_remove = [
            k for k, _ in ordered_keys[: len(self._cache) - self._max_cache_size]
        ]

        for k in keys_to_remove:
            self._cache.pop(k, None)
            self._cache_ttl.pop(k, None)

    def validate(
        self, data: Dict[str, Any], validators: Dict[str, Callable[[Any], bool]]
    ) -> None:
        """Validate data against validators.

        Args:
            data: The data to validate.
            validators: Dictionary mapping field names to validator functions.

        Raises:
            ValidationError: If validation fails.
        """
        errors = {}

        for field, validator in validators.items():
            if field in data:
                if not validator(data[field]):
                    errors[field] = f"Validation failed for field {field}"

        if errors:
            raise ValidationError(f"Validation errors: {errors}")

    def get_by_id(self, id: Any) -> Optional[T]:
        """Get an entity by its ID.

        Args:
            id: The ID of the entity.

        Returns:
            The entity if found, None otherwise.

        Raises:
            EntityNotFoundError: If the entity is not found.
        """
        try:
            entity = self.repository.get_by_id(self.db, id)
            if entity is None:
                raise EntityNotFoundError(f"Entity with ID {id} not found")
            return entity
        except EntityNotFoundError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Error getting entity by ID: {str(e)}")
            if self.test_mode:
                raise
            return None

    def get_all(self) -> List[T]:
        """Get all entities.

        Returns:
            A list of all entities.
        """
        try:
            return self.repository.get_all(self.db)
        except Exception as e:
            self.logger.error(f"Error getting all entities: {str(e)}")
            if self.test_mode:
                raise
            return []

    def create(self, **kwargs) -> Optional[T]:
        """Create a new entity.

        Args:
            **kwargs: The attributes of the entity.

        Returns:
            The created entity if successful, None otherwise.

        Raises:
            ValidationError: If validation fails.
            DatabaseError: If a database operation fails.
        """
        try:
            with self.transaction():
                return self.repository.create(self.db, **kwargs)
        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            if self.test_mode:
                raise
            return None

    def update(self, id: Any, **kwargs) -> Optional[T]:
        """Update an entity.

        Args:
            id: The ID of the entity.
            **kwargs: The attributes to update.

        Returns:
            The updated entity if successful, None otherwise.

        Raises:
            EntityNotFoundError: If the entity is not found.
            ValidationError: If validation fails.
            DatabaseError: If a database operation fails.
        """
        try:
            with self.transaction():
                entity = self.repository.get_by_id(self.db, id)
                if entity is None:
                    raise EntityNotFoundError(f"Entity with ID {id} not found")
                return self.repository.update(self.db, id, **kwargs)
        except (EntityNotFoundError, ValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            if self.test_mode:
                raise
            return None

    def delete(self, id: Any) -> bool:
        """Delete an entity.

        Args:
            id: The ID of the entity.

        Returns:
            True if the entity was deleted, False otherwise.

        Raises:
            EntityNotFoundError: If the entity is not found.
            DatabaseError: If a database operation fails.
        """
        try:
            with self.transaction():
                entity = self.repository.get_by_id(self.db, id)
                if entity is None:
                    raise EntityNotFoundError(f"Entity with ID {id} not found")
                return self.repository.delete(self.db, id)
        except (EntityNotFoundError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            if self.test_mode:
                raise
            return False

    def filter_by(self, **kwargs) -> List[T]:
        """Filter entities by attributes.

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            A list of entities matching the filter.
        """
        try:
            return self.repository.filter_by(self.db, **kwargs)
        except Exception as e:
            self.logger.error(f"Error filtering entities: {str(e)}")
            if self.test_mode:
                raise
            return []

    def count(self) -> int:
        """Count the number of entities.

        Returns:
            The number of entities.
        """
        try:
            return self.repository.count(self.db)
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            if self.test_mode:
                raise
            return 0

    def exists(self, id: Any) -> bool:
        """Check if an entity exists.

        Args:
            id: The ID of the entity.

        Returns:
            True if the entity exists, False otherwise.
        """
        try:
            return self.repository.exists(self.db, id)
        except Exception as e:
            self.logger.error(f"Error checking if entity exists: {str(e)}")
            if self.test_mode:
                raise
            return False


def handle_service_errors(service_name: str = "service"):
    """
    Decorator to handle service errors in a standardized way.

    Args:
        service_name: The name of the service for error logging

    Returns:
        A decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"{service_name}")
            try:
                return func(*args, **kwargs)
            except ServiceError as e:
                logger.error(f"Service error in {func.__name__}: {str(e)}")
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                return {
                    "success": False,
                    "error": f"An unexpected error occurred: {str(e)}",
                }

        return wrapper

    return decorator
