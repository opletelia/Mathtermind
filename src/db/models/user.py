import uuid
from typing import List, Optional

from sqlalchemy import (JSON, Boolean, Enum, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.achievement import UserAchievement
from src.db.models.base import Base
from src.db.models.enums import AgeGroup, FontSize, PreferredSubject, ThemeType
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from src.db.models.progress import (CompletedCourse, ContentState, Progress,
                                    UserContentProgress)
from src.db.models.tools import UserToolUsage


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User model representing a student in the learning platform."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    age_group: Mapped[AgeGroup] = mapped_column(Enum(AgeGroup), nullable=False)

    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    experience_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_study_time: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # in minutes

    settings: Mapped[List["UserSetting"]] = relationship(
        "UserSetting", back_populates="user", cascade="all, delete-orphan"
    )
    progress: Mapped[List["Progress"]] = relationship(
        "Progress", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    content_progress: Mapped[List["UserContentProgress"]] = relationship(
        "UserContentProgress",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tool_usages: Mapped[List["UserToolUsage"]] = relationship(
        "UserToolUsage", back_populates="user", cascade="all, delete-orphan"
    )
    content_states: Mapped[List["ContentState"]] = relationship(
        "ContentState", back_populates="user", cascade="all, delete-orphan"
    )
    completed_courses: Mapped[List["CompletedCourse"]] = relationship(
        "CompletedCourse", back_populates="user", cascade="all, delete-orphan"
    )
    answers: Mapped[List["UserAnswer"]] = relationship(
        "UserAnswer", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
    )


class UserSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User preferences and settings."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    theme: Mapped[ThemeType] = mapped_column(
        Enum(ThemeType), default=ThemeType.LIGHT, nullable=False
    )

    accessibility_font_size: Mapped[FontSize] = mapped_column(
        Enum(FontSize), default=FontSize.MEDIUM, nullable=False
    )
    accessibility_high_contrast: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    study_daily_goal_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    study_preferred_subject: Mapped[PreferredSubject] = mapped_column(
        Enum(PreferredSubject), default=PreferredSubject.MATH, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="settings")

    __table_args__ = (Index("idx_user_setting_user_id", "user_id"),)


class Setting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Application-wide settings."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_setting_key", "key"),
        Index("idx_setting_is_protected", "is_protected"),
    )


class UserAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Records of user answers to questions."""

    __tablename__ = "user_answers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="answers")

    __table_args__ = (
        Index("idx_user_answer_user_id", "user_id"),
        Index("idx_user_answer_question_id", "question_id"),
        Index("idx_user_answer_is_correct", "is_correct"),
    )
