import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.core.error_handling.exceptions import (BusinessLogicError,
                                                ResourceNotFoundError,
                                                ValidationError)
from src.db.models.enums import DifficultyLevel
from src.models.lesson import Lesson
from src.services.lesson_service import LessonService


class TestLessonServiceCompletion(unittest.TestCase):
    """Test cases for the lesson completion management functions in the LessonService class."""

    def setUp(self):
        """Set up test fixtures before each test method is called."""
        self.user_id = "11111111-1111-1111-1111-111111111111"
        self.lesson_id = "22222222-2222-2222-2222-222222222222"
        self.course_id = "33333333-3333-3333-3333-333333333333"
        self.content_id1 = "44444444-4444-4444-4444-444444444444"
        self.content_id2 = "55555555-5555-5555-5555-555555555555"

        self.db_lesson = MagicMock(
            id=uuid.UUID(self.lesson_id),
            title="Test Lesson",
            description="Test lesson description",
            lesson_order=1,
            estimated_time=60,
            points_reward=10,
            difficulty_level="INTERMEDIATE",
            course_id=uuid.UUID(self.course_id),
            metadata={},
        )

        self.sample_criteria = {
            "required_content_ids": [self.content_id1, self.content_id2],
            "required_score": 80,
            "required_time_spent": 30,
            "assessment_required": True,
            "prerequisites_required": False,
        }

        self.mock_db = MagicMock()

        self.lesson_service = LessonService()

        self.lesson_repo_mock = MagicMock()
        self.progress_service_mock = MagicMock()

        self.lesson_repo_mock.get_lesson.return_value = self.db_lesson

        self.progress_service_mock.has_completed_content = MagicMock(return_value=True)
        self.progress_service_mock.get_assessment_score = MagicMock(return_value=90)
        self.progress_service_mock.get_time_spent = MagicMock(return_value=60)
        self.progress_service_mock.get_activity_count = MagicMock(return_value=5)
        self.progress_service_mock.has_content_interaction = MagicMock(
            return_value=True
        )

        completed_lesson_mock = MagicMock(id="comp-lesson-1")
        self.progress_service_mock.complete_lesson.return_value = completed_lesson_mock

        self.lesson_service.lesson_repo = self.lesson_repo_mock
        self.lesson_service.progress_service = self.progress_service_mock
        self.lesson_service.db = self.mock_db

    def test_set_completion_criteria(self):
        """Test setting completion criteria for a lesson."""
        updated_lesson = MagicMock()
        updated_lesson.id = self.db_lesson.id
        updated_lesson.title = self.db_lesson.title
        updated_lesson.metadata = {"completion_criteria": self.sample_criteria}

        self.lesson_repo_mock.update_lesson_metadata.return_value = updated_lesson

        mock_transaction_context = MagicMock()
        mock_transaction_context.__enter__ = MagicMock(return_value=self.mock_db)
        mock_transaction_context.__exit__ = MagicMock(return_value=None)
        self.lesson_service.transaction = MagicMock(
            return_value=mock_transaction_context
        )

        result = self.lesson_service.set_completion_criteria(
            lesson_id=self.lesson_id, completion_criteria=self.sample_criteria
        )

        self.assertTrue(result)
        self.lesson_repo_mock.update_lesson_metadata.assert_called_once()

    def test_set_completion_criteria_validation_error(self):
        """Test validation error when setting invalid completion criteria."""
        invalid_criteria = {
            "required_score": 110,
            "assessment_required": True,
        }

        with self.assertRaises(ValidationError):
            self.lesson_service.set_completion_criteria(
                lesson_id=self.lesson_id, completion_criteria=invalid_criteria
            )

    def test_get_completion_criteria(self):
        """Test getting completion criteria for a lesson."""
        self.db_lesson.metadata = {"completion_criteria": self.sample_criteria}
        self.lesson_repo_mock.get_lesson.return_value = self.db_lesson

        mock_transaction_context = MagicMock()
        mock_transaction_context.__enter__ = MagicMock(return_value=self.mock_db)
        mock_transaction_context.__exit__ = MagicMock(return_value=None)
        self.lesson_service.transaction = MagicMock(
            return_value=mock_transaction_context
        )

        result = self.lesson_service.get_completion_criteria(lesson_id=self.lesson_id)

        self.assertEqual(result, self.sample_criteria)

    def test_get_completion_criteria_not_set(self):
        """Test getting completion criteria when not set."""
        self.db_lesson.metadata = {}
        self.lesson_repo_mock.get_lesson.return_value = self.db_lesson

        mock_transaction_context = MagicMock()
        mock_transaction_context.__enter__ = MagicMock(return_value=self.mock_db)
        mock_transaction_context.__exit__ = MagicMock(return_value=None)
        self.lesson_service.transaction = MagicMock(
            return_value=mock_transaction_context
        )

        result = self.lesson_service.get_completion_criteria(lesson_id=self.lesson_id)

        self.assertEqual(result, {})

    def test_check_completion_criteria_no_criteria_set(self):
        """Test checking completion criteria when none are set."""
        self.lesson_service.get_completion_criteria = MagicMock(return_value={})

        result, unmet = self.lesson_service.check_completion_criteria_met(
            user_id=self.user_id, lesson_id=self.lesson_id
        )

        self.assertTrue(result)
        self.assertEqual(len(unmet), 0)
        self.lesson_service.get_completion_criteria.assert_called_once_with(
            self.lesson_id
        )

    def test_check_completion_criteria_met_all_criteria_met(self):
        """Test checking if all completion criteria are met."""
        self.db_lesson.metadata = {"completion_criteria": self.sample_criteria}

        self.progress_service_mock.has_completed_content.return_value = True
        self.progress_service_mock.get_assessment_score.return_value = 85
        self.progress_service_mock.get_time_spent.return_value = 45

        self.lesson_service.check_prerequisites_satisfied = MagicMock(
            return_value=(True, [])
        )
        self.lesson_service.get_completion_criteria = MagicMock(
            return_value=self.sample_criteria
        )

        result, unmet = self.lesson_service.check_completion_criteria_met(
            user_id=self.user_id, lesson_id=self.lesson_id
        )

        self.assertTrue(result)
        self.assertEqual(len(unmet), 0)

    def test_check_completion_criteria_met_some_criteria_not_met(self):
        """Test checking when some completion criteria are not met."""
        self.progress_service_mock.has_completed_content.side_effect = (
            lambda user_id, content_id: content_id == self.content_id1
        )
        self.progress_service_mock.get_assessment_score.return_value = (
            70  # Below required 80
        )
        self.progress_service_mock.get_time_spent.return_value = 45  # Above required 30

        self.lesson_service.check_prerequisites_satisfied = MagicMock(
            return_value=(True, [])
        )
        self.lesson_service.get_completion_criteria = MagicMock(
            return_value=self.sample_criteria
        )

        result, unmet = self.lesson_service.check_completion_criteria_met(
            user_id=self.user_id, lesson_id=self.lesson_id
        )

        self.assertFalse(result)
        self.assertGreater(len(unmet), 0)

    def test_mark_lesson_complete_criteria_met(self):
        """Test marking a lesson as complete when criteria are met."""
        self.lesson_service.check_completion_criteria_met = MagicMock(
            return_value=(True, [])
        )

        ui_lesson = Lesson(
            id=self.lesson_id,
            title=self.db_lesson.title,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            lesson_order=self.db_lesson.lesson_order,
            estimated_time=self.db_lesson.estimated_time,
            points_reward=self.db_lesson.points_reward,
            course_id=self.course_id,
        )
        self.lesson_service.get_lesson_by_id = MagicMock(return_value=ui_lesson)

        result = self.lesson_service.mark_lesson_complete(
            user_id=self.user_id, lesson_id=self.lesson_id
        )

        self.assertTrue(result)
        self.lesson_service.check_completion_criteria_met.assert_called_once_with(
            self.user_id, self.lesson_id
        )
        self.lesson_service.get_lesson_by_id.assert_called_once_with(self.lesson_id)
        self.progress_service_mock.complete_lesson.assert_called_once_with(
            user_id=self.user_id, lesson_id=self.lesson_id, course_id=self.course_id
        )

    def test_mark_lesson_complete_criteria_not_met(self):
        """Test marking a lesson as complete when criteria are not met."""
        unmet_criteria = [
            "Assessment score below required",
            "Content item not completed",
        ]
        self.lesson_service.check_completion_criteria_met = MagicMock(
            return_value=(False, unmet_criteria)
        )

        with self.assertRaises(BusinessLogicError):
            self.lesson_service.mark_lesson_complete(
                user_id=self.user_id, lesson_id=self.lesson_id
            )

        self.lesson_service.check_completion_criteria_met.assert_called_once_with(
            self.user_id, self.lesson_id
        )
        self.progress_service_mock.complete_lesson.assert_not_called()

    def test_mark_lesson_complete_override_criteria(self):
        """Test marking a lesson complete with override_criteria=True."""
        ui_lesson = Lesson(
            id=self.lesson_id,
            title=self.db_lesson.title,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            lesson_order=self.db_lesson.lesson_order,
            estimated_time=self.db_lesson.estimated_time,
            points_reward=self.db_lesson.points_reward,
            course_id=self.course_id,
        )
        self.lesson_service.get_lesson_by_id = MagicMock(return_value=ui_lesson)

        self.lesson_service.check_completion_criteria_met = MagicMock()

        result = self.lesson_service.mark_lesson_complete(
            user_id=self.user_id, lesson_id=self.lesson_id, override_criteria=True
        )

        self.assertTrue(result)
        self.lesson_service.check_completion_criteria_met.assert_not_called()
        self.progress_service_mock.complete_lesson.assert_called_once_with(
            user_id=self.user_id, lesson_id=self.lesson_id, course_id=self.course_id
        )

    def test_validate_completion_criteria_valid(self):
        """Test validation of valid completion criteria."""
        valid_criteria = {
            "required_content_ids": [self.content_id1, self.content_id2],
            "required_score": 80,
            "assessment_required": True,
            "required_time_spent": 30,
        }

        self.lesson_service._validate_completion_criteria(valid_criteria)

    def test_validate_completion_criteria_invalid_format(self):
        """Test validation error with invalid completion criteria format."""
        with self.assertRaises(ValidationError):
            self.lesson_service._validate_completion_criteria("not a dictionary")

        with self.assertRaises(ValidationError):
            self.lesson_service._validate_completion_criteria(
                {"required_score": 150}  # Over 100%
            )

        with self.assertRaises(ValidationError):
            self.lesson_service._validate_completion_criteria(
                {"required_time_spent": -10}  # Negative time
            )

        with self.assertRaises(ValidationError):
            self.lesson_service._validate_completion_criteria(
                {"required_content_ids": ["not-a-uuid"]}
            )


if __name__ == "__main__":
    unittest.main()
