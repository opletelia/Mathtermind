"""
Repository module for Progress model in the Mathtermind application.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload, selectinload

from src.db.models import Progress

from .base_repository import BaseRepository


class ProgressRepository(BaseRepository[Progress]):
    """Repository for Progress model."""

    def __init__(self):
        """Initialize the repository with the Progress model."""
        super().__init__(Progress)

    def create_progress(
        self,
        db: Session,
        user_id: uuid.UUID,
        course_id: uuid.UUID,
        current_lesson_id: Optional[uuid.UUID] = None,
    ) -> Progress:
        """
        Create a new progress record for a user's course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID
            current_lesson_id: Current lesson ID (optional)

        Returns:
            Created progress record
        """
        progress_data = {"completed_content_ids": [], "last_position": None}

        progress = Progress(
            user_id=user_id,
            course_id=course_id,
            current_lesson_id=current_lesson_id,
            total_points_earned=0,
            time_spent=0,
            progress_percentage=0.0,
            progress_data=progress_data,
            last_accessed=datetime.now(timezone.utc),
            is_completed=False,
        )

        db.add(progress)
        db.commit()
        db.refresh(progress)
        return progress

    def get_user_progress(self, db: Session, user_id: uuid.UUID) -> List[Progress]:
        """
        Get all progress records for a user.

        Args:
            db: Database session
            user_id: User ID as UUID object

        Returns:
            List of progress records for the user
        """
        result = db.query(Progress).filter(Progress.user_id == user_id).all()
        return result

    def get_course_progress(
        self, db: Session, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> Optional[Progress]:
        """
        Get a user's progress in a specific course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID

        Returns:
            Progress record or None if not found
        """
        return (
            db.query(Progress)
            .filter(Progress.user_id == user_id, Progress.course_id == course_id)
            .first()
        )

    def update_progress_percentage(
        self, db: Session, progress_id: uuid.UUID, percentage: float
    ) -> Optional[Progress]:
        """
        Update the progress percentage for a progress record.

        Args:
            db: Database session
            progress_id: Progress record ID
            percentage: New progress percentage (0-100)

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            progress.progress_percentage = min(100.0, max(0.0, percentage))
            progress.last_accessed = datetime.now(timezone.utc)

            if progress.progress_percentage >= 100.0:
                progress.is_completed = True

            db.commit()
            db.refresh(progress)
        return progress

    def update_current_lesson(
        self, db: Session, progress_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> Optional[Progress]:
        """
        Update the current lesson for a progress record.

        Args:
            db: Database session
            progress_id: Progress record ID
            lesson_id: New current lesson ID

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            progress.current_lesson_id = lesson_id
            progress.last_accessed = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def add_points(
        self, db: Session, progress_id: uuid.UUID, points: int
    ) -> Optional[Progress]:
        """
        Add points to a progress record.

        Args:
            db: Database session
            progress_id: Progress record ID
            points: Points to add

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            progress.total_points_earned += points
            progress.last_accessed = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def add_time_spent(
        self, db: Session, progress_id: uuid.UUID, minutes: int
    ) -> Optional[Progress]:
        """
        Add time spent to a progress record.

        Args:
            db: Database session
            progress_id: Progress record ID
            minutes: Minutes to add

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            progress.time_spent += minutes
            progress.last_accessed = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def mark_as_completed(
        self, db: Session, progress_id: uuid.UUID
    ) -> Optional[Progress]:
        """
        Mark a progress record as completed.

        Args:
            db: Database session
            progress_id: Progress record ID

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            progress.is_completed = True
            progress.progress_percentage = 100.0
            progress.last_accessed = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    def get_completed_courses(self, db: Session, user_id: uuid.UUID) -> List[Progress]:
        """
        Get all completed course progress records for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of completed progress records
        """
        return (
            db.query(Progress)
            .filter(Progress.user_id == user_id, Progress.is_completed == True)
            .all()
        )

    def update_progress_data(
        self, db: Session, progress_id: uuid.UUID, data_updates: Dict[str, Any]
    ) -> Optional[Progress]:
        """
        Update the progress_data JSON field with new information.

        Args:
            db: Database session
            progress_id: Progress record ID
            data_updates: Dictionary of updates to merge into progress_data

        Returns:
            Updated progress record or None if not found
        """
        progress = self.get_by_id(db, progress_id)
        if progress:
            if progress.progress_data is None:
                progress.progress_data = {}

            for key, value in data_updates.items():
                progress.progress_data[key] = value

            progress.last_accessed = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress
