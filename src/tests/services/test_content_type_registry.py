import json
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from src.core.error_handling.exceptions import ContentError
from src.models.content import (AssessmentContent, Content, ExerciseContent,
                                InteractiveContent, QuizContent,
                                ResourceContent, TheoryContent)
from src.services.content_type_registry import (ContentTypeInfo,
                                                ContentTypeRegistry)


class TestContentTypeRegistry(unittest.TestCase):
    """Test suite for ContentTypeRegistry."""

    def setUp(self):
        """Set up tests."""
        ContentTypeRegistry._instance = None
        self.registry = ContentTypeRegistry()

        self.valid_theory_data = {
            "title": "Sample Theory Content",
            "content_type": "theory",
            "lesson_id": "lesson1",
            "order": 1,
            "text_content": "This is sample theory content.",
        }

        self.valid_exercise_data = {
            "title": "Sample Exercise Content",
            "content_type": "exercise",
            "lesson_id": "lesson1",
            "order": 2,
            "problem_statement": "Solve this problem.",
        }

        self.invalid_theory_data = {
            "title": "Invalid Theory Content",
            "content_type": "theory",
            "lesson_id": "lesson1",
            "order": 1,
        }

    def test_singleton_pattern(self):
        """Test that ContentTypeRegistry follows singleton pattern."""
        registry1 = ContentTypeRegistry()
        registry2 = ContentTypeRegistry()

        self.assertIs(registry1, registry2)
        self.assertIs(registry1, self.registry)

    def test_register_content_type(self):
        """Test registering a new content type."""

        class MockContent(Content):
            content_type = "mock"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        result = self.registry.register_content_type(
            name="mock",
            display_name="Mock Content",
            description="A mock content type for testing",
            model_class=MockContent,
        )

        self.assertTrue(result)
        content_type = self.registry.get_content_type("mock")
        self.assertIsNotNone(content_type)
        self.assertEqual(content_type.name, "mock")

    def test_register_duplicate_content_type(self):
        """Test registering a duplicate content type."""

        class MockContent1(Content):
            content_type = "duplicate"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        result1 = self.registry.register_content_type(
            name="duplicate",
            display_name="Duplicate Content",
            description="A duplicate content type",
            model_class=MockContent1,
        )

        self.assertTrue(result1)

        class MockContent2(Content):
            content_type = "duplicate"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        result2 = self.registry.register_content_type(
            name="duplicate",
            display_name="Another Duplicate",
            description="This should fail",
            model_class=MockContent2,
        )

        self.assertFalse(result2)

    def test_get_content_type(self):
        """Test getting a registered content type."""
        content_type = self.registry.get_content_type("theory")

        self.assertIsNotNone(content_type)
        self.assertEqual(content_type.name, "theory")
        self.assertEqual(content_type.model_class, TheoryContent)

    def test_get_nonexistent_content_type(self):
        """Test getting an unregistered content type."""
        content_type = self.registry.get_content_type("nonexistent")
        self.assertIsNone(content_type)

    def test_get_all_content_types(self):
        """Test getting all registered content types."""
        content_types = self.registry.get_all_content_types()

        self.assertIsInstance(content_types, list)
        self.assertGreater(len(content_types), 0)

        type_names = [ct.name for ct in content_types]
        self.assertIn("theory", type_names)
        self.assertIn("exercise", type_names)
        self.assertIn("quiz", type_names)
        self.assertIn("assessment", type_names)
        self.assertIn("interactive", type_names)
        self.assertIn("resource", type_names)

    def test_create_content_instance_valid(self):
        """Test creating a valid content instance."""
        with patch.object(self.registry, "create_content_instance") as mock_create:
            mock_content = MagicMock(spec=TheoryContent)
            mock_content.id = "test-id-1"
            mock_content.title = "Sample Theory Content"
            mock_content.content_type = "theory"
            mock_content.lesson_id = "lesson1"
            mock_content.order = 1
            mock_content.text_content = "This is sample theory content"
            mock_create.return_value = mock_content

            result = self.registry.create_content_instance(
                content_type="theory",
                id="test-id-1",
                title="Sample Theory Content",
                lesson_id="lesson1",
                order=1,
                text_content="This is sample theory content",
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.id, "test-id-1")
            self.assertEqual(result.title, "Sample Theory Content")
            self.assertEqual(result.content_type, "theory")

            mock_create.assert_called_once()

    def test_create_content_instance_validation_failure(self):
        """Test that validation failures during content creation raise ContentError."""

        def mock_create_with_validation_error(content_type, **kwargs):
            raise ContentError(
                message="Content validation failed: Text content is required for theory content",
                content_type=content_type,
                details={
                    "validation_errors": ["Text content is required for theory content"]
                },
            )

        with patch.object(
            self.registry,
            "create_content_instance",
            side_effect=mock_create_with_validation_error,
        ):
            with self.assertRaises(ContentError):
                self.registry.create_content_instance(
                    content_type="theory",
                    id="test-id-2",
                    title="Invalid Theory Content",
                    lesson_id="lesson1",
                    order=1,
                    text_content="",
                )

    def test_validate_content_valid(self):
        """Test validating valid content."""
        theory_content = TheoryContent(
            id="1",
            title="Test Theory",
            content_type="theory",
            order=1,
            lesson_id="lesson1",
            text_content="This is valid theory content.",
        )

        errors = self.registry.validate_content(theory_content)

        self.assertEqual(len(errors), 0)

    def test_validate_content_invalid(self):
        """Test validating invalid content."""
        invalid_theory = MagicMock(spec=TheoryContent)
        invalid_theory.id = "2"
        invalid_theory.title = "Test Theory"
        invalid_theory.content_type = "theory"
        invalid_theory.order = 2
        invalid_theory.lesson_id = "lesson1"
        invalid_theory.text_content = ""

        errors = self.registry.validate_content(invalid_theory)

        self.assertGreater(len(errors), 0)
        error_text = " ".join(errors)
        self.assertIn("content", error_text.lower())

    def test_validate_content_unknown_type(self):
        """Test validating content with unknown type."""
        mock_content = MagicMock(spec=Content)
        mock_content.content_type = "nonexistent"

        errors = self.registry.validate_content(mock_content)

        self.assertGreater(len(errors), 0)
        error_text = " ".join(errors)
        self.assertIn("Unknown content type", error_text)

    def test_unregister_content_type(self):
        """Test unregistering a content type."""

        class CustomContent(Content):
            content_type = "custom"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        self.registry.register_content_type(
            name="custom",
            display_name="Custom Content",
            description="A custom content type for testing",
            model_class=CustomContent,
        )

        content_type = self.registry.get_content_type("custom")
        self.assertIsNotNone(content_type)

        result = self.registry.unregister_content_type("custom")
        self.assertTrue(result)

        content_type = self.registry.get_content_type("custom")
        self.assertIsNone(content_type)

    def test_unregister_default_content_type(self):
        """Test attempting to unregister a default content type."""
        result = self.registry.unregister_content_type("theory")
        self.assertFalse(result)

        content_type = self.registry.get_content_type("theory")
        self.assertIsNotNone(content_type)

    def test_type_specific_validation(self):
        """Test type-specific validation functions."""
        theory_content = MagicMock(spec=TheoryContent)
        theory_content.text_content = ""

        errors = self.registry._validate_theory_content(theory_content)
        self.assertGreater(len(errors), 0)
        self.assertIn("Text content is required", errors[0])

        exercise_content = MagicMock(spec=ExerciseContent)
        exercise_content.problem_statement = ""

        errors = self.registry._validate_exercise_content(exercise_content)
        self.assertGreater(len(errors), 0)
        self.assertIn("Problem statement is required", errors[0])

        quiz_content = MagicMock(spec=QuizContent)
        quiz_content.questions = []

        errors = self.registry._validate_quiz_content(quiz_content)
        self.assertGreater(len(errors), 0)
        self.assertIn("At least one question is required", errors[0])


if __name__ == "__main__":
    unittest.main()
