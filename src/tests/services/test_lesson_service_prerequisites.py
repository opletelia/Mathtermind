import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.core.error_handling import (BusinessLogicError, ResourceNotFoundError,
                                     ValidationError)
from src.db.models.enums import DifficultyLevel
from src.models.lesson import Lesson
from src.services.lesson_service import LessonService

lesson_repo_mock = MagicMock()
lesson_repo_patch = patch("src.db.repositories.lesson_repo", lesson_repo_mock)

progress_service_mock = MagicMock()
progress_service_class_mock = MagicMock(return_value=progress_service_mock)
progress_service_patch = patch(
    "src.services.progress_service.ProgressService", progress_service_class_mock
)


class TestLessonServicePrerequisites(unittest.TestCase):
    """Tests for the lesson sequencing and prerequisites functionality."""

    def setUp(self):
        """Set up the test environment."""
        lesson_repo_patch.start()
        progress_service_patch.start()

        self.lesson_service = LessonService(repo=lesson_repo_mock)

        self.mock_db = MagicMock()
        self.lesson_service.db = self.mock_db

        lesson_repo_mock.reset_mock()
        progress_service_mock.reset_mock()
        progress_service_class_mock.reset_mock()

        self.course_id = str(uuid.uuid4())

        self.lesson1_id = str(uuid.uuid4())
        self.lesson2_id = str(uuid.uuid4())
        self.lesson3_id = str(uuid.uuid4())

        self.db_lesson1 = MagicMock()
        self.db_lesson1.id = uuid.UUID(self.lesson1_id)
        self.db_lesson1.title = "Lesson 1"
        self.db_lesson1.difficulty_level = DifficultyLevel.BEGINNER
        self.db_lesson1.lesson_order = 1
        self.db_lesson1.estimated_time = 30
        self.db_lesson1.points_reward = 10
        self.db_lesson1.prerequisites = {}
        self.db_lesson1.learning_objectives = ["Basic concepts"]

        self.db_lesson2 = MagicMock()
        self.db_lesson2.id = uuid.UUID(self.lesson2_id)
        self.db_lesson2.title = "Lesson 2"
        self.db_lesson2.difficulty_level = DifficultyLevel.BEGINNER
        self.db_lesson2.lesson_order = 2
        self.db_lesson2.estimated_time = 45
        self.db_lesson2.points_reward = 15
        self.db_lesson2.prerequisites = {"lessons": [str(self.db_lesson1.id)]}
        self.db_lesson2.learning_objectives = ["Apply basic concepts"]

        self.db_lesson3 = MagicMock()
        self.db_lesson3.id = uuid.UUID(self.lesson3_id)
        self.db_lesson3.title = "Lesson 3"
        self.db_lesson3.difficulty_level = DifficultyLevel.INTERMEDIATE
        self.db_lesson3.lesson_order = 3
        self.db_lesson3.estimated_time = 60
        self.db_lesson3.points_reward = 20
        self.db_lesson3.prerequisites = {
            "lessons": [str(self.db_lesson1.id), str(self.db_lesson2.id)]
        }
        self.db_lesson3.learning_objectives = ["Evaluate knowledge"]

    def tearDown(self):
        """Clean up after each test."""
        lesson_repo_patch.stop()
        progress_service_patch.stop()

    def test_get_prerequisite_lessons(self):
        """Test getting prerequisite lessons for a lesson."""
        lesson_repo_mock.get_lesson.side_effect = (
            lambda session, lesson_id: self.db_lesson3
        )
        lesson_repo_mock.get_prerequisite_lessons.return_value = [
            self.db_lesson1,
            self.db_lesson2,
        ]

        result = self.lesson_service.get_prerequisite_lessons(lesson_id=self.lesson3_id)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Lesson 1")
        self.assertEqual(result[1].title, "Lesson 2")
        lesson_repo_mock.get_prerequisite_lessons.assert_called_once()

    def test_get_dependent_lessons(self):
        """Test getting lessons that depend on a specific lesson."""
        lesson_repo_mock.get_lesson.side_effect = (
            lambda session, lesson_id: self.db_lesson1
        )
        lesson_repo_mock.get_dependent_lessons.return_value = [
            self.db_lesson2,
            self.db_lesson3,
        ]

        result = self.lesson_service.get_dependent_lessons(lesson_id=self.lesson1_id)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Lesson 2")
        self.assertEqual(result[1].title, "Lesson 3")
        lesson_repo_mock.get_dependent_lessons.assert_called_once()

    def test_add_prerequisite(self):
        """Test adding a prerequisite to a lesson."""
        lesson_repo_mock.get_lesson.side_effect = lambda session, lesson_id: {
            uuid.UUID(self.lesson2_id): self.db_lesson2,
            uuid.UUID(self.lesson1_id): self.db_lesson1,
        }.get(lesson_id)

        lesson_repo_mock.get_dependent_lessons.return_value = []

        updated_lesson = MagicMock()
        updated_lesson.id = self.db_lesson2.id
        updated_lesson.title = self.db_lesson2.title
        updated_lesson.difficulty_level = self.db_lesson2.difficulty_level
        updated_lesson.lesson_order = self.db_lesson2.lesson_order
        updated_lesson.estimated_time = self.db_lesson2.estimated_time
        updated_lesson.points_reward = self.db_lesson2.points_reward
        updated_lesson.prerequisites = {"lessons": [str(self.db_lesson1.id)]}
        updated_lesson.learning_objectives = self.db_lesson2.learning_objectives

        lesson_repo_mock.update_lesson.return_value = updated_lesson

        self.db_lesson2.prerequisites = {}

        result = self.lesson_service.add_prerequisite(
            lesson_id=self.lesson2_id, prerequisite_id=self.lesson1_id
        )

        self.assertTrue(result)
        lesson_repo_mock.update_lesson.assert_called_once()

    def test_add_circular_prerequisite(self):
        """Test adding a prerequisite that would create a circular dependency."""
        lesson_repo_mock.get_lesson.side_effect = lambda db, lesson_id: {
            uuid.UUID(self.lesson1_id): self.db_lesson1,
            uuid.UUID(self.lesson3_id): self.db_lesson3,
        }.get(lesson_id)

        lesson_repo_mock.get_dependent_lessons.return_value = [
            self.db_lesson2,
            self.db_lesson3,
        ]

        with self.assertRaises(BusinessLogicError):
            self.lesson_service.add_prerequisite(
                lesson_id=self.lesson1_id, prerequisite_id=self.lesson3_id
            )

    def test_remove_prerequisite(self):
        """Test removing a prerequisite from a lesson."""
        lesson_repo_mock.get_lesson.side_effect = (
            lambda session, lesson_id: self.db_lesson3
        )

        self.db_lesson3.prerequisites = {
            "lessons": [str(self.db_lesson1.id), str(self.db_lesson2.id)]
        }

        updated_lesson = MagicMock()
        updated_lesson.id = self.db_lesson3.id
        updated_lesson.title = self.db_lesson3.title
        updated_lesson.difficulty_level = self.db_lesson3.difficulty_level
        updated_lesson.lesson_order = self.db_lesson3.lesson_order
        updated_lesson.estimated_time = self.db_lesson3.estimated_time
        updated_lesson.points_reward = self.db_lesson3.points_reward
        updated_lesson.prerequisites = {
            "lessons": [str(self.db_lesson1.id)]  # Removed lesson2
        }
        updated_lesson.learning_objectives = self.db_lesson3.learning_objectives

        lesson_repo_mock.update_lesson.return_value = updated_lesson

        result = self.lesson_service.remove_prerequisite(
            lesson_id=self.lesson3_id, prerequisite_id=self.lesson2_id
        )

        self.assertTrue(result)
        lesson_repo_mock.update_lesson.assert_called_once()

    def test_check_prerequisites_satisfied(self):
        """Test checking if a user has satisfied all prerequisites for a lesson."""
        lesson_repo_mock.get_lesson.side_effect = (
            lambda session, lesson_id: self.db_lesson3
        )

        self.db_lesson3.prerequisites = {
            "lessons": [str(self.db_lesson1.id), str(self.db_lesson2.id)]
        }

        lesson_repo_mock.get_prerequisite_lessons.return_value = [
            self.db_lesson1,
            self.db_lesson2,
        ]

        progress_service_mock.has_completed_lesson.side_effect = (
            lambda user_id, lesson_id: lesson_id == self.lesson1_id
        )

        user_id = str(uuid.uuid4())
        result, missing = self.lesson_service.check_prerequisites_satisfied(
            user_id=user_id, lesson_id=self.lesson3_id
        )

        self.assertFalse(result)
        self.assertEqual(len(missing), 2)
        self.assertTrue(any(lesson.title == "Lesson 2" for lesson in missing))

    def test_reorder_lessons(self):
        """Test reordering lessons in a course."""
        lesson_repo_mock.get_lessons_by_course_id.return_value = [
            self.db_lesson1,
            self.db_lesson2,
            self.db_lesson3,
        ]

        lesson_repo_mock.update_lesson_order.return_value = True

        lesson_repo_mock.get_lesson.side_effect = lambda session, lesson_id: {
            uuid.UUID(self.lesson1_id): self.db_lesson1,
            uuid.UUID(self.lesson2_id): self.db_lesson2,
            uuid.UUID(self.lesson3_id): self.db_lesson3,
        }.get(lesson_id)

        new_order = {self.lesson1_id: 2, self.lesson2_id: 1, self.lesson3_id: 3}

        result = self.lesson_service.reorder_lessons(
            course_id=self.course_id, new_order=new_order
        )

        self.assertTrue(result)
        self.assertEqual(lesson_repo_mock.update_lesson_order.call_count, 3)

    def test_validate_lesson_dependencies(self):
        """Test validating that lesson dependencies make sense with lesson order."""
        lesson_repo_mock.get_lessons_by_course_id.return_value = [
            self.db_lesson1,
            self.db_lesson2,
            self.db_lesson3,
        ]

        result, issues = self.lesson_service.validate_lesson_dependencies(
            course_id=self.course_id
        )

        self.assertTrue(result)
        self.assertEqual(len(issues), 0)

    def test_validate_lesson_dependencies_with_issues(self):
        """Test validation finds issues when prerequisites are in wrong order."""
        bad_lesson = MagicMock()
        bad_lesson.id = uuid.uuid4()
        bad_lesson.title = "Bad Lesson"
        bad_lesson.lesson_order = 1
        bad_lesson.prerequisites = {"lessons": [str(self.db_lesson2.id)]}

        lesson_repo_mock.get_lessons_by_course_id.return_value = [
            bad_lesson,
            self.db_lesson2,
            self.db_lesson3,
        ]

        result, issues = self.lesson_service.validate_lesson_dependencies(
            course_id=self.course_id
        )

        self.assertFalse(result)
        self.assertEqual(len(issues), 3)
        self.assertTrue(
            any("Bad Lesson" in issue and "Lesson 2" in issue for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
