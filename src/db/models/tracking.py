import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LearningSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Records of individual learning sessions."""

    __tablename__ = "learning_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # in minutes
    # JSON Structure for session_data:
    # {
    #     "activities": [
    #         {
    #             "type": "lesson" | "quiz" | "practice",
    #             "id": uuid,
    #             "start_time": datetime,
    #             "end_time": datetime,
    #             "completed": bool,
    #             "performance": {
    #                 "score": float,
    #                 "time_spent": int,
    #                 "mistakes": int
    #             }
    #         }
    #     ],
    #     "focus_metrics": {
    #         "breaks_taken": int,
    #         "average_response_time": float,
    #         "completion_rate": float
    #     }
    # }
    session_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_learning_session_user_id", "user_id"),
        Index("idx_learning_session_start_time", "start_time"),
    )


class ErrorLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Records of student mistakes for analysis."""

    __tablename__ = "error_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
    )
    # JSON Structure for error_data:
    # {
    #     "error_type": "concept_misunderstanding" | "calculation" | "logic" | "syntax",
    #     "topic": str,
    #     "subtopic": str,
    #     "question_context": str,
    #     "student_answer": str,
    #     "correct_answer": str,
    #     "misconception_pattern": str,
    #     "recommended_resources": [
    #         {
    #             "type": "lesson" | "exercise" | "example",
    #             "id": uuid,
    #             "description": str
    #         }
    #     ]
    # }
    error_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship("User")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")

    __table_args__ = (
        Index("idx_error_log_user_id", "user_id"),
        Index("idx_error_log_lesson_id", "lesson_id"),
        Index("idx_error_log_created_at", "created_at"),
    )


class StudyStreak(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks user's learning consistency."""

    __tablename__ = "study_streaks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_study_date: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # JSON Structure for streak_data:
    # {
    #     "daily_records": [
    #         {
    #             "date": datetime,
    #             "minutes_studied": int,
    #             "topics_covered": [str],
    #             "achievements_earned": [uuid]
    #         }
    #     ],
    #     "weekly_summary": {
    #         "total_time": int,
    #         "topics_mastered": [str],
    #         "average_daily_time": float
    #     }
    # }
    streak_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_study_streak_user_id", "user_id"),
        Index("idx_study_streak_current_streak", "current_streak"),
        Index("idx_study_streak_last_study_date", "last_study_date"),
    )
