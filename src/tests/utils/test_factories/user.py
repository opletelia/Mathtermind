import uuid
from typing import Any, Dict

from src.db.models import User
from src.db.models.enums import AgeGroup
from src.tests.utils.test_factories.base import BaseFactory


class UserFactory(BaseFactory[User]):
    """Factory for creating User instances."""

    model_class = User

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for User attributes."""
        return {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            "password_hash": "hashed_password",
            "age_group": AgeGroup.FIFTEEN_TO_SEVENTEEN,
            "points": 0,
            "experience_level": 1,
            "total_study_time": 0,
        }
