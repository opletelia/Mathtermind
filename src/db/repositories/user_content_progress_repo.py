"""
Repository module for UserContentProgress model in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import Content, UserContentProgress

from .base_repository import BaseRepository


class UserContentProgressRepository(BaseRepository[UserContentProgress]):
    """Repository for UserContentProgress model."""

    def __init__(self):
        """Initialize the repository with the UserContentProgress model."""
        super().__init__(UserContentProgress)

    def create_progress(
        self,
        db: Session,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
        lesson_id: uuid.UUID,
        progress_id: uuid.UUID,
        status: str = "not_started",
        score: Optional[float] = None,
        time_spent: int = 0,
        last_interaction: Optional[datetime] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> UserContentProgress:
        """
        Create a new content progress record.

        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID
            lesson_id: Lesson ID containing this content
            progress_id: Progress record ID
            status: Progress status (not_started, in_progress, completed)
            score: Score for the content (if applicable)
            time_spent: Time spent on the content in seconds
            last_interaction: Last interaction time
            custom_data: Custom data specific to content type

        Returns:
            Created user content progress record
        """
        user_content_progress = UserContentProgress(
            user_id=user_id,
            content_id=content_id,
            lesson_id=lesson_id,
            progress_id=progress_id,
            status=status,
            score=score,
            time_spent=time_spent,
            last_interaction=last_interaction or datetime.now(timezone.utc),
            custom_data=custom_data or {},
        )

        db.add(user_content_progress)
        db.commit()
        db.refresh(user_content_progress)
        return user_content_progress

    def get_progress(
        self, db: Session, user_id: uuid.UUID, content_id: uuid.UUID
    ) -> Optional[UserContentProgress]:
        """
        Get progress for a specific content item.

        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID

        Returns:
            User content progress record or None if not found
        """
        return (
            db.query(UserContentProgress)
            .filter(
                UserContentProgress.user_id == user_id,
                UserContentProgress.content_id == content_id,
            )
            .first()
        )

    def get_lesson_progress(
        self, db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> List[UserContentProgress]:
        """
        Get all content progress records for a lesson.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID

        Returns:
            List of user content progress records
        """
        return (
            db.query(UserContentProgress)
            .filter(
                UserContentProgress.user_id == user_id,
                UserContentProgress.lesson_id == lesson_id,
            )
            .all()
        )

    def update_progress(
        self,
        db: Session,
        progress_id: uuid.UUID,
        status: Optional[str] = None,
        score: Optional[float] = None,
        time_spent: Optional[int] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserContentProgress]:
        """
        Update a content progress record.

        Args:
            db: Database session
            progress_id: Progress record ID
            status: New status
            score: New score
            time_spent: Additional time spent
            custom_data: Updated custom data

        Returns:
            Updated user content progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            if status:
                progress.status = status

            if score is not None:
                progress.score = score

            if time_spent is not None:
                progress.time_spent += time_spent

            if custom_data is not None:
                # Merge the existing custom data with the new data
                if not progress.custom_data:
                    progress.custom_data = {}
                progress.custom_data.update(custom_data)

            progress.last_interaction = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def mark_as_completed(
        self,
        db: Session,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
        score: Optional[float] = None,
        time_spent: Optional[int] = None,
    ) -> Optional[UserContentProgress]:
        """
        Mark a content item as completed.

        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID
            score: Final score
            time_spent: Additional time spent

        Returns:
            Updated user content progress record or None if not found
        """
        progress = self.get_progress(db, user_id, content_id)
        if progress:
            progress.status = "completed"

            if score is not None:
                progress.score = score

            if time_spent is not None:
                progress.time_spent += time_spent

            progress.last_interaction = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def count_completed_content(
        self, db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> int:
        """
        Count the number of completed content items in a lesson.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID

        Returns:
            Number of completed content items
        """
        return (
            db.query(UserContentProgress)
            .filter(
                UserContentProgress.user_id == user_id,
                UserContentProgress.lesson_id == lesson_id,
                UserContentProgress.status == "completed",
            )
            .count()
        )

    def count_all_completed_content(
        self, db: Session, user_id: uuid.UUID
    ) -> int:
        """
        Count the total number of completed content items for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Total number of completed content items
        """
        return (
            db.query(UserContentProgress)
            .filter(
                UserContentProgress.user_id == user_id,
                UserContentProgress.status == "completed",
            )
            .count()
        )

    def get_content_completion_percentage(
        self, db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> float:
        """
        Calculate the percentage of completed content in a lesson.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID

        Returns:
            Percentage of completed content (0-100)
        """
        total_content = db.query(Content).filter(Content.lesson_id == lesson_id).count()

        if total_content == 0:
            return 0.0

        completed_content = self.count_completed_content(db, user_id, lesson_id)
        return (completed_content / total_content) * 100

    def get_recent_progress(
        self, db: Session, user_id: uuid.UUID, limit: int = 5
    ) -> List[UserContentProgress]:
        """
        Get the most recent content progress updates for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of user content progress records
        """
        return (
            db.query(UserContentProgress)
            .filter(UserContentProgress.user_id == user_id)
            .order_by(desc(UserContentProgress.last_interaction))
            .limit(limit)
            .all()
        )

    def update_custom_data(
        self,
        db: Session,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
        custom_data: Dict[str, Any],
    ) -> Optional[UserContentProgress]:
        """
        Update the custom data for a content progress record.

        Args:
            db: Database session
            user_id: User ID
            content_id: Content ID
            custom_data: New custom data to merge with existing data

        Returns:
            Updated user content progress record or None if not found
        """
        progress = self.get_progress(db, user_id, content_id)
        if progress:
            if not progress.custom_data:
                progress.custom_data = {}

            progress.custom_data.update(custom_data)
            progress.last_interaction = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

