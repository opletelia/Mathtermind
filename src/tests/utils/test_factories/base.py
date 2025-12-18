import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Type, TypeVar

T = TypeVar("T")


class BaseFactory(Generic[T]):
    """
    Base factory class with common functionality for all factories.

    Attributes:
        model_class: The model class this factory creates.
    """

    model_class: Type[T]

    @classmethod
    def create(cls, **kwargs) -> T:
        """
        Create an instance of the model with default values overridden by kwargs.

        Args:
            **kwargs: Attributes to override defaults.

        Returns:
            An instance of the model.
        """
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()

        now = datetime.now(timezone.utc)
        if hasattr(cls.model_class, "created_at") and "created_at" not in kwargs:
            kwargs["created_at"] = now
        if hasattr(cls.model_class, "updated_at") and "updated_at" not in kwargs:
            kwargs["updated_at"] = now

        merged_kwargs = {**cls._get_defaults(), **kwargs}

        return cls.model_class(**merged_kwargs)

    @classmethod
    def create_batch(cls, count: int, **kwargs) -> List[T]:
        """
        Create multiple instances of the model.

        Args:
            count: Number of instances to create.
            **kwargs: Attributes to override defaults.

        Returns:
            A list of model instances.
        """
        return [cls.create(**kwargs) for _ in range(count)]

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """
        Get default values for the model attributes.

        Returns:
            A dictionary of default values.
        """
        return {}
