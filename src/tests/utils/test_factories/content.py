import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from src.db.models import Course, Lesson
from src.db.models.content import (AssessmentContent, ExerciseContent,
                                   InteractiveContent, TheoryContent)
from src.db.models.enums import (AnswerType, ContentType, DifficultyLevel,
                                 InteractiveType, Topic)
from src.tests.utils.test_factories.base import BaseFactory


class CourseFactory(BaseFactory[Course]):
    """Factory for creating Course instances."""

    model_class = Course

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for Course attributes."""
        return {
            "topic": Topic.MATHEMATICS,
            "name": f"Test Course {uuid.uuid4().hex[:8]}",
            "description": "A test course for unit testing",
        }


class LessonFactory(BaseFactory[Lesson]):
    """Factory for creating Lesson instances."""

    model_class = Lesson

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for Lesson attributes."""
        return {
            "course_id": uuid.uuid4(),
            "title": f"Test Lesson {uuid.uuid4().hex[:8]}",
            "description": "A test lesson for unit testing",
            "order": 1,
            "lesson_type": ContentType.THEORY,
        }

    @classmethod
    def with_course(cls, course: Course = None, **kwargs) -> Lesson:
        """
        Create a lesson associated with a course.

        Args:
            course: The course to associate with the lesson.
            **kwargs: Additional attributes to override defaults.

        Returns:
            Lesson: A lesson associated with the course.
        """
        if course is None:
            course = CourseFactory.create()

        return cls.create(course_id=course.id, **kwargs)


class ContentFactory:
    """Factory for creating Content instances of different types."""

    @staticmethod
    def theory(lesson_id: uuid.UUID = None, **kwargs) -> TheoryContent:
        """
        Create a theory content.

        Args:
            lesson_id: The ID of the lesson this content belongs to.
            **kwargs: Additional attributes to override defaults.

        Returns:
            TheoryContent: A theory content instance.
        """
        if lesson_id is None:
            lesson_id = uuid.uuid4()

        defaults = {
            "id": uuid.uuid4(),
            "lesson_id": lesson_id,
            "title": f"Test Theory Content {uuid.uuid4().hex[:8]}",
            "content_type": ContentType.THEORY,
            "text_content": "This is a test theory content for unit testing.",
            "media_urls": json.dumps(["https://example.com/image.jpg"]),
            "order": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        merged_kwargs = {**defaults, **kwargs}
        return TheoryContent(**merged_kwargs)

    @staticmethod
    def exercise(lesson_id: uuid.UUID = None, **kwargs) -> ExerciseContent:
        """
        Create an exercise content.

        Args:
            lesson_id: The ID of the lesson this content belongs to.
            **kwargs: Additional attributes to override defaults.

        Returns:
            ExerciseContent: An exercise content instance.
        """
        if lesson_id is None:
            lesson_id = uuid.uuid4()

        defaults = {
            "id": uuid.uuid4(),
            "lesson_id": lesson_id,
            "title": f"Test Exercise Content {uuid.uuid4().hex[:8]}",
            "content_type": ContentType.EXERCISE,
            "problem_statement": "Solve this problem.",
            "hints": json.dumps(["Hint 1", "Hint 2"]),
            "solution": "The solution is X.",
            "difficulty": DifficultyLevel.INTERMEDIATE,
            "order": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        merged_kwargs = {**defaults, **kwargs}
        return ExerciseContent(**merged_kwargs)

    @staticmethod
    def assessment(lesson_id: uuid.UUID = None, **kwargs) -> AssessmentContent:
        """
        Create an assessment content.

        Args:
            lesson_id: The ID of the lesson this content belongs to.
            **kwargs: Additional attributes to override defaults.

        Returns:
            AssessmentContent: An assessment content instance.
        """
        if lesson_id is None:
            lesson_id = uuid.uuid4()

        defaults = {
            "id": uuid.uuid4(),
            "lesson_id": lesson_id,
            "title": f"Test Assessment Content {uuid.uuid4().hex[:8]}",
            "content_type": ContentType.ASSESSMENT,
            "questions": json.dumps(
                [
                    {
                        "id": str(uuid.uuid4()),
                        "text": "What is 2+2?",
                        "answer_type": AnswerType.MULTIPLE_CHOICE.value,
                        "options": ["3", "4", "5", "6"],
                        "correct_answer": "4",
                        "explanation": "2+2 equals 4",
                    }
                ]
            ),
            "time_limit": 300,  # 5 minutes in seconds
            "passing_score": 70,
            "order": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        merged_kwargs = {**defaults, **kwargs}
        return AssessmentContent(**merged_kwargs)

    @staticmethod
    def interactive(lesson_id: uuid.UUID = None, **kwargs) -> InteractiveContent:
        """
        Create an interactive content.

        Args:
            lesson_id: The ID of the lesson this content belongs to.
            **kwargs: Additional attributes to override defaults.

        Returns:
            InteractiveContent: An interactive content instance.
        """
        if lesson_id is None:
            lesson_id = uuid.uuid4()

        defaults = {
            "id": uuid.uuid4(),
            "lesson_id": lesson_id,
            "title": f"Test Interactive Content {uuid.uuid4().hex[:8]}",
            "content_type": ContentType.INTERACTIVE,
            "interactive_type": InteractiveType.SIMULATION,
            "interactive_config": json.dumps(
                {
                    "simulation_type": "graph_plot",
                    "initial_state": {
                        "equation": "y = x^2",
                        "domain": [-10, 10],
                        "range": [-10, 10],
                    },
                    "ui_config": {
                        "show_grid": True,
                        "show_axes": True,
                        "show_labels": True,
                    },
                }
            ),
            "learning_objectives": json.dumps(
                [
                    "Understand the relationship between equations and graphs",
                    "Visualize how changing parameters affects the graph",
                ]
            ),
            "order": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        merged_kwargs = {**defaults, **kwargs}
        return InteractiveContent(**merged_kwargs)
