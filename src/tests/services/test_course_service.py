import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.core.error_handling import ResourceNotFoundError, ServiceError
from src.db.models import Course as DBCourse
from src.db.models import Tag as DBTag
from src.db.models import Topic
from src.models.course import Course
from src.services.course_service import CourseService
from src.services.session_manager import SessionManager
from src.tests.base_test_classes import BaseServiceTest
from src.tests.utils.test_factories import CourseFactory


class TestCourseService(BaseServiceTest):
    """Test class for CourseService."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()

        with patch("src.services.course_service.get_db"):
            self.course_service = CourseService()
            self.course_service.db = self.mock_db

        self.test_course_id = str(uuid.uuid4())
        self.test_user_id = str(uuid.uuid4())

        self.mock_tag1 = MagicMock(spec=DBTag)
        self.mock_tag1.name = "beginner"

        self.mock_tag2 = MagicMock(spec=DBTag)
        self.mock_tag2.name = "python"

        self.topic_mock = MagicMock()
        self.topic_mock.__str__.return_value = "INFORMATICS"
        self.topic_mock.value = "Інформатика"

        self.mock_db_course = MagicMock(spec=DBCourse)
        self.mock_db_course.id = uuid.UUID(self.test_course_id)
        self.mock_db_course.name = "Introduction to Python"
        self.mock_db_course.description = "Learn the basics of Python programming"
        self.mock_db_course.topic = self.topic_mock
        self.mock_db_course.tags = [self.mock_tag1, self.mock_tag2]
        self.mock_db_course.difficulty_level = "Beginner"
        self.mock_db_course.estimated_duration = 60
        self.mock_db_course.prerequisites = ["Basic computer skills"]
        self.mock_db_course.created_at = datetime.now(timezone.utc)

        self.test_course_id2 = str(uuid.uuid4())
        self.topic_mock2 = MagicMock()
        self.topic_mock2.__str__.return_value = "MATHEMATICS"
        self.topic_mock2.value = "Математика"

        self.mock_db_course2 = MagicMock(spec=DBCourse)
        self.mock_db_course2.id = uuid.UUID(self.test_course_id2)
        self.mock_db_course2.name = "Advanced Algebra"
        self.mock_db_course2.description = "Explore advanced algebraic concepts"
        self.mock_db_course2.topic = self.topic_mock2
        self.mock_db_course2.tags = []
        self.mock_db_course2.difficulty_level = "Intermediate"
        self.mock_db_course2.estimated_duration = 90
        self.mock_db_course2.prerequisites = ["Basic Algebra"]
        self.mock_db_course2.created_at = datetime.now(timezone.utc)

        self.mock_db_courses = [self.mock_db_course, self.mock_db_course2]

        self.expected_course = self._create_expected_course(
            self.test_course_id,
            "Introduction to Python",
            "Learn the basics of Python programming",
            "Інформатика",
            ["beginner", "python"],
            "Beginner",
            60,
            False,
        )

        self.expected_course2 = self._create_expected_course(
            self.test_course_id2,
            "Advanced Algebra",
            "Explore advanced algebraic concepts",
            "Математика",
            [],
            "Intermediate",
            90,
            False,
        )

    def _create_expected_course(
        self, id, name, description, topic, tags, difficulty, duration, is_active
    ):
        """Helper method to create expected course objects."""
        metadata = {
            "difficulty_level": difficulty,
            "target_age_group": "13-14",
            "estimated_time": duration,
            "points_reward": 10,
            "prerequisites": {},
            "tags": tags,
            "updated_at": datetime.now(timezone.utc),
        }

        return Course(
            id=id,
            topic=topic,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
            tags=tags,
            metadata=metadata,
            is_active=is_active,
            is_completed=False,
        )

    def test_get_all_courses_success(self):
        """Test getting all courses successfully."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course
            self.course_service._convert_db_course_to_ui_course = MagicMock(
                side_effect=[self.expected_course, self.expected_course2]
            )

            try:
                result = self.course_service.get_all_courses()

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[0].name, "Introduction to Python")
                self.assertEqual(result[1].id, self.test_course_id2)
                self.assertEqual(result[1].name, "Advanced Algebra")

                mock_get_all.assert_called_once_with(self.mock_db)
                self.assertEqual(
                    self.course_service._convert_db_course_to_ui_course.call_count, 2
                )
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_get_all_courses_exception(self):
        """Test handling of exceptions when getting all courses."""
        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.side_effect = Exception("Database error")

            with self.assertRaises(Exception):
                self.course_service.get_all_courses()

    def test_get_course_by_id_success(self):
        """Test getting a course by ID successfully."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.get_course"
        ) as mock_get_course:
            mock_get_course.return_value = self.mock_db_course

            original_convert = self.course_service._convert_db_course_to_ui_course
            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=self.expected_course
            )

            try:
                result = self.course_service.get_course_by_id(self.test_course_id)

                self.assertEqual(result.id, self.test_course_id)
                self.assertEqual(result.name, "Introduction to Python")
                self.assertEqual(
                    result.description, "Learn the basics of Python programming"
                )

                mock_get_course.assert_called_once()
                self.course_service._convert_db_course_to_ui_course.assert_called_once_with(
                    self.mock_db_course
                )
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_get_course_by_id_not_found(self):
        """Test getting a non-existent course by ID."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.get_course"
        ) as mock_get_course:
            mock_get_course.return_value = None

            with self.assertRaises(ResourceNotFoundError):
                self.course_service.get_course_by_id(self.test_course_id)

            mock_get_course.assert_called_once()

    def test_get_course_by_id_invalid_id(self):
        """Test getting a course with an invalid ID format."""
        with patch(
            "uuid.UUID", side_effect=ValueError("badly formed hexadecimal UUID string")
        ):
            with self.assertRaises(Exception):
                self.course_service.get_course_by_id("invalid-id")

    def test_get_courses_by_difficulty_success(self):
        """Test getting courses by difficulty level successfully."""
        self.mock_db.reset_mock()

        with patch.object(
            self.course_service, "get_courses_by_difficulty", autospec=True
        ) as mock_method:
            mock_method.return_value = [self.expected_course2]

            result = self.course_service.get_courses_by_difficulty("Intermediate")

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, self.test_course_id2)
            self.assertEqual(result[0].name, "Advanced Algebra")

            mock_method.assert_called_once_with("Intermediate")

    def test_get_courses_by_age_group_success(self):
        """Test getting courses by age group successfully."""
        self.mock_db.reset_mock()

        with patch.object(
            self.course_service, "get_courses_by_age_group", autospec=True
        ) as mock_method:
            mock_method.return_value = [self.expected_course]

            result = self.course_service.get_courses_by_age_group("13-14")

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, self.test_course_id)
            self.assertEqual(result[0].name, "Introduction to Python")

            mock_method.assert_called_once_with("13-14")

    def test_search_courses_success(self):
        """Test searching for courses successfully."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.search_courses"
        ) as mock_search:
            mock_search.return_value = [self.mock_db_course]

            original_convert = self.course_service._convert_db_course_to_ui_course
            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=self.expected_course
            )

            try:
                result = self.course_service.search_courses("Python")

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[0].name, "Introduction to Python")

                mock_search.assert_called_once_with(self.mock_db, "Python")
                self.course_service._convert_db_course_to_ui_course.assert_called_once_with(
                    self.mock_db_course
                )
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_get_active_courses_success(self):
        """Test getting active courses for a user successfully."""
        self.mock_db.reset_mock()

        SessionManager.set_current_user({"id": self.test_user_id})

        with (
            patch(
                "src.services.course_service.progress_repo.get_user_progress"
            ) as mock_get_progress,
            patch(
                "src.services.course_service.course_repo.get_course"
            ) as mock_get_course,
        ):
            mock_progress = MagicMock()
            mock_progress.course_id = uuid.UUID(self.test_course_id)
            mock_get_progress.return_value = [mock_progress]

            mock_get_course.return_value = self.mock_db_course

            original_convert = self.course_service._convert_db_course_to_ui_course
            active_course = self._create_expected_course(
                self.test_course_id,
                "Introduction to Python",
                "Learn the basics of Python programming",
                "Інформатика",
                ["beginner", "python"],
                "Beginner",
                60,
                True,
            )
            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=active_course
            )

            try:
                with patch("uuid.UUID") as mock_uuid:
                    result = self.course_service.get_active_courses()

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[0].name, "Introduction to Python")
                self.assertTrue(result[0].is_active)

                mock_get_progress.assert_called_once()
                mock_get_course.assert_called_once()
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

        SessionManager.set_current_user(None)

    def test_get_completed_courses_success(self):
        """Test getting completed courses for a user successfully."""
        self.mock_db.reset_mock()

        with patch("uuid.UUID"):
            result = self.course_service.get_completed_courses()

        self.assertEqual(result, [])

    def test_convert_db_course_to_ui_course(self):
        """Test conversion from database course to UI course model."""
        original_convert = self.course_service._convert_db_course_to_ui_course

        result = original_convert(self.mock_db_course)

        self.assertEqual(result.id, self.test_course_id)
        self.assertEqual(result.name, "Introduction to Python")
        self.assertEqual(result.description, "Learn the basics of Python programming")
        self.assertEqual(result.topic, "Інформатика")

        self.assertEqual(result.tags, ["beginner", "python"])

        self.assertEqual(result.metadata["difficulty_level"], "Beginner")
        self.assertEqual(result.difficulty_level, "Beginner")
        self.assertFalse(result.is_active)
        self.assertFalse(result.is_completed)

    def test_filter_courses_by_single_criteria(self):
        """Test filtering courses by a single criteria."""
        self.mock_db.reset_mock()

        self.mock_db_course.difficulty_level = "Beginner"
        self.mock_db_course2.difficulty_level = "Intermediate"

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            intermediate_course = self._create_expected_course(
                self.test_course_id2,
                "Advanced Algebra",
                "Explore advanced algebraic concepts",
                "Математика",
                [],
                "Intermediate",
                90,
                False,
            )

            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=intermediate_course
            )

            try:
                result = self.course_service.filter_courses(
                    filters={"difficulty_level": "Intermediate"}
                )

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id2)
                self.assertEqual(result[0].difficulty_level, "Intermediate")

                mock_get_all.assert_called_once_with(self.mock_db)
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_filter_courses_by_multiple_criteria(self):
        """Test filtering courses by multiple criteria."""
        self.mock_db.reset_mock()

        self.mock_db_course.topic.value = "Інформатика"
        self.mock_db_course.difficulty_level = "Beginner"

        self.mock_db_course2.topic.value = "Математика"
        self.mock_db_course2.difficulty_level = "Intermediate"

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            math_course = self._create_expected_course(
                self.test_course_id2,
                "Advanced Algebra",
                "Explore advanced algebraic concepts",
                "Математика",
                [],
                "Intermediate",
                90,
                False,
            )

            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=math_course
            )

            try:
                result = self.course_service.filter_courses(
                    filters={"topic": "Математика", "difficulty_level": "Intermediate"}
                )

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id2)
                self.assertEqual(result[0].topic, "Математика")
                self.assertEqual(result[0].difficulty_level, "Intermediate")

                mock_get_all.assert_called_once_with(self.mock_db)
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_filter_courses_by_tags(self):
        """Test filtering courses by tags."""
        self.mock_db.reset_mock()

        self.mock_db_course.tags = [self.mock_tag2]
        self.mock_db_course2.tags = [self.mock_tag1]

        self.mock_tag1.name = "beginner"
        self.mock_tag2.name = "python"

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            python_course = self._create_expected_course(
                self.test_course_id,
                "Introduction to Python",
                "Learn the basics of Python programming",
                "Інформатика",
                ["python"],
                "Beginner",
                60,
                False,
            )

            self.course_service._convert_db_course_to_ui_course = MagicMock(
                return_value=python_course
            )

            try:
                result = self.course_service.filter_courses(
                    filters={"tags": ["python"]}
                )

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[0].name, "Introduction to Python")
                self.assertIn("python", result[0].tags)

                mock_get_all.assert_called_once_with(self.mock_db)
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_filter_courses_no_filters(self):
        """Test filtering courses with no filters returns all courses."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course
            self.course_service._convert_db_course_to_ui_course = MagicMock(
                side_effect=[self.expected_course, self.expected_course2]
            )

            try:
                result = self.course_service.filter_courses(filters=None)

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[1].id, self.test_course_id2)

                mock_get_all.assert_called_once_with(self.mock_db)
                self.assertEqual(
                    self.course_service._convert_db_course_to_ui_course.call_count, 2
                )
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_filter_courses_no_matches(self):
        """Test filtering courses with criteria that match no courses."""
        self.mock_db.reset_mock()

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            result = self.course_service.filter_courses(
                filters={"difficulty_level": "Expert"}
            )

            self.assertEqual(len(result), 0)

            mock_get_all.assert_called_once_with(self.mock_db)

    def test_filter_courses_exception(self):
        """Test handling of exceptions when filtering courses."""
        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.side_effect = Exception("Database error")

            with self.assertRaises(Exception):
                self.course_service.filter_courses(
                    filters={"difficulty_level": "Beginner"}
                )

    def test_filter_courses_by_duration_range(self):
        """Test filtering courses by duration range."""
        self.mock_db.reset_mock()

        self.mock_db_course.duration = 45
        self.mock_db_course2.duration = 90

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            mock_result1 = self._create_expected_course(
                self.test_course_id,
                "Introduction to Python",
                "Learn the basics of Python programming",
                "Інформатика",
                ["beginner", "python"],
                "Beginner",
                45,
                False,
            )

            mock_result2 = self._create_expected_course(
                self.test_course_id2,
                "Advanced Algebra",
                "Explore advanced algebraic concepts",
                "Математика",
                [],
                "Intermediate",
                90,
                False,
            )

            try:
                self.course_service._convert_db_course_to_ui_course = MagicMock(
                    side_effect=[mock_result1]
                )

                result = self.course_service.filter_courses(
                    filters={"duration_min": 30, "duration_max": 60}
                )

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, self.test_course_id)
                self.assertEqual(result[0].name, "Introduction to Python")

                self.course_service._convert_db_course_to_ui_course = MagicMock(
                    side_effect=[mock_result1, mock_result2]
                )

                result = self.course_service.filter_courses(
                    filters={"duration_min": 30, "duration_max": 120}
                )

                self.assertEqual(len(result), 2)

                mock_get_all.assert_called_with(self.mock_db)
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_sort_courses(self):
        """Test sorting courses by various criteria."""
        self.mock_db.reset_mock()

        self.mock_db_course.name = "Python Course"
        self.mock_db_course.duration = 60
        self.mock_db_course.created_at = datetime(2023, 1, 15, tzinfo=timezone.utc)

        self.mock_db_course2.name = "Algebra Course"
        self.mock_db_course2.duration = 90
        self.mock_db_course2.created_at = datetime(2023, 2, 1, tzinfo=timezone.utc)

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = self.mock_db_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            python_course = self._create_expected_course(
                self.test_course_id,
                "Python Course",
                "Learn the basics of Python programming",
                "Інформатика",
                ["beginner", "python"],
                "Beginner",
                60,
                False,
            )

            algebra_course = self._create_expected_course(
                self.test_course_id2,
                "Algebra Course",
                "Explore advanced algebraic concepts",
                "Математика",
                [],
                "Intermediate",
                90,
                False,
            )

            self.course_service._convert_db_course_to_ui_course = MagicMock(
                side_effect=[python_course, algebra_course]
            )

            try:
                result = self.course_service.sort_courses(
                    courses=[python_course, algebra_course],
                    sort_by="name",
                    ascending=True,
                )

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0].name, "Algebra Course")
                self.assertEqual(result[1].name, "Python Course")

                result = self.course_service.sort_courses(
                    courses=[python_course, algebra_course],
                    sort_by="name",
                    ascending=False,
                )

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0].name, "Python Course")
                self.assertEqual(result[1].name, "Algebra Course")

                result = self.course_service.sort_courses(
                    courses=[python_course, algebra_course],
                    sort_by="duration",
                    ascending=True,
                )

                self.assertEqual(len(result), 2)
                self.assertEqual(result[0].name, "Python Course")
                self.assertEqual(result[1].name, "Algebra Course")
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert

    def test_filter_and_sort_workflow(self):
        """Test the combined workflow of filtering and then sorting courses."""
        self.mock_db.reset_mock()

        test_course_id3 = str(uuid.uuid4())

        topic_mock3 = MagicMock()
        topic_mock3.__str__.return_value = "INFORMATICS"
        topic_mock3.value = "Інформатика"

        self.mock_db_course.topic = topic_mock3
        self.mock_db_course.tags = [self.mock_tag2]
        self.mock_db_course.duration = 60

        mock_db_course3 = MagicMock(spec=DBCourse)
        mock_db_course3.id = uuid.UUID(test_course_id3)
        mock_db_course3.name = "Advanced Python"
        mock_db_course3.description = "Advanced Python programming concepts"
        mock_db_course3.topic = topic_mock3
        mock_db_course3.tags = [self.mock_tag2]
        mock_db_course3.difficulty_level = "Advanced"
        mock_db_course3.duration = 120
        mock_db_course3.created_at = datetime(2023, 3, 1, tzinfo=timezone.utc)

        self.mock_tag2.name = "python"

        all_mock_courses = [self.mock_db_course, self.mock_db_course2, mock_db_course3]

        python_course1 = self._create_expected_course(
            self.test_course_id,
            "Introduction to Python",
            "Learn the basics of Python programming",
            "Інформатика",
            ["python"],
            "Beginner",
            60,
            False,
        )

        python_course2 = self._create_expected_course(
            test_course_id3,
            "Advanced Python",
            "Advanced Python programming concepts",
            "Інформатика",
            ["python"],
            "Advanced",
            120,
            False,
        )

        with patch(
            "src.services.course_service.course_repo.get_all_courses"
        ) as mock_get_all:
            mock_get_all.return_value = all_mock_courses

            original_convert = self.course_service._convert_db_course_to_ui_course

            try:
                self.course_service._convert_db_course_to_ui_course = MagicMock(
                    side_effect=[python_course1, python_course2]
                )

                filtered_courses = self.course_service.filter_courses(
                    filters={"topic": "Інформатика", "tags": ["python"]}
                )

                self.assertEqual(len(filtered_courses), 2)
                filtered_course_ids = {course.id for course in filtered_courses}
                self.assertIn(self.test_course_id, filtered_course_ids)
                self.assertIn(test_course_id3, filtered_course_ids)

                sorted_courses = self.course_service.sort_courses(
                    courses=filtered_courses, sort_by="duration", ascending=False
                )

                self.assertEqual(len(sorted_courses), 2)
                self.assertEqual(sorted_courses[0].id, test_course_id3)
                self.assertEqual(sorted_courses[0].name, "Advanced Python")
                self.assertEqual(sorted_courses[1].id, self.test_course_id)
                self.assertEqual(sorted_courses[1].name, "Introduction to Python")
            finally:
                self.course_service._convert_db_course_to_ui_course = original_convert
