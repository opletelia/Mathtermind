import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from src.db.models import User
from src.db.models.achievement import Achievement, UserAchievement
from src.tests.utils.test_factories.base import BaseFactory
from src.tests.utils.test_factories.user import UserFactory


class AchievementFactory(BaseFactory[Achievement]):
    """Factory for creating Achievement instances."""

    model_class = Achievement

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for Achievement attributes."""
        return {
            "title": f"Test Achievement {uuid.uuid4().hex[:8]}",
            "description": "A test achievement for unit testing",
            "icon": "trophy",
            "category": "Learning",
            "criteria": json.dumps(
                {
                    "type": "points",
                    "requirements": {"points_required": 100},
                    "progress_tracking": {
                        "count_type": "cumulative",
                        "reset_period": "never",
                    },
                }
            ),
            "points": 50,
            "is_active": True,
        }


class UserAchievementFactory(BaseFactory[UserAchievement]):
    """Factory for creating UserAchievement instances."""

    model_class = UserAchievement

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for UserAchievement attributes."""
        return {
            "user_id": uuid.uuid4(),
            "achievement_id": uuid.uuid4(),
            "achieved_at": datetime.now(timezone.utc),
            "notification_sent": False,
        }

    @classmethod
    def with_user_and_achievement(
        cls, user: User = None, achievement: Achievement = None, **kwargs
    ) -> UserAchievement:
        """
        Create a user achievement associated with a user and achievement.

        Args:
            user: The user to associate with the achievement.
            achievement: The achievement to associate with the user.
            **kwargs: Additional attributes to override defaults.

        Returns:
            UserAchievement: A user achievement instance.
        """
        if user is None:
            user = UserFactory.create()

        if achievement is None:
            achievement = AchievementFactory.create()

        return cls.create(user_id=user.id, achievement_id=achievement.id, **kwargs)
