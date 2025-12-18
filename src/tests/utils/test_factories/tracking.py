import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from src.db.models import User
from src.db.models.tracking import LearningSession, StudyStreak
from src.tests.utils.test_factories.base import BaseFactory
from src.tests.utils.test_factories.user import UserFactory


class LearningSessionFactory(BaseFactory[LearningSession]):
    """Factory for creating LearningSession instances."""

    model_class = LearningSession

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for LearningSession attributes."""
        now = datetime.now(timezone.utc)
        return {
            "user_id": uuid.uuid4(),
            "start_time": now - timedelta(hours=1),
            "end_time": now,
            "duration": 3600,  # 1 hour in seconds
            "activity_summary": json.dumps(
                {
                    "courses_accessed": [str(uuid.uuid4())],
                    "lessons_completed": 2,
                    "exercises_attempted": 5,
                    "points_earned": 100,
                }
            ),
        }

    @classmethod
    def with_user(cls, user: User = None, **kwargs) -> LearningSession:
        """
        Create a learning session associated with a user.

        Args:
            user: The user to associate with the learning session.
            **kwargs: Additional attributes to override defaults.

        Returns:
            LearningSession: A learning session instance.
        """
        if user is None:
            user = UserFactory.create()

        return cls.create(user_id=user.id, **kwargs)


class StudyStreakFactory(BaseFactory[StudyStreak]):
    """Factory for creating StudyStreak instances."""

    model_class = StudyStreak

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for StudyStreak attributes."""
        return {
            "user_id": uuid.uuid4(),
            "current_streak": 5,
            "longest_streak": 10,
            "last_study_date": datetime.now(timezone.utc).date(),
        }

    @classmethod
    def with_user(cls, user: User = None, **kwargs) -> StudyStreak:
        """
        Create a study streak associated with a user.

        Args:
            user: The user to associate with the study streak.
            **kwargs: Additional attributes to override defaults.

        Returns:
            StudyStreak: A study streak instance.
        """
        if user is None:
            user = UserFactory.create()

        return cls.create(user_id=user.id, **kwargs)
