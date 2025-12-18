import uuid
from typing import Any, Dict

from src.db.models import Tag
from src.db.models.enums import Category
from src.tests.utils.test_factories.base import BaseFactory


class TagFactory(BaseFactory[Tag]):
    """Factory for creating Tag instances."""

    model_class = Tag

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for Tag attributes."""
        return {"name": f"Test Tag {uuid.uuid4().hex[:8]}", "category": Category.TOPIC}
