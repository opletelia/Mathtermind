import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from src.core.error_handling.exceptions import ContentError
from src.models.content import (AssessmentContent, Content, ExerciseContent,
                                InteractiveContent, QuizContent,
                                ResourceContent, TheoryContent)

logger = logging.getLogger(__name__)


@dataclass
class ContentTypeInfo:
    """Metadata about a content type."""

    name: str
    display_name: str
    description: str
    model_class: Type[Content]
    validation_function: Optional[Callable[[Any], List[str]]] = None
    allowed_parent_types: List[str] = None
    metadata_schema: Dict[str, Any] = None
    icon: str = None


class ContentTypeRegistry:
    """Central registry for content types."""

    _instance = None

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ContentTypeRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the registry with default content types."""
        self._types: Dict[str, ContentTypeInfo] = {}
        self._register_default_types()

    def _register_default_types(self):
        """Register the default content types."""
        self.register_content_type(
            name="theory",
            display_name="Theory",
            description="Theoretical material explaining concepts",
            model_class=TheoryContent,
            validation_function=self._validate_theory_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "complexity": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                    },
                },
            },
            icon="book",
        )

        self.register_content_type(
            name="exercise",
            display_name="Exercise",
            description="Practice exercises for applying concepts",
            model_class=ExerciseContent,
            validation_function=self._validate_exercise_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]}
                },
            },
            icon="pencil",
        )

        self.register_content_type(
            name="quiz",
            display_name="Quiz",
            description="Multiple-choice or short-answer questions",
            model_class=QuizContent,
            validation_function=self._validate_quiz_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "quiz_type": {
                        "type": "string",
                        "enum": ["multiple_choice", "short_answer", "mixed"],
                    }
                },
            },
            icon="question-circle",
        )

        self.register_content_type(
            name="assessment",
            display_name="Assessment",
            description="Formal assessment with scoring",
            model_class=AssessmentContent,
            validation_function=self._validate_assessment_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "grading_scale": {"type": "string"},
                    "is_timed": {"type": "boolean"},
                },
            },
            icon="clipboard-check",
        )

        self.register_content_type(
            name="interactive",
            display_name="Interactive Activity",
            description="Interactive elements like simulations or tools",
            model_class=InteractiveContent,
            validation_function=self._validate_interactive_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "interaction_type": {
                        "type": "string",
                        "enum": ["simulation", "tool", "game", "visualization"],
                    }
                },
            },
            icon="laptop-code",
        )

        self.register_content_type(
            name="resource",
            display_name="Resource",
            description="External resources like links or files",
            model_class=ResourceContent,
            validation_function=self._validate_resource_content,
            metadata_schema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["link", "pdf", "video", "audio", "other"],
                    }
                },
            },
            icon="link",
        )

    def register_content_type(
        self,
        name: str,
        display_name: str,
        description: str,
        model_class: Type[Content],
        validation_function: Optional[Callable[[Any], List[str]]] = None,
        allowed_parent_types: List[str] = None,
        metadata_schema: Dict[str, Any] = None,
        icon: str = None,
    ) -> bool:
        """
        Register a new content type.

        Args:
            name: The internal name of the content type
            display_name: The user-friendly display name
            description: A description of the content type
            model_class: The model class for this content type
            validation_function: Optional function to validate content of this type
            allowed_parent_types: Optional list of content types that can contain this type
            metadata_schema: Optional JSON schema for custom metadata
            icon: Optional icon identifier for UI display

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            if name in self._types:
                logger.warning(f"Content type '{name}' is already registered")
                return False

            if not issubclass(model_class, Content):
                logger.error(f"Model class for '{name}' must be a subclass of Content")
                return False

            content_type_info = ContentTypeInfo(
                name=name,
                display_name=display_name,
                description=description,
                model_class=model_class,
                validation_function=validation_function,
                allowed_parent_types=allowed_parent_types,
                metadata_schema=metadata_schema,
                icon=icon,
            )

            self._types[name] = content_type_info
            logger.info(f"Content type '{name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Error registering content type '{name}': {str(e)}")
            return False

    def unregister_content_type(self, name: str) -> bool:
        """
        Unregister a content type.

        Args:
            name: The name of the content type to unregister

        Returns:
            True if unregistration was successful, False otherwise
        """
        try:
            if name not in self._types:
                logger.warning(f"Content type '{name}' is not registered")
                return False

            if name in [
                "theory",
                "exercise",
                "quiz",
                "assessment",
                "interactive",
                "resource",
            ]:
                logger.warning(f"Cannot unregister default content type '{name}'")
                return False

            del self._types[name]
            logger.info(f"Content type '{name}' unregistered successfully")
            return True
        except Exception as e:
            logger.error(f"Error unregistering content type '{name}': {str(e)}")
            return False

    def get_content_type(self, name: str) -> Optional[ContentTypeInfo]:
        """
        Get information about a content type.

        Args:
            name: The name of the content type

        Returns:
            ContentTypeInfo object if found, None otherwise
        """
        return self._types.get(name)

    def get_all_content_types(self) -> List[ContentTypeInfo]:
        """
        Get all registered content types.

        Returns:
            List of ContentTypeInfo objects
        """
        return list(self._types.values())

    def validate_content(self, content: Content) -> List[str]:
        """
        Validate content against its type's validation rules.

        Args:
            content: The content to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        try:
            content_type = self.get_content_type(content.content_type)
            if not content_type:
                return [f"Unknown content type: {content.content_type}"]

            errors = []
            if not content.title:
                errors.append("Title is required")

            if content_type.validation_function:
                type_errors = content_type.validation_function(content)
                if type_errors:
                    errors.extend(type_errors)

            return errors
        except Exception as e:
            logger.error(f"Error validating content: {str(e)}")
            return [f"Validation error: {str(e)}"]

    def create_content_instance(self, content_type: str, **kwargs) -> Optional[Content]:
        """
        Create a new content instance of the specified type.

        Args:
            content_type: The type of content to create
            **kwargs: Parameters to pass to the constructor

        Returns:
            Created content instance if successful, None otherwise
        """
        try:
            type_info = self.get_content_type(content_type)
            if not type_info:
                logger.warning(f"Unknown content type: {content_type}")
                return None

            instance = type_info.model_class(**kwargs)

            errors = self.validate_content(instance)
            if errors:
                error_list = "; ".join(errors)
                logger.warning(f"Content validation failed: {error_list}")
                raise ContentError(
                    message=f"Content validation failed: {error_list}",
                    content_type=content_type,
                    details={"validation_errors": errors},
                )

            return instance
        except Exception as e:
            if not isinstance(e, ContentError):
                logger.error(f"Error creating content instance: {str(e)}")
            return None

    def _validate_theory_content(self, content: TheoryContent) -> List[str]:
        """Validate theory content."""
        errors = []
        if not content.text_content:
            errors.append("Text content is required for theory content")
        return errors

    def _validate_exercise_content(self, content: ExerciseContent) -> List[str]:
        """Validate exercise content."""
        errors = []
        if not content.problem_statement:
            errors.append("Problem statement is required for exercise content")
        return errors

    def _validate_quiz_content(self, content: QuizContent) -> List[str]:
        """Validate quiz content."""
        errors = []
        if not content.questions:
            errors.append("At least one question is required for quiz content")
        return errors

    def _validate_assessment_content(self, content: AssessmentContent) -> List[str]:
        """Validate assessment content."""
        errors = []
        if not content.questions:
            errors.append("At least one question is required for assessment content")
        return errors

    def _validate_interactive_content(self, content: InteractiveContent) -> List[str]:
        """Validate interactive content."""
        errors = []
        if not content.interaction_type:
            errors.append("Interaction type is required for interactive content")
        if not content.interaction_data:
            errors.append("Interaction data is required for interactive content")
        return errors

    def _validate_resource_content(self, content: ResourceContent) -> List[str]:
        """Validate resource content."""
        errors = []
        if not content.resource_type:
            errors.append("Resource type is required for resource content")
        if not content.resource_url:
            errors.append("Resource URL is required for resource content")
        return errors
