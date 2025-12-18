import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Union

from src.db.models import Course, User
from src.db.models.content import (AssessmentContent, ExerciseContent,
                                   InteractiveContent, TheoryContent)
from src.db.models.progress import Progress, UserContentProgress
from src.tests.utils.test_factories.base import BaseFactory
from src.tests.utils.test_factories.content import (ContentFactory,
                                                    CourseFactory)
from src.tests.utils.test_factories.user import UserFactory


class ProgressFactory(BaseFactory[Progress]):
    """Factory for creating Progress instances."""

    model_class = Progress

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for Progress attributes."""
        return {
            "user_id": uuid.uuid4(),
            "course_id": uuid.uuid4(),
            "status": "in_progress",
            "completion_percentage": 50,
            "last_accessed": datetime.now(timezone.utc),
        }

    @classmethod
    def with_user_and_course(
        cls, user: User = None, course: Course = None, **kwargs
    ) -> Progress:
        """
        Create a progress associated with a user and course.

        Args:
            user: The user to associate with the progress.
            course: The course to associate with the progress.
            **kwargs: Additional attributes to override defaults.

        Returns:
            Progress: A progress instance.
        """
        if user is None:
            user = UserFactory.create()

        if course is None:
            course = CourseFactory.create()

        return cls.create(user_id=user.id, course_id=course.id, **kwargs)


class UserContentProgressFactory(BaseFactory[UserContentProgress]):
    """Factory for creating UserContentProgress instances."""

    model_class = UserContentProgress

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for UserContentProgress attributes."""
        return {
            "user_id": uuid.uuid4(),
            "content_id": uuid.uuid4(),
            "status": "completed",
            "score": 90,
            "time_spent": 300,  # in seconds
            "completed_at": datetime.now(timezone.utc),
        }

    @classmethod
    def with_user_and_content(
        cls,
        user: User = None,
        content: Union[
            TheoryContent, ExerciseContent, AssessmentContent, InteractiveContent
        ] = None,
        **kwargs
    ) -> UserContentProgress:
        """
        Create a user content progress associated with a user and content.

        Args:
            user: The user to associate with the progress.
            content: The content to associate with the progress.
            **kwargs: Additional attributes to override defaults.

        Returns:
            UserContentProgress: A user content progress instance.
        """
        if user is None:
            user = UserFactory.create()

        if content is None:
            content = ContentFactory.theory()

        return cls.create(user_id=user.id, content_id=content.id, **kwargs)
