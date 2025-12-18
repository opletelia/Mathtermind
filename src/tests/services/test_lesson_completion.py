import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.core.error_handling import ResourceNotFoundError, ValidationError
from src.db.models.enums import DifficultyLevel
from src.models.lesson import Lesson
from src.services.lesson_service import LessonService

lesson_repo_mock = MagicMock()
lesson_repo_patch = patch("src.db.repositories.lesson_repo", lesson_repo_mock)


class TestLessonCompletion(unittest.TestCase):
    """Tests for the lesson completion criteria management functionality."""

    def setUp(self):
        """Set up the test environment."""
        lesson_repo_patch.start()

        self.lesson_service = LessonService()

        self.lesson_service.lesson_repo = lesson_repo_mock

        self.mock_db = MagicMock()
        self.lesson_service.db = self.mock_db

        transaction_cm = MagicMock()
        transaction_cm.__enter__ = MagicMock(return_value=self.mock_db)
        transaction_cm.__exit__ = MagicMock(return_value=None)
        self.lesson_service.transaction = MagicMock(return_value=transaction_cm)

        self.mock_progress_service = MagicMock()
        self.lesson_service.progress_service = self.mock_progress_service

        self.course_id = str(uuid.uuid4())
        self.lesson_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())

        self.db_lesson = MagicMock()
        self.db_lesson.id = uuid.UUID(self.lesson_id)
        self.db_lesson.title = "Test Lesson"
        self.db_lesson.difficulty_level = DifficultyLevel.BEGINNER
        self.db_lesson.lesson_order = 1
        self.db_lesson.estimated_time = 30
        self.db_lesson.points_reward = 10
        self.db_lesson.prerequisites = {}
        self.db_lesson.learning_objectives = ["Basic concepts"]
        self.db_lesson.course_id = uuid.UUID(self.course_id)

        self.db_lesson.metadata = {
            "completion_criteria": {
                "required_score": 70,
                "required_content_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
                "required_time_spent": 15,  # minutes
            }
        }

        lesson_repo_mock.reset_mock()

    def tearDown(self):
        """Clean up after each test."""
        lesson_repo_patch.stop()

    def test_set_completion_criteria(self):
        """Test setting completion criteria for a lesson."""
        completion_criteria = {
            "required_score": 80,
            "required_content_ids": [str(uuid.uuid4())],
            "required_time_spent": 20,
        }

        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        updated_lesson = MagicMock()
        updated_lesson.id = self.db_lesson.id
        updated_lesson.metadata = {"completion_criteria": completion_criteria}
        lesson_repo_mock.update_lesson_metadata.return_value = updated_lesson

        result = self.lesson_service.set_completion_criteria(
            lesson_id=self.lesson_id, completion_criteria=completion_criteria
        )

        self.assertTrue(result)
        lesson_repo_mock.update_lesson_metadata.assert_called_once()
        call_args = lesson_repo_mock.update_lesson_metadata.call_args[0]
        self.assertEqual(call_args[1], uuid.UUID(self.lesson_id))
        self.assertEqual(call_args[2], {"completion_criteria": completion_criteria})

    def test_get_completion_criteria(self):
        """Test getting completion criteria for a lesson."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        result = self.lesson_service.get_completion_criteria(lesson_id=self.lesson_id)

        self.assertIsNotNone(result)
        self.assertEqual(result["required_score"], 70)
        self.assertEqual(len(result["required_content_ids"]), 2)
        self.assertEqual(result["required_time_spent"], 15)

    def test_get_completion_criteria_not_found(self):
        """Test getting completion criteria for a lesson that doesn't exist."""
        lesson_repo_mock.get_lesson.return_value = None

        with self.assertRaises(ResourceNotFoundError):
            self.lesson_service.get_completion_criteria(lesson_id=self.lesson_id)

    def test_check_lesson_completion_criteria_met(self):
        """Test checking if a user has met a lesson's completion criteria."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.mock_progress_service.get_lesson_score.return_value = (
            85  # Above required_score of 70
        )
        self.mock_progress_service.get_assessment_score.return_value = (
            85  # Above required_score of 70
        )
        self.mock_progress_service.get_completed_content_ids.return_value = (
            self.db_lesson.metadata["completion_criteria"]["required_content_ids"]
        )
        self.mock_progress_service.get_time_spent_on_lesson.return_value = (
            20  # Above required_time_spent of 15
        )
        self.mock_progress_service.get_time_spent.return_value = (
            20  # Above required_time_spent of 15
        )
        self.mock_progress_service.has_completed_content.return_value = True

        self.mock_progress_service.is_content_completed.return_value = True

        with patch.object(
            self.lesson_service,
            "check_prerequisites_satisfied",
            return_value=(True, []),
        ):
            result, missing = self.lesson_service.check_completion_criteria_met(
                user_id=self.user_id, lesson_id=self.lesson_id
            )

            self.assertTrue(result)
            self.assertEqual(len(missing), 0)

    def test_check_lesson_completion_criteria_not_met(self):
        """Test checking if a user has not met a lesson's completion criteria."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.mock_progress_service.get_lesson_score.return_value = (
            65  # Below required_score of 70
        )
        self.mock_progress_service.get_assessment_score.return_value = (
            65  # Below required_score of 70
        )
        self.mock_progress_service.get_completed_content_ids.return_value = [
            self.db_lesson.metadata["completion_criteria"]["required_content_ids"][0]
        ]  # Missing one content
        self.mock_progress_service.get_time_spent_on_lesson.return_value = (
            10  # Below required_time_spent of 15
        )
        self.mock_progress_service.get_time_spent.return_value = (
            10  # Below required_time_spent of 15
        )
        self.mock_progress_service.has_completed_content.return_value = False

        self.mock_progress_service.is_content_completed.return_value = False

        with patch.object(
            self.lesson_service,
            "check_prerequisites_satisfied",
            return_value=(True, []),
        ):
            result, missing = self.lesson_service.check_completion_criteria_met(
                user_id=self.user_id, lesson_id=self.lesson_id
            )

            self.assertFalse(result)
            self.assertTrue(len(missing) >= 2)  # At least missing score and content
            self.assertTrue(any(item.lower().find("score") >= 0 for item in missing))
            self.assertTrue(any(item.lower().find("content") >= 0 for item in missing))
            self.assertTrue(any(item.lower().find("time") >= 0 for item in missing))

    def test_mark_lesson_complete(self):
        """Test marking a lesson as complete for a user."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.mock_progress_service.complete_lesson.return_value = True

        with patch.object(
            self.lesson_service,
            "check_completion_criteria_met",
            return_value=(True, []),
        ), patch.object(
            self.lesson_service, "get_lesson_by_id", return_value=self.db_lesson
        ):
            result = self.lesson_service.mark_lesson_complete(
                user_id=self.user_id, lesson_id=self.lesson_id
            )

            self.assertTrue(result)

            self.assertEqual(self.mock_progress_service.complete_lesson.call_count, 1)
            call_kwargs = self.mock_progress_service.complete_lesson.call_args.kwargs
            self.assertEqual(call_kwargs["user_id"], self.user_id)
            self.assertEqual(call_kwargs["lesson_id"], self.lesson_id)
            self.assertIn("course_id", call_kwargs)

    def test_mark_lesson_complete_criteria_not_met(self):
        """Test attempting to mark a lesson complete when criteria aren't met."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.lesson_service.check_completion_criteria_met = MagicMock(
            return_value=(False, ["Score below required minimum"])
        )

        with self.assertRaises(Exception) as context:
            self.lesson_service.mark_lesson_complete(
                user_id=self.user_id, lesson_id=self.lesson_id, override_criteria=False
            )

        self.assertIn("Completion criteria not met", str(context.exception))

    def test_mark_lesson_complete_with_override(self):
        """Test marking a lesson complete with criteria override."""
        lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.mock_progress_service.complete_lesson.return_value = True

        with patch.object(
            self.lesson_service, "get_lesson_by_id", return_value=self.db_lesson
        ):
            result = self.lesson_service.mark_lesson_complete(
                user_id=self.user_id, lesson_id=self.lesson_id, override_criteria=True
            )

            self.assertTrue(result)

            self.assertEqual(self.mock_progress_service.complete_lesson.call_count, 1)
            call_args = self.mock_progress_service.complete_lesson.call_args[1]
            self.assertEqual(call_args["user_id"], self.user_id)
            self.assertEqual(call_args["lesson_id"], self.lesson_id)
            self.assertIn("course_id", call_args)


if __name__ == "__main__":
    unittest.main()
