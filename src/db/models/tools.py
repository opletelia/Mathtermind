from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import (
    Index,
    String,
    Text,
    Integer,
    Enum,
    TIMESTAMP,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import MathToolType, InformaticsToolType
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LearningTool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Base model for learning tools."""

    __tablename__ = "learning_tools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_category: Mapped[str] = mapped_column(
        Enum("Math", "Informatics", "General", name="tool_category_enum"),
        nullable=False,
    )

    # Polymorphic mapping
    tool_type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_on": tool_type,
        "polymorphic_identity": "learning_tool",
    }

    __table_args__ = (
        Index("idx_learning_tool_category", "tool_category"),
        Index("idx_learning_tool_type", "tool_type"),
    )


class MathTool(LearningTool):
    """Mathematical tools for learning."""

    __tablename__ = "math_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_tools.id", ondelete="CASCADE"),
        primary_key=True,
    )
    math_tool_type: Mapped[MathToolType] = mapped_column(
        Enum(MathToolType), nullable=False
    )
    # JSON Structure for capabilities:
    # {
    #     "functions": [str],  # List of supported functions
    #     "input_types": [str],  # Types of input supported
    #     "output_formats": [str],  # Types of output provided
    #     "limitations": [str]  # Any limitations of the tool
    # }
    capabilities: Mapped[dict] = mapped_column(JSON, nullable=False)
    # JSON Structure for default_config:
    # {
    #     "initial_state": {},  # Tool-specific initial configuration
    #     "ui_settings": {},  # UI-related settings
    #     "computation_settings": {}  # Settings for computations
    # }
    default_config: Mapped[dict] = mapped_column(JSON, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "math_tool"}

    __table_args__ = (Index("idx_math_tool_type", "math_tool_type"),)


class InformaticsTool(LearningTool):
    """Informatics tools for learning programming and algorithms."""

    __tablename__ = "informatics_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_tools.id", ondelete="CASCADE"),
        primary_key=True,
    )
    informatics_tool_type: Mapped[InformaticsToolType] = mapped_column(
        Enum(InformaticsToolType), nullable=False
    )
    # JSON Structure for capabilities:
    # {
    #     "languages": [str],  # Supported programming languages
    #     "features": [str],  # Tool features
    #     "input_types": [str],  # Types of input supported
    #     "output_types": [str],  # Types of output provided
    #     "limitations": [str]  # Any limitations of the tool
    # }
    capabilities: Mapped[dict] = mapped_column(JSON, nullable=False)
    # JSON Structure for default_config:
    # {
    #     "initial_state": {},  # Tool-specific initial configuration
    #     "ui_settings": {},  # UI-related settings
    #     "execution_settings": {}  # Settings for code execution or visualization
    # }
    default_config: Mapped[dict] = mapped_column(JSON, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "informatics_tool"}

    __table_args__ = (Index("idx_informatics_tool_type", "informatics_tool_type"),)


class UserToolUsage(UUIDPrimaryKeyMixin, Base):
    """Tracks how users interact with learning tools."""

    __tablename__ = "user_tool_usages"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # in seconds
    # JSON Structure for usage_data:
    # {
    #     "actions": [
    #         {
    #             "action_type": str,
    #             "timestamp": datetime,
    #             "details": {}
    #         }
    #     ],
    #     "inputs": {},  # User inputs to the tool
    #     "outputs": {},  # Tool outputs
    #     "errors": []  # Any errors encountered
    # }
    usage_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tool_usages")
    tool: Mapped["LearningTool"] = relationship("LearningTool")
    content: Mapped[Optional["Content"]] = relationship("Content")

    __table_args__ = (
        Index("idx_user_tool_usage_user_id", "user_id"),
        Index("idx_user_tool_usage_tool_id", "tool_id"),
        Index("idx_user_tool_usage_content_id", "content_id"),
        Index("idx_user_tool_usage_start_time", "start_time"),
    )

