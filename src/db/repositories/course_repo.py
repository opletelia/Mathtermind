"""
Repository module for Course model in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import Course, Lesson

from .base_repository import BaseRepository


class CourseRepository(BaseRepository[Course]):
    """Repository for Course model."""

    def __init__(self):
        """Initialize the repository with the Course model."""
        super().__init__(Course)

    def get_all_courses(self, db: Session) -> List[Course]:
        """
        Get all courses.

        Args:
            db: Database session

        Returns:
            List of all courses
        """
        return db.query(Course).all()

    def get_course(self, db: Session, course_id: uuid.UUID) -> Optional[Course]:
        """
        Get a course by ID.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            Course if found, None otherwise
        """
        return self.get_by_id(db, course_id)

    def create_course(
        self,
        db: Session,
        topic: str,
        name: str,
        description: str,
        # difficulty_level: str = "beginner",
        # target_age_group: str = "15-17",
        duration: Optional[int] = None,  # ,
        # prerequisites: Optional[List[uuid.UUID]] = None,
        # tags: Optional[List[str]] = None,
        # is_published: bool = False,
        # thumbnail_url: Optional[str] = None,
        # points_reward: int = 100,
        # author_id: Optional[uuid.UUID] = None,
        # metadata: Optional[Dict[str, Any]] = None
    ) -> Course:
        """
        Create a new course.

        Args:
            db: Database session
            topic: Course topic (math, programming, etc.)
            name: Course name
            description: Course description
            difficulty_level: Course difficulty level (beginner, intermediate, advanced)
            target_age_group: Target age group
            estimated_time: Estimated time to complete in minutes
            prerequisites: List of prerequisite course IDs
            tags: List of tags
            is_published: Whether the course is published
            thumbnail_url: URL to course thumbnail image
            points_reward: Points reward for completing the course
            author_id: Author/creator user ID
            metadata: Additional metadata

        Returns:
            Created course
        """
        course = Course(
            topic=topic,
            name=name,
            description=description,
            # difficulty_level=difficulty_level,
            # target_age_group=target_age_group,
            duration=duration,  # ,
            # prerequisites=prerequisites or [],
            # tags=tags or [],
            # is_published=is_published,
            # humbnail_url=thumbnail_url,
            # points_reward=points_reward,
            # author_id=author_id,
            # created_at=datetime.now(timezone.utc),
            # metadata=metadata or {}
        )

        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    def update_course(
        self,
        db: Session,
        course_id: uuid.UUID,
        topic: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        # difficulty_level: Optional[str] = None,
        # target_age_group: Optional[str] = None,
        duration: Optional[int] = None,  # ,
        # prerequisites: Optional[List[uuid.UUID]] = None,
        # tags: Optional[List[str]] = None,
        # is_published: Optional[bool] = None,
        # thumbnail_url: Optional[str] = None,
        # points_reward: Optional[int] = None,
        # metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Course]:
        """
        Update a course.

        Args:
            db: Database session
            course_id: Course ID
            topic: New course topic
            name: New course name
            description: New course description
            difficulty_level: New difficulty level
            target_age_group: New target age group
            estimated_time: New estimated time
            prerequisites: New list of prerequisite course IDs
            tags: New list of tags
            is_published: New published status
            thumbnail_url: New thumbnail URL
            points_reward: New points reward
            metadata: New metadata to merge with existing

        Returns:
            Updated course or None if not found
        """
        course = self.get_by_id(db, course_id)
        if course:
            if topic is not None:
                course.topic = topic

            if name is not None:
                course.name = name

            """if description is not None:
                course.description = description
                
            if difficulty_level is not None:
                course.difficulty_level = difficulty_level
                
            if target_age_group is not None:
                course.target_age_group = target_age_group"""

            if duration is not None:
                course.duration = duration

            """if prerequisites is not None:
                course.prerequisites = prerequisites
                
            if tags is not None:
                course.tags = tags
                
            if is_published is not None:
                course.is_published = is_published
                
            if thumbnail_url is not None:
                course.thumbnail_url = thumbnail_url
                
            if points_reward is not None:
                course.points_reward = points_reward
                
            if metadata is not None:
                if not course.metadata:
                    course.metadata = {}
                course.metadata.update(metadata)"""

            # Update last modified time
            course.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(course)
        return course

    def delete_course(self, db, course_id):
        if isinstance(course_id, str):
            course_id = UUID(course_id)

        course = db.query(Course).filter(Course.id == course_id).first()

        if course:
            db.delete(course)
            db.commit()

        return course

    def get_courses_by_topic(self, db: Session, topic: str) -> List[Course]:
        """
        Get all courses for a topic.

        Args:
            db: Database session
            topic: Course topic

        Returns:
            List of courses
        """
        return db.query(Course).filter(Course.topic == topic).all()

    def get_published_courses(self, db: Session) -> List[Course]:
        """
        Get all published courses.

        Args:
            db: Database session

        Returns:
            List of published courses
        """
        return db.query(Course).filter(Course.is_published == True).all()

    def get_courses_with_lessons(
        self, db: Session, course_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get a course with all its lessons.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            Dictionary with course and lessons
        """
        course = self.get_by_id(db, course_id)
        if not course:
            return None

        lessons = (
            db.query(Lesson)
            .filter(Lesson.course_id == course_id)
            .order_by(Lesson.order)
            .all()
        )

        return {"course": course, "lessons": lessons}

    def publish_course(self, db: Session, course_id: uuid.UUID) -> Optional[Course]:
        """
        Publish a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            Updated course or None if not found
        """
        return self.update_course(db, course_id, is_published=True)

    def unpublish_course(self, db: Session, course_id: uuid.UUID) -> Optional[Course]:
        """
        Unpublish a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            Updated course or None if not found
        """
        return self.update_course(db, course_id, is_published=False)

    def search_courses(
        self,
        db: Session,
        query: str,
        topic: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        published_only: bool = True,
    ) -> List[Course]:
        """
        Search for courses.

        Args:
            db: Database session
            query: Search query
            topic: Optional topic filter
            difficulty_level: Optional difficulty level filter
            published_only: Whether to return only published courses

        Returns:
            List of matching courses
        """
        search_filter = Course.name.ilike(f"%{query}%") | Course.description.ilike(
            f"%{query}%"
        )

        filters = [search_filter]

        if topic:
            filters.append(Course.topic == topic)

        if difficulty_level:
            filters.append(Course.difficulty_level == difficulty_level)

        if published_only:
            filters.append(Course.is_published == True)

        return db.query(Course).filter(*filters).all()

    def get_courses_by_tag(self, db: Session, tag: str) -> List[Course]:
        """
        Get all courses with a specific tag.

        Args:
            db: Database session
            tag: Tag to search for

        Returns:
            List of courses with the tag
        """
        # Note: This is inefficient in SQL but works for JSONB arrays
        courses = db.query(Course).all()
        return [c for c in courses if c.tags and tag in c.tags]

    def get_prerequisite_courses(
        self, db: Session, course_id: uuid.UUID
    ) -> List[Course]:
        """
        Get all prerequisite courses for a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            List of prerequisite courses
        """
        course = self.get_by_id(db, course_id)
        if not course or not course.prerequisites:
            return []

        # Convert string IDs to UUIDs for query
        prerequisite_uuids = [uuid.UUID(pid) for pid in course.prerequisites]
        return db.query(Course).filter(Course.id.in_(prerequisite_uuids)).all()

    def get_by_topic(self, db: Session, topic: str) -> List[Course]:
        """
        Get all courses for a specific topic.

        Args:
            db: Database session
            topic: Course topic

        Returns:
            List of courses for the topic
        """
        return db.query(Course).filter(Course.topic == topic).all()

    def count_all(self, db: Session) -> int:
        """
        Count all courses in the database.

        Args:
            db: Database session

        Returns:
            Total number of courses
        """
        return db.query(Course).count()

    def update_course_metadata(
        self, db: Session, course_id: uuid.UUID, metadata: Dict[str, Any]
    ) -> Optional[Course]:
        """
        Update the metadata of a course.

        Args:
            db: Database session
            course_id: Course ID
            metadata: New metadata to merge with existing

        Returns:
            Updated course or None if not found
        """
        return self.update_course(db, course_id, metadata=metadata)
