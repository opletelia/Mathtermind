import uuid
from typing import List, Optional

from sqlalchemy import (JSON, Enum, Float, ForeignKey, Index, Integer, String,
                        Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import (Category, ContentType, DifficultyLevel,
                                 ResourceType, Topic)
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from src.db.models.progress import Progress, UserContentProgress


class Course(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Course model representing a complete learning module."""

    __tablename__ = "courses"

    topic: Mapped[Topic] = mapped_column(Enum(Topic), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes

    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson", back_populates="course", cascade="all, delete-orphan"
    )
    progress: Mapped[List["Progress"]] = relationship(
        "Progress", back_populates="course"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary="course_tags", back_populates="courses"
    )

    __table_args__ = (
        Index("idx_course_topic", "topic"),
        Index("idx_course_name", "name"),
    )

    @property
    def formatted_duration(self) -> str:
        estimated_time = 0

        estimated_time = self.duration

        hours = estimated_time // 60
        minutes = estimated_time % 60

        if hours > 0 and minutes > 0:
            return f"Тривалість: {hours} год {minutes} хв"
        elif hours > 0:
            return f"Тривалість: {hours} год"
        else:
            return f"Тривалість: {minutes} хв"

    """@property
    def formatted_updated_date(self) -> str:
        if not self.updated_at:
            return "—"
        return self.updated_at.strftime("%d %B %Y")


    @property
    def formatted_created_date(self) -> str:
        return self.created_at.strftime("%d %B %Y")"""

    @property
    def formatted_created_date(self) -> str:
        """Return formatted created date string"""
        if self.created_at is None:
            return "Не вказано"
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted updated date string"""
        if self.updated_at is None:
            return "Не вказано"
        return self.updated_at.strftime("%d %B %Y")


class CourseTag(Base):
    """Association table for courses and tags."""

    __tablename__ = "course_tags"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        Index("idx_course_tag_course_id", "course_id"),
        Index("idx_course_tag_tag_id", "tag_id"),
    )


class Lesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Individual lesson within a course."""

    __tablename__ = "lessons"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_time: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes
    points_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    contents: Mapped[List["Content"]] = relationship(
        "Content", back_populates="lesson", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_lesson_course_id", "course_id"),
        Index("idx_lesson_lesson_order", "lesson_order"),
    )

    @property
    def formatted_created_date(self) -> str:
        """Return formatted created date string"""
        if self.created_at is None:
            return "Не вказано"
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted updated date string"""
        if self.updated_at is None:
            return "Не вказано"
        return self.updated_at.strftime("%d %B %Y")


class Content(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Base model for all learning content with polymorphic mapping."""

    __tablename__ = "content"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": content_type,
        "polymorphic_identity": "content",
    }
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="contents")
    user_progress: Mapped[List["UserContentProgress"]] = relationship(
        "UserContentProgress",
        back_populates="content",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_content_lesson_id", "lesson_id"),
        Index("idx_content_content_type", "content_type"),
        Index("idx_content_order", "order"),
    )


class TheoryContent(Content):
    """Theoretical content with explanations."""

    __tablename__ = "theory_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    references: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "theory"}


class ExerciseContent(Content):
    """Practice exercises for reinforcement."""

    __tablename__ = "exercise_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    problems: Mapped[dict] = mapped_column(JSON, nullable=False)
    estimated_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # in minutes

    __mapper_args__ = {"polymorphic_identity": "exercise"}


class AssessmentContent(Content):
    """Formal assessments (quizzes)."""

    __tablename__ = "assessment_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    questions: Mapped[dict] = mapped_column(JSON, nullable=False)
    time_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # in minutes
    passing_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    attempts_allowed: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "assessment"}


class InteractiveContent(Content):
    """Interactive elements like simulations."""

    __tablename__ = "interactive_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    interactive_type: Mapped[str] = mapped_column(
        Enum(
            "simulation",
            "tool",
            "game",
            "visualization",
            name="interactive_type_enum",
        ),
        nullable=False,
    )
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "interactive"}


class ResourceContent(Content):
    """Educational resources and media files as content."""

    __tablename__ = "resource_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), nullable=False
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resource_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    creator: Mapped[Optional["User"]] = relationship("User")

    __mapper_args__ = {"polymorphic_identity": "resource"}


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tags for categorizing content."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category: Mapped[Category] = mapped_column(
        Enum(Category), nullable=False, default=Category.TOPIC
    )

    courses: Mapped[List["Course"]] = relationship(
        "Course", secondary="course_tags", back_populates="tags"
    )

    __table_args__ = (
        Index("idx_tag_name", "name"),
        Index("idx_tag_category", "category"),
    )
