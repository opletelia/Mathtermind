import uuid
from datetime import datetime, timezone

import pytest

from src.db.models import User
from src.db.repositories.base_repository import BaseRepository
from src.tests.utils.test_factories import UserFactory


@pytest.mark.repository
@pytest.mark.unit
class TestBaseRepository:
    """Tests for the BaseRepository class."""

    def setup_method(self):
        """Set up the test environment before each test."""
        self.user_repo = BaseRepository(User)

    def test_get_by_id(self, test_db, test_user):
        """Test getting an entity by ID."""
        user_id = test_user.id

        result = self.user_repo.get_by_id(test_db, user_id)

        assert result is not None
        assert result.id == user_id
        assert result.username == "testuser"
        assert result.email == "testuser@example.com"

    def test_get_all(self, test_db, test_user):
        """Test getting all entities."""
        another_user = UserFactory.create(
            username="anotheruser", email="another@example.com"
        )
        test_db.add(another_user)
        test_db.commit()

        results = self.user_repo.get_all(test_db)

        assert results is not None
        assert len(results) >= 2

        user_emails = [user.email for user in results]
        assert test_user.email in user_emails
        assert another_user.email in user_emails

    def test_create(self, test_db):
        """Test creating an entity."""
        user_data = UserFactory._get_defaults()
        user_data["id"] = uuid.uuid4()

        result = self.user_repo.create(test_db, **user_data)

        assert result is not None
        assert result.id == user_data["id"]
        assert result.username == user_data["username"]
        assert result.email == user_data["email"]

        fetched_user = test_db.query(User).filter_by(id=user_data["id"]).first()
        assert fetched_user is not None
        assert fetched_user.username == user_data["username"]
        assert fetched_user.email == user_data["email"]

    def test_update(self, test_db, test_user):
        """Test updating an entity."""
        user_id = test_user.id
        new_username = "updateduser"

        result = self.user_repo.update(test_db, user_id, username=new_username)

        assert result is not None
        assert result.username == new_username

        updated_user = test_db.query(User).filter_by(id=user_id).first()
        assert updated_user is not None
        assert updated_user.username == new_username

    def test_delete(self, test_db, test_user):
        """Test deleting an entity."""
        user_id = test_user.id

        result = self.user_repo.delete(test_db, user_id)

        assert result is True

        deleted_user = test_db.query(User).filter_by(id=user_id).first()
        assert deleted_user is None

    def test_filter_by(self, test_db, test_user):
        """Test filtering entities by criteria."""
        users = [
            UserFactory.create(username=f"filteruser{i}", points=i * 100)
            for i in range(1, 4)
        ]
        for user in users:
            test_db.add(user)
        test_db.commit()

        results = self.user_repo.filter_by(test_db, username="filteruser2")

        assert results is not None
        assert len(results) == 1
        assert results[0].username == "filteruser2"
        assert results[0].points == 200

    def test_count(self, test_db, test_user):
        """Test counting entities."""
        users = UserFactory.create_batch(3)
        for user in users:
            test_db.add(user)
        test_db.commit()

        initial_count = test_db.query(User).count()

        result = self.user_repo.count(test_db)

        assert result == initial_count
