import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from src.db.models.enums import InformaticsToolType, MathToolType
from src.db.models.tools import InformaticsTool, LearningTool, MathTool


class LearningToolFactory:
    """Factory for creating LearningTool instances of different types."""

    @staticmethod
    def math_tool(**kwargs) -> MathTool:
        """
        Create a math tool.

        Args:
            **kwargs: Attributes to override defaults.

        Returns:
            MathTool: A math tool instance.
        """
        tool_id = kwargs.get("id", uuid.uuid4())
        now = datetime.now(timezone.utc)

        learning_tool = LearningTool(
            id=tool_id,
            name=kwargs.get("name", f"Test Math Tool {uuid.uuid4().hex[:8]}"),
            description=kwargs.get("description", "A test math tool for unit testing"),
            tool_category=kwargs.get("tool_category", "Math"),
            tool_type=kwargs.get("tool_type", "math_tool"),
            created_at=kwargs.get("created_at", now),
            updated_at=kwargs.get("updated_at", now),
        )

        math_tool = MathTool(
            id=tool_id,
            math_tool_type=kwargs.get("math_tool_type", MathToolType.GRAPHING),
            capabilities=kwargs.get(
                "capabilities",
                json.dumps(
                    {
                        "functions": ["add", "subtract", "multiply", "divide"],
                        "input_types": ["integer", "float"],
                        "output_formats": ["decimal", "fraction"],
                        "limitations": ["no complex numbers"],
                    }
                ),
            ),
            default_config=kwargs.get(
                "default_config",
                json.dumps(
                    {
                        "initial_state": {},
                        "ui_settings": {"theme": "light"},
                        "computation_settings": {"precision": 2},
                    }
                ),
            ),
        )

        return math_tool

    @staticmethod
    def informatics_tool(**kwargs) -> InformaticsTool:
        """
        Create an informatics tool.

        Args:
            **kwargs: Attributes to override defaults.

        Returns:
            InformaticsTool: An informatics tool instance.
        """
        tool_id = kwargs.get("id", uuid.uuid4())
        now = datetime.now(timezone.utc)

        learning_tool = LearningTool(
            id=tool_id,
            name=kwargs.get("name", f"Test Informatics Tool {uuid.uuid4().hex[:8]}"),
            description=kwargs.get(
                "description", "A test informatics tool for unit testing"
            ),
            tool_category=kwargs.get("tool_category", "Informatics"),
            tool_type=kwargs.get("tool_type", "informatics_tool"),
            created_at=kwargs.get("created_at", now),
            updated_at=kwargs.get("updated_at", now),
        )

        informatics_tool = InformaticsTool(
            id=tool_id,
            informatics_tool_type=kwargs.get(
                "informatics_tool_type", InformaticsToolType.CODE_EDITOR
            ),
            capabilities=kwargs.get(
                "capabilities",
                json.dumps(
                    {
                        "languages": ["python", "javascript"],
                        "features": ["syntax highlighting", "code completion"],
                        "input_types": ["text"],
                        "output_types": ["console", "visualization"],
                        "limitations": ["no debugging"],
                    }
                ),
            ),
            default_config=kwargs.get(
                "default_config",
                json.dumps(
                    {
                        "initial_state": {},
                        "ui_settings": {"theme": "dark"},
                        "execution_settings": {"timeout": 5000},
                    }
                ),
            ),
        )

        return informatics_tool
