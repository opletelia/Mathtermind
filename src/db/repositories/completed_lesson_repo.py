"""
Repository module for CompletedLesson model in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import CompletedLesson

from .base_repository import BaseRepository


class CompletedLessonRepository(BaseRepository[CompletedLesson]):
    """Repository for CompletedLesson model."""

    def __init__(self):
        """Initialize the repository with the CompletedLesson model."""
        super().__init__(CompletedLesson)

    def create_completed_lesson(
        self,
        db: Session,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        course_id: uuid.UUID,
        score: Optional[float] = None,
        time_spent: int = 0,
    ) -> CompletedLesson:
        """
        Record a completed lesson.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID
            course_id: Course ID
            score: Optional score for the lesson
            time_spent: Time spent on the lesson in minutes

        Returns:
            Created completed lesson record
        """
        completed_lesson = CompletedLesson(
            user_id=user_id,
            lesson_id=lesson_id,
            course_id=course_id,
            completed_at=datetime.now(timezone.utc),
            score=score,
            time_spent=time_spent,
        )

        db.add(completed_lesson)
        db.commit()
        db.refresh(completed_lesson)
        return completed_lesson

    def get_user_completed_lessons(
        self, db: Session, user_id: uuid.UUID
    ) -> List[CompletedLesson]:
        """
        Get all completed lessons for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of completed lesson records
        """
        return (
            db.query(CompletedLesson).filter(CompletedLesson.user_id == user_id).all()
        )

    def count_user_completed_lessons(self, db: Session, user_id: uuid.UUID) -> int:
        return (
            db.query(CompletedLesson)
            .filter(CompletedLesson.user_id == user_id)
            .count()
        )

    def get_user_completed_lessons_count_by_day(
        self, db: Session, user_id: uuid.UUID, since: datetime
    ):
        day_expr = func.date(CompletedLesson.completed_at)
        return (
            db.query(day_expr.label("day"), func.count(CompletedLesson.id).label("count"))
            .filter(
                CompletedLesson.user_id == user_id,
                CompletedLesson.completed_at >= since,
            )
            .group_by(day_expr)
            .order_by(day_expr)
            .all()
        )

    def get_course_completed_lessons(
        self, db: Session, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> List[CompletedLesson]:
        """
        Get all completed lessons for a user in a specific course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID

        Returns:
            List of completed lesson records
        """
        return (
            db.query(CompletedLesson)
            .filter(
                CompletedLesson.user_id == user_id,
                CompletedLesson.course_id == course_id,
            )
            .all()
        )

    def is_lesson_completed(
        self, db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> bool:
        """
        Check if a lesson has been completed by a user.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID

        Returns:
            True if the lesson has been completed, False otherwise
        """
        return (
            db.query(CompletedLesson)
            .filter(
                CompletedLesson.user_id == user_id,
                CompletedLesson.lesson_id == lesson_id,
            )
            .first()
            is not None
        )

    def get_lesson_completion(
        self, db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> Optional[CompletedLesson]:
        """
        Get the completion record for a specific lesson.

        Args:
            db: Database session
            user_id: User ID
            lesson_id: Lesson ID

        Returns:
            Completed lesson record or None if not found
        """
        return (
            db.query(CompletedLesson)
            .filter(
                CompletedLesson.user_id == user_id,
                CompletedLesson.lesson_id == lesson_id,
            )
            .first()
        )

    def update_lesson_score(
        self, db: Session, completion_id: uuid.UUID, score: float
    ) -> Optional[CompletedLesson]:
        """
        Update the score for a completed lesson.

        Args:
            db: Database session
            completion_id: Completed lesson record ID
            score: New score

        Returns:
            Updated completed lesson record or None if not found
        """
        completion = self.get_by_id(db, completion_id)
        if completion:
            completion.score = score
            db.commit()
            db.refresh(completion)
        return completion

    def update_lesson_time_spent(
        self, db: Session, completion_id: uuid.UUID, time_spent: int
    ) -> Optional[CompletedLesson]:
        """
        Update the time spent for a completed lesson.

        Args:
            db: Database session
            completion_id: Completed lesson record ID
            time_spent: New time spent in minutes

        Returns:
            Updated completed lesson record or None if not found
        """
        completion = self.get_by_id(db, completion_id)
        if completion:
            completion.time_spent = time_spent
            db.commit()
            db.refresh(completion)
        return completion

    def count_completed_lessons(
        self, db: Session, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> int:
        """
        Count the number of completed lessons for a user in a course.

        Args:
            db: Database session
            user_id: User ID
            course_id: Course ID

        Returns:
            Number of completed lessons
        """
        return (
            db.query(CompletedLesson)
            .filter(
                CompletedLesson.user_id == user_id,
                CompletedLesson.course_id == course_id,
            )
            .count()
        )

