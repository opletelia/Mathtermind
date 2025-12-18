"""
Init module for repositories layer.

This module imports and initializes all repository classes.
"""

from src.db.repositories.achievement_repo import AchievementRepository
from src.db.repositories.completed_course_repo import CompletedCourseRepository
from src.db.repositories.completed_lesson_repo import CompletedLessonRepository
from src.db.repositories.content_repo import ContentRepository
from src.db.repositories.course_repo import CourseRepository
from src.db.repositories.lesson_repo import LessonRepository
from src.db.repositories.progress_repo import ProgressRepository
from src.db.repositories.user_answer_repository import UserAnswersRepository
from src.db.repositories.user_content_progress_repo import \
    UserContentProgressRepository
from src.db.repositories.user_repo import UserRepository

user_repo = UserRepository()
course_repo = CourseRepository()
lesson_repo = LessonRepository()
achievement_repo = AchievementRepository()
progress_repo = ProgressRepository()
content_repo = ContentRepository()
user_content_progress_repo = UserContentProgressRepository()
completed_course_repo = CompletedCourseRepository()
completed_lesson_repo = CompletedLessonRepository()
user_answers_repo = UserAnswersRepository()

__all__ = [
    "user_repo",
    "course_repo",
    "lesson_repo",
    "achievement_repo",
    "progress_repo",
    "content_repo",
    "user_content_progress_repo",
    "completed_course_repo",
    "completed_lesson_repo",
    "user_answers_repo",
]
