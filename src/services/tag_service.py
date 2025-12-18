import uuid
from typing import List, Optional, Union

from src.core import get_logger
from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ServiceError, create_error_boundary,
                                     handle_service_errors, report_error)
from src.db.models.content import Tag as DbTag
from src.db.models.enums import Category
from src.db.repositories.tag_repo import TagRepository
from src.models.course import Course
from src.models.tag import Tag, TagCategory
from src.services.base_service import BaseService

logger = get_logger(__name__)


class TagService(BaseService):
    """
    Service for managing tags.

    This service provides methods for creating, retrieving, updating, and deleting tags,
    as well as associating tags with courses.
    """

    def __init__(self, tag_repository=None, test_session=None):
        """
        Initialize the TagService.

        Args:
            tag_repository: The tag repository to use. If None, a new instance will be created.
            test_session: Optional test session to use instead of self.db (for testing)
        """
        super().__init__(repository=tag_repository or TagRepository())
        logger.debug("TagService initialized")

        if test_session is not None:
            self.db = test_session

    @handle_service_errors(service_name="tag")
    def create_tag(self, name: str, category: TagCategory) -> Optional[Tag]:
        """
        Create a new tag.

        Args:
            name: The name of the tag
            category: The category of the tag

        Returns:
            The created tag, or None if creation failed
        """
        logger.info(f"Creating tag: {name}, category: {category}")

        db_category = self._convert_ui_category_to_db_category(category)

        db_tag = self.repository.create_tag(self.db, name, db_category)
        if not db_tag:
            logger.error(f"Failed to create tag: {name}")
            return None

        return self._convert_db_tag_to_ui_tag(db_tag)

    @handle_service_errors(service_name="tag")
    def get_tag_by_id(self, tag_id: str) -> Optional[Tag]:
        """
        Get a tag by its ID.

        Args:
            tag_id: The ID of the tag to retrieve

        Returns:
            The tag, or None if not found
        """
        logger.info(f"Getting tag by ID: {tag_id}")

        try:
            tag_uuid = uuid.UUID(tag_id)

            db_tag = self.repository.get_tag_by_id(self.db, tag_uuid)
            if not db_tag:
                logger.warning(f"Tag with ID {tag_id} not found")
                return None

            return self._convert_db_tag_to_ui_tag(db_tag)
        except ValueError:
            logger.error(f"Invalid tag ID format: {tag_id}")
            return None

    @handle_service_errors(service_name="tag")
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Get a tag by its name.

        Args:
            name: The name of the tag to retrieve

        Returns:
            The tag, or None if not found
        """
        logger.info(f"Getting tag by name: {name}")

        db_tag = self.repository.get_tag_by_name(self.db, name)
        if not db_tag:
            logger.warning(f"Tag with name '{name}' not found")
            return None

        return self._convert_db_tag_to_ui_tag(db_tag)

    @handle_service_errors(service_name="tag")
    def get_all_tags(self) -> List[Tag]:
        """
        Get all tags.

        Returns:
            List of all tags
        """
        logger.info("Getting all tags")

        db_tags = self.repository.get_all_tags(self.db)

        ui_tags = [self._convert_db_tag_to_ui_tag(db_tag) for db_tag in db_tags]

        logger.debug(f"Found {len(ui_tags)} tags")
        return ui_tags

    @handle_service_errors(service_name="tag")
    def get_tags_by_category(self, category: TagCategory) -> List[Tag]:
        """
        Get all tags of a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of tags in the specified category
        """
        logger.info(f"Getting tags by category: {category}")

        db_category = self._convert_ui_category_to_db_category(category)

        db_tags = self.repository.get_tags_by_category(self.db, db_category)

        ui_tags = [self._convert_db_tag_to_ui_tag(db_tag) for db_tag in db_tags]

        logger.debug(f"Found {len(ui_tags)} tags in category {category}")
        return ui_tags

    @handle_service_errors(service_name="tag")
    def update_tag(
        self,
        tag_id: str,
        name: Optional[str] = None,
        category: Optional[TagCategory] = None,
    ) -> Optional[Tag]:
        """
        Update a tag.

        Args:
            tag_id: The ID of the tag to update
            name: The new name for the tag (optional)
            category: The new category for the tag (optional)

        Returns:
            The updated tag, or None if update failed
        """
        logger.info(f"Updating tag: {tag_id}, name: {name}, category: {category}")

        db_category = None
        if category is not None:
            db_category = self._convert_ui_category_to_db_category(category)

        try:
            tag_uuid = uuid.UUID(tag_id)

            db_tag = self.repository.update_tag(
                self.db, tag_uuid, name=name, category=db_category
            )
            if not db_tag:
                logger.warning(f"Tag with ID {tag_id} not found for update")
                return None

            return self._convert_db_tag_to_ui_tag(db_tag)
        except ValueError:
            logger.error(f"Invalid tag ID format: {tag_id}")
            return None

    @handle_service_errors(service_name="tag")
    def delete_tag(self, tag_id: str) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: The ID of the tag to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        logger.info(f"Deleting tag: {tag_id}")

        try:
            tag_uuid = uuid.UUID(tag_id)

            result = self.repository.delete_tag(self.db, tag_uuid)

            if result:
                logger.debug(f"Tag {tag_id} deleted successfully")
            else:
                logger.warning(f"Failed to delete tag {tag_id}")

            return result
        except ValueError:
            logger.error(f"Invalid tag ID format: {tag_id}")
            return False

    @handle_service_errors(service_name="tag")
    def add_tag_to_course(self, tag_id: str, course_id: str) -> bool:
        """
        Associate a tag with a course.

        Args:
            tag_id: The ID of the tag
            course_id: The ID of the course

        Returns:
            True if association was successful, False otherwise
        """
        logger.info(f"Adding tag {tag_id} to course {course_id}")

        try:
            tag_uuid = uuid.UUID(tag_id)
            course_uuid = uuid.UUID(course_id)

            result = self.repository.add_tag_to_course(self.db, tag_uuid, course_uuid)

            if result:
                logger.debug(f"Tag {tag_id} added to course {course_id} successfully")
            else:
                logger.warning(f"Failed to add tag {tag_id} to course {course_id}")

            return result
        except ValueError as e:
            logger.error(f"Invalid ID format: {str(e)}")
            return False

    @handle_service_errors(service_name="tag")
    def remove_tag_from_course(self, tag_id: str, course_id: str) -> bool:
        """
        Remove a tag association from a course.

        Args:
            tag_id: The ID of the tag
            course_id: The ID of the course

        Returns:
            True if removal was successful, False otherwise
        """
        logger.info(f"Removing tag {tag_id} from course {course_id}")

        try:
            tag_uuid = uuid.UUID(tag_id)
            course_uuid = uuid.UUID(course_id)

            result = self.repository.remove_tag_from_course(
                self.db, tag_uuid, course_uuid
            )

            if result:
                logger.debug(
                    f"Tag {tag_id} removed from course {course_id} successfully"
                )
            else:
                logger.warning(f"Failed to remove tag {tag_id} from course {course_id}")

            return result
        except ValueError as e:
            logger.error(f"Invalid ID format: {str(e)}")
            return False

    @handle_service_errors(service_name="tag")
    def get_course_tags(self, course_id: str) -> List[Tag]:
        """
        Get all tags associated with a specific course.

        Args:
            course_id: The ID of the course

        Returns:
            List of tags associated with the course
        """
        logger.info(f"Getting tags for course {course_id}")

        try:
            course_uuid = uuid.UUID(course_id)

            db_tags = self.repository.get_course_tags(self.db, course_uuid)

            ui_tags = [self._convert_db_tag_to_ui_tag(db_tag) for db_tag in db_tags]

            logger.debug(f"Found {len(ui_tags)} tags for course {course_id}")
            return ui_tags
        except ValueError:
            logger.error(f"Invalid course ID format: {course_id}")
            return []

    @handle_service_errors(service_name="tag")
    def get_courses_by_tag(self, tag_id: str) -> List[Course]:
        """
        Get all courses associated with a specific tag.

        Args:
            tag_id: The ID of the tag

        Returns:
            List of courses associated with the tag
        """
        logger.info(f"Getting courses for tag {tag_id}")

        try:
            tag_uuid = uuid.UUID(tag_id)

            db_courses = self.repository.get_courses_by_tag(self.db, tag_uuid)

            from src.services.course_service import CourseService

            course_service = CourseService()

            ui_courses = [
                course_service._convert_db_course_to_ui_course(db_course)
                for db_course in db_courses
            ]

            logger.debug(f"Found {len(ui_courses)} courses for tag {tag_id}")
            return ui_courses
        except ValueError:
            logger.error(f"Invalid tag ID format: {tag_id}")
            return []
        except Exception as e:
            logger.error(f"Error getting courses by tag: {str(e)}")
            return []

    @handle_service_errors(service_name="tag")
    def get_or_create_tag(self, name: str, category: TagCategory) -> Optional[Tag]:
        """
        Get a tag by name, or create it if it doesn't exist.

        Args:
            name: The name of the tag
            category: The category of the tag

        Returns:
            The existing or created tag, or None if operation failed
        """
        logger.info(f"Getting or creating tag: {name}, category: {category}")

        tag = self.get_tag_by_name(name)
        if tag:
            logger.debug(f"Found existing tag: {name}")
            return tag

        logger.debug(f"Creating new tag: {name}")
        return self.create_tag(name, category)

    def _convert_db_tag_to_ui_tag(self, db_tag: DbTag) -> Tag:
        """
        Convert a database tag to a UI tag.

        Args:
            db_tag: The database tag to convert

        Returns:
            The converted UI tag
        """
        ui_category = TagCategory.from_db_category(db_tag.category)

        return Tag(id=str(db_tag.id), name=db_tag.name, category=ui_category)

    def _convert_ui_category_to_db_category(self, ui_category: TagCategory) -> Category:
        """
        Convert a UI category to a database category.

        Args:
            ui_category: The UI category to convert

        Returns:
            The converted database category
        """
        mapping = {
            TagCategory.TOPIC: Category.TOPIC,
            TagCategory.SKILL: Category.SKILL,
            TagCategory.DIFFICULTY: Category.DIFFICULTY,
            TagCategory.AGE: Category.AGE,
            TagCategory.OTHER: Category.OTHER,
        }
        return mapping.get(ui_category, Category.OTHER)
