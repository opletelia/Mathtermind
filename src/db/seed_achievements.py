import uuid
from datetime import datetime, timezone

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db import get_db
from src.db.models import Achievement, User, UserAchievement

logger = get_logger(__name__)


@handle_db_errors(operation="seed_achievements")
def seed_achievements() -> None:
    logger.info("Seeding achievements...")

    db = next(get_db())

    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        logger.warning("Admin user not found. Skipping achievements seeding.")
        return

    existing_titles = {
        a[0]
        for a in db.query(Achievement.title).all()
    }

    now = datetime.now(timezone.utc)
    desired = [
        {
            "title": "Перші кроки",
            "description": "Розпочніть свій перший урок у Mathtermind.",
            "icon": "icon/badges/badge1.svg",
            "category": "Learning",
            "criteria": {"type": "first_lesson", "required": 1},
            "points": 10,
        },
        {
            "title": "Дослідник",
            "description": "Перегляньте 5 різних розділів уроку.",
            "icon": "icon/badges/badge2.svg",
            "category": "Engagement",
            "criteria": {"type": "content_viewed", "required": 5},
            "points": 15,
        },
        {
            "title": "Наполегливість",
            "description": "Навчайтесь 7 днів поспіль.",
            "icon": "icon/badges/badge3.svg",
            "category": "Engagement",
            "criteria": {"type": "streak", "required": 7},
            "points": 50,
        },
        {
            "title": "Майстер задач",
            "description": "Розв'яжіть 10 завдань.",
            "icon": "icon/badges/badge1.svg",
            "category": "Mastery",
            "criteria": {"type": "tasks_completed", "required": 10},
            "points": 30,
        },
        {
            "title": "Швидкий старт",
            "description": "Завершіть 3 уроки.",
            "icon": "icon/badges/badge2.svg",
            "category": "Learning",
            "criteria": {"type": "lessons_completed", "required": 3},
            "points": 25,
        },
        {
            "title": "Серія успіхів",
            "description": "Отримайте 100% за тест.",
            "icon": "icon/badges/badge3.svg",
            "category": "Mastery",
            "criteria": {"type": "perfect_score", "required": 1},
            "points": 40,
        },
        {
            "title": "Уважний учень",
            "description": "Повністю завершіть один курс.",
            "icon": "icon/badges/badge1.svg",
            "category": "Learning",
            "criteria": {"type": "courses_completed", "required": 1},
            "points": 100,
        },
    ]

    created = 0
    for item in desired:
        if item["title"] in existing_titles:
            continue

        db.add(
            Achievement(
                id=uuid.uuid4(),
                title=item["title"],
                description=item["description"],
                icon=item["icon"],
                category=item.get("category", "Engagement"),
                criteria=item.get("criteria", {"type": "seeded"}),
                points=item.get("points", 0),
                created_at=now,
                updated_at=now,
            )
        )
        created += 1

    if created:
        db.commit()
        logger.info(f"Created {created} achievements")

    updated = 0
    for item in desired:
        existing_achievement = (
            db.query(Achievement)
            .filter(Achievement.title == item["title"])
            .first()
        )
        if existing_achievement and existing_achievement.criteria.get("type") == "seeded":
            existing_achievement.criteria = item.get("criteria", {"type": "seeded"})
            existing_achievement.category = item.get("category", "Engagement")
            existing_achievement.points = item.get("points", 0)
            updated += 1

    if updated:
        db.commit()
        logger.info(f"Updated {updated} achievements with new criteria")

    earned_count = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == admin_user.id)
        .count()
    )

    achievements_to_award = (
        db.query(Achievement)
        .order_by(Achievement.created_at)
        .limit(2)
        .all()
    )

    for ach in achievements_to_award:
        existing = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == admin_user.id,
                UserAchievement.achievement_id == ach.id,
            )
            .first()
        )
        if existing:
            continue

        ua = UserAchievement(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            achievement_id=ach.id,
            achieved_at=datetime.now(timezone.utc),
            notification_sent=False,
        )
        db.add(ua)

    db.commit()
    logger.info("Seeded achievements awarded to admin")
