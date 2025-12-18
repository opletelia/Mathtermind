import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from sqlalchemy.exc import SQLAlchemyError

from src.core import get_logger
from src.core.error_handling.exceptions import (ContentError,
                                                ContentValidationError)
from src.db import get_db
from src.db.models import Content as DBContent
from src.db.models import Course as DBCourse
from src.db.models import Lesson as DBLesson
from src.db.repositories import (ContentRepository, CourseRepository,
                                 LessonRepository)
from src.models.content import (AssessmentContent, Content, ExerciseContent,
                                InteractiveContent, QuizContent,
                                ResourceContent, TheoryContent)
from src.models.course import Course
from src.models.lesson import Lesson
from src.services.content_type_registry import ContentTypeRegistry

T = TypeVar("T", bound=Content)

logger = get_logger(__name__)


class ContentValidationService:
    """Provides lightweight validation helpers for content operations."""

    def __init__(self, type_registry: ContentTypeRegistry):
        self.type_registry = type_registry

    def validate_content(self, content: Any) -> Tuple[bool, List[str]]:
        try:
            if isinstance(content, dict):
                return self._validate_content_dict(content)
            if isinstance(content, Content):
                errors = self.type_registry.validate_content(content)
                return (len(errors) == 0, errors)
            return True, []
        except Exception as exc:
            logger.error(f"Validation error: {exc}")
            return False, [str(exc)]

    def _validate_content_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if not data.get("content_type"):
            errors.append("content_type is required")
        if not data.get("title"):
            errors.append("title is required")
        if not data.get("lesson_id"):
            errors.append("lesson_id is required")
        return (len(errors) == 0, errors)

    def validate_content_references(
        self, _content: Optional[Content], references: List[Any]
    ) -> Tuple[bool, List[str]]:
        errors = []
        if not isinstance(references, list):
            return False, ["references must be a list"]
        for ref in references:
            if not isinstance(ref, (str, dict)):
                errors.append("Each reference must be a string or dict")
        return (len(errors) == 0, errors)

    def validate_content_metadata(
        self, content_type: str, metadata: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        if not isinstance(metadata, dict):
            return False, ["metadata must be a dict"]
        return True, []

    def validate_content_update(
        self, content: Content, updates: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        errors = []
        protected_fields = {"id", "lesson_id", "created_at", "updated_at"}
        for key in updates.keys():
            if key in protected_fields:
                errors.append(f"Field '{key}' cannot be updated")
        return (len(errors) == 0, errors)


class ContentService:
    """Service for managing content."""

    def __init__(self):
        """Initialize the content service."""
        self.db = next(get_db())
        self.content_repo = ContentRepository()
        self.lesson_repo = LessonRepository()
        self.course_repo = CourseRepository()
        self.type_registry = ContentTypeRegistry()
        self.validation_service = ContentValidationService(self.type_registry)

    def get_content_by_id(self, content_id: str) -> Optional[Content]:
        """
        Get content by ID.

        Args:
            content_id: The ID of the content

        Returns:
            The content item if found, None otherwise
        """
        try:
            content_uuid = uuid.UUID(content_id)

            db_content = self.content_repo.get_by_id(self.db, content_uuid)

            if not db_content:
                return None

            return self._convert_db_content_to_ui_content(db_content)
        except Exception as e:
            logger.error(f"Error getting content by ID: {str(e)}")
            return None

    def get_lesson_content(self, lesson_id: str) -> List[Content]:
        """
        Get all content items for a lesson.

        Args:
            lesson_id: The ID of the lesson

        Returns:
            A list of content items
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            db_content_items = self.content_repo.get_lesson_content(
                self.db, lesson_uuid
            )

            return [
                self._convert_db_content_to_ui_content(item)
                for item in db_content_items
            ]
        except Exception as e:
            logger.error(f"Error getting lesson content: {str(e)}")
            return []

    def create_content(
        self,
        content_type: str,
        lesson_id: str,
        title: str,
        description: str,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        **content_data,
    ) -> Optional[Content]:
        """
        Create content of any type using the content type registry.

        Args:
            content_type: The type of content to create
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata
            **content_data: Additional data specific to the content type

        Returns:
            The created content if successful, None otherwise

        Raises:
            ContentValidationError: If the content fails validation
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            all_data = {
                "content_type": content_type,
                "lesson_id": lesson_id,
                "title": title,
                "description": description,
                "order": order,
                "estimated_time": estimated_time,
                "metadata": metadata or {},
                **content_data,
            }

            is_valid, errors = self.validation_service.validate_content(all_data)
            if not is_valid:
                error_list = "; ".join(errors)
                logger.warning(f"Content validation failed: {error_list}")
                raise ContentValidationError(
                    message=f"Content validation failed: {error_list}",
                    content_type=content_type,
                    validation_errors=errors,
                )

            db_content_data = {k: v for k, v in content_data.items()}

            db_content = self.content_repo.create(
                db=self.db,
                lesson_id=lesson_uuid,
                title=title,
                content_type=content_type,
                order=order,
                description=description,
                content_data=db_content_data,
                estimated_time=estimated_time,
                metadata=metadata or {},
            )

            if not db_content:
                return None

            content = self._convert_db_content_to_ui_content(db_content)

            is_valid, errors = self.validation_service.validate_content(content)
            if not is_valid:
                self.content_repo.delete(self.db, db_content.id)
                error_list = "; ".join(errors)
                logger.warning(
                    f"Content validation failed after creation: {error_list}"
                )
                raise ContentValidationError(
                    message=f"Content validation failed after creation: {error_list}",
                    content_type=content_type,
                    validation_errors=errors,
                )

            return content
        except ContentValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            self.db.rollback()
            return None

    def create_theory_content(
        self,
        lesson_id: str,
        title: str,
        description: str,
        text_content: str,
        images: Optional[List[Dict[str, Any]]] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
        references: Optional[List[Dict[str, Any]]] = None,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[TheoryContent]:
        """
        Create theory content.

        Args:
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            text_content: The main text content
            images: Optional list of images
            examples: Optional list of examples
            references: Optional list of references
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata

        Returns:
            The created theory content if successful, None otherwise
        """
        try:
            if references:
                is_valid, errors = self.validation_service.validate_content_references(
                    None, references
                )
                if not is_valid:
                    error_list = "; ".join(errors)
                    logger.warning(f"References validation failed: {error_list}")
                    raise ContentValidationError(
                        message=f"References validation failed: {error_list}",
                        content_type="theory",
                        validation_errors=errors,
                    )

            if metadata:
                is_valid, errors = self.validation_service.validate_content_metadata(
                    "theory", metadata
                )
                if not is_valid:
                    error_list = "; ".join(errors)
                    logger.warning(f"Metadata validation failed: {error_list}")
                    raise ContentValidationError(
                        message=f"Metadata validation failed: {error_list}",
                        content_type="theory",
                        validation_errors=errors,
                    )

            return self.create_content(
                content_type="theory",
                lesson_id=lesson_id,
                title=title,
                description=description,
                order=order,
                estimated_time=estimated_time,
                metadata=metadata,
                text_content=text_content,
                images=images or [],
                examples=examples or [],
                references=references or [],
            )
        except Exception as e:
            if not isinstance(e, ContentValidationError):
                logger.error(f"Error creating theory content: {str(e)}")
            self.db.rollback()
            return None

    def create_exercise_content(
        self,
        lesson_id: str,
        title: str,
        description: str,
        problem_statement: str,
        solution: str,
        difficulty: str,
        hints: Optional[List[str]] = None,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExerciseContent]:
        """
        Create exercise content.

        Args:
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            problem_statement: The problem statement
            solution: The solution to the problem
            difficulty: The difficulty level
            hints: Optional list of hints
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata

        Returns:
            The created exercise content if successful, None otherwise
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            content_data = {
                "problem_statement": problem_statement,
                "solution": solution,
                "difficulty": difficulty,
                "hints": hints or [],
            }

            db_content = self.content_repo.create(
                db=self.db,
                lesson_id=lesson_uuid,
                title=title,
                content_type="exercise",
                order=order,
                description=description,
                content_data=content_data,
                estimated_time=estimated_time,
                metadata=metadata or {},
            )

            if not db_content:
                return None

            return self._convert_db_content_to_ui_content(db_content)
        except Exception as e:
            logger.error(f"Error creating exercise content: {str(e)}")
            self.db.rollback()
            return None

    def create_assessment_content(
        self,
        lesson_id: str,
        title: str,
        description: str,
        questions: List[Dict[str, Any]],
        passing_score: int,
        time_limit: int,
        attempts_allowed: int,
        is_final: bool = False,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AssessmentContent]:
        """
        Create assessment content.

        Args:
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            questions: List of questions
            passing_score: The passing score percentage
            time_limit: The time limit in minutes
            attempts_allowed: The number of attempts allowed
            is_final: Whether this is a final assessment
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata

        Returns:
            The created assessment content if successful, None otherwise
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            content_data = {
                "questions": questions,
                "passing_score": passing_score,
                "time_limit": time_limit,
                "attempts_allowed": attempts_allowed,
                "is_final": is_final,
            }

            db_content = self.content_repo.create(
                db=self.db,
                lesson_id=lesson_uuid,
                title=title,
                content_type="assessment",
                order=order,
                description=description,
                content_data=content_data,
                estimated_time=estimated_time,
                metadata=metadata or {},
            )

            if not db_content:
                return None

            return self._convert_db_content_to_ui_content(db_content)
        except Exception as e:
            logger.error(f"Error creating assessment content: {str(e)}")
            self.db.rollback()
            return None

    def create_interactive_content(
        self,
        lesson_id: str,
        title: str,
        description: str,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        instructions: Optional[str] = None,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[InteractiveContent]:
        """
        Create interactive content.

        Args:
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            interaction_type: The type of interaction
            interaction_data: The interaction data
            instructions: Optional instructions for the interactive content
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata

        Returns:
            The created interactive content if successful, None otherwise
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            content_data = {
                "interaction_type": interaction_type,
                "interaction_data": interaction_data,
                "instructions": instructions,
            }

            db_content = self.content_repo.create(
                db=self.db,
                lesson_id=lesson_uuid,
                title=title,
                content_type="interactive",
                order=order,
                description=description,
                content_data=content_data,
                estimated_time=estimated_time,
                metadata=metadata or {},
            )

            if not db_content:
                return None

            return self._convert_db_content_to_ui_content(db_content)
        except Exception as e:
            logger.error(f"Error creating interactive content: {str(e)}")
            self.db.rollback()
            return None

    def create_resource_content(
        self,
        lesson_id: str,
        title: str,
        description: str,
        resource_type: str,
        resource_url: str,
        is_required: bool = False,
        created_by: Optional[str] = None,
        resource_metadata: Optional[Dict[str, Any]] = None,
        order: int = 0,
        estimated_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ResourceContent]:
        """
        Create resource content.

        Args:
            lesson_id: The ID of the lesson
            title: The title of the content
            description: The description of the content
            resource_type: The type of resource (pdf, video, link, etc.)
            resource_url: The URL to the resource
            is_required: Whether the resource is required
            created_by: Optional creator of the resource
            resource_metadata: Optional metadata specific to the resource
            order: The order of the content within the lesson
            estimated_time: The estimated time to complete in minutes
            metadata: Additional metadata

        Returns:
            The created resource content if successful, None otherwise
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            content_data = {
                "resource_type": resource_type,
                "resource_url": resource_url,
                "description": description,
                "is_required": is_required,
                "created_by": created_by,
                "resource_metadata": resource_metadata or {},
            }

            db_content = self.content_repo.create(
                db=self.db,
                lesson_id=lesson_uuid,
                title=title,
                content_type="resource",
                order=order,
                description=description,
                content_data=content_data,
                estimated_time=estimated_time,
                metadata=metadata or {},
            )

            if not db_content:
                return None

            return self._convert_db_content_to_ui_content(db_content)
        except Exception as e:
            logger.error(f"Error creating resource content: {str(e)}")
            self.db.rollback()
            return None

    def update_content(
        self, content_id: str, updates: Dict[str, Any]
    ) -> Optional[Content]:
        """
        Update content.

        Args:
            content_id: The ID of the content
            updates: The updates to apply

        Returns:
            The updated content if successful, None otherwise
        """
        try:
            content_uuid = uuid.UUID(content_id)

            db_content = self.content_repo.get_by_id(self.db, content_uuid)
            if not db_content:
                logger.warning(f"Content not found: {content_id}")
                return None

            current_content = self._convert_db_content_to_ui_content(db_content)

            is_valid, errors = self.validation_service.validate_content_update(
                current_content, updates
            )
            if not is_valid:
                error_list = "; ".join(errors)
                logger.warning(f"Update validation failed: {error_list}")
                raise ContentValidationError(
                    message=f"Update validation failed: {error_list}",
                    content_id=content_id,
                    content_type=db_content.content_type,
                    validation_errors=errors,
                )

            for key, value in updates.items():
                if hasattr(db_content, key):
                    setattr(db_content, key, value)

            updated_content = self.content_repo.update(self.db, db_content)

            if not updated_content:
                return None

            return self._convert_db_content_to_ui_content(updated_content)
        except Exception as e:
            if not isinstance(e, ContentValidationError):
                logger.error(f"Error updating content: {str(e)}")
            self.db.rollback()
            return None

    def update_content_data(
        self, content_id: str, content_data_updates: Dict[str, Any]
    ) -> Optional[Content]:
        """
        Update content data.

        Args:
            content_id: The ID of the content
            content_data_updates: The updates to apply to the content data

        Returns:
            The updated content if successful, None otherwise
        """
        try:
            content_uuid = uuid.UUID(content_id)

            db_content = self.content_repo.get_by_id(self.db, content_uuid)
            if not db_content:
                logger.warning(f"Content not found: {content_id}")
                return None

            content_data = db_content.content_data or {}
            for key, value in content_data_updates.items():
                content_data[key] = value

            db_content.content_data = content_data
            updated_content = self.content_repo.update(self.db, db_content)

            if not updated_content:
                return None

            return self._convert_db_content_to_ui_content(updated_content)
        except Exception as e:
            logger.error(f"Error updating content data: {str(e)}")
            self.db.rollback()
            return None

    def delete_content(self, content_id: str) -> bool:
        """
        Delete content.

        Args:
            content_id: The ID of the content

        Returns:
            True if successful, False otherwise
        """
        try:
            content_uuid = uuid.UUID(content_id)

            return self.content_repo.delete(self.db, content_uuid)
        except Exception as e:
            logger.error(f"Error deleting content: {str(e)}")
            self.db.rollback()
            return False

    def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        """
        Get lesson by ID.

        Args:
            lesson_id: The ID of the lesson

        Returns:
            The lesson if found, None otherwise
        """
        try:
            lesson_uuid = uuid.UUID(lesson_id)

            db_lesson = self.lesson_repo.get_by_id(self.db, lesson_uuid)

            if not db_lesson:
                return None

            return self._convert_db_lesson_to_ui_lesson(db_lesson)
        except Exception as e:
            logger.error(f"Error getting lesson by ID: {str(e)}")
            return None

    def get_course_lessons(self, course_id: str) -> List[Lesson]:
        """
        Get all lessons for a course.

        Args:
            course_id: The ID of the course

        Returns:
            A list of lessons
        """
        try:
            course_uuid = uuid.UUID(course_id)

            db_lessons = self.lesson_repo.get_lessons_by_course_id(self.db, course_uuid)

            return [
                self._convert_db_lesson_to_ui_lesson(lesson) for lesson in db_lessons
            ]
        except Exception as e:
            logger.error(f"Error getting course lessons: {str(e)}")
            return []

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get course by ID.

        Args:
            course_id: The ID of the course

        Returns:
            The course if found, None otherwise
        """
        try:
            course_uuid = uuid.UUID(course_id)

            db_course = self.course_repo.get_by_id(self.db, course_uuid)

            if not db_course:
                return None

            return self._convert_db_course_to_ui_course(db_course)
        except Exception as e:
            logger.error(f"Error getting course by ID: {str(e)}")
            return None

    def get_all_courses(self, include_inactive: bool = False) -> List[Course]:
        """
        Get all courses.

        Args:
            include_inactive: Whether to include inactive courses

        Returns:
            A list of courses
        """
        try:
            if include_inactive:
                db_courses = self.course_repo.get_all(self.db)
            else:
                db_courses = self.course_repo.get_active_courses(self.db)

            return [
                self._convert_db_course_to_ui_course(course) for course in db_courses
            ]
        except Exception as e:
            logger.error(f"Error getting all courses: {str(e)}")
            return []

    def get_content_state(
        self, user_id: str, content_id: str, state_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the state of a content item.

        Args:
            user_id: User ID
            content_id: Content ID
            state_type: Type of state to retrieve

        Returns:
            State data as a dictionary or None if not found
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            state = self.content_state_repo.get_state(
                db=self.db,
                user_id=user_uuid,
                content_id=content_uuid,
                state_type=state_type,
            )

            return state
        except Exception as e:
            logger.error(f"Error getting content state: {str(e)}")
            return None

    def update_content_state(
        self, user_id: str, content_id: str, state_type: str, value: Any
    ) -> bool:
        """
        Update the state of a content item.

        Args:
            user_id: User ID
            content_id: Content ID
            state_type: Type of state to update
            value: The state value to save

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            result = self.content_state_repo.set_state(
                db=self.db,
                user_id=user_uuid,
                content_id=content_uuid,
                state_type=state_type,
                value=value,
            )

            return result
        except Exception as e:
            logger.error(f"Error updating content state: {str(e)}")
            return False

    def _convert_db_content_to_ui_content(self, db_content: DBContent) -> Content:
        """
        Convert a database content to a UI content.

        Args:
            db_content: The database content (should be an instance of DBTheoryContent, DBExerciseContent etc.)

        Returns:
            The corresponding UI content
        """
        base_attrs = {
            "id": str(db_content.id),
            "title": db_content.title,
            "content_type": db_content.content_type.value,
            "order": db_content.order,
            "lesson_id": str(db_content.lesson_id),
            "description": db_content.description,
            "created_at": db_content.created_at,
            "updated_at": db_content.updated_at,
            "metadata": db_content.metadata or {},
        }

        if db_content.content_type.value == "theory":
            return TheoryContent(
                **base_attrs,
                text_content=getattr(db_content, "text_content", ""),
                images=getattr(db_content, "images", []),
                examples=getattr(db_content, "examples", {}),
                references=getattr(db_content, "references", {}),
            )
        elif db_content.content_type.value == "exercise":
            logger.info(
                f"Converting EXERCISE content: ID={db_content.id}, Title={db_content.title}"
            )
            logger.info(
                f"Raw db_content for exercise: {vars(db_content) if hasattr(db_content, '__dict__') else db_content}"
            )

            db_problems_data = getattr(db_content, "problems", None)
            logger.info(
                f"Extracted db_problems_data (from db_content.problems): {db_problems_data}"
            )

            problem_statement_val = ""
            solution_val = ""
            difficulty_val = "medium"
            hints_val = []
            answer_type_val = "text"
            initial_code_val = ""

            if isinstance(db_problems_data, dict):
                if "question" in db_problems_data:
                    problem_statement_val = db_problems_data.get("question", "")
                    solution_val = db_problems_data.get("solution", "")
                    difficulty_val = db_problems_data.get("difficulty", difficulty_val)
                    hints_val = db_problems_data.get("hints", [])
                    answer_type_val = db_problems_data.get(
                        "answer_type", answer_type_val
                    )
                    initial_code_val = (
                        db_problems_data.get("initial_code")
                        or db_problems_data.get("buggy_code")
                        or db_problems_data.get("code")
                        or initial_code_val
                    )
                    logger.info(
                        f"Using direct format: Statement='{problem_statement_val[:50]}...', Solution exists={bool(solution_val)}, "
                        f"answer_type={answer_type_val}, initial_code={'yes' if initial_code_val else 'no'}"
                    )
                elif (
                    "exercises" in db_problems_data
                    and isinstance(db_problems_data["exercises"], list)
                    and len(db_problems_data["exercises"]) > 0
                ):
                    first_exercise = db_problems_data["exercises"][0]
                    if isinstance(first_exercise, dict):
                        problem_statement_val = first_exercise.get("question", "")
                        solution_val = first_exercise.get("answer", "")
                        difficulty_val = first_exercise.get(
                            "difficulty", difficulty_val
                        )
                        hints_val = first_exercise.get("hints", [])
                        answer_type_val = first_exercise.get(
                            "answer_type", answer_type_val
                        )
                        initial_code_val = (
                            first_exercise.get("initial_code")
                            or first_exercise.get("buggy_code")
                            or first_exercise.get("code")
                            or initial_code_val
                        )
                        logger.info(
                            f"Using exercises list format: Statement='{problem_statement_val[:50]}...', Solution exists={bool(solution_val)}"
                        )
                    else:
                        logger.warning(
                            f"First item in 'problems.exercises' is not a dict for ExerciseContent ID: {db_content.id}"
                        )
                else:
                    logger.warning(
                        f"'problems' dict has no 'question' or 'exercises' field for ExerciseContent ID: {db_content.id}"
                    )
            else:
                logger.warning(
                    f"'problems' field is not a dict for ExerciseContent ID: {db_content.id}. Proceeding with empty values."
                )

            logger.info(
                f"Final values for UI ExerciseContent: Statement='{problem_statement_val}', Solution='{solution_val}', Difficulty='{difficulty_val}', answer_type='{answer_type_val}'"
            )

            return ExerciseContent(
                **base_attrs,
                problem_statement=problem_statement_val,
                solution=solution_val,
                difficulty=difficulty_val,
                hints=hints_val,
                answer_type=answer_type_val,
                initial_code=initial_code_val,
            )
        elif db_content.content_type.value == "quiz":
            return QuizContent(
                **base_attrs,
                questions=getattr(db_content, "questions", []),
                passing_score=getattr(db_content, "passing_score", 70.0),
            )
        elif db_content.content_type.value == "assessment":
            return AssessmentContent(
                **base_attrs,
                questions=getattr(db_content, "questions", []),
                passing_score=getattr(db_content, "passing_score", 70.0),
                time_limit=getattr(db_content, "time_limit", None),
                attempts_allowed=getattr(db_content, "attempts_allowed", 1),
                is_final=getattr(db_content, "is_final", False),
            )
        elif db_content.content_type.value == "interactive":
            logger.info(
                f"Attempting to convert INTERACTIVE content: ID={db_content.id}, Title={db_content.title}"
            )
            logger.info(
                f"Raw db_content for interactive: {vars(db_content) if hasattr(db_content, '__dict__') else db_content}"
            )
            logger.info(f"Type of db_content: {type(db_content)}")

            retrieved_interaction_type = getattr(
                db_content, "interactive_type", "INTERACTION_TYPE_NOT_FOUND"
            )
            retrieved_configuration = getattr(
                db_content, "configuration", "CONFIGURATION_NOT_FOUND"
            )
            retrieved_instructions = getattr(
                db_content, "instructions", "INSTRUCTIONS_NOT_FOUND"
            )

            logger.info(
                f"getattr(db_content, 'interactive_type'): {retrieved_interaction_type}"
            )
            logger.info(
                f"getattr(db_content, 'configuration'): {retrieved_configuration}"
            )
            logger.info(
                f"getattr(db_content, 'instructions'): {retrieved_instructions}"
            )

            interaction_data: Dict[str, Any] = {}
            if isinstance(retrieved_configuration, dict):
                interaction_data = retrieved_configuration
            elif retrieved_configuration not in (None, "CONFIGURATION_NOT_FOUND"):
                logger.warning(
                    f"Interactive configuration is not a dict for content ID {db_content.id}; got {type(retrieved_configuration)}"
                )

            if not interaction_data:
                interaction_data = {"raw": retrieved_configuration}

            return InteractiveContent(
                **base_attrs,
                interaction_type=retrieved_interaction_type,
                interaction_data=interaction_data,
                instructions=(
                    retrieved_instructions
                    if retrieved_instructions != "INSTRUCTIONS_NOT_FOUND"
                    else None
                ),
            )
        elif db_content.content_type.value == "resource":
            content_data = db_content.content_data or {}
            logger.info(
                f"Converting RESOURCE content: ID={db_content.id}, Title={db_content.title}, content_data: {content_data}"
            )

            return ResourceContent(
                **base_attrs,
                resource_type=content_data.get("resource_type", "link"),
                resource_url=content_data.get("resource_url", ""),
                description=content_data.get(
                    "description", base_attrs.get("description", "")
                ),
                is_required=content_data.get("is_required", False),
                created_by=(
                    str(content_data.get("created_by"))
                    if content_data.get("created_by")
                    else None
                ),
                resource_metadata=content_data.get("resource_metadata", {}),
            )
        else:
            logger.warning(
                f"Encountered an unknown DB content type: {db_content.content_type.value} for content ID {db_content.id}. Returning base Content model."
            )
            return Content(**base_attrs)

    def _convert_db_lesson_to_ui_lesson(self, db_lesson: DBLesson) -> Lesson:
        """
        Convert a database lesson to a UI lesson.

        Args:
            db_lesson: The database lesson

        Returns:
            The corresponding UI lesson
        """
        return Lesson(
            id=str(db_lesson.id),
            title=db_lesson.title,
            content=db_lesson.content,
            lesson_type=db_lesson.lesson_type,
            difficulty_level=db_lesson.difficulty_level,
            lesson_order=db_lesson.lesson_order,
            estimated_time=db_lesson.estimated_time,
            points_reward=db_lesson.points_reward,
            section=getattr(db_lesson, "section", None),
            prerequisites=db_lesson.prerequisites,
            learning_objectives=db_lesson.learning_objectives,
            course_id=str(db_lesson.course_id),
            topic=db_lesson.topic,
            skills_taught=db_lesson.skills_taught,
            metadata=db_lesson.metadata,
            created_at=db_lesson.created_at,
            updated_at=db_lesson.updated_at,
        )

    def _convert_db_course_to_ui_course(self, db_course: DBCourse) -> Course:
        """
        Convert a database course to a UI course.

        Args:
            db_course: The database course

        Returns:
            The corresponding UI course
        """
        return Course(
            id=str(db_course.id),
            topic=db_course.topic,
            name=db_course.name,
            description=db_course.description,
            created_at=db_course.created_at,
            tags=db_course.tags,
            metadata=db_course.metadata,
            is_active=db_course.is_active,
            is_completed=False,
        )

    def get_content_types(self) -> List[Dict[str, Any]]:
        """
        Get all registered content types.

        Returns:
            List of content type info dictionaries
        """
        try:
            type_infos = self.type_registry.get_all_content_types()

            result = []
            for type_info in type_infos:
                result.append(
                    {
                        "type": type_info.name,
                        "name": type_info.display_name,
                        "description": type_info.description,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error getting content types: {str(e)}")
            return []

    def validate_content_item(self, content: Content) -> Tuple[bool, List[str]]:
        """
        Validate a content item.

        Args:
            content: The content to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        try:
            return self.validation_service.validate_content(content)
        except Exception as e:
            logger.error(f"Error validating content: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
