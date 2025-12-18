import uuid
from datetime import datetime, timezone

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db import get_db
from src.db.models import User
from src.db.models.enums import AgeGroup
from src.services.password_utils import hash_password

logger = get_logger(__name__)


@handle_db_errors(operation="seed_users")
def seed_users():
    """
    Seed the database with sample user data.
    """
    logger.info("Seeding users...")

    db = next(get_db())

    existing_users = db.query(User).count()
    if existing_users > 0:
        logger.info(f"Found {existing_users} existing users. Skipping seeding.")
        return

    users = [
        {
            "id": uuid.uuid4(),
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "first_name": "Адміністратор",
            "last_name": "Системи",
            "avatar_url": "icon/icon_users.PNG",
            "profile_data": {
                "phone_number": "+380671234567",
                "date_of_birth": "01.01.1990",
            },
            "age_group": AgeGroup.FIFTEEN_TO_SEVENTEEN,
            "points": 1000,
            "experience_level": 5,
            "total_study_time": 3600,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "username": "student",
            "email": "student@example.com",
            "password_hash": hash_password("student123"),
            "role": "user",
            "first_name": "Степан",
            "last_name": "Іваненко",
            "avatar_url": "icon/icon_users.PNG",
            "profile_data": {
                "phone_number": "+380671234567",
                "date_of_birth": "15.06.2015",
            },
            "age_group": AgeGroup.THIRTEEN_TO_FOURTEEN,
            "points": 500,
            "experience_level": 3,
            "total_study_time": 1800,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "username": "teacher",
            "email": "teacher@example.com",
            "password_hash": hash_password("teacher123"),
            "role": "user",
            "first_name": "Іван",
            "last_name": "Іваненко",
            "avatar_url": "icon/icon_users.PNG",
            "profile_data": {
                "phone_number": "+380671234567",
                "date_of_birth": "20.09.1985",
            },
            "age_group": AgeGroup.FIFTEEN_TO_SEVENTEEN,
            "points": 800,
            "experience_level": 4,
            "total_study_time": 2700,
            "created_at": datetime.now(timezone.utc),
        },
    ]

    for user_data in users:
        user = User(**user_data)
        db.add(user)

    db.commit()
    logger.info(f"Created {len(users)} sample users")
