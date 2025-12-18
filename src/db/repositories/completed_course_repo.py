"""
Repository module for CompletedCourse model in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.models import CompletedCourse

from .base_repository import BaseRepository


class CompletedCourseRepository(BaseRepository[CompletedCourse]):
    """Repository for CompletedCourse model."""

    def __init__(self):
        """Initialize the repository with the CompletedCourse model."""
        super().__init__(CompletedCourse)

    def create_completed_course(
        self,
        db: Session,
        user_id: uuid.UUID,
        course_id: uuid.UUID,
        final_score: Optional[float] = None,
        total_time_spent: int = 0,
        completed_lessons_count: int = 0,
        achievements_earned: Optional[List[uuid.UUID]] = None,
        certificate_id: Optional[uuid.UUID] = None,
    ) -> CompletedCourse:
        """
        Record a completed course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID
            final_score: Final score for the course
            total_time_spent: Total time spent on the course in minutes
            completed_lessons_count: Number of completed lessons
            achievements_earned: List of achievement IDs earned through this course
            certificate_id: Certificate ID if a certificate was issued

        Returns:
            Created completed course record
        """
        completed_course = CompletedCourse(
            user_id=user_id,
            course_id=course_id,
            completed_at=datetime.now(timezone.utc),
            final_score=final_score,
            total_time_spent=total_time_spent,
            completed_lessons_count=completed_lessons_count,
            achievements_earned=achievements_earned if achievements_earned else [],
            certificate_id=certificate_id,
        )

        db.add(completed_course)
        db.commit()
        db.refresh(completed_course)
        return completed_course

    def get_user_completed_courses(
        self, db: Session, user_id: uuid.UUID
    ) -> List[CompletedCourse]:
        """
        Get all completed courses for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of completed course records
        """
        return (
            db.query(CompletedCourse).filter(CompletedCourse.user_id == user_id).all()
        )

    def is_course_completed(
        self, db: Session, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> bool:
        """
        Check if a course has been completed by a user.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID

        Returns:
            True if the course has been completed, False otherwise
        """
        return (
            db.query(CompletedCourse)
            .filter(
                CompletedCourse.user_id == user_id,
                CompletedCourse.course_id == course_id,
            )
            .first()
            is not None
        )

    def get_course_completion(
        self, db: Session, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> Optional[CompletedCourse]:
        """
        Get the completion record for a specific course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID

        Returns:
            Completed course record or None if not found
        """
        return (
            db.query(CompletedCourse)
            .filter(
                CompletedCourse.user_id == user_id,
                CompletedCourse.course_id == course_id,
            )
            .first()
        )

    def add_achievement(
        self, db: Session, completion_id: uuid.UUID, achievement_id: uuid.UUID
    ) -> Optional[CompletedCourse]:
        """
        Add an achievement to a completed course record.

        Args:
            db: Database session
            completion_id: Completed course record ID
            achievement_id: Achievement ID to add

        Returns:
            Updated completed course record or None if not found
        """
        completion = self.get_by_id(db, completion_id)
        if completion:
            if not completion.achievements_earned:
                completion.achievements_earned = []

            if achievement_id not in completion.achievements_earned:
                completion.achievements_earned.append(achievement_id)

            db.commit()
            db.refresh(completion)
        return completion

    def update_certificate(
        self, db: Session, completion_id: uuid.UUID, certificate_id: uuid.UUID
    ) -> Optional[CompletedCourse]:
        """
        Update the certificate ID for a completed course.

        Args:
            db: Database session
            completion_id: Completed course record ID
            certificate_id: New certificate ID

        Returns:
            Updated completed course record or None if not found
        """
        completion = self.get_by_id(db, completion_id)
        if completion:
            completion.certificate_id = certificate_id
            db.commit()
            db.refresh(completion)
        return completion

    def count_completed_courses(self, db: Session, user_id: uuid.UUID) -> int:
        """
        Count the number of completed courses for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of completed courses
        """
        return (
            db.query(CompletedCourse).filter(CompletedCourse.user_id == user_id).count()
        )

    def get_recent_completions(
        self, db: Session, user_id: uuid.UUID, limit: int = 5
    ) -> List[CompletedCourse]:
        """
        Get the most recent course completions for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of completed course records
        """
        return (
            db.query(CompletedCourse)
            .filter(CompletedCourse.user_id == user_id)
            .order_by(CompletedCourse.completed_at.desc())
            .limit(limit)
            .all()
        )

