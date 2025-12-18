import contextlib
import unittest
import uuid
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.core.error_handling.exceptions import (ResourceNotFoundError,
                                                ValidationError)
from src.db.models.enums import DifficultyLevel
from src.db.repositories import lesson_repo
from src.models.lesson import Lesson
from src.services.lesson_service import LessonService


class TestLessonServiceCreation(unittest.TestCase):
    """Test cases for lesson service creation functionality."""

    def setUp(self):
        """Set up test resources."""
        self.mock_db = MagicMock()

        self.lesson_service = LessonService()

        self.lesson_id = str(uuid.uuid4())

        self.sample_lesson = Lesson(
            id=uuid.UUID(self.lesson_id),
            title="Test Lesson",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_time=30,
            points_reward=10,
            lesson_order=1,
            prerequisites=["Basic Math"],
            learning_objectives=["Learn Something"],
            content={"blocks": []},
            course_id=str(uuid.uuid4()),
        )

        self.db_lesson = MagicMock()
        self.db_lesson.id = uuid.UUID(self.lesson_id)
        self.db_lesson.title = "Test Lesson"
        self.db_lesson.difficulty_level = DifficultyLevel.BEGINNER
        self.db_lesson.estimated_time = 30
        self.db_lesson.points_reward = 10
        self.db_lesson.lesson_order = 1
        self.db_lesson.prerequisites = ["Basic Math"]
        self.db_lesson.learning_objectives = ["Learn Something"]
        self.db_lesson.content = {"blocks": []}
        self.db_lesson.course_id = uuid.uuid4()

        self.mock_transaction_context = MagicMock()
        self.mock_transaction_context.__enter__ = MagicMock(return_value=self.mock_db)
        self.mock_transaction_context.__exit__ = MagicMock(return_value=None)

        self.lesson_service.transaction = MagicMock(
            return_value=self.mock_transaction_context
        )

    def test_create_lesson(self):
        """Test creating a new lesson."""
        lesson_data = {
            "title": "New Lesson",
            "course_id": str(uuid.uuid4()),
            "difficulty_level": "BEGINNER",
            "estimated_time": 30,
            "points_reward": 10,
            "lesson_order": 1,
            "prerequisites": ["Basic Math"],
            "learning_objectives": ["Learn Something"],
            "content": {"blocks": []},
        }

        with patch.object(lesson_repo, "create_lesson") as mock_create:
            mock_db_lesson = MagicMock()
            mock_db_lesson.id = self.db_lesson.id
            mock_db_lesson.title = "New Lesson"
            mock_db_lesson.difficulty_level = DifficultyLevel.BEGINNER
            mock_db_lesson.course_id = self.db_lesson.course_id
            mock_db_lesson.lesson_order = 1
            mock_db_lesson.estimated_time = 30
            mock_db_lesson.points_reward = 10
            mock_db_lesson.prerequisites = ["Basic Math"]
            mock_db_lesson.learning_objectives = ["Learn Something"]
            mock_db_lesson.content = {"blocks": []}

            mock_create.return_value = mock_db_lesson

            result = self.lesson_service.create_lesson(**lesson_data)

            self.assertEqual(str(result.id), str(self.sample_lesson.id))
            self.assertEqual(result.title, lesson_data["title"])

            mock_create.assert_called_once()

    def test_create_lesson_validation_error(self):
        """Test validation error when creating a lesson with invalid data."""
        lesson_data = {
            "title": "",
            "difficulty_level": "BEGINNER",
            "lesson_order": 1,
            "estimated_time": 30,
            "points_reward": 10,
        }

        with self.assertRaises(ValidationError):
            self.lesson_service.create_lesson(
                course_id=str(self.sample_lesson.course_id), **lesson_data
            )

    def test_update_lesson(self):
        """Test updating an existing lesson."""
        update_data = {
            "title": "Updated Lesson",
            "difficulty_level": "INTERMEDIATE",
            "estimated_time": 45,
        }

        with patch.object(lesson_repo, "get_lesson") as mock_get, patch.object(
            lesson_repo, "update_lesson"
        ) as mock_update:
            mock_get.return_value = self.db_lesson
            updated_lesson = MagicMock()
            updated_lesson.id = uuid.UUID(self.lesson_id)
            updated_lesson.title = "Updated Lesson"
            updated_lesson.difficulty_level = DifficultyLevel.INTERMEDIATE
            updated_lesson.estimated_time = 45
            updated_lesson.lesson_order = self.db_lesson.lesson_order
            updated_lesson.points_reward = self.db_lesson.points_reward
            updated_lesson.prerequisites = self.db_lesson.prerequisites
            updated_lesson.learning_objectives = self.db_lesson.learning_objectives
            mock_update.return_value = updated_lesson

            result = self.lesson_service.update_lesson(
                lesson_id=self.lesson_id, **update_data
            )

            self.assertEqual(str(result.id), str(self.sample_lesson.id))
            self.assertEqual(result.title, "Updated Lesson")
            self.assertEqual(
                result.difficulty_level, DifficultyLevel.INTERMEDIATE.value
            )
            self.assertEqual(result.estimated_time, 45)
            mock_update.assert_called_once()

    def test_update_lesson_not_found(self):
        """Test updating a lesson that doesn't exist."""
        update_data = {"title": "Updated Lesson"}

        with patch.object(lesson_repo, "get_lesson") as mock_get:
            mock_get.return_value = None

            with self.assertRaises(ResourceNotFoundError):
                self.lesson_service.update_lesson(
                    lesson_id=self.lesson_id, **update_data
                )

    def test_delete_lesson(self):
        """Test deleting a lesson."""
        with patch.object(lesson_repo, "get_lesson") as mock_get, patch.object(
            lesson_repo, "delete_lesson"
        ) as mock_delete:
            mock_get.return_value = self.db_lesson
            mock_delete.return_value = self.db_lesson

            result = self.lesson_service.delete_lesson(lesson_id=self.lesson_id)

            self.assertTrue(result)
            mock_delete.assert_called_once()

    def test_update_lesson_order(self):
        """Test updating lesson order."""
        with patch.object(lesson_repo, "get_lesson") as mock_get, patch.object(
            lesson_repo, "update_lesson_order"
        ) as mock_update_order:
            mock_get.return_value = self.db_lesson
            mock_update_order.return_value = True

            result = self.lesson_service.update_lesson_order(
                lesson_id=self.lesson_id, new_order=2
            )

            self.assertTrue(result)
            mock_update_order.assert_called_once()

    def test_validate_lesson_data(self):
        """Test validation of lesson data through the create_lesson method."""
        invalid_title_data = {
            "title": "",
            "difficulty_level": "BEGINNER",
            "course_id": str(uuid.uuid4()),
            "lesson_order": 1,
            "estimated_time": 30,
            "points_reward": 10,
        }

        with self.assertRaises(ValidationError):
            self.lesson_service.create_lesson(**invalid_title_data)

        missing_title_data = {
            "title": "",
            "difficulty_level": "BEGINNER",
            "lesson_order": 1,
            "estimated_time": 30,
        }

        with self.assertRaises(ValidationError):
            self.lesson_service.create_lesson(
                course_id=str(uuid.uuid4()), **missing_title_data
            )


if __name__ == "__main__":
    unittest.main()
