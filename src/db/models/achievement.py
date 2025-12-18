import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (JSON, TIMESTAMP, Boolean, Enum, ForeignKey, Index,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Achievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Achievements that users can unlock."""

    __tablename__ = "achievements"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "Learning",
            "Engagement",
            "Mastery",
            "Challenge",
            name="achievement_category_enum",
        ),
        nullable=False,
        default="Learning",
    )
    # JSON Structure for criteria:
    # {
    #     "type": "course_completion" | "points" | "streak" | "time" | "perfect_score",
    #     "requirements": {
    #         "course_ids": [uuid],  # for course_completion
    #         "points_required": int,  # for points
    #         "days_required": int,   # for streak
    #         "time_required": int,   # for time (minutes)
    #         "quiz_ids": [uuid]      # for perfect_score
    #     },
    #     "progress_tracking": {
    #         "count_type": "cumulative" | "consecutive",
    #         "reset_period": "never" | "daily" | "weekly" | "monthly"
    #     }
    # }
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    user_achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="achievement"
    )

    __table_args__ = (Index("idx_achievement_category", "category"),)


class UserAchievement(UUIDPrimaryKeyMixin, Base):
    """Records of achievements earned by users."""

    __tablename__ = "user_achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
    )
    achieved_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notification_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="user_achievements"
    )

    __table_args__ = (
        Index("idx_user_achievement_user_id", "user_id"),
        Index("idx_user_achievement_achievement_id", "achievement_id"),
        Index("idx_user_achievement_notification_sent", "notification_sent"),
    )
