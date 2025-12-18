import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (JSON, TIMESTAMP, Boolean, Enum, Float, ForeignKey,
                        Index, Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Progress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks user progress in courses."""

    __tablename__ = "progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
    )
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # in minutes
    progress_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    progress_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_accessed: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="progress")
    course: Mapped["Course"] = relationship("Course", back_populates="progress")
    current_lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
    completed_lessons: Mapped[List["CompletedLesson"]] = relationship(
        "CompletedLesson",
        primaryjoin="and_(Progress.user_id==CompletedLesson.user_id, "
        "foreign(Progress.course_id)==CompletedLesson.course_id)",
        viewonly=True,
    )
    content_states: Mapped[List["ContentState"]] = relationship(
        "ContentState", back_populates="progress", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_progress_user_id", "user_id"),
        Index("idx_progress_course_id", "course_id"),
        Index("idx_progress_is_completed", "is_completed"),
        Index("idx_progress_last_accessed", "last_accessed"),
    )


class UserContentProgress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks user progress through individual content items."""

    __tablename__ = "user_content_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # in seconds
    last_interaction: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="content_progress")
    content: Mapped["Content"] = relationship("Content", back_populates="user_progress")
    content_states: Mapped[List["ContentState"]] = relationship(
        "ContentState",
        primaryjoin="and_(foreign(UserContentProgress.user_id)==ContentState.user_id, "
        "foreign(UserContentProgress.content_id)==ContentState.content_id)",
        viewonly=True,
    )

    __table_args__ = (
        Index("idx_user_content_progress_user_id", "user_id"),
        Index("idx_user_content_progress_content_id", "content_id"),
        Index("idx_user_content_progress_is_completed", "is_completed"),
        Index(
            "uq_user_content_progress_user_content",
            "user_id",
            "content_id",
            unique=True,
        ),
    )


class ContentState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores detailed state information for resuming content."""

    __tablename__ = "content_states"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("progress.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
    )
    state_type: Mapped[str] = mapped_column(String(50), nullable=False)
    numeric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    json_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    progress: Mapped["Progress"] = relationship(
        "Progress", back_populates="content_states"
    )
    content: Mapped["Content"] = relationship("Content")

    __table_args__ = (
        Index("idx_content_state_user_id", "user_id"),
        Index("idx_content_state_progress_id", "progress_id"),
        Index("idx_content_state_content_id", "content_id"),
        Index("idx_content_state_state_type", "state_type"),
        Index(
            "uq_content_state_user_content_type",
            "user_id",
            "content_id",
            "state_type",
            unique=True,
        ),
    )


class CompletedLesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Normalized model for completed lessons."""

    __tablename__ = "completed_lessons"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_spent: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes

    user: Mapped["User"] = relationship("User")
    lesson: Mapped["Lesson"] = relationship("Lesson")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        Index("idx_completed_lesson_user_id", "user_id"),
        Index("idx_completed_lesson_lesson_id", "lesson_id"),
        Index("idx_completed_lesson_course_id", "course_id"),
        Index("idx_completed_lesson_completed_at", "completed_at"),
        Index("uq_completed_lesson_user_lesson", "user_id", "lesson_id", unique=True),
    )


class CompletedCourse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Records when a user completes an entire course."""

    __tablename__ = "completed_courses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_time_spent: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes
    completed_lessons_count: Mapped[int] = mapped_column(Integer, nullable=False)
    achievements_earned: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        JSON, nullable=True
    )  # List of achievement IDs earned through this course
    certificate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # If a certificate was issued TODO: probably remove

    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        Index("idx_completed_course_user_id", "user_id"),
        Index("idx_completed_course_course_id", "course_id"),
        Index("idx_completed_course_completed_at", "completed_at"),
        Index("uq_completed_course_user_course", "user_id", "course_id", unique=True),
    )
