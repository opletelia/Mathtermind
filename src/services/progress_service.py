import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from src.db import get_db
from src.db.models import CompletedCourse as DBCompletedCourse
from src.db.models import CompletedLesson as DBCompletedLesson
from src.db.models import ContentState as DBContentState
from src.db.models import Progress as DBProgress
from src.db.models import UserContentProgress as DBUserContentProgress
from src.db.repositories import (CompletedCourseRepository,
                                 CompletedLessonRepository, ContentRepository,
                                 CourseRepository, LessonRepository,
                                 ProgressRepository,
                                 UserContentProgressRepository)
from src.models.progress import (CompletedCourse, CompletedLesson,
                                 ContentState, Progress, UserContentProgress)
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProgressService(BaseService):
    """Service for managing user progress."""

    def __init__(self):
        """Initialize the progress service."""
        super().__init__()
        self.progress_repo = ProgressRepository()
        self.completed_lesson_repo = CompletedLessonRepository()
        self.completed_course_repo = CompletedCourseRepository()
        self.user_content_progress_repo = UserContentProgressRepository()
        self.lesson_repo = LessonRepository()
        self.course_repo = CourseRepository()
        self.content_repo = ContentRepository()

    def get_all_progress(self) -> List[Progress]:
        """
        Get all progress records from the database.

        Returns:
            A list of all progress records
        """
        try:
            with self.transaction() as session:
                db_progress_records = session.query(DBProgress).all()
                return [
                    self._convert_db_progress_to_ui_progress(record)
                    for record in db_progress_records
                ]
        except Exception as e:
            logger.error(f"Error getting all progress: {str(e)}")
            return []

    def get_user_progress(self, user_id: str) -> List[Progress]:
        """
        Get all progress records for a user.

        Args:
            user_id: The ID of the user (string, will be converted to UUID)

        Returns:
            A list of progress records
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            with self.transaction() as session:
                db_progress_records = self.progress_repo.get_user_progress(
                    session, user_uuid
                )
                return [
                    self._convert_db_progress_to_ui_progress(record)
                    for record in db_progress_records
                ]
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return []

    def get_course_progress(self, user_id: str, course_id: str) -> Optional[Progress]:
        """
        Get progress for a specific course.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            The progress record if found, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            db = next(get_db())
            db_progress = self.progress_repo.get_course_progress(
                db, user_uuid, course_uuid
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error getting course progress: {str(e)}")
            return None

    def create_course_progress(
        self, user_id: str, course_id: str
    ) -> Optional[Progress]:
        """
        Create a new progress record for a course.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            The created progress record if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            from src.db import get_db

            db = next(get_db())

            existing_progress = self.progress_repo.get_course_progress(
                db, user_uuid, course_uuid
            )
            if existing_progress:
                return self._convert_db_progress_to_ui_progress(existing_progress)

            course = self.course_repo.get_by_id(db, course_uuid)
            if not course:
                logger.warning(f"Course not found: {course_id}")
                return None

            lessons = self.lesson_repo.get_lessons_by_course_id(db, course_uuid)
            first_lesson_id = lessons[0].id if lessons else None

            db_progress = self.progress_repo.create_progress(
                db=db,
                user_id=user_uuid,
                course_id=course_uuid,
                current_lesson_id=first_lesson_id,
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error creating course progress: {str(e)}")
            self.db.rollback()
            return None

    def update_progress_percentage(
        self, progress_id: str, percentage: float
    ) -> Optional[Progress]:
        """
        Update the progress percentage.

        Args:
            progress_id: The ID of the progress record
            percentage: The new progress percentage

        Returns:
            The updated progress record if successful, None otherwise
        """
        try:
            progress_uuid = uuid.UUID(progress_id)

            db_progress = self.progress_repo.update_progress_percentage(
                progress_id=progress_uuid, percentage=percentage
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error updating progress percentage: {str(e)}")
            self.db.rollback()
            return None

    def update_current_lesson(
        self, progress_id: str, lesson_id: str
    ) -> Optional[Progress]:
        """
        Update the current lesson.

        Args:
            progress_id: The ID of the progress record
            lesson_id: The ID of the new current lesson

        Returns:
            The updated progress record if successful, None otherwise
        """
        try:
            progress_uuid = uuid.UUID(progress_id)
            lesson_uuid = uuid.UUID(lesson_id)

            db_progress = self.progress_repo.update_current_lesson(
                progress_id=progress_uuid, lesson_id=lesson_uuid
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error updating current lesson: {str(e)}")
            self.db.rollback()
            return None

    def add_points(self, progress_id: str, points: int) -> Optional[Progress]:
        """
        Add points to the progress.

        Args:
            progress_id: The ID of the progress record
            points: The points to add

        Returns:
            The updated progress record if successful, None otherwise
        """
        try:
            progress_uuid = uuid.UUID(progress_id)

            db_progress = self.progress_repo.add_points(
                progress_id=progress_uuid, points=points
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error adding points: {str(e)}")
            self.db.rollback()
            return None

    def add_time_spent(self, progress_id: str, minutes: int) -> Optional[Progress]:
        """
        Add time spent to the progress.

        Args:
            progress_id: The ID of the progress record
            minutes: The minutes to add

        Returns:
            The updated progress record if successful, None otherwise
        """
        try:
            progress_uuid = uuid.UUID(progress_id)

            db_progress = self.progress_repo.add_time_spent(
                progress_id=progress_uuid, minutes=minutes
            )

            if not db_progress:
                return None

            return self._convert_db_progress_to_ui_progress(db_progress)
        except Exception as e:
            logger.error(f"Error adding time spent: {str(e)}")
            self.db.rollback()
            return None

    def complete_progress(self, user_id: str, progress_id: str) -> None:
        """
        Mark progress as completed.

        Args:
            user_id: The ID of the user
            progress_id: The ID of the progress record
        """
        progress_uuid = uuid.UUID(progress_id)

        self.progress_repo.mark_as_completed(progress_uuid)

    def complete_lesson(
        self,
        user_id: str,
        lesson_id: str,
        course_id: str,
        score: Optional[int] = None,
        time_spent: Optional[int] = None,
    ) -> Optional[CompletedLesson]:
        """
        Mark a lesson as complete for a user.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson
            course_id: The ID of the course the lesson belongs to
            score: Optional score achieved in the lesson
            time_spent: Optional time spent on the lesson in minutes

        Returns:
            The completed lesson record if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)
            course_uuid = uuid.UUID(course_id)

            is_completed = self.completed_lesson_repo.is_lesson_completed(
                self.db, user_uuid, lesson_uuid
            )
            if is_completed:
                db_completed = self.completed_lesson_repo.get_lesson_completion(
                    self.db, user_uuid, lesson_uuid
                )
                return self._convert_db_completed_lesson_to_ui_completed_lesson(
                    db_completed
                )

            effective_time_spent = time_spent if time_spent is not None else 0
            db_completed = self.completed_lesson_repo.create_completed_lesson(
                self.db,
                user_id=user_uuid,
                lesson_id=lesson_uuid,
                course_id=course_uuid,
                score=score,
                time_spent=effective_time_spent,
            )

            if not db_completed:
                return None

            progress = self.progress_repo.get_course_progress(
                self.db, user_uuid, course_uuid
            )
            if progress:
                lessons = self.lesson_repo.get_lessons_by_course_id(
                    self.db, course_uuid
                )
                total_lessons = len(lessons)
                completed_lessons = self.completed_lesson_repo.count_completed_lessons(
                    self.db, user_uuid, course_uuid
                )

                if total_lessons > 0:
                    new_percentage = (completed_lessons / total_lessons) * 100
                    self.progress_repo.update_progress_percentage(
                        self.db, progress.id, new_percentage
                    )

                if completed_lessons == total_lessons:
                    self.progress_repo.mark_as_completed(progress.id)

                    self.completed_course_repo.create_completed_course(
                        user_id=user_uuid, course_id=course_uuid
                    )

            self._check_achievements_after_completion(user_id)

            return self._convert_db_completed_lesson_to_ui_completed_lesson(
                db_completed
            )
        except Exception as e:
            logger.error(f"Error completing lesson: {str(e)}")
            self.db.rollback()
            return None

    def get_user_completed_lessons(self, user_id: str) -> List[CompletedLesson]:
        """
        Get all completed lessons for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of completed lessons
        """
        try:
            user_uuid = uuid.UUID(user_id)

            db_completed_lessons = (
                self.completed_lesson_repo.get_user_completed_lessons(user_uuid)
            )

            return [
                self._convert_db_completed_lesson_to_ui_completed_lesson(lesson)
                for lesson in db_completed_lessons
            ]
        except Exception as e:
            logger.error(f"Error getting user completed lessons: {str(e)}")
            return []

    def has_completed_lesson(self, user_id: str, lesson_id: str) -> bool:
        """
        Check if a user has completed a specific lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson to check

        Returns:
            True if the user has completed the lesson, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            db_completed_lesson = self.completed_lesson_repo.get_lesson_completion(
                self.db, user_uuid, lesson_uuid
            )

            return db_completed_lesson is not None
        except Exception as e:
            logger.error(f"Error checking if lesson is completed: {str(e)}")
            return False

    def get_lesson_completion(
        self, user_id: str, lesson_id: str
    ) -> Optional[CompletedLesson]:
        """
        Get the completed lesson record for a user and lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            The completed lesson record if found, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            db_completed = self.completed_lesson_repo.get_lesson_completion(
                self.db, user_uuid, lesson_uuid
            )

            if db_completed:
                return self._convert_db_completed_lesson_to_ui_completed_lesson(
                    db_completed
                )
            return None
        except Exception as e:
            logger.error(f"Error getting lesson completion: {str(e)}")
            return None

    def get_course_completed_lessons(
        self, user_id: str, course_id: str
    ) -> List[CompletedLesson]:
        """
        Get all completed lessons for a user in a course.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            A list of completed lesson records
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            with self.transaction() as session:
                db_completed_lessons = (
                    self.completed_lesson_repo.get_course_completed_lessons(
                        db=session, user_id=user_uuid, course_id=course_uuid
                    )
                )

                return [
                    self._convert_db_completed_lesson_to_ui_completed_lesson(record)
                    for record in db_completed_lessons
                ]
        except Exception as e:
            logger.error(f"Error getting course completed lessons: {str(e)}")
            return []

    def get_user_completed_courses(self, user_id: str) -> List[CompletedCourse]:
        """
        Get all completed courses for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of completed course records
        """
        try:
            user_uuid = uuid.UUID(user_id)

            db_completed_courses = (
                self.completed_course_repo.get_user_completed_courses(user_uuid)
            )

            return [
                self._convert_db_completed_course_to_ui_completed_course(record)
                for record in db_completed_courses
            ]
        except Exception as e:
            logger.error(f"Error getting user completed courses: {str(e)}")
            return []

    def get_course_completion(
        self, user_id: str, course_id: str
    ) -> Optional[CompletedCourse]:
        """
        Get the completion record for a course.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            The completed course record if found, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            db_completion = self.completed_course_repo.get_course_completion(
                user_id=user_uuid, course_id=course_uuid
            )

            if not db_completion:
                return None

            return self._convert_db_completed_course_to_ui_completed_course(
                db_completion
            )
        except Exception as e:
            logger.error(f"Error getting course completion: {str(e)}")
            return None

    def get_content_progress(
        self, user_id: str, content_id: str
    ) -> Optional[UserContentProgress]:
        """
        Get user progress for a specific content item.

        Args:
            user_id: The ID of the user
            content_id: The ID of the content

        Returns:
            The user content progress record if found, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            db_content_progress = self.user_content_progress_repo.get_content_progress(
                user_id=user_uuid, content_id=content_uuid
            )

            if not db_content_progress:
                return None

            return self._convert_db_user_content_progress_to_ui_user_content_progress(
                db_content_progress
            )
        except Exception as e:
            logger.error(f"Error getting content progress: {str(e)}")
            return None

    def update_content_progress(
        self,
        user_id: str,
        content_id: str,
        status: str,
        score: Optional[int] = None,
        time_spent: Optional[int] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserContentProgress]:
        """
        Update or create user progress for a content item.

        Args:
            user_id: The ID of the user
            content_id: The ID of the content
            status: The status of the content progress
            score: Optional score for the content
            time_spent: Optional time spent on the content in minutes
            custom_data: Optional custom data

        Returns:
            The updated or created user content progress record if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            db_content_progress = self.user_content_progress_repo.get_content_progress(
                user_id=user_uuid, content_id=content_uuid
            )

            if db_content_progress:
                updates = {}
                if status:
                    updates["status"] = status
                if score is not None:
                    updates["score"] = score
                if time_spent is not None:
                    updates["time_spent"] = db_content_progress.time_spent + time_spent
                if custom_data is not None:
                    existing_data = db_content_progress.custom_data or {}
                    existing_data.update(custom_data)
                    updates["custom_data"] = existing_data

                db_content_progress = (
                    self.user_content_progress_repo.update_content_progress(
                        progress_id=db_content_progress.id, updates=updates
                    )
                )
            else:
                db_content_progress = (
                    self.user_content_progress_repo.create_content_progress(
                        user_id=user_uuid,
                        content_id=content_uuid,
                        status=status,
                        score=score,
                        time_spent=time_spent,
                        custom_data=custom_data,
                    )
                )

            if not db_content_progress:
                return None

            if status == "completed":
                self._check_achievements_after_completion(user_id)

            return self._convert_db_user_content_progress_to_ui_user_content_progress(
                db_content_progress
            )
        except Exception as e:
            logger.error(f"Error updating content progress: {str(e)}")
            self.db.rollback()
            return None

    def _convert_db_progress_to_ui_progress(self, db_progress: DBProgress) -> Progress:
        """
        Convert a database progress to a UI progress.

        Args:
            db_progress: The database progress

        Returns:
            The corresponding UI progress
        """
        return Progress(
            id=str(db_progress.id),
            user_id=str(db_progress.user_id),
            course_id=str(db_progress.course_id),
            current_lesson_id=(
                str(db_progress.current_lesson_id)
                if db_progress.current_lesson_id
                else None
            ),
            total_points_earned=db_progress.total_points_earned,
            time_spent=db_progress.time_spent,
            progress_percentage=db_progress.progress_percentage,
            progress_data=db_progress.progress_data,
            last_accessed=db_progress.last_accessed,
            is_completed=db_progress.is_completed,
            created_at=db_progress.created_at,
            updated_at=db_progress.updated_at,
        )

    def _convert_db_completed_lesson_to_ui_completed_lesson(
        self, db_completed_lesson: DBCompletedLesson
    ) -> CompletedLesson:
        """
        Convert a database completed lesson to a UI completed lesson.

        Args:
            db_completed_lesson: The database completed lesson

        Returns:
            The corresponding UI completed lesson
        """
        return CompletedLesson(
            id=str(db_completed_lesson.id),
            user_id=str(db_completed_lesson.user_id),
            lesson_id=str(db_completed_lesson.lesson_id),
            course_id=str(db_completed_lesson.course_id),
            completed_at=db_completed_lesson.completed_at,
            score=db_completed_lesson.score,
            time_spent=db_completed_lesson.time_spent,
            created_at=db_completed_lesson.created_at,
            updated_at=db_completed_lesson.updated_at,
        )

    def _convert_db_completed_course_to_ui_completed_course(
        self, db_completed_course: DBCompletedCourse
    ) -> CompletedCourse:
        """
        Convert a database completed course to a UI completed course.

        Args:
            db_completed_course: The database completed course

        Returns:
            The corresponding UI completed course
        """
        return CompletedCourse(
            id=str(db_completed_course.id),
            user_id=str(db_completed_course.user_id),
            course_id=str(db_completed_course.course_id),
            completed_at=db_completed_course.completed_at,
            final_score=db_completed_course.final_score,
            total_time_spent=db_completed_course.total_time_spent,
            completed_lessons_count=db_completed_course.completed_lessons_count,
            achievements_earned=db_completed_course.achievements_earned,
            certificate_id=db_completed_course.certificate_id,
            created_at=db_completed_course.created_at,
            updated_at=db_completed_course.updated_at,
        )

    def _convert_db_user_content_progress_to_ui_user_content_progress(
        self, db_content_progress: DBUserContentProgress
    ) -> UserContentProgress:
        """
        Convert a database user content progress to a UI user content progress.

        Args:
            db_content_progress: The database user content progress

        Returns:
            The corresponding UI user content progress
        """
        return UserContentProgress(
            id=str(db_content_progress.id),
            user_id=str(db_content_progress.user_id),
            content_id=str(db_content_progress.content_id),
            lesson_id=(
                str(db_content_progress.lesson_id)
                if db_content_progress.lesson_id
                else None
            ),
            progress_id=(
                str(db_content_progress.progress_id)
                if db_content_progress.progress_id
                else None
            ),
            status=db_content_progress.status,
            score=db_content_progress.score,
            time_spent=db_content_progress.time_spent,
            last_interaction=db_content_progress.last_interaction,
            custom_data=db_content_progress.custom_data,
            created_at=db_content_progress.created_at,
            updated_at=db_content_progress.updated_at,
        )

    def mark_lesson_complete(self, user_id: str, lesson_id: str) -> bool:
        """
        Mark a lesson as complete for a user.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            True if the lesson was marked as complete, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            lesson = self.lesson_repo.get_lesson(self.db, lesson_uuid)
            if not lesson:
                logger.warning(f"Lesson not found with ID: {lesson_id}")
                return False

            course_id = lesson.course_id

            return self.complete_lesson(user_id, str(course_id), lesson_id)
        except Exception as e:
            logger.error(f"Error marking lesson as complete: {str(e)}")
            return False

    def get_lesson_score(self, user_id: str, lesson_id: str) -> float:
        """
        Get the user's score for a lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            The user's score for the lesson (0-100)
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            completed_lesson = self.completed_lesson_repo.get_by_user_and_lesson(
                self.db, user_uuid, lesson_uuid
            )

            if completed_lesson and completed_lesson.score is not None:
                return completed_lesson.score

            content_items = self.lesson_repo.get_lesson_content(self.db, lesson_uuid)
            if not content_items:
                return 0.0

            total_score = 0.0
            scored_items = 0

            for content in content_items:
                progress = self.user_content_progress_repo.get_progress(
                    self.db, user_uuid, content.id
                )
                if progress and progress.score is not None:
                    total_score += progress.score
                    scored_items += 1

            if scored_items == 0:
                return 0.0

            return total_score / scored_items
        except Exception as e:
            logger.error(f"Error getting lesson score: {str(e)}")
            return 0.0

    def get_completed_content_ids(self, user_id: str, lesson_id: str) -> List[str]:
        """
        Get the IDs of content items the user has completed in a lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            List of content IDs the user has completed
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            completed_lesson = self.completed_lesson_repo.get_lesson_completion(
                self.db, user_uuid, lesson_uuid
            )

            if completed_lesson:
                content_items = self.lesson_repo.get_lesson_content(
                    self.db, lesson_uuid
                )
                return [str(item.id) for item in content_items]

            content_items = self.lesson_repo.get_lesson_content(self.db, lesson_uuid)
            completed_ids = []

            for content in content_items:
                progress = self.user_content_progress_repo.get_progress(
                    self.db, user_uuid, content.id
                )
                if progress and progress.is_completed:
                    completed_ids.append(str(content.id))

            return completed_ids
        except Exception as e:
            logger.error(f"Error getting completed content IDs: {str(e)}")
            return []

    def get_time_spent_on_lesson(self, user_id: str, lesson_id: str) -> int:
        """
        Get the total time spent on a lesson by the user.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            Time spent in minutes
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            completed_lesson = self.completed_lesson_repo.get_lesson_completion(
                self.db, user_uuid, lesson_uuid
            )

            if completed_lesson and completed_lesson.time_spent is not None:
                return completed_lesson.time_spent

            content_items = self.lesson_repo.get_lesson_content(self.db, lesson_uuid)
            total_time = 0

            for content in content_items:
                progress = self.user_content_progress_repo.get_progress(
                    self.db, user_uuid, content.id
                )
                if progress and progress.time_spent is not None:
                    total_time += progress.time_spent

            return total_time
        except Exception as e:
            logger.error(f"Error getting time spent on lesson: {str(e)}")
            return 0

    def has_completed_content(self, user_id: str, content_id: str) -> bool:
        """
        Check if a user has completed a specific content item.

        Args:
            user_id: The ID of the user
            content_id: The ID of the content item

        Returns:
            True if the user has completed the content, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            progress = self.user_content_progress_repo.get_progress(
                self.db, user_uuid, content_uuid
            )

            return progress is not None and progress.is_completed
        except Exception as e:
            logger.error(f"Error checking if content is completed: {str(e)}")
            return False

    def get_assessment_score(self, user_id: str, lesson_id: str) -> Optional[float]:
        """
        Get the user's assessment score for a lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            The assessment score or None if not available
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            completed_lesson = self.completed_lesson_repo.get_lesson_completion(
                self.db, user_uuid, lesson_uuid
            )

            if completed_lesson and completed_lesson.score is not None:
                return completed_lesson.score

            content_items = self.lesson_repo.get_lesson_content(self.db, lesson_uuid)

            for content in content_items:
                if content.content_type.lower() in [
                    "assessment",
                    "quiz",
                    "test",
                    "exam",
                ]:
                    progress = self.user_content_progress_repo.get_progress(
                        self.db, user_uuid, content.id
                    )
                    if progress and progress.score is not None:
                        return progress.score

            return None
        except Exception as e:
            logger.error(f"Error getting assessment score: {str(e)}")
            return None

    def get_time_spent(self, user_id: str, lesson_id: str) -> Optional[int]:
        """
        Get the total time spent on a lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            Time spent in minutes or None if not available
        """
        try:
            return self.get_time_spent_on_lesson(user_id, lesson_id)
        except Exception as e:
            logger.error(f"Error getting time spent: {str(e)}")
            return None

    def get_activity_count(self, user_id: str, lesson_id: str) -> int:
        """
        Get the count of user activities in a lesson.

        Args:
            user_id: The ID of the user
            lesson_id: The ID of the lesson

        Returns:
            The number of activities recorded
        """
        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id)

            content_items = self.lesson_repo.get_lesson_content(self.db, lesson_uuid)

            activity_count = 0

            for content in content_items:
                progress = self.user_content_progress_repo.get_progress(
                    self.db, user_uuid, content.id
                )
                if progress:
                    activity_count += 1

            return activity_count
        except Exception as e:
            logger.error(f"Error getting activity count: {str(e)}")
            return 0

    def get_user_progress_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive progress statistics for a user.

        Args:
            user_id: The ID of the user (string, will be converted to UUID)

        Returns:
            Dictionary containing progress statistics
        """
        try:
            # Convert string to UUID object
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            with self.transaction() as session:
                # Get total courses
                total_courses = self.course_repo.count_all(session)

                # Count completed courses (is_completed=True from Progress table)
                completed_courses = self.progress_repo.get_completed_courses(
                    session, user_uuid
                )
                completed_courses_count = len(completed_courses)

                # Get total lessons
                total_lessons = self.lesson_repo.count_all(session)

                # Get completed lessons from CompletedLesson table
                completed_lessons = (
                    self.completed_lesson_repo.get_user_completed_lessons(
                        session, user_uuid
                    )
                )
                completed_lessons_count = len(completed_lessons)

                # Count all tasks from completed lessons
                from src.db.models import Content
                total_tasks_count = 0
                for completed_lesson in completed_lessons:
                    lesson_id = completed_lesson.lesson_id
                    task_count = (
                        session.query(Content)
                        .filter(Content.lesson_id == lesson_id)
                        .count()
                    )
                    total_tasks_count += task_count

                # Get courses by category
                informatics_courses = self.course_repo.get_by_topic(
                    session, "Інформатика"
                )
                mathematics_courses = self.course_repo.get_by_topic(
                    session, "Математика"
                )

                # Calculate category progress
                informatics_progress = self._calculate_category_progress(
                    user_uuid, informatics_courses
                )
                mathematics_progress = self._calculate_category_progress(
                    user_uuid, mathematics_courses
                )

                return {
                    "total_courses": total_courses,
                    "completed_courses": completed_courses_count,
                    "total_lessons": total_lessons,
                    "completed_lessons": completed_lessons_count,
                    "total_tasks": total_tasks_count,
                    "informatics_progress": informatics_progress,
                    "mathematics_progress": mathematics_progress,
                    "courses_by_category": {
                        "Інформатика": informatics_courses,
                        "Математика": mathematics_courses,
                    },
                }
        except Exception as e:
            logger.error(f"Error getting user progress stats: {str(e)}")
            return {
                "total_courses": 0,
                "completed_courses": 0,
                "total_lessons": 0,
                "completed_lessons": 0,
                "total_tasks": 0,
                "informatics_progress": 0.0,
                "mathematics_progress": 0.0,
                "courses_by_category": {"Інформатика": [], "Математика": []},
            }

    def _calculate_category_progress(self, user_id: uuid.UUID, courses: List) -> float:
        """
        Calculate average progress percentage for a category.

        Args:
            user_id: The user UUID
            courses: List of courses in the category

        Returns:
            Average progress percentage
        """
        if not courses:
            return 0.0

        total_progress = 0.0
        course_count = 0

        for course in courses:
            progress = self.progress_repo.get_course_progress(
                self.db, user_id, course.id
            )
            if progress:
                total_progress += progress.progress_percentage
                course_count += 1

        return total_progress / course_count if course_count > 0 else 0.0

    def _check_achievements_after_completion(self, user_id: str) -> None:
        """
        Check and award achievements after lesson/course completion.

        Args:
            user_id: The ID of the user
        """
        try:
            from src.services.achievement_service import AchievementService
            achievement_service = AchievementService()
            awarded = achievement_service.check_all_achievements(user_id)
            if awarded:
                logger.info(
                    f"Awarded {len(awarded)} achievements to user {user_id}"
                )
        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")

    def get_course_progress_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of courses with their progress information.

        Args:
            user_id: The ID of the user

        Returns:
            List of dictionaries with course progress information
        """
        try:
            user_uuid = uuid.UUID(user_id)

            with self.transaction() as session:
                courses = self.course_repo.get_all(session)
                course_progress_list = []

                for course in courses:
                    progress = self.progress_repo.get_course_progress(
                        session, user_uuid, course.id
                    )

                    # Get lesson count
                    lessons = self.lesson_repo.get_lessons_by_course_id(
                        session, course.id
                    )
                    total_lessons = len(lessons)

                    completed_lessons_count = 0
                    if progress:
                        completed_lessons_count = (
                            self.completed_lesson_repo.count_completed_lessons(
                                session, user_uuid, course.id
                            )
                        )

                    course_progress_list.append(
                        {
                            "id": str(course.id),
                            "title": course.name,
                            "description": course.description,
                            "topic": course.topic.value,
                            "total_lessons": total_lessons,
                            "completed_lessons": completed_lessons_count,
                            "progress_percentage": (
                                progress.progress_percentage if progress else 0.0
                            ),
                            "is_completed": (
                                progress.is_completed if progress else False
                            ),
                        }
                    )

                course_progress_list.sort(
                    key=lambda x: x["progress_percentage"], reverse=True
                )
                return course_progress_list

        except Exception as e:
            logger.error(f"Error getting course progress list: {str(e)}")
            return []

    def get_category_course_progress(
        self, user_id: str, topic: str
    ) -> List[Dict[str, Any]]:
        """
        Get course progress for a specific category/topic.

        Args:
            user_id: The ID of the user
            topic: The topic (Інформатика or Математика)

        Returns:
            List of course progress information for the topic
        """
        try:
            user_uuid = uuid.UUID(user_id)

            with self.transaction() as session:
                courses = self.course_repo.get_by_topic(session, topic)
                category_progress = []

                for course in courses:
                    progress = self.progress_repo.get_course_progress(
                        session, user_uuid, course.id
                    )

                    lessons = self.lesson_repo.get_lessons_by_course_id(
                        session, course.id
                    )
                    total_lessons = len(lessons)

                    completed_lessons_count = 0
                    if progress:
                        completed_lessons_count = (
                            self.completed_lesson_repo.count_completed_lessons(
                                session, user_uuid, course.id
                            )
                        )

                    category_progress.append(
                        {
                            "id": str(course.id),
                            "title": course.name,
                            "total_lessons": total_lessons,
                            "completed_lessons": completed_lessons_count,
                            "progress_percentage": (
                                progress.progress_percentage if progress else 0.0
                            ),
                        }
                    )

                category_progress.sort(
                    key=lambda x: x["progress_percentage"], reverse=True
                )
                return category_progress

        except Exception as e:
            logger.error(f"Error getting category course progress: {str(e)}")
            return []

    def has_content_interaction(self, user_id: str, content_id: str) -> bool:
        """
        Check if a user has interacted with a specific content item.

        Args:
            user_id: The ID of the user
            content_id: The ID of the content item

        Returns:
            True if the user has interacted with the content, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            progress = self.user_content_progress_repo.get_progress(
                self.db, user_uuid, content_uuid
            )

            return progress is not None
        except Exception as e:
            logger.error(f"Error checking content interaction: {str(e)}")
            return False

    def calculate_weighted_course_progress(
        self, user_id: str, course_id: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate a weighted progress percentage based on content difficulty and importance.

        This method implements a more sophisticated progress calculation algorithm that
        considers each content item's difficulty level and assigned importance when
        calculating overall course progress. Content with higher difficulty or importance
        contributes more to the overall progress percentage.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            A tuple containing:
            - The weighted progress percentage (0-100)
            - A dictionary with detailed progress metrics
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            lessons = self.lesson_repo.get_lessons_by_course_id(self.db, course_uuid)
            if not lessons:
                logger.warning(f"No lessons found for course ID: {course_id}")
                return 0.0, {"status": "no_lessons", "details": {}}

            all_content = []
            lesson_weights = {}
            for lesson in lessons:
                lesson_obj, content_items = self.lesson_repo.get_lesson_with_content(
                    self.db, lesson.id
                )
                all_content.extend(content_items)

                order_factor = lesson.lesson_order / len(lessons)  # Normalized to 0-1
                difficulty_factor = (
                    lesson.difficulty_level.value / 5.0
                )  # Assuming 5 levels, normalized to 0-1

                lesson_weights[str(lesson.id)] = (
                    0.5 + ((order_factor + difficulty_factor) / 2) * 0.5
                )

            if not all_content:
                logger.warning(f"No content items found for course ID: {course_id}")
                return 0.0, {"status": "no_content", "details": {}}

            content_weights = {}
            total_weight = 0.0

            for content in all_content:
                base_weight = 1.0
                if content.content_type.lower() in ["assessment", "quiz", "exam"]:
                    base_weight = 2.0  # Assessments count twice as much
                elif content.content_type.lower() in ["exercise", "practice"]:
                    base_weight = 1.5  # Exercises count 1.5 times as much

                if hasattr(content, "metadata") and content.metadata:
                    importance = content.metadata.get("importance", 1.0)
                    base_weight *= importance

                    points = content.metadata.get("points", 1.0)
                    base_weight *= points

                lesson_id = (
                    str(content.lesson_id) if hasattr(content, "lesson_id") else None
                )
                if lesson_id and lesson_id in lesson_weights:
                    base_weight *= lesson_weights[lesson_id]

                content_weights[str(content.id)] = base_weight
                total_weight += base_weight

            if total_weight > 0:
                for content_id in content_weights:
                    content_weights[content_id] /= total_weight

            completed_content_ids = set()
            partial_content_progress = {}

            for content in all_content:
                content_id = str(content.id)

                progress = self.user_content_progress_repo.get_progress(
                    self.db, user_uuid, content.id
                )

                if progress:
                    if progress.status.lower() == "completed":
                        completed_content_ids.add(content_id)
                    elif (
                        hasattr(progress, "percentage")
                        and progress.percentage is not None
                    ):
                        partial_content_progress[content_id] = (
                            progress.percentage / 100.0
                        )
                    elif hasattr(progress, "score") and progress.score is not None:
                        partial_content_progress[content_id] = progress.score / 100.0

            weighted_progress = 0.0

            for content_id in completed_content_ids:
                weighted_progress += content_weights.get(content_id, 0.0)

            for content_id, partial in partial_content_progress.items():
                if content_id not in completed_content_ids:
                    weighted_progress += content_weights.get(content_id, 0.0) * partial

            weighted_percentage = float(weighted_progress * 100.0)

            details = {
                "completed_count": len(completed_content_ids),
                "total_count": len(all_content),
                "completion_ratio": len(completed_content_ids) / len(all_content),
                "partial_progress_count": len(partial_content_progress),
                "content_weights": content_weights,
                "lesson_weights": lesson_weights,
            }

            progress_record = self.progress_repo.get_course_progress(
                self.db, user_uuid, course_uuid
            )
            if progress_record:
                self.progress_repo.update_progress_percentage(
                    self.db, progress_record.id, weighted_percentage
                )

                self.progress_repo.update_progress_data(
                    self.db,
                    progress_record.id,
                    {
                        "weighted_calculation": details,
                        "last_calculation": datetime.utcnow().isoformat(),
                    },
                )

            return weighted_percentage, {"status": "success", "details": details}
        except Exception as e:
            logger.error(f"Error calculating weighted progress: {str(e)}")
            return 0.0, {"status": "error", "message": str(e)}

    def update_course_progress_with_weighting(
        self, user_id: str, course_id: str
    ) -> Optional[Progress]:
        """
        Update course progress using the weighted calculation algorithm.

        This method applies the weighted progress calculation and updates the progress record
        in the database, returning the updated Progress model.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            The updated progress record if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            progress_record = self.progress_repo.get_course_progress(
                self.db, user_uuid, course_uuid
            )
            if not progress_record:
                progress_record = self.create_course_progress(user_id, course_id)
                if not progress_record:
                    return None

            weighted_percentage, details = self.calculate_weighted_course_progress(
                user_id, course_id
            )

            if details.get("status") == "success":
                updated_record = self.progress_repo.get_course_progress(
                    self.db, user_uuid, course_uuid
                )
                if updated_record:
                    return self._convert_db_progress_to_ui_progress(updated_record)

            return None
        except Exception as e:
            logger.error(f"Error updating course progress with weighting: {str(e)}")
            return None

    def sync_progress_data(self, user_id: str, course_id: str) -> bool:
        """
        Synchronize progress data between related repositories.

        This method ensures that progress data is consistent across different repositories,
        such as updating progress percentages when lessons are completed or ensuring
        that completed lesson counts match the course progress.

        Args:
            user_id: The ID of the user
            course_id: The ID of the course

        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            course_uuid = uuid.UUID(course_id)

            progress = self.progress_repo.get_course_progress(
                self.db, user_uuid, course_uuid
            )
            if not progress:
                logger.warning(
                    f"No progress record found for user {user_id} in course {course_id}"
                )
                return False

            lessons = self.lesson_repo.get_lessons_by_course_id(self.db, course_uuid)
            if not lessons:
                logger.warning(f"No lessons found for course {course_id}")
                return False

            completed_lessons = self.completed_lesson_repo.get_course_completed_lessons(
                self.db, user_uuid, course_uuid
            )
            completed_lesson_ids = {
                str(lesson.lesson_id) for lesson in completed_lessons
            }

            total_lessons = len(lessons)
            completed_count = len(completed_lesson_ids)
            simple_percentage = (
                (completed_count / total_lessons * 100) if total_lessons > 0 else 0
            )

            course_completion = self.completed_course_repo.get_course_completion(
                self.db, user_uuid, course_uuid
            )

            content_progress = []
            for lesson in lessons:
                lesson_obj, content_items = self.lesson_repo.get_lesson_with_content(
                    self.db, lesson.id
                )
                for content in content_items:
                    progress_item = self.user_content_progress_repo.get_progress(
                        self.db, user_uuid, content.id
                    )
                    if progress_item:
                        content_progress.append(progress_item)

            total_time_spent = sum(
                item.time_spent
                for item in content_progress
                if item.time_spent is not None
            )

            scores = [item.score for item in content_progress if item.score is not None]
            avg_score = sum(scores) / len(scores) if scores else None

            updates = {
                "time_spent": total_time_spent,
                "progress_data": {
                    "completed_lesson_count": completed_count,
                    "total_lesson_count": total_lessons,
                    "simple_percentage": simple_percentage,
                    "average_score": avg_score,
                    "content_progress_count": len(content_progress),
                    "last_sync": datetime.utcnow().isoformat(),
                },
            }

            self.progress_repo.update_progress_data(
                self.db, progress.id, updates["progress_data"]
            )

            if (
                completed_count == total_lessons
                and total_lessons > 0
                and not progress.is_completed
            ):
                self.progress_repo.complete_progress(self.db, progress.id)

                if not course_completion:
                    self.completed_course_repo.create_completed_course(
                        self.db,
                        user_id=user_uuid,
                        course_id=course_uuid,
                        final_score=avg_score,
                        total_time_spent=total_time_spent,
                        completed_lessons_count=completed_count,
                    )

            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error synchronizing progress data: {str(e)}")
            self.db.rollback()
            return False

    def get_user_activity_by_day(self, user_id: str) -> tuple:
        """
        Get user completed lessons for the last 7 days to populate the activity graph.

        Args:
            user_id: The ID of the user

        Returns:
            Tuple containing (list of activity counts, list of day labels)
        """
        default_data = [0, 0, 0, 0, 0, 0, 0]
        default_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

        try:
            if not user_id:
                logger.info("No user ID provided for activity data")
                return default_data, default_labels

            user_uuid = uuid.UUID(user_id)

            completed_count = self.completed_lesson_repo.count_user_completed_lessons(
                self.db, user_uuid
            )

            logger.info(
                f"Found {completed_count} total completed lessons for user {user_id}"
            )

            if completed_count == 0:
                logger.info("No completed lessons found, returning zeros")
                return default_data, default_labels

            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            logger.info(
                f"Getting completed lessons since: {seven_days_ago.strftime('%Y-%m-%d')}"
            )

            rows = self.completed_lesson_repo.get_user_completed_lessons_count_by_day(
                self.db, user_uuid, seven_days_ago
            )

            day_counts = {
                (row.day.strftime("%Y-%m-%d") if hasattr(row.day, "strftime") else str(row.day)): row.count
                for row in rows
            }
            logger.info(f"Raw completed lessons by day: {day_counts}")

            today = datetime.now(timezone.utc).date()
            day_names = {
                0: "Пн",
                1: "Вт",
                2: "Ср",
                3: "Чт",
                4: "Пт",
                5: "Сб",
                6: "Нд",
            }

            data = []
            labels = []

            logger.info(f"Day-by-day activity data:")
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                weekday = day.weekday()
                day_iso = day.strftime("%Y-%m-%d")
                count = day_counts.get(day_iso, 0)

                data.append(count)
                labels.append(day_names[weekday])
                logger.info(
                    f"  {day_iso} ({day_names[weekday]}): {count} completed lessons"
                )

            logger.info(f"Activity data for chart: {data}")
            logger.info(f"Activity labels for chart: {labels}")

            return data, labels

        except Exception as e:
            logger.error(
                f"Error getting user completed lessons data: {e}", exc_info=True
            )
            return default_data, default_labels

    def get_all_progress(self) -> List[Progress]:
        try:
            db_records = self.progress_repo.get_all(self.db)
            return [self._convert_db_progress_to_ui_progress(r) for r in db_records]
        except Exception as e:
            logger.error(f"Error getting all progress: {str(e)}")
            return []
