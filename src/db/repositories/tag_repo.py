"""
Repository module for Tag entity operations.

This module contains the TagRepository class, which handles database
operations related to tags in the Mathtermind application.
"""

import logging
import uuid
from typing import List, Optional, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.models.content import Course, CourseTag, Tag
from src.db.models.enums import Category


class TagRepository:
    """Repository for Tag entity."""

    def create_tag(
        self, session: Session, name: str, category: Category
    ) -> Optional[Tag]:
        """
        Create a new tag in the database.

        Args:
            session: The database session
            name: The name of the tag
            category: The category of the tag

        Returns:
            The created Tag instance, or None if an error occurred
        """
        try:
            tag = Tag(id=uuid.uuid4(), name=name, category=category)
            session.add(tag)
            session.commit()
            return tag
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating tag: {str(e)}")
            return None

    def get_tag_by_id(self, session: Session, tag_id: uuid.UUID) -> Optional[Tag]:
        """
        Get a tag by its ID.

        Args:
            session: The database session
            tag_id: The ID of the tag to retrieve

        Returns:
            The Tag instance, or None if not found
        """
        try:
            return session.query(Tag).filter(Tag.id == tag_id).first()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving tag by ID: {str(e)}")
            return None

    def get_tag_by_name(self, session: Session, name: str) -> Optional[Tag]:
        """
        Get a tag by its name.

        Args:
            session: The database session
            name: The name of the tag to retrieve

        Returns:
            The Tag instance, or None if not found
        """
        try:
            return session.query(Tag).filter(Tag.name == name).first()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving tag by name: {str(e)}")
            return None

    def get_all_tags(self, session: Session) -> List[Tag]:
        """
        Get all tags in the database.

        Args:
            session: The database session

        Returns:
            List of all Tag instances
        """
        try:
            return session.query(Tag).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving all tags: {str(e)}")
            return []

    def get_tags_by_category(self, session: Session, category: Category) -> List[Tag]:
        """
        Get all tags of a specific category.

        Args:
            session: The database session
            category: The category to filter by

        Returns:
            List of Tag instances in the specified category
        """
        try:
            return session.query(Tag).filter(Tag.category == category).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving tags by category: {str(e)}")
            return []

    def update_tag(
        self,
        session: Session,
        tag_id: uuid.UUID,
        name: Optional[str] = None,
        category: Optional[Category] = None,
    ) -> Optional[Tag]:
        """
        Update a tag in the database.

        Args:
            session: The database session
            tag_id: The ID of the tag to update
            name: The new name for the tag (optional)
            category: The new category for the tag (optional)

        Returns:
            The updated Tag instance, or None if not found or if an error occurred
        """
        try:
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                return None

            if name is not None:
                tag.name = name
            if category is not None:
                tag.category = category

            session.commit()
            return tag
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error updating tag: {str(e)}")
            return None

    def delete_tag(self, session: Session, tag_id: uuid.UUID) -> bool:
        """
        Delete a tag from the database.

        Args:
            session: The database session
            tag_id: The ID of the tag to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                return False

            session.delete(tag)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error deleting tag: {str(e)}")
            return False

    def add_tag_to_course(
        self, session: Session, tag_id: uuid.UUID, course_id: uuid.UUID
    ) -> bool:
        """
        Associate a tag with a course.

        Args:
            session: The database session
            tag_id: The ID of the tag
            course_id: The ID of the course

        Returns:
            True if association was successful, False otherwise
        """
        try:
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                logging.error(f"Tag with ID {tag_id} not found")
                return False

            course = session.query(Course).filter(Course.id == course_id).first()
            if not course:
                logging.error(f"Course with ID {course_id} not found")
                return False

            existing = (
                session.query(CourseTag)
                .filter(CourseTag.tag_id == tag_id, CourseTag.course_id == course_id)
                .first()
            )

            if existing:
                logging.info(f"Tag {tag_id} already associated with course {course_id}")
                return True

            course_tag = CourseTag(tag_id=tag_id, course_id=course_id)
            session.add(course_tag)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error adding tag to course: {str(e)}")
            return False

    def remove_tag_from_course(
        self, session: Session, tag_id: uuid.UUID, course_id: uuid.UUID
    ) -> bool:
        """
        Remove a tag association from a course.

        Args:
            session: The database session
            tag_id: The ID of the tag
            course_id: The ID of the course

        Returns:
            True if removal was successful, False otherwise
        """
        try:
            association = (
                session.query(CourseTag)
                .filter(CourseTag.tag_id == tag_id, CourseTag.course_id == course_id)
                .first()
            )

            if not association:
                logging.error(
                    f"Association between tag {tag_id} and course {course_id} not found"
                )
                return False

            session.delete(association)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error removing tag from course: {str(e)}")
            return False

    def get_course_tags(self, session: Session, course_id: uuid.UUID) -> List[Tag]:
        """
        Get all tags associated with a specific course.

        Args:
            session: The database session
            course_id: The ID of the course

        Returns:
            List of Tag instances associated with the course
        """
        try:
            return (
                session.query(Tag)
                .join(CourseTag, Tag.id == CourseTag.tag_id)
                .filter(CourseTag.course_id == course_id)
                .all()
            )
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving course tags: {str(e)}")
            return []

    def get_courses_by_tag(self, session: Session, tag_id: uuid.UUID) -> List[Course]:
        """
        Get all courses associated with a specific tag.

        Args:
            session: The database session
            tag_id: The ID of the tag

        Returns:
            List of Course instances associated with the tag
        """
        try:
            return (
                session.query(Course)
                .join(CourseTag, Course.id == CourseTag.course_id)
                .filter(CourseTag.tag_id == tag_id)
                .all()
            )
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving courses by tag: {str(e)}")
            return []
