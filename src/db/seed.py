"""
Seed script for populating the database with initial data.
"""

from typing import Any, Dict

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db.seed_courses import seed_courses
from src.db.seed_achievements import seed_achievements
from src.db.seed_users import seed_users
from src.db.seeds.seed_programming_course import seed_programming_course
from src.db.seeds.seed_math_course import seed_math_course

from .seed_progress import seed_progress

logger = get_logger(__name__)


@handle_db_errors(operation="seed_database")
def seed_database(options: Dict[str, Any] = None) -> None:
    """
    Seed the database with initial data.

    Args:
        options: Options for controlling the seeding process
    """
    logger.info("Seeding database...")

    seed_users()
    seed_achievements()
    seed_courses()
    seed_progress()
    seed_programming_course()
    seed_math_course()

    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_database()
