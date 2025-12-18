import unittest
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


class BaseRepositoryTest:
    """Base class for repository tests."""

    @pytest.fixture(autouse=True)
    def setup_db(self, test_db):
        """Set up the test database."""
        self.db = test_db

    def create_test_data(self):
        """Create test data for the repository tests.

        This method should be overridden by subclasses to create
        specific test data for each repository.
        """
        pass


class BaseServiceTest(unittest.TestCase):
    """Base class for service tests."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mock_db = MagicMock()

        self.mock_session = self.mock_db

        self.get_db_patcher = patch("src.db.get_db")
        self.mock_get_db = self.get_db_patcher.start()
        self.mock_get_db.side_effect = lambda: iter([self.mock_db])

    def tearDown(self):
        """Clean up after each test."""
        self.get_db_patcher.stop()

    def mock_repository_method(self, repository_path, method_name, return_value):
        """Mock a repository method.

        Args:
            repository_path (str): The import path to the repository module.
            method_name (str): The name of the method to mock.
            return_value: The value to return when the method is called.

        Returns:
            MagicMock: The mock object.
        """
        patcher = patch(f"{repository_path}.{method_name}")
        mock_method = patcher.start()
        mock_method.return_value = return_value
        self.addCleanup(patcher.stop)
        return mock_method


class BaseModelTest:
    """Base class for model tests."""

    @pytest.fixture(autouse=True)
    def setup_db(self, test_db):
        """Set up the test database."""
        self.db = test_db

    def validate_model_attributes(self, model_instance, expected_attributes):
        """Validate that a model instance has the expected attributes.

        Args:
            model_instance: The model instance to validate.
            expected_attributes (dict): A dictionary of attribute names and expected values.
        """
        for attr_name, expected_value in expected_attributes.items():
            assert hasattr(
                model_instance, attr_name
            ), f"Model does not have attribute {attr_name}"
            assert (
                getattr(model_instance, attr_name) == expected_value
            ), f"Expected {attr_name} to be {expected_value}, got {getattr(model_instance, attr_name)}"
