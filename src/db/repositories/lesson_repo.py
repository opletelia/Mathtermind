"""
Repository module for Lesson model in the Mathtermind application.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

from src.db.models import Content, Lesson
from src.models.content import ExerciseContent, TheoryContent

from .base_repository import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    """Repository for Lesson model."""

    def __init__(self):
        """Initialize the repository with the Lesson model."""
        super().__init__(Lesson)

    def get_lesson(self, db: Session, lesson_id: uuid.UUID) -> Optional[Lesson]:
        """
        Get a lesson by its ID. Alias for get_by_id.

        Args:
            db: Database session
            lesson_id: Lesson ID

        Returns:
            Lesson if found, None otherwise
        """
        return self.get_by_id(db, lesson_id)

    def create_lesson(
        self,
        db: Session,
        course_id: uuid.UUID,
        title: str,
        lesson_order: int,
        estimated_time: int = 0,
        points_reward: int = 10,
        section: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
    ) -> Lesson:

        lesson = Lesson(
            course_id=course_id,
            title=title,
            section=section,
            lesson_order=lesson_order,
            estimated_time=estimated_time,
            points_reward=points_reward,
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        theory_text = content.get("theory") if content else None
        if theory_text:
            theory_content = TheoryContent(id=lesson.id, text_content=theory_text)
            db.add(theory_content)

        tasks_data = content.get("tasks") if content else None
        if tasks_data:
            exercise_content = ExerciseContent(id=lesson.id, problems=tasks_data)
            db.add(exercise_content)

        db.commit()
        return lesson

    def update_lesson(
        self,
        db: Session,
        lesson_id: uuid.UUID,
        title: Optional[str] = None,
        lesson_order: Optional[int] = None,
        prerequisites: Optional[Dict[str, Any]] = None,
        estimated_time: Optional[int] = None,
        # difficulty_level: Optional[str] = None,
        points_reward: Optional[int] = None,
        learning_objectives: Optional[List[str]] = None,
        content: Optional[Dict[str, Any]] = None,
        is_required: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        # ,lesson_type: Optional[str] = None
    ) -> Optional[Lesson]:
        """
        Update a lesson.

        Args:
            db: Database session
            lesson_id: Lesson ID
            title: New lesson title
            lesson_order: New display order
            prerequisites: New dictionary of prerequisite lessons
            estimated_time: New estimated time to complete
            difficulty_level: New difficulty level
            points_reward: New points reward
            learning_objectives: New learning objectives
            content: New content
            is_required: New required status
            metadata: New metadata to merge with existing
            lesson_type: Deprecated parameter, kept for database compatibility

        Returns:
            Updated lesson or None if not found

        Note:
            lesson_type is deprecated. Lessons are containers for content items.
            Content items have types, not lessons.
        """
        lesson = self.get_by_id(db, lesson_id)
        if lesson:
            if title is not None:
                lesson.title = title

            """if lesson_type is not None:
                # This is kept for database compatibility but is deprecated
                lesson.lesson_type = lesson_type"""

            if lesson_order is not None:
                lesson.lesson_order = lesson_order

            if prerequisites is not None:
                lesson.prerequisites = prerequisites

            if estimated_time is not None:
                lesson.estimated_time = estimated_time

            """if difficulty_level is not None:
                lesson.difficulty_level = difficulty_level"""

            if points_reward is not None:
                lesson.points_reward = points_reward

            if learning_objectives is not None:
                lesson.learning_objectives = learning_objectives

            if content is not None:
                lesson.content = content

            if is_required is not None:
                lesson.is_required = is_required

            if metadata is not None:
                if not lesson.metadata:
                    lesson.metadata = {}
                lesson.metadata.update(metadata)

            db.commit()
            db.refresh(lesson)
        return lesson

    def delete_lesson(self, db: Session, lesson_id: uuid.UUID) -> Optional[Lesson]:
        """
        Delete a lesson.

        Args:
            db: Database session
            lesson_id: Lesson ID

        Returns:
            Deleted lesson or None if not found
        """
        lesson = self.get_by_id(db, lesson_id)
        if lesson:
            db.delete(lesson)
            db.commit()
        return lesson

    def get_lessons_by_course_id(
        self, db: Session, course_id: uuid.UUID
    ) -> List[Lesson]:
        """
        Get all lessons for a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            List of lessons
        """
        return (
            db.query(Lesson)
            .options(selectinload(Lesson.contents))
            .filter(Lesson.course_id == course_id)
            .order_by(Lesson.lesson_order)
            .all()
        )

    def get_required_lessons(self, db: Session, course_id: uuid.UUID) -> List[Lesson]:
        """
        Get all required lessons for a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            List of required lessons
        """
        return (
            db.query(Lesson)
            .filter(Lesson.course_id == course_id, Lesson.is_required == True)
            .order_by(Lesson.lesson_order)
            .all()
        )

    def get_lesson_with_content(
        self, db: Session, lesson_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get a lesson with all its content items.

        Args:
            db: Database session
            lesson_id: Lesson ID

        Returns:
            Dictionary with lesson and content items
        """
        lesson = self.get_by_id(db, lesson_id)
        if not lesson:
            return None

        content_items = (
            db.query(Content)
            .filter(Content.lesson_id == lesson_id)
            .order_by(Content.order)
            .all()
        )

        return {"lesson": lesson, "content": content_items}

    def update_lesson_order(
        self, db: Session, lesson_id: uuid.UUID, new_order: int
    ) -> Optional[Lesson]:
        """
        Update the order of a lesson.

        Args:
            db: Database session
            lesson_id: Lesson ID
            new_order: New display order

        Returns:
            Updated lesson or None if not found
        """
        return self.update_lesson(db, lesson_id, lesson_order=new_order)

    def get_prerequisite_lessons(
        self, db: Session, lesson_id: uuid.UUID
    ) -> List[Lesson]:
        """
        Get all prerequisite lessons for a lesson.

        Args:
            db: Database session
            lesson_id: Lesson ID

        Returns:
            List of prerequisite lessons
        """
        lesson = self.get_by_id(db, lesson_id)
        if not lesson or not lesson.prerequisites:
            return []

        return db.query(Lesson).filter(Lesson.id.in_(lesson.prerequisites)).all()

    def get_dependent_lessons(self, db: Session, lesson_id: uuid.UUID) -> List[Lesson]:
        """
        Get all lessons that have this lesson as a prerequisite.

        Args:
            db: Database session
            lesson_id: Lesson ID

        Returns:
            List of dependent lessons
        """
        lessons = db.query(Lesson).all()
        dependent_lessons = []

        for lesson in lessons:
            if lesson.prerequisites and lesson_id in lesson.prerequisites:
                dependent_lessons.append(lesson)

        return dependent_lessons

    def count_all(self, db: Session) -> int:
        """
        Count all lessons in the database.

        Args:
            db: Database session

        Returns:
            Total number of lessons
        """
        return db.query(Lesson).count()

    def update_lesson_metadata(
        self, db: Session, lesson_id: uuid.UUID, metadata: Dict[str, Any]
    ) -> Optional[Lesson]:
        """
        Update the metadata of a lesson.

        Args:
            db: Database session
            lesson_id: Lesson ID
            metadata: New metadata to merge with existing

        Returns:
            Updated lesson or None if not found
        """
        return self.update_lesson(db, lesson_id, metadata=metadata)

    def get_all_lessons(self, db: Session) -> List[Lesson]:
        """
        Get all lessons.

        Args:
            db: Database session

        Returns:
            List of all lessons
        """
        return db.query(Lesson).all()
