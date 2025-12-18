import operator
import uuid
from datetime import datetime, timezone
from functools import reduce
from typing import Any, Dict, List, Optional, Union, cast

from src.core import get_logger
from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ServiceError, create_error_boundary,
                                     handle_service_errors, report_error)
from src.db import get_db
from src.db.models import Course as DBCourse
from src.db.repositories import course_repo, progress_repo
from src.db.repositories.course_repo import CourseRepository
from src.models.course import Course
from src.models.tag import Tag, TagCategory
from src.services.base_service import BaseService
from src.services.session_manager import SessionManager

logger = get_logger(__name__)


class CourseService(BaseService):
    """
    Service class for handling course data operations.
    This class provides methods for fetching, filtering, and managing courses.
    """

    def __init__(self, tag_service=None):
        """
        Initialize the course service with a database connection.

        Args:
            tag_service: The TagService instance to use for tag-related operations.
                If None, will be lazily initialized when needed.
        """
        super().__init__(repository=course_repo)
        self._tag_service = tag_service
        logger.debug("CourseService initialized")

    @property
    def tag_service(self):
        """
        Get the tag service, initializing it if necessary.

        Returns:
            The TagService instance.
        """
        if self._tag_service is None:
            from src.services.tag_service import TagService

            self._tag_service = TagService()
            logger.debug("TagService lazily initialized")
        return self._tag_service

    @handle_service_errors(service_name="course")
    def get_all_courses(self) -> List[Course]:
        """
        Get all available courses from the database.

        Returns:
            A list of all courses.
        """
        logger.info("Fetching all courses")

        db_courses = course_repo.get_all_courses(self.db)
        course_count = len(db_courses)
        logger.debug(f"Found {course_count} courses")

        return [self._convert_db_course_to_ui_course(course) for course in db_courses]

    @handle_service_errors(service_name="course")
    def get_active_courses(self) -> List[Course]:
        """
        Get courses that the user is currently enrolled in.

        Returns:
            A list of active courses for the current user.
        """
        logger.info("Fetching active courses for user")

        current_user = SessionManager.get_current_user()
        user_id = current_user.get("id") if isinstance(current_user, dict) else None
        if not user_id:
            logger.warning("No current user in session; returning empty active courses list")
            return []

        with create_error_boundary("fetch_user_progress"):
            user_uuid = uuid.UUID(user_id)

            user_progress = progress_repo.get_user_progress(self.db, user_uuid)

            course_ids = [progress.course_id for progress in user_progress]
            logger.debug(f"User enrolled in {len(course_ids)} courses")

            active_courses = []
            for course_id in course_ids:
                course = course_repo.get_course(self.db, course_id)
                if course:
                    ui_course = self._convert_db_course_to_ui_course(course)
                    ui_course.is_active = True
                    active_courses.append(ui_course)

            logger.info(f"Found {len(active_courses)} active courses for user")
            return active_courses

        logger.warning("Error in fetching user progress. Returning empty active courses list.")
        return []

    @handle_service_errors(service_name="course")
    def get_completed_courses(self) -> List[Course]:
        """
        Get courses that the user has completed.

        Returns:
            A list of completed courses for the current user.
        """
        logger.info("Fetching completed courses for user")

        current_user = SessionManager.get_current_user()
        user_id = current_user.get("id") if isinstance(current_user, dict) else None
        if not user_id:
            logger.warning("No current user in session; returning empty completed courses list")
            return []

        with create_error_boundary("fetch_completed_courses"):
            user_uuid = uuid.UUID(user_id)

            completed_course_ids = set()

            try:
                from src.db.repositories import CompletedCourseRepository

                completed_course_repo = CompletedCourseRepository()
                db_completed = completed_course_repo.get_by_user_id(self.db, user_uuid)
                completed_course_ids = {row.course_id for row in db_completed}
            except Exception as e:
                logger.warning(f"CompletedCourseRepository not usable; falling back: {e}")
                try:
                    from src.db.repositories import CompletedLessonRepository

                    completed_lesson_repo = CompletedLessonRepository()
                    db_completed_lessons = completed_lesson_repo.get_by_user_id(
                        self.db, user_uuid
                    )
                    for row in db_completed_lessons:
                        lesson = getattr(row, "lesson", None)
                        if lesson and getattr(lesson, "course_id", None):
                            completed_course_ids.add(lesson.course_id)
                except Exception as inner:
                    logger.warning(f"Completed lesson fallback failed: {inner}")
                    completed_course_ids = set()

            completed_courses: List[Course] = []
            for course_id in completed_course_ids:
                course = course_repo.get_course(self.db, course_id)
                if course:
                    ui_course = self._convert_db_course_to_ui_course(course)
                    ui_course.is_completed = True
                    completed_courses.append(ui_course)

            logger.info(f"Found {len(completed_courses)} completed courses for user")
            return completed_courses

    @handle_service_errors(service_name="course")
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get a course by its ID.

        Args:
            course_id: The ID of the course to retrieve.

        Returns:
            The course if found, None otherwise.

        Raises:
            ResourceNotFoundError: If the course with the given ID is not found.
        """
        logger.info(f"Fetching course with ID: {course_id}")

        try:
            course_uuid = uuid.UUID(course_id)
            db_course = course_repo.get_course(self.db, course_uuid)

            if not db_course:
                logger.warning(f"Course with ID {course_id} not found")
                raise ResourceNotFoundError(
                    message=f"Course with ID {course_id} not found",
                    resource_type="course",
                    resource_id=course_id,
                )

            logger.debug(f"Course found: {db_course.name}")
            return self._convert_db_course_to_ui_course(db_course)

        except ValueError:
            logger.error(f"Invalid course ID format: {course_id}")
            raise ServiceError(
                message=f"Invalid course ID format: {course_id}",
                service="course",
                details={"course_id": course_id},
            )

    @handle_service_errors(service_name="course")
    def filter_courses(self, filters: Dict[str, Any] = None) -> List[Course]:
        """
        Get courses filtered by various criteria.

        This method provides a flexible way to filter courses by multiple criteria
        such as difficulty level, age group, topic, duration range, etc.

        Args:
            filters: A dictionary of filter criteria. Supported filters include:
                - difficulty_level: The difficulty level to filter by
                - age_group: The target age group to filter by
                - topic: The topic/subject to filter by
                - is_active: Whether to return only active courses
                - is_completed: Whether to return only completed courses
                - tags: List of tags to filter by
                - duration_min: Minimum duration in minutes
                - duration_max: Maximum duration in minutes

        Returns:
            A list of courses matching all the specified filter criteria.
        """
        logger.info(f"Filtering courses with criteria: {filters}")

        try:
            db_courses = course_repo.get_all_courses(self.db)

            if not filters:
                logger.debug(
                    f"No filters provided, returning all {len(db_courses)} courses"
                )
                return [
                    self._convert_db_course_to_ui_course(course)
                    for course in db_courses
                ]

            filtered_courses = []

            for course in db_courses:
                matches_all_filters = True

                for filter_key, filter_value in filters.items():
                    if filter_key == "difficulty_level" and hasattr(
                        course, "difficulty_level"
                    ):
                        if course.difficulty_level != filter_value:
                            matches_all_filters = False
                            break

                    elif filter_key == "age_group" and hasattr(
                        course, "target_age_group"
                    ):
                        if course.target_age_group != filter_value:
                            matches_all_filters = False
                            break

                    elif filter_key == "topic" and hasattr(course, "topic"):
                        course_topic = (
                            course.topic.value
                            if hasattr(course.topic, "value")
                            else str(course.topic)
                        )
                        if course_topic != filter_value:
                            matches_all_filters = False
                            break

                    elif filter_key == "tags" and hasattr(course, "tags"):
                        course_tag_names = (
                            [tag.name for tag in course.tags] if course.tags else []
                        )
                        if not any(tag in course_tag_names for tag in filter_value):
                            matches_all_filters = False
                            break

                    elif filter_key == "duration_min" and hasattr(course, "duration"):
                        if course.duration < filter_value:
                            matches_all_filters = False
                            break

                    elif filter_key == "duration_max" and hasattr(course, "duration"):
                        if course.duration > filter_value:
                            matches_all_filters = False
                            break

                if matches_all_filters:
                    filtered_courses.append(course)

            course_count = len(filtered_courses)
            logger.debug(f"Found {course_count} courses matching filters {filters}")

            return [
                self._convert_db_course_to_ui_course(course)
                for course in filtered_courses
            ]

        except Exception as e:
            logger.error(f"Error filtering courses: {str(e)}")
            report_error(e, operation="filter_courses", filters=filters)
            raise ServiceError(
                message=f"Error filtering courses: {str(e)}",
                service="course",
                details={"filters": filters},
            )

    @handle_service_errors(service_name="course")
    def sort_courses(
        self, courses: List[Course], sort_by: str = "name", ascending: bool = True
    ) -> List[Course]:
        """
        Sort a list of courses by the specified criteria.

        Args:
            courses: The list of courses to sort
            sort_by: The field to sort by. Supported fields are:
                - name: Sort by course name
                - duration: Sort by course duration
                - created_at: Sort by creation date
                - difficulty_level: Sort by difficulty level
            ascending: Whether to sort in ascending (True) or descending (False) order

        Returns:
            A sorted list of courses
        """
        logger.info(
            f"Sorting courses by {sort_by} {'ascending' if ascending else 'descending'}"
        )

        valid_sort_fields = ["name", "duration", "created_at", "difficulty_level"]

        if sort_by not in valid_sort_fields:
            logger.warning(f"Invalid sort field: {sort_by}. Using default 'name'.")
            sort_by = "name"

        try:
            if sort_by == "name":

                def sort_key(course):
                    return course.name.lower()

            elif sort_by == "duration":

                def sort_key(course):
                    return (
                        course.metadata.get("estimated_time", 0)
                        if hasattr(course, "metadata")
                        else 0
                    )

            elif sort_by == "created_at":

                def sort_key(course):
                    return course.created_at

            elif sort_by == "difficulty_level":
                difficulty_map = {
                    "Beginner": 1,
                    "Intermediate": 2,
                    "Advanced": 3,
                    "Expert": 4,
                }

                def sort_key(course):
                    difficulty = (
                        course.difficulty_level
                        if hasattr(course, "difficulty_level")
                        else "Beginner"
                    )
                    return difficulty_map.get(difficulty, 0)

            sorted_courses = sorted(courses, key=sort_key, reverse=not ascending)

            logger.debug(f"Sorted {len(sorted_courses)} courses")
            return sorted_courses

        except Exception as e:
            logger.error(f"Error sorting courses: {str(e)}")
            report_error(
                e, operation="sort_courses", sort_by=sort_by, ascending=ascending
            )
            logger.warning("Returning unsorted course list due to sorting error")
            return courses

    @handle_service_errors(service_name="course")
    def get_courses_by_difficulty(self, difficulty_level: str) -> List[Course]:
        """
        Get courses filtered by difficulty level.

        Args:
            difficulty_level: The difficulty level to filter by.

        Returns:
            A list of courses with the specified difficulty level.
        """
        logger.info(f"Fetching courses with difficulty level: {difficulty_level}")
        return self.filter_courses(filters={"difficulty_level": difficulty_level})

    @handle_service_errors(service_name="course")
    def get_courses_by_age_group(self, age_group: str) -> List[Course]:
        """
        Get courses filtered by target age group.

        Args:
            age_group: The age group to filter by.

        Returns:
            A list of courses for the specified age group.
        """
        logger.info(f"Fetching courses for age group: {age_group}")
        return self.filter_courses(filters={"age_group": age_group})

    @handle_service_errors(service_name="course")
    def search_courses(self, query: str) -> List[Course]:
        """
        Search for courses by name or description.

        Args:
            query: The search query.

        Returns:
            A list of courses matching the search query.
        """
        logger.info(f"Searching courses with query: {query}")

        db_courses = course_repo.search_courses(self.db, query)
        course_count = len(db_courses)
        logger.debug(f"Found {course_count} courses matching search query '{query}'")

        return [self._convert_db_course_to_ui_course(course) for course in db_courses]

    @handle_service_errors(service_name="course")
    def _convert_db_course_to_ui_course(self, db_course: DBCourse) -> Course:
        """
        Convert a database course model to a UI course model.

        Args:
            db_course: The database course model.

        Returns:
            The UI course model.
        """
        logger.debug(f"Converting DB course to UI course: {db_course.id}")

        try:
            metadata = {
                "difficulty_level": "Beginner",
                "target_age_group": "13-14",
                "estimated_time": 60,  # Default TODO: extract into const
                "points_reward": 10,
                "prerequisites": {},
                "tags": [],
                "updated_at": datetime.now(timezone.utc),
            }

            if hasattr(db_course, "difficulty_level") and db_course.difficulty_level:
                metadata["difficulty_level"] = db_course.difficulty_level

            if hasattr(db_course, "duration") and db_course.duration:
                metadata["estimated_time"] = db_course.duration

            tags = (
                [tag.name for tag in db_course.tags]
                if hasattr(db_course, "tags") and db_course.tags
                else []
            )
            metadata["tags"] = tags

            return Course(
                id=str(db_course.id),
                topic=(
                    db_course.topic.value
                    if hasattr(db_course.topic, "value")
                    else db_course.topic
                ),
                name=db_course.name,
                description=db_course.description,
                created_at=db_course.created_at,
                tags=tags,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error converting DB course to UI course: {str(e)}")
            report_error(e, operation="convert_db_course", course_id=str(db_course.id))

            return Course(
                id=str(db_course.id) if hasattr(db_course, "id") else "unknown",
                topic="Informatics",
                name=db_course.name if hasattr(db_course, "name") else "Unknown Course",
                description=(
                    db_course.description
                    if hasattr(db_course, "description")
                    else "No description available"
                ),
                created_at=datetime.now(timezone.utc),
                tags=[],
                metadata={},
            )

    @handle_service_errors(service_name="course")
    def add_tag_to_course(self, course_id: str, tag_id: str) -> bool:
        """
        Add a tag to a course.

        Args:
            course_id: ID of the course
            tag_id: ID of the tag to add

        Returns:
            True if the tag was added successfully, False otherwise
        """
        logger.info(f"Adding tag to course: {course_id}, tag_id: {tag_id}")
        try:
            return self.tag_service.add_tag_to_course(tag_id, course_id)
        except Exception as e:
            logger.error(f"Error adding tag to course: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def remove_tag_from_course(self, course_id: str, tag_id: str) -> bool:
        """
        Remove a tag from a course.

        Args:
            course_id: ID of the course
            tag_id: ID of the tag to remove

        Returns:
            True if the tag was removed successfully, False otherwise
        """
        logger.info(f"Removing tag from course: {course_id}, tag_id: {tag_id}")
        try:
            return self.tag_service.remove_tag_from_course(tag_id, course_id)
        except Exception as e:
            logger.error(f"Error removing tag from course: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def get_course_tags(self, course_id: str) -> List[Tag]:
        """
        Get all tags for a course.

        Args:
            course_id: ID of the course

        Returns:
            List of tags associated with the course
        """
        logger.info(f"Getting tags for course: {course_id}")
        try:
            return self.tag_service.get_course_tags(course_id)
        except Exception as e:
            logger.error(f"Error getting course tags: {str(e)}")
            return []

    @handle_service_errors(service_name="course")
    def add_tag_by_name_to_course(
        self, course_id: str, tag_name: str, category: TagCategory
    ) -> bool:
        """
        Add a tag to a course by name, creating the tag if it doesn't exist.

        Args:
            course_id: ID of the course
            tag_name: Name of the tag
            category: Category of the tag

        Returns:
            True if the tag was added successfully, False otherwise
        """
        logger.info(
            f"Adding tag by name to course: {course_id}, tag_name: {tag_name}, category: {category}"
        )
        try:
            tag = self.tag_service.get_tag_by_name(tag_name)

            if not tag:
                tag = self.tag_service.create_tag(tag_name, category)
                if not tag:
                    logger.error(f"Failed to create tag: {tag_name}")
                    return False

            return self.tag_service.add_tag_to_course(tag.id, course_id)
        except Exception as e:
            logger.error(f"Error adding tag by name to course: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def add_tags_to_course(self, course_id: str, tag_names: List[str]) -> bool:
        """
        Add multiple tags to a course by name.

        Args:
            course_id: ID of the course
            tag_names: List of tag names to add

        Returns:
            True if all tags were added successfully, False if any failed
        """
        logger.info(f"Adding tags to course: {course_id}, tag_names: {tag_names}")
        try:
            all_successful = True

            for tag_name in tag_names:
                tag = self.tag_service.get_tag_by_name(tag_name)
                if not tag:
                    logger.warning(f"Tag not found: {tag_name}")
                    all_successful = False
                    continue

                success = self.tag_service.add_tag_to_course(tag.id, course_id)
                if not success:
                    all_successful = False

            return all_successful
        except Exception as e:
            logger.error(f"Error adding tags to course: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def add_tags_to_course_with_categories(
        self, course_id: str, tags: List[Dict[str, Union[str, TagCategory]]]
    ) -> bool:
        """
        Add multiple tags with categories to a course.

        Args:
            course_id: ID of the course
            tags: List of dictionaries with 'name' and 'category' keys

        Returns:
            True if all tags were added successfully, False if any failed
        """
        logger.info(f"Adding tags with categories to course: {course_id}, tags: {tags}")
        try:
            all_successful = True

            for tag_data in tags:
                tag_name = str(tag_data.get("name"))
                tag_category = cast(TagCategory, tag_data.get("category"))

                tag = self.tag_service.get_or_create_tag(tag_name, tag_category)
                if not tag:
                    logger.warning(f"Failed to get or create tag: {tag_name}")
                    all_successful = False
                    continue

                success = self.tag_service.add_tag_to_course(tag.id, course_id)
                if not success:
                    all_successful = False

            return all_successful
        except Exception as e:
            logger.error(f"Error adding tags with categories to course: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def update_course_tags(
        self, course_id: str, new_tags: List[Dict[str, Union[str, TagCategory]]]
    ) -> bool:
        """
        Update a course's tags, removing tags not in the new list and adding new ones.

        Args:
            course_id: ID of the course
            new_tags: List of dictionaries with 'name' and 'category' keys

        Returns:
            True if the update was successful, False otherwise
        """
        logger.info(f"Updating course tags: {course_id}, new_tags: {new_tags}")
        try:
            current_tags = self.get_course_tags(course_id)

            updated_tags = []
            for tag_data in new_tags:
                tag_name = str(tag_data.get("name"))
                tag_category = cast(TagCategory, tag_data.get("category"))

                tag = self.tag_service.get_or_create_tag(tag_name, tag_category)
                if not tag:
                    logger.warning(f"Failed to get or create tag: {tag_name}")
                    return False

                updated_tags.append(tag)

            current_tag_names = {tag.name for tag in current_tags}
            updated_tag_names = {tag.name for tag in updated_tags}

            tags_to_remove = [
                tag for tag in current_tags if tag.name not in updated_tag_names
            ]

            tags_to_add = [
                tag for tag in updated_tags if tag.name not in current_tag_names
            ]

            for tag in tags_to_remove:
                success = self.tag_service.remove_tag_from_course(tag.id, course_id)
                if not success:
                    logger.warning(f"Failed to remove tag: {tag.name}")
                    return False

            for tag in tags_to_add:
                success = self.tag_service.add_tag_to_course(tag.id, course_id)
                if not success:
                    logger.warning(f"Failed to add tag: {tag.name}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error updating course tags: {str(e)}")
            return False

    @handle_service_errors(service_name="course")
    def create_course(
        self,
        topic: str,
        name: str,
        description: str,
        difficulty_level: str = "beginner",
        target_age_group: str = "15-17",
        duration: int = 1,
        metadata: dict = None,
    ) -> Course:

        metadata = metadata or {}
        self.course_repo = CourseRepository()

        db_session = self.db
        db_course = self.course_repo.create_course(
            db=db_session,
            topic=topic,
            name=name,
            description=description,
            duration=duration,
        )
        return db_course

    @handle_service_errors(service_name="course")
    def update_course(self, course_id: str, **data) -> Course:
        db_session = next(get_db())
        self.course_repo = CourseRepository()
        try:
            updated_course = self.course_repo.update_course(
                db=db_session,
                course_id=uuid.UUID(course_id),
                topic=data.get("topic"),
                name=data.get("name"),
                description=data.get("description"),
                duration=data.get("duration"),
            )
            if not updated_course:
                raise ValueError("Курс не знайдено")
            return updated_course
        finally:
            db_session.close()

    @handle_service_errors(service_name="course")
    def delete_course(self, course_id: str):
        import uuid

        try:
            course_id = uuid.UUID(course_id)
        except:
            raise ValueError("Invalid course_id format")

        repo = CourseRepository()
        db = self.db
        return repo.delete_course(db=db, course_id=course_id)
