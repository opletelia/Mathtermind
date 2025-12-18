import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.db.models import User
from src.services.base_service import (BaseService, DatabaseError,
                                       EntityNotFoundError, ValidationError)
from src.tests.base_test_classes import BaseServiceTest
from src.tests.utils.test_factories import UserFactory


@pytest.mark.service
@pytest.mark.unit
class TestBaseService(BaseServiceTest):
    """Tests for the BaseService class."""

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

    def test_get_by_id(self):
        """Test getting an entity by ID."""
        self.mock_repository.get_by_id.return_value = self.test_user

        result = self.service.get_by_id(self.test_user_id)

        assert result == self.test_user
        self.mock_repository.get_by_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_get_by_id_exception(self):
        """Test getting an entity by ID when an exception occurs."""
        self.mock_repository.get_by_id.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.get_by_id(self.test_user_id)

        self.mock_repository.get_by_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_get_by_id_not_found(self):
        """Test getting an entity by ID when it doesn't exist."""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.get_by_id(self.test_user_id)

    def test_get_all(self):
        """Test getting all entities."""
        users = UserFactory.create_batch(3)
        self.mock_repository.get_all.return_value = users

        result = self.service.get_all()

        assert result == users
        self.mock_repository.get_all.assert_called_once_with(self.mock_db)

    def test_get_all_exception(self):
        """Test getting all entities when an exception occurs."""
        self.mock_repository.get_all.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.get_all()

        self.mock_repository.get_all.assert_called_once_with(self.mock_db)

    def test_create(self):
        """Test creating an entity."""
        user_data = UserFactory._get_defaults()
        user_data["id"] = self.test_user_id

        self.mock_repository.create.return_value = self.test_user

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            result = self.service.create(**user_data)

            assert result == self.test_user
            self.mock_repository.create.assert_called_once_with(
                self.mock_db, **user_data
            )

    def test_create_exception(self):
        """Test creating an entity when an exception occurs."""
        user_data = UserFactory._get_defaults()
        user_data["id"] = self.test_user_id

        self.mock_repository.create.side_effect = Exception("Database error")

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(Exception):
                self.service.create(**user_data)

            self.mock_repository.create.assert_called_once_with(
                self.mock_db, **user_data
            )

    def test_update(self):
        """Test updating an entity."""
        update_data = {"username": "updateduser"}
        self.mock_repository.get_by_id.return_value = self.test_user
        self.mock_repository.update.return_value = self.test_user

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            result = self.service.update(self.test_user_id, **update_data)

            assert result == self.test_user
            self.mock_repository.update.assert_called_once_with(
                self.mock_db, self.test_user_id, **update_data
            )

    def test_update_exception(self):
        """Test updating an entity when an exception occurs."""
        update_data = {"username": "updateduser"}
        self.mock_repository.get_by_id.return_value = self.test_user
        self.mock_repository.update.side_effect = Exception("Database error")

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(Exception):
                self.service.update(self.test_user_id, **update_data)

            self.mock_repository.get_by_id.assert_called_once_with(
                self.mock_db, self.test_user_id
            )
            self.mock_repository.update.assert_called_once_with(
                self.mock_db, self.test_user_id, **update_data
            )

    def test_update_entity_not_found(self):
        """Test updating an entity when it doesn't exist."""
        update_data = {"username": "updateduser"}
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.update(self.test_user_id, **update_data)

    def test_delete(self):
        """Test deleting an entity."""
        self.mock_repository.get_by_id.return_value = self.test_user
        self.mock_repository.delete.return_value = True

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            result = self.service.delete(self.test_user_id)

            assert result is True
            self.mock_repository.delete.assert_called_once_with(
                self.mock_db, self.test_user_id
            )

    def test_delete_exception(self):
        """Test deleting an entity when an exception occurs."""
        self.mock_repository.get_by_id.return_value = self.test_user
        self.mock_repository.delete.side_effect = Exception("Database error")

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(Exception):
                self.service.delete(self.test_user_id)

            self.mock_repository.get_by_id.assert_called_once_with(
                self.mock_db, self.test_user_id
            )
            self.mock_repository.delete.assert_called_once_with(
                self.mock_db, self.test_user_id
            )

    def test_delete_entity_not_found(self):
        """Test deleting an entity when it doesn't exist."""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError):
            self.service.delete(self.test_user_id)

    def test_filter_by(self):
        """Test filtering entities by criteria."""
        users = [
            UserFactory.create(username=f"filteruser{i}", points=i * 100)
            for i in range(1, 4)
        ]

        filter_criteria = {"username": "filteruser1"}
        self.mock_repository.filter_by.return_value = [users[0]]

        result = self.service.filter_by(**filter_criteria)

        assert result == [users[0]]
        self.mock_repository.filter_by.assert_called_once_with(
            self.mock_db, **filter_criteria
        )

    def test_filter_by_exception(self):
        """Test filtering entities when an exception occurs."""
        filter_criteria = {"username": "filteruser1"}
        self.mock_repository.filter_by.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.filter_by(**filter_criteria)

        self.mock_repository.filter_by.assert_called_once_with(
            self.mock_db, **filter_criteria
        )

    def test_count(self):
        """Test counting entities."""
        self.mock_repository.count.return_value = 5

        result = self.service.count()

        assert result == 5
        self.mock_repository.count.assert_called_once_with(self.mock_db)

    def test_count_exception(self):
        """Test counting entities when an exception occurs."""
        self.mock_repository.count.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.count()

        self.mock_repository.count.assert_called_once_with(self.mock_db)

    def test_exists(self):
        """Test checking if an entity exists."""
        self.mock_repository.exists.return_value = True

        result = self.service.exists(self.test_user_id)

        assert result is True
        self.mock_repository.exists.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_exists_exception(self):
        """Test checking if an entity exists when an exception occurs."""
        self.mock_repository.exists.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.exists(self.test_user_id)

        self.mock_repository.exists.assert_called_once_with(
            self.mock_db, self.test_user_id
        )
