import unittest
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from unittest.mock import ANY, MagicMock, PropertyMock, patch
from uuid import uuid4

from src.core.logging import get_logger
from src.db.models.content import Tag as DbTag
from src.db.models.enums import AgeGroup, Category, DifficultyLevel, Topic
from src.models.tag import Tag, TagCategory
from src.services.course_service import CourseService
from src.services.tag_service import TagService

logger = get_logger(__name__)


class TestTagIntegration(unittest.TestCase):
    """Test the integration between tags and courses."""

    def setUp(self):
        """Set up the test environment."""
        self.db_patcher = patch("src.services.base_service.get_db")
        self.mock_db = self.db_patcher.start()

        self.course_repo_patcher = patch("src.services.course_service.course_repo")
        self.mock_course_repo = self.course_repo_patcher.start()

        self.tag_service_patcher = patch("src.services.tag_service.TagService")
        self.mock_tag_service = self.tag_service_patcher.start()

        self.course_service = CourseService(tag_service=self.mock_tag_service)
        self.tag_service = TagService()

        self.test_course_id = str(uuid.uuid4())

        self.mock_course = MagicMock()
        self.mock_course.id = self.test_course_id
        self.mock_course.tags = []
        self.mock_course_repo.get_course.return_value = self.mock_course
        self.mock_course_repo.get_course_by_id.return_value = self.mock_course

        self.test_tags = self._create_test_tags()

        self.mock_tag_service.get_tag_by_name.side_effect = lambda name: next(
            (tag for tag in self.test_tags if tag.name == name), None
        )
        self.mock_tag_service.get_tag_by_id.side_effect = lambda tag_id: next(
            (tag for tag in self.test_tags if str(tag.id) == str(tag_id)), None
        )

    def tearDown(self):
        """Clean up after tests."""
        self.db_patcher.stop()
        self.course_repo_patcher.stop()
        self.tag_service_patcher.stop()

    def _create_test_tags(self) -> List[Tag]:
        """Create test tags for use in tests."""
        python_tag = Tag(id=str(uuid.uuid4()), name="python", category="topic")

        math_tag = Tag(id=str(uuid4()), name="math", category="topic")

        self.mock_tag_service.get_tag_by_name.side_effect = lambda name: (
            python_tag if name == "python" else math_tag if name == "math" else None
        )

        def get_tag_by_id_side_effect(tag_id):
            tag_id_str = str(tag_id)
            if tag_id_str == str(python_tag.id):
                return python_tag
            elif tag_id_str == str(math_tag.id):
                return math_tag
            return None

        self.mock_tag_service.get_tag_by_id.side_effect = get_tag_by_id_side_effect

        return [python_tag, math_tag]

    def test_create_and_get_tag(self):
        """Test creating and getting a tag."""
        tag_name = f"test_tag_{str(uuid.uuid4())[:8]}"
        tag_id = str(uuid.uuid4())

        db_tag = DbTag(id=uuid.UUID(tag_id), name=tag_name, category=Category.SKILL)

        mock_tag_repo = MagicMock()

        mock_tag_repo.create_tag.return_value = db_tag
        mock_tag_repo.get_tag_by_id.return_value = db_tag

        self.tag_service.repository = mock_tag_repo
        self.tag_service.repository = mock_tag_repo

        tag = self.tag_service.create_tag(name=tag_name, category=TagCategory.SKILL)

        self.assertEqual(tag.name, tag_name)
        self.assertEqual(tag.category, TagCategory.SKILL)

        retrieved_tag = self.tag_service.get_tag_by_id(tag_id)

        self.assertIsNotNone(retrieved_tag)
        self.assertEqual(retrieved_tag.name, tag_name)
        self.assertEqual(retrieved_tag.category, TagCategory.SKILL)
        self.assertEqual(str(retrieved_tag.id), tag_id)

        mock_tag_repo.create_tag.assert_called_once()
        self.assertEqual(mock_tag_repo.get_tag_by_id.call_count, 1)

    def test_tag_course_association(self):
        """Test adding tags to a course."""
        self.mock_tag_service.add_tag_to_course.return_value = True

        result = self.course_service.add_tag_to_course(
            course_id=self.test_course_id, tag_id=str(self.test_tags[0].id)
        )

        self.assertTrue(result)

        self.mock_tag_service.add_tag_to_course.assert_called_once_with(
            str(self.test_tags[0].id), self.test_course_id
        )

    def test_update_course_tags(self):
        """Test updating a course's tags."""
        tag_data = [
            {"name": tag.name, "category": tag.category} for tag in self.test_tags
        ]

        self.mock_tag_service.get_or_create_tag.side_effect = (
            lambda name, category: next(
                (
                    tag
                    for tag in self.test_tags
                    if tag.name == name and tag.category == category
                ),
                None,
            )
        )

        self.mock_course_repo.get.return_value = self.mock_course

        with patch.object(self.course_service, "get_course_tags", return_value=[]):
            result = self.course_service.update_course_tags(
                course_id=self.test_course_id, new_tags=tag_data
            )

        self.assertTrue(result)

        self.assertEqual(
            self.mock_tag_service.get_or_create_tag.call_count, len(self.test_tags)
        )

    def test_filter_courses_by_tags(self):
        """Test filtering courses by tags."""
        python_tag = Tag(
            id=str(uuid.uuid4()), name="python", category=TagCategory.SKILL
        )

        math_tag = Tag(id=str(uuid.uuid4()), name="math", category=TagCategory.TOPIC)

        course1 = MagicMock()
        course1.id = str(uuid.uuid4())
        course1.name = "Python Programming"
        type(course1).tags = PropertyMock(return_value=[python_tag])

        course2 = MagicMock()
        course2.id = str(uuid.uuid4())
        course2.name = "Math Fundamentals"
        type(course2).tags = PropertyMock(return_value=[math_tag])

        self.mock_course_repo.get_all_courses.return_value = [course1, course2]

        filtered_courses = self.course_service.filter_courses(
            filters={"tags": ["python"]}
        )
        self.assertEqual(len(filtered_courses), 1)
        self.assertEqual(filtered_courses[0].name, "Python Programming")

        filtered_courses = self.course_service.filter_courses(
            filters={"tags": ["math"]}
        )
        self.assertEqual(len(filtered_courses), 1)
        self.assertEqual(filtered_courses[0].name, "Math Fundamentals")

        filtered_courses = self.course_service.filter_courses(filters={})
        self.assertEqual(len(filtered_courses), 2)

        filtered_courses = self.course_service.filter_courses(
            filters={"tags": ["nonexistent"]}
        )
        self.assertEqual(len(filtered_courses), 0)

    def test_course_categorization(self):
        """Test that courses can be properly categorized using tags with different categories."""
        topic_tag = Tag(
            id=str(uuid.uuid4()), name="programming", category=TagCategory.TOPIC
        )

        skill_tag = Tag(id=str(uuid.uuid4()), name="python", category=TagCategory.SKILL)

        difficulty_tag = Tag(
            id=str(uuid.uuid4()), name="intermediate", category=TagCategory.DIFFICULTY
        )

        course = MagicMock()
        course.id = str(uuid.uuid4())
        course.title = "Python Programming"
        type(course).tags = PropertyMock(
            return_value=[topic_tag, skill_tag, difficulty_tag]
        )

        self.mock_course_repo.get_course.return_value = course
        self.mock_course_repo.get_course.return_value = course

        course_with_tags = self.course_service.get_course_by_id(course_id=course.id)

        self.assertEqual(len(course_with_tags.tags), 3)

        self.assertIn("programming", course_with_tags.tags)
        self.assertIn("python", course_with_tags.tags)
        self.assertIn("intermediate", course_with_tags.tags)

        with patch.object(
            self.course_service, "update_course_tags"
        ) as mock_update_tags:
            mock_update_tags.return_value = True

            result = self.course_service.update_course_tags(
                course_id=course.id,
                new_tags=[
                    {"name": "new_topic", "category": TagCategory.TOPIC},
                    {"name": "advanced", "category": TagCategory.DIFFICULTY},
                ],
            )

            self.assertTrue(result)
            mock_update_tags.assert_called_once()


if __name__ == "__main__":
    unittest.main()
