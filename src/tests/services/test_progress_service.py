import logging
import uuid
from datetime import datetime, timezone
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.core.error_handling.exceptions import (DatabaseError,
                                                ResourceNotFoundError,
                                                ValidationError)
from src.db.models import CompletedCourse as DBCompletedCourse
from src.db.models import CompletedLesson as DBCompletedLesson
from src.db.models import ContentState as DBContentState
from src.db.models import Progress as DBProgress
from src.db.models import UserContentProgress as DBUserContentProgress
from src.db.repositories import (CompletedCourseRepository,
                                 CompletedLessonRepository, ContentRepository,
                                 CourseRepository, LessonRepository,
                                 ProgressRepository,
                                 UserContentProgressRepository)
from src.models.progress import (CompletedCourse, CompletedLesson,
                                 ContentState, Progress, UserContentProgress)
from src.services.progress_service import ProgressService
from src.tests.base_test_classes import BaseServiceTest

logger = logging.getLogger(__name__)


class TestProgressService(BaseServiceTest):
    """Tests for ProgressService"""

    def setUp(self):
        """Set up the test environment before each test."""
        self.user_id = str(uuid.uuid4())
        self.course_id = str(uuid.uuid4())
        self.lesson_id = str(uuid.uuid4())
        self.content_id = str(uuid.uuid4())
        self.progress_id = str(uuid.uuid4())
        self.completed_lesson_id = str(uuid.uuid4())

        self.progress_repo_mock = MagicMock(spec=ProgressRepository)
        self.completed_lesson_repo_mock = MagicMock(spec=CompletedLessonRepository)
        self.completed_course_repo_mock = MagicMock(spec=CompletedCourseRepository)
        self.user_content_progress_repo_mock = MagicMock(
            spec=UserContentProgressRepository
        )
        self.lesson_repo_mock = MagicMock(spec=LessonRepository)
        self.course_repo_mock = MagicMock(spec=CourseRepository)
        self.content_repo_mock = MagicMock(spec=ContentRepository)

        self.progress_service = ProgressService()
        self.progress_service.progress_repo = self.progress_repo_mock
        self.progress_service.completed_lesson_repo = self.completed_lesson_repo_mock
        self.progress_service.completed_course_repo = self.completed_course_repo_mock
        self.progress_service.user_content_progress_repo = (
            self.user_content_progress_repo_mock
        )
        self.progress_service.lesson_repo = self.lesson_repo_mock
        self.progress_service.course_repo = self.course_repo_mock
        self.progress_service.content_repo = self.content_repo_mock

        self.mock_db = MagicMock()

        self.progress_service.db = self.mock_db

        self.mock_ui_progress = MagicMock(spec=Progress)
        self.mock_ui_progress.user_id = self.user_id
        self.mock_ui_progress.course_id = self.course_id
        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=self.mock_ui_progress
        )

        # Create mock objects for testing
        self.mock_db_progress = MagicMock(spec=DBProgress)
        self.mock_db_progress.id = uuid.UUID(self.progress_id)
        self.mock_db_progress.user_id = uuid.UUID(self.user_id)
        self.mock_db_progress.course_id = uuid.UUID(self.course_id)

        self.mock_db_completed_lesson = MagicMock(spec=DBCompletedLesson)
        self.mock_db_completed_lesson.id = uuid.uuid4()
        self.mock_db_completed_lesson.user_id = uuid.UUID(self.user_id)
        self.mock_db_completed_lesson.lesson_id = uuid.UUID(self.lesson_id)

        self.mock_db_completed_course = MagicMock(spec=DBCompletedCourse)
        self.mock_db_completed_course.id = uuid.uuid4()
        self.mock_db_completed_course.user_id = uuid.UUID(self.user_id)
        self.mock_db_completed_course.course_id = uuid.UUID(self.course_id)

        self.mock_db_user_content_progress = MagicMock(spec=DBUserContentProgress)
        self.mock_db_user_content_progress.id = uuid.uuid4()
        self.mock_db_user_content_progress.user_id = uuid.UUID(self.user_id)
        self.mock_db_user_content_progress.lesson_id = uuid.UUID(self.lesson_id)
        self.mock_db_user_content_progress.content_id = uuid.UUID(self.content_id)

        for repo_mock in [
            self.progress_repo_mock,
            self.completed_lesson_repo_mock,
            self.completed_course_repo_mock,
            self.user_content_progress_repo_mock,
            self.lesson_repo_mock,
            self.course_repo_mock,
            self.content_repo_mock,
        ]:
            for method_name in dir(repo_mock):
                if not method_name.startswith("_") and callable(
                    getattr(repo_mock, method_name)
                ):
                    method = getattr(repo_mock, method_name)
                    if isinstance(method, MagicMock):
                        method.side_effect = None

    def tearDown(self):
        """Clean up test case."""
        pass

    def test_get_user_progress_success(self):
        mock_progress1 = MagicMock(spec=DBProgress)
        mock_progress1.id = uuid.UUID(self.progress_id)
        mock_progress1.user_id = uuid.UUID(self.user_id)
        mock_progress1.course_id = uuid.UUID(self.course_id)

        mock_progress2 = MagicMock(spec=DBProgress)
        mock_progress2.id = uuid.uuid4()
        mock_progress2.user_id = uuid.UUID(self.user_id)
        mock_progress2.course_id = uuid.uuid4()

        self.progress_repo_mock.get_user_progress.return_value = [
            mock_progress1,
            mock_progress2,
        ]

        mock_ui_progress1 = MagicMock(spec=Progress)
        mock_ui_progress2 = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            side_effect=[mock_ui_progress1, mock_ui_progress2]
        )

        result = self.progress_service.get_user_progress(self.user_id)

        self.progress_repo_mock.get_user_progress.assert_called_once()
        self.assertEqual(len(self.progress_repo_mock.get_user_progress.call_args[0]), 2)
        self.assertEqual(
            self.progress_repo_mock.get_user_progress.call_args[0][1],
            uuid.UUID(self.user_id),
        )
        assert self.progress_service._convert_db_progress_to_ui_progress.call_count == 2
        assert len(result) == 2
        assert result[0] == mock_ui_progress1
        assert result[1] == mock_ui_progress2

    def test_get_user_progress_empty(self):
        """Test getting user progress when there are no records."""
        self.progress_repo_mock.get_user_progress.return_value = []
        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=[]
        )

        result = self.progress_service.get_user_progress(self.user_id)

        self.progress_repo_mock.get_user_progress.assert_called_once()
        self.assertEqual(len(self.progress_repo_mock.get_user_progress.call_args[0]), 2)
        self.assertEqual(
            self.progress_repo_mock.get_user_progress.call_args[0][1],
            uuid.UUID(self.user_id),
        )
        assert len(result) == 0

    def test_get_user_progress_exception(self):
        self.progress_repo_mock.get_user_progress.side_effect = Exception(
            "Database error"
        )

        with self.assertLogs("src.services.progress_service", level="ERROR") as log:
            result = self.progress_service.get_user_progress(self.user_id)

            assert "Error getting user progress: Database error" in log.output[0]

        self.progress_repo_mock.get_user_progress.assert_called_once()
        self.assertEqual(len(self.progress_repo_mock.get_user_progress.call_args[0]), 2)
        self.assertEqual(
            self.progress_repo_mock.get_user_progress.call_args[0][1],
            uuid.UUID(self.user_id),
        )
        assert len(result) == 0

    def test_get_course_progress_success(self):
        """Test getting course progress successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)
        mock_progress.user_id = uuid.UUID(self.user_id)
        mock_progress.course_id = uuid.UUID(self.course_id)

        self.progress_repo_mock.get_course_progress.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        result = self.progress_service.get_course_progress(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_get_course_progress_not_found(self):
        """Test getting course progress when it doesn't exist."""
        self.progress_repo_mock.get_course_progress.return_value = None

        result = self.progress_service.get_course_progress(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        assert result is None

    def test_get_course_progress_exception(self):
        """Test getting course progress when an exception occurs."""
        self.progress_repo_mock.get_course_progress.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.get_course_progress(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        assert result is None

    def test_create_course_progress_success(self):
        """Test creating course progress successfully."""
        mock_course = MagicMock()
        mock_lesson = MagicMock()
        mock_lesson.id = uuid.UUID(self.lesson_id)

        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)
        mock_progress.user_id = uuid.UUID(self.user_id)
        mock_progress.course_id = uuid.UUID(self.course_id)

        self.progress_repo_mock.get_course_progress.return_value = None
        self.course_repo_mock.get_by_id.return_value = mock_course
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [mock_lesson]
        self.progress_repo_mock.create_progress.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        result = self.progress_service.create_course_progress(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.course_repo_mock.get_by_id.assert_called_once_with(
            ANY, uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            ANY, uuid.UUID(self.course_id)
        )
        self.progress_repo_mock.create_progress.assert_called_once_with(
            db=ANY,
            user_id=uuid.UUID(self.user_id),
            course_id=uuid.UUID(self.course_id),
            current_lesson_id=uuid.UUID(self.lesson_id),
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_create_course_progress_already_exists(self):
        """Test creating course progress when it already exists."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)
        mock_progress.user_id = uuid.UUID(self.user_id)
        mock_progress.course_id = uuid.UUID(self.course_id)

        self.progress_repo_mock.get_course_progress.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        result = self.progress_service.create_course_progress(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.course_repo_mock.get_by_id.assert_not_called()
        self.progress_repo_mock.create_progress.assert_not_called()
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_create_course_progress_course_not_found(self):
        """Test creating course progress when the course doesn't exist."""
        self.progress_repo_mock.get_course_progress.return_value = None
        self.course_repo_mock.get_by_id.return_value = None

        result = self.progress_service.create_course_progress(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.course_repo_mock.get_by_id.assert_called_once_with(
            ANY, uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lessons_by_course_id.assert_not_called()
        self.progress_repo_mock.create_progress.assert_not_called()
        assert result is None

    def test_create_course_progress_exception(self):
        """Test creating course progress when an exception occurs."""
        self.progress_repo_mock.get_course_progress.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.create_course_progress(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        assert result is None

    def test_update_progress_percentage_success(self):
        """Test updating progress percentage successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.progress_repo_mock.update_progress_percentage.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        percentage = 75.5
        result = self.progress_service.update_progress_percentage(
            self.progress_id, percentage
        )

        self.progress_repo_mock.update_progress_percentage.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), percentage=percentage
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_update_progress_percentage_not_found(self):
        """Test updating progress percentage when the progress is not found."""
        self.progress_repo_mock.update_progress_percentage.return_value = None

        percentage = 75.5
        result = self.progress_service.update_progress_percentage(
            self.progress_id, percentage
        )

        self.progress_repo_mock.update_progress_percentage.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), percentage=percentage
        )
        assert result is None

    def test_update_progress_percentage_exception(self):
        """Test updating progress percentage when an exception occurs."""
        self.progress_repo_mock.update_progress_percentage.side_effect = Exception(
            "Database error"
        )

        percentage = 75.5
        result = self.progress_service.update_progress_percentage(
            self.progress_id, percentage
        )

        self.progress_repo_mock.update_progress_percentage.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), percentage=percentage
        )
        assert result is None

    def test_update_current_lesson_success(self):
        """Test updating current lesson successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.progress_repo_mock.update_current_lesson.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        result = self.progress_service.update_current_lesson(
            self.progress_id, self.lesson_id
        )

        self.progress_repo_mock.update_current_lesson.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), lesson_id=uuid.UUID(self.lesson_id)
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_update_current_lesson_not_found(self):
        """Test updating current lesson when the progress is not found."""
        self.progress_repo_mock.update_current_lesson.return_value = None

        result = self.progress_service.update_current_lesson(
            self.progress_id, self.lesson_id
        )

        self.progress_repo_mock.update_current_lesson.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), lesson_id=uuid.UUID(self.lesson_id)
        )
        assert result is None

    def test_update_current_lesson_exception(self):
        """Test updating current lesson when an exception occurs."""
        self.progress_repo_mock.update_current_lesson.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.update_current_lesson(
            self.progress_id, self.lesson_id
        )

        self.progress_repo_mock.update_current_lesson.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), lesson_id=uuid.UUID(self.lesson_id)
        )
        assert result is None

    def test_add_points_success(self):
        """Test adding points successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.progress_repo_mock.add_points.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        points = 50
        result = self.progress_service.add_points(self.progress_id, points)

        self.progress_repo_mock.add_points.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), points=points
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_add_points_not_found(self):
        """Test adding points when the progress is not found."""
        self.progress_repo_mock.add_points.return_value = None

        points = 50
        result = self.progress_service.add_points(self.progress_id, points)

        self.progress_repo_mock.add_points.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), points=points
        )
        assert result is None

    def test_add_points_exception(self):
        """Test adding points when an exception occurs."""
        self.progress_repo_mock.add_points.side_effect = Exception("Database error")

        points = 50
        result = self.progress_service.add_points(self.progress_id, points)

        self.progress_repo_mock.add_points.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), points=points
        )
        assert result is None

    def test_add_time_spent_success(self):
        """Test adding time spent successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.progress_repo_mock.add_time_spent.return_value = mock_progress

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        minutes = 30
        result = self.progress_service.add_time_spent(self.progress_id, minutes)

        self.progress_repo_mock.add_time_spent.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), minutes=minutes
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_progress
        )
        assert result == mock_ui_progress

    def test_add_time_spent_not_found(self):
        """Test adding time spent when the progress is not found."""
        self.progress_repo_mock.add_time_spent.return_value = None

        minutes = 30
        result = self.progress_service.add_time_spent(self.progress_id, minutes)

        self.progress_repo_mock.add_time_spent.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), minutes=minutes
        )
        assert result is None

    def test_add_time_spent_exception(self):
        """Test adding time spent when an exception occurs."""
        self.progress_repo_mock.add_time_spent.side_effect = Exception("Database error")

        minutes = 30
        result = self.progress_service.add_time_spent(self.progress_id, minutes)

        self.progress_repo_mock.add_time_spent.assert_called_once_with(
            progress_id=uuid.UUID(self.progress_id), minutes=minutes
        )
        assert result is None

    def test_complete_progress_success(self):
        """Test completing progress successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.progress_repo_mock.mark_as_completed.return_value = mock_progress

        self.progress_service.complete_progress(
            user_id=self.user_id, progress_id=self.progress_id
        )

        self.progress_repo_mock.mark_as_completed.assert_called_once_with(
            uuid.UUID(self.progress_id)
        )

    def test_complete_progress_not_found(self):
        """Test completing progress when the progress is not found."""
        self.progress_repo_mock.mark_as_completed.return_value = None

        self.progress_service.complete_progress(
            user_id=self.user_id, progress_id=self.progress_id
        )

        self.progress_repo_mock.mark_as_completed.assert_called_once_with(
            uuid.UUID(self.progress_id)
        )

    def test_complete_progress_exception(self):
        """Test completing progress when an exception occurs."""
        self.progress_repo_mock.mark_as_completed.side_effect = Exception(
            "Database error"
        )

        with self.assertRaises(Exception):
            self.progress_service.complete_progress(
                user_id=self.user_id, progress_id=self.progress_id
            )

        self.progress_repo_mock.mark_as_completed.assert_called_once_with(
            uuid.UUID(self.progress_id)
        )

    def test_complete_lesson_success(self):
        """Test completing a lesson successfully."""
        mock_completed_lesson = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson.id = uuid.uuid4()
        mock_completed_lesson.user_id = uuid.UUID(self.user_id)
        mock_completed_lesson.lesson_id = uuid.UUID(self.lesson_id)
        mock_completed_lesson.course_id = uuid.UUID(self.course_id)

        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.completed_lesson_repo_mock.is_lesson_completed.return_value = False
        self.completed_lesson_repo_mock.create_completed_lesson.return_value = (
            mock_completed_lesson
        )
        self.progress_repo_mock.get_course_progress.return_value = mock_progress
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [
            MagicMock() for _ in range(10)
        ]
        self.completed_lesson_repo_mock.count_completed_lessons.return_value = 5

        mock_ui_completed_lesson = MagicMock(spec=CompletedLesson)

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson = (
            MagicMock(return_value=mock_ui_completed_lesson)
        )

        score = 95
        time_spent = 45
        result = self.progress_service.complete_lesson(
            self.user_id, self.lesson_id, self.course_id, score, time_spent
        )

        self.completed_lesson_repo_mock.is_lesson_completed.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.lesson_id)
        )
        self.completed_lesson_repo_mock.create_completed_lesson.assert_called_once_with(
            ANY,
            user_id=uuid.UUID(self.user_id),
            lesson_id=uuid.UUID(self.lesson_id),
            course_id=uuid.UUID(self.course_id),
            score=score,
            time_spent=time_spent,
        )
        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            ANY, uuid.UUID(self.course_id)
        )
        self.completed_lesson_repo_mock.count_completed_lessons.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.progress_repo_mock.update_progress_percentage.assert_called_once_with(
            mock_progress.id, 50.0
        )
        self.progress_repo_mock.mark_as_completed.assert_not_called()
        self.completed_course_repo_mock.create_completed_course.assert_not_called()

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson.assert_called_once_with(
            mock_completed_lesson
        )
        assert result == mock_ui_completed_lesson

    def test_complete_lesson_already_completed(self):
        """Test completing a lesson that's already completed."""
        mock_completed_lesson = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson.id = uuid.uuid4()
        mock_completed_lesson.user_id = uuid.UUID(self.user_id)
        mock_completed_lesson.lesson_id = uuid.UUID(self.lesson_id)
        mock_completed_lesson.course_id = uuid.UUID(self.course_id)

        self.completed_lesson_repo_mock.is_lesson_completed.return_value = True
        self.completed_lesson_repo_mock.get_lesson_completion.return_value = (
            mock_completed_lesson
        )

        mock_ui_completed_lesson = MagicMock(spec=CompletedLesson)

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson = (
            MagicMock(return_value=mock_ui_completed_lesson)
        )

        result = self.progress_service.complete_lesson(
            self.user_id, self.lesson_id, self.course_id
        )

        self.completed_lesson_repo_mock.is_lesson_completed.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.lesson_id)
        )
        self.completed_lesson_repo_mock.get_lesson_completion.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.lesson_id)
        )
        self.completed_lesson_repo_mock.create_completed_lesson.assert_not_called()
        self.progress_repo_mock.get_course_progress.assert_not_called()

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson.assert_called_once_with(
            mock_completed_lesson
        )
        assert result == mock_ui_completed_lesson

    def test_complete_lesson_all_lessons_completed(self):
        """Test completing the last lesson in a course."""
        mock_completed_lesson = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson.id = uuid.uuid4()
        mock_completed_lesson.user_id = uuid.UUID(self.user_id)
        mock_completed_lesson.lesson_id = uuid.UUID(self.lesson_id)
        mock_completed_lesson.course_id = uuid.UUID(self.course_id)

        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        self.completed_lesson_repo_mock.is_lesson_completed.return_value = False
        self.completed_lesson_repo_mock.create_completed_lesson.return_value = (
            mock_completed_lesson
        )
        self.progress_repo_mock.get_course_progress.return_value = mock_progress
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [
            MagicMock() for _ in range(10)
        ]
        self.completed_lesson_repo_mock.count_completed_lessons.return_value = (
            10  # All lessons completed
        )

        mock_ui_completed_lesson = MagicMock(spec=CompletedLesson)

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson = (
            MagicMock(return_value=mock_ui_completed_lesson)
        )

        result = self.progress_service.complete_lesson(
            self.user_id, self.lesson_id, self.course_id
        )

        self.completed_lesson_repo_mock.is_lesson_completed.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.lesson_id)
        )
        self.completed_lesson_repo_mock.create_completed_lesson.assert_called_once_with(
            ANY,
            user_id=uuid.UUID(self.user_id),
            lesson_id=uuid.UUID(self.lesson_id),
            course_id=uuid.UUID(self.course_id),
            score=None,
            time_spent=0,
        )
        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            ANY, uuid.UUID(self.course_id)
        )
        self.completed_lesson_repo_mock.count_completed_lessons.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.progress_repo_mock.update_progress_percentage.assert_called_once_with(
            mock_progress.id, 100.0
        )
        self.progress_repo_mock.mark_as_completed.assert_called_once_with(
            mock_progress.id
        )
        self.completed_course_repo_mock.create_completed_course.assert_called_once_with(
            user_id=uuid.UUID(self.user_id), course_id=uuid.UUID(self.course_id)
        )

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson.assert_called_once_with(
            mock_completed_lesson
        )
        assert result == mock_ui_completed_lesson

    def test_complete_lesson_exception(self):
        """Test completing a lesson when an exception occurs."""
        self.completed_lesson_repo_mock.is_lesson_completed.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.complete_lesson(
            self.user_id, self.lesson_id, self.course_id
        )

        self.completed_lesson_repo_mock.is_lesson_completed.assert_called_once_with(
            ANY, uuid.UUID(self.user_id), uuid.UUID(self.lesson_id)
        )
        assert result is None

    def test_get_user_completed_lessons_success(self):
        """Test getting all completed lessons for a user successfully."""
        mock_completed_lesson1 = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson1.id = uuid.uuid4()
        mock_completed_lesson1.user_id = uuid.UUID(self.user_id)

        mock_completed_lesson2 = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson2.id = uuid.uuid4()
        mock_completed_lesson2.user_id = uuid.UUID(self.user_id)

        self.completed_lesson_repo_mock.get_user_completed_lessons.return_value = [
            mock_completed_lesson1,
            mock_completed_lesson2,
        ]

        mock_ui_completed_lesson1 = MagicMock(spec=CompletedLesson)
        mock_ui_completed_lesson2 = MagicMock(spec=CompletedLesson)

        self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson = (
            MagicMock(
                side_effect=[mock_ui_completed_lesson1, mock_ui_completed_lesson2]
            )
        )

        result = self.progress_service.get_user_completed_lessons(self.user_id)

        self.completed_lesson_repo_mock.get_user_completed_lessons.assert_called_once_with(
            uuid.UUID(self.user_id)
        )
        assert (
            self.progress_service._convert_db_completed_lesson_to_ui_completed_lesson.call_count
            == 2
        )
        assert len(result) == 2
        assert result[0] == mock_ui_completed_lesson1
        assert result[1] == mock_ui_completed_lesson2

    def test_get_user_completed_lessons_empty(self):
        """Test getting completed lessons when there are none."""
        self.completed_lesson_repo_mock.get_user_completed_lessons.return_value = []

        result = self.progress_service.get_user_completed_lessons(self.user_id)

        self.completed_lesson_repo_mock.get_user_completed_lessons.assert_called_once_with(
            uuid.UUID(self.user_id)
        )
        assert len(result) == 0

    def test_get_user_completed_lessons_exception(self):
        """Test getting completed lessons when an exception occurs."""
        self.completed_lesson_repo_mock.get_user_completed_lessons.side_effect = (
            Exception("Database error")
        )

        result = self.progress_service.get_user_completed_lessons(self.user_id)

        self.completed_lesson_repo_mock.get_user_completed_lessons.assert_called_once_with(
            uuid.UUID(self.user_id)
        )
        assert len(result) == 0

    def test_calculate_weighted_course_progress_success(self):
        """Test calculating weighted course progress successfully."""
        mock_lesson1 = MagicMock()
        mock_lesson1.id = uuid.uuid4()
        mock_lesson1.lesson_order = 1
        mock_lesson1.difficulty_level.value = 2
        mock_lesson2 = MagicMock()
        mock_lesson2.id = uuid.uuid4()
        mock_lesson2.lesson_order = 2
        mock_lesson2.difficulty_level.value = 3

        mock_content1 = MagicMock()
        mock_content1.id = uuid.uuid4()
        mock_content1.content_type = "theory"
        mock_content1.lesson_id = mock_lesson1.id
        mock_content1.metadata = {"importance": 1.0, "points": 1.0}

        mock_content2 = MagicMock()
        mock_content2.id = uuid.uuid4()
        mock_content2.content_type = "exercise"
        mock_content2.lesson_id = mock_lesson1.id
        mock_content2.metadata = {"importance": 1.5, "points": 1.0}

        mock_content3 = MagicMock()
        mock_content3.id = uuid.uuid4()
        mock_content3.content_type = "quiz"
        mock_content3.lesson_id = mock_lesson2.id
        mock_content3.metadata = {"importance": 2.0, "points": 2.0}

        mock_content_progress1 = MagicMock()
        mock_content_progress1.status = "completed"

        mock_content_progress2 = MagicMock()
        mock_content_progress2.status = "in_progress"
        mock_content_progress2.percentage = 50

        mock_content_progress3 = MagicMock()
        mock_content_progress3.status = "not_started"
        mock_content_progress3.score = None

        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.uuid4()

        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [
            mock_lesson1,
            mock_lesson2,
        ]
        self.lesson_repo_mock.get_lesson_with_content.side_effect = (
            lambda db, lesson_id: {
                mock_lesson1.id: (mock_lesson1, [mock_content1, mock_content2]),
                mock_lesson2.id: (mock_lesson2, [mock_content3]),
            }.get(lesson_id, (None, []))
        )

        self.user_content_progress_repo_mock.get_progress.side_effect = (
            lambda db, user_id, content_id: {
                mock_content1.id: mock_content_progress1,
                mock_content2.id: mock_content_progress2,
                mock_content3.id: mock_content_progress3,
            }.get(content_id, None)
        )

        self.progress_repo_mock.get_course_progress.return_value = mock_progress

        weighted_percentage, details = (
            self.progress_service.calculate_weighted_course_progress(
                self.user_id, self.course_id
            )
        )

        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            self.mock_db, uuid.UUID(self.course_id)
        )
        assert self.lesson_repo_mock.get_lesson_with_content.call_count == 2
        assert self.user_content_progress_repo_mock.get_progress.call_count == 3

        self.progress_repo_mock.update_progress_percentage.assert_called_once()
        self.progress_repo_mock.update_progress_data.assert_called_once()

        assert isinstance(weighted_percentage, float)
        assert 0 <= weighted_percentage <= 100.0
        assert details["status"] == "success"
        assert "details" in details
        assert "completed_count" in details["details"]
        assert "total_count" in details["details"]
        assert "completion_ratio" in details["details"]
        assert "content_weights" in details["details"]
        assert "lesson_weights" in details["details"]

    def test_calculate_weighted_course_progress_no_lessons(self):
        """Test calculating weighted course progress when there are no lessons."""
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = []

        weighted_percentage, details = (
            self.progress_service.calculate_weighted_course_progress(
                self.user_id, self.course_id
            )
        )

        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            self.mock_db, uuid.UUID(self.course_id)
        )

        self.lesson_repo_mock.get_lesson_with_content.assert_not_called()
        self.user_content_progress_repo_mock.get_progress.assert_not_called()
        self.progress_repo_mock.update_progress_percentage.assert_not_called()
        self.progress_repo_mock.update_progress_data.assert_not_called()

        assert weighted_percentage == 0.0
        assert details["status"] == "no_lessons"

    def test_calculate_weighted_course_progress_no_content(self):
        """Test calculating weighted progress when there is no content in lessons."""
        mock_lesson = MagicMock()
        mock_lesson.id = uuid.uuid4()

        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [mock_lesson]
        self.lesson_repo_mock.get_lesson_with_content.return_value = (mock_lesson, [])

        weighted_percentage, details = (
            self.progress_service.calculate_weighted_course_progress(
                self.user_id, self.course_id
            )
        )

        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            self.mock_db, uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lesson_with_content.assert_called_once_with(
            self.mock_db, mock_lesson.id
        )

        self.user_content_progress_repo_mock.get_progress.assert_not_called()

        assert weighted_percentage == 0.0
        assert details["status"] == "no_content"

    def test_calculate_weighted_course_progress_exception(self):
        """Test calculating weighted progress when an exception occurs."""
        self.lesson_repo_mock.get_lessons_by_course_id.side_effect = Exception(
            "Database error"
        )

        weighted_percentage, details = (
            self.progress_service.calculate_weighted_course_progress(
                self.user_id, self.course_id
            )
        )

        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            self.mock_db, uuid.UUID(self.course_id)
        )

        assert weighted_percentage == 0.0
        assert details["status"] == "error"
        assert "message" in details

    def test_update_course_progress_with_weighting_success(self):
        """Test updating course progress with weighting successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)

        mock_updated_progress = MagicMock(spec=DBProgress)
        mock_updated_progress.id = uuid.UUID(self.progress_id)

        mock_ui_progress = MagicMock(spec=Progress)

        self.progress_repo_mock.get_course_progress.side_effect = [
            mock_progress,
            mock_updated_progress,
        ]
        self.progress_service.calculate_weighted_course_progress = MagicMock(
            return_value=(75.5, {"status": "success", "details": {}})
        )
        self.progress_service._convert_db_progress_to_ui_progress = MagicMock(
            return_value=mock_ui_progress
        )

        result = self.progress_service.update_course_progress_with_weighting(
            self.user_id, self.course_id
        )

        assert self.progress_repo_mock.get_course_progress.call_count == 2
        self.progress_service.calculate_weighted_course_progress.assert_called_once_with(
            self.user_id, self.course_id
        )
        self.progress_service._convert_db_progress_to_ui_progress.assert_called_once_with(
            mock_updated_progress
        )

        assert result == mock_ui_progress

    def test_update_course_progress_with_weighting_create_new(self):
        """Test updating course progress with weighting when no progress record exists."""
        self.progress_repo_mock.get_course_progress.return_value = None

        mock_created_progress = MagicMock(spec=Progress)
        self.progress_service.create_course_progress = MagicMock(
            return_value=mock_created_progress
        )

        self.progress_service.calculate_weighted_course_progress = MagicMock(
            return_value=(0.0, {"status": "no_lessons", "details": {}})
        )

        result = self.progress_service.update_course_progress_with_weighting(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            self.mock_db, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.progress_service.create_course_progress.assert_called_once_with(
            self.user_id, self.course_id
        )
        self.progress_service.calculate_weighted_course_progress.assert_called_once_with(
            self.user_id, self.course_id
        )

        assert result is None

    def test_update_course_progress_with_weighting_exception(self):
        """Test updating course progress with weighting when an exception occurs."""
        self.progress_repo_mock.get_course_progress.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.update_course_progress_with_weighting(
            self.user_id, self.course_id
        )

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            self.mock_db, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )

        assert result is None

    def test_sync_progress_data_success(self):
        """Test synchronizing progress data successfully."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)
        mock_progress.is_completed = False

        mock_lesson1 = MagicMock()
        mock_lesson1.id = uuid.uuid4()

        mock_lesson2 = MagicMock()
        mock_lesson2.id = uuid.uuid4()

        mock_completed_lesson = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson.lesson_id = mock_lesson1.id

        mock_content1 = MagicMock()
        mock_content1.id = uuid.uuid4()

        mock_content2 = MagicMock()
        mock_content2.id = uuid.uuid4()

        mock_content_progress1 = MagicMock(spec=DBUserContentProgress)
        mock_content_progress1.time_spent = 30
        mock_content_progress1.score = 80

        mock_content_progress2 = MagicMock(spec=DBUserContentProgress)
        mock_content_progress2.time_spent = 45
        mock_content_progress2.score = 90

        self.progress_repo_mock.get_course_progress.return_value = mock_progress
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [
            mock_lesson1,
            mock_lesson2,
        ]
        self.completed_lesson_repo_mock.get_course_completed_lessons.return_value = [
            mock_completed_lesson
        ]
        self.completed_course_repo_mock.get_course_completion.return_value = None

        self.lesson_repo_mock.get_lesson_with_content.side_effect = (
            lambda db, lesson_id: {
                mock_lesson1.id: (mock_lesson1, [mock_content1]),
                mock_lesson2.id: (mock_lesson2, [mock_content2]),
            }.get(lesson_id, (None, []))
        )

        self.user_content_progress_repo_mock.get_progress.side_effect = (
            lambda db, user_id, content_id: {
                mock_content1.id: mock_content_progress1,
                mock_content2.id: mock_content_progress2,
            }.get(content_id, None)
        )

        self.progress_service.calculate_total_time_spent = MagicMock(return_value=75)

        self.progress_service.calculate_weighted_course_progress = MagicMock(
            return_value=(50.0, {"status": "success", "details": {}})
        )

        result = self.progress_service.sync_progress_data(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once()
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once()
        self.completed_lesson_repo_mock.get_course_completed_lessons.assert_called_once()
        assert self.lesson_repo_mock.get_lesson_with_content.call_count == 2
        assert self.user_content_progress_repo_mock.get_progress.call_count >= 2

        assert self.progress_repo_mock.update_progress_data.call_count >= 1
        self.completed_course_repo_mock.get_course_completion.assert_called_once()

        assert result is True

    def test_sync_progress_data_course_completed(self):
        """Test synchronizing progress data when all lessons are completed."""
        mock_progress = MagicMock(spec=DBProgress)
        mock_progress.id = uuid.UUID(self.progress_id)
        mock_progress.is_completed = False

        mock_lesson = MagicMock()
        mock_lesson.id = uuid.uuid4()

        mock_completed_lesson = MagicMock(spec=DBCompletedLesson)
        mock_completed_lesson.lesson_id = mock_lesson.id

        self.progress_repo_mock.get_course_progress.return_value = mock_progress
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = [mock_lesson]
        self.completed_lesson_repo_mock.get_course_completed_lessons.return_value = [
            mock_completed_lesson
        ]
        self.completed_course_repo_mock.get_course_completion.return_value = None
        self.lesson_repo_mock.get_lesson_with_content.return_value = (mock_lesson, [])

        self.progress_repo_mock.update_progress_data.return_value = mock_progress

        self.progress_repo_mock.complete_progress = MagicMock()

        self.progress_service.calculate_weighted_course_progress = MagicMock(
            return_value=(100.0, {"status": "success", "details": {}})
        )

        result = self.progress_service.sync_progress_data(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once()
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once()
        self.completed_lesson_repo_mock.get_course_completed_lessons.assert_called_once()

        self.progress_repo_mock.update_progress_data.assert_called()
        self.progress_repo_mock.complete_progress.assert_called_once()

        assert result is True

    def test_sync_progress_data_no_progress(self):
        """Test synchronizing progress data when there is no progress record."""
        self.progress_repo_mock.get_course_progress.return_value = None

        result = self.progress_service.sync_progress_data(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            self.mock_db, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )

        self.lesson_repo_mock.get_lessons_by_course_id.assert_not_called()

        assert result is False

    def test_sync_progress_data_no_lessons(self):
        """Test synchronizing progress data when there are no lessons."""
        mock_progress = MagicMock(spec=DBProgress)

        self.progress_repo_mock.get_course_progress.return_value = mock_progress
        self.lesson_repo_mock.get_lessons_by_course_id.return_value = []

        result = self.progress_service.sync_progress_data(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            self.mock_db, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )
        self.lesson_repo_mock.get_lessons_by_course_id.assert_called_once_with(
            self.mock_db, uuid.UUID(self.course_id)
        )

        assert result is False

    def test_sync_progress_data_exception(self):
        """Test synchronizing progress data when an exception occurs."""
        self.progress_repo_mock.get_course_progress.side_effect = Exception(
            "Database error"
        )

        result = self.progress_service.sync_progress_data(self.user_id, self.course_id)

        self.progress_repo_mock.get_course_progress.assert_called_once_with(
            self.mock_db, uuid.UUID(self.user_id), uuid.UUID(self.course_id)
        )

        self.mock_db.rollback.assert_called_once()

        assert result is False

    def test_get_all_progress_exception(self):
        """Test getting all progress when an exception occurs."""
        # Mock the transaction to raise an exception
        self.progress_service.transaction = MagicMock(
            side_effect=Exception("Database error")
        )

        result = self.progress_service.get_all_progress()

        assert result == []
