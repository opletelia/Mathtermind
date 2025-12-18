import time
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, call, patch

import pytest
from sqlalchemy.exc import DataError, IntegrityError

from src.db.models import User
from src.services.base_service import (BaseService, DatabaseError,
                                       EntityNotFoundError, ServiceError,
                                       ValidationError)
from src.tests.base_test_classes import BaseServiceTest
from src.tests.utils.test_factories import UserFactory


@pytest.mark.service
@pytest.mark.unit
class TestEnhancedBaseService(BaseServiceTest):
    """Tests for the enhanced BaseService class."""

    def setUp(self):
        """Set up the test environment before each test."""
        super().setUp()

        self.mock_repository = MagicMock()

        self.service = BaseService(repository=self.mock_repository, test_mode=True)

        self.service.db = self.mock_db

        self.test_user_id = uuid.uuid4()

        self.test_user = UserFactory.create(
            id=self.test_user_id, username="testuser", email="testuser@example.com"
        )

    def test_transaction_context_manager_success(self):
        """Test that the transaction context manager commits on success."""
        with self.service.transaction():
            pass

        self.mock_db.commit.assert_called_once()
        self.mock_db.rollback.assert_not_called()

    def test_transaction_context_manager_exception(self):
        """Test that the transaction context manager rolls back on exception."""
        with pytest.raises(Exception):
            with self.service.transaction():
                raise Exception("Test exception")

        self.mock_db.rollback.assert_called_once()
        self.mock_db.commit.assert_not_called()

    def test_transaction_context_manager_sqlalchemy_error(self):
        """Test that the transaction context manager handles SQLAlchemy errors."""
        with pytest.raises(DatabaseError):
            with self.service.transaction():
                raise IntegrityError("statement", "params", "orig")

        self.mock_db.rollback.assert_called_once()
        self.mock_db.commit.assert_not_called()

    def test_execute_in_transaction(self):
        """Test executing a function in a transaction."""
        mock_func = MagicMock()
        mock_func.return_value = "result"

        result = self.service.execute_in_transaction(mock_func, "arg1", kwarg1="value")

        assert result == "result"
        mock_func.assert_called_once_with("arg1", kwarg1="value")
        self.mock_db.commit.assert_called_once()

    def test_batch_operation(self):
        """Test batch operation functionality."""
        items = ["item1", "item2", "item3", "item4", "item5"]
        operation = MagicMock()

        self.service.batch_operation(items, operation, batch_size=2)

        assert operation.call_count == 5
        assert self.mock_db.commit.call_count == 3

    def test_cache_decorator(self):
        """Test that the cache decorator caches function results."""
        test_func = MagicMock()
        test_func.return_value = "cached_result"

        cached_func = self.service.cache("test_key")(test_func)

        result1 = cached_func("arg1", kwarg1="value")

        result2 = cached_func("arg1", kwarg1="value")

        assert result1 == "cached_result"
        assert result2 == "cached_result"
        test_func.assert_called_once()

    def test_cache_with_different_args(self):
        """Test that the cache uses different keys for different args."""
        test_func = MagicMock()
        test_func.side_effect = ["result1", "result2"]

        cached_func = self.service.cache("test_key")(test_func)

        result1 = cached_func("arg1")
        result2 = cached_func("arg2")

        # Assert
        assert result1 == "result1"
        assert result2 == "result2"
        assert test_func.call_count == 2

    def test_cache_ttl_expiration(self):
        """Test that cached items expire after TTL."""
        test_func = MagicMock()
        test_func.side_effect = ["result1", "result2"]

        cached_func = self.service.cache("test_key", ttl=timedelta(milliseconds=1))(
            test_func
        )

        result1 = cached_func("arg")

        time.sleep(0.01)

        result2 = cached_func("arg")

        assert result1 == "result1"
        assert result2 == "result2"
        assert test_func.call_count == 2

    def test_invalidate_cache(self):
        """Test that invalidate_cache removes cache entries."""
        test_func1 = MagicMock(return_value="result1")
        test_func2 = MagicMock(return_value="result2")

        cached_func1 = self.service.cache("key1")(test_func1)
        cached_func2 = self.service.cache("key2")(test_func2)

        cached_func1()
        cached_func2()

        self.service.invalidate_cache("key1")

        cached_func1()
        cached_func2()

        # Assert
        assert test_func1.call_count == 2
        assert test_func2.call_count == 1

    def test_invalidate_all_cache(self):
        """Test that invalidate_cache without a key prefix clears all cache."""
        test_func1 = MagicMock(return_value="result1")
        test_func2 = MagicMock(return_value="result2")

        cached_func1 = self.service.cache("key1")(test_func1)
        cached_func2 = self.service.cache("key2")(test_func2)

        cached_func1()
        cached_func2()

        self.service.invalidate_cache()

        cached_func1()
        cached_func2()

        assert test_func1.call_count == 2
        assert test_func2.call_count == 2

    def test_manage_cache_size(self):
        """Test that cache size is managed correctly."""
        self.service._max_cache_size = 2

        test_func = MagicMock()
        test_func.side_effect = ["result1", "result2", "result3"]

        cached_func = self.service.cache("test_key")(test_func)

        cached_func("arg1")
        cached_func("arg2")
        cached_func("arg3")

        self.service._manage_cache_size()

        assert len(self.service._cache) <= 2

    def test_validate_success(self):
        """Test validation with valid data."""
        data = {"name": "Valid Name", "age": 25}
        validators = {
            "name": lambda x: isinstance(x, str) and len(x) > 0,
            "age": lambda x: isinstance(x, int) and x > 0,
        }

        try:
            self.service.validate(data, validators)
            validation_passed = True
        except ValidationError:
            validation_passed = False

        assert validation_passed

    def test_validate_failure(self):
        """Test validation with invalid data."""
        data = {"name": "", "age": -5}
        validators = {
            "name": lambda x: isinstance(x, str) and len(x) > 0,
            "age": lambda x: isinstance(x, int) and x > 0,
        }

        with pytest.raises(ValidationError):
            self.service.validate(data, validators)

    def test_get_by_id_not_found(self):
        """Test getting an entity by ID when it doesn't exist."""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.get_by_id(self.test_user_id)

    def test_update_entity_not_found(self):
        """Test updating an entity when it doesn't exist."""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.update(self.test_user_id, username="newname")

    def test_delete_entity_not_found(self):
        """Test deleting an entity when it doesn't exist."""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.delete(self.test_user_id)

    def test_exists(self):
        """Test the exists method."""
        self.mock_repository.exists.return_value = True

        result = self.service.exists(self.test_user_id)

        assert result is True
        self.mock_repository.exists.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_exists_exception(self):
        """Test the exists method when an exception occurs."""
        self.mock_repository.exists.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.exists(self.test_user_id)

        self.mock_repository.exists.assert_called_once_with(
            self.mock_db, self.test_user_id
        )
