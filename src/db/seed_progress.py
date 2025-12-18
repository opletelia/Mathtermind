import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db import get_db
from src.db.models import (CompletedCourse, CompletedLesson, Content,
                           ContentState, Course, Lesson, Progress, User,
                           UserContentProgress)

logger = get_logger(__name__)


@handle_db_errors(operation="seed_progress")
def seed_progress():
    """
    Seed the database with sample progress data for the admin user.
    """
    logger.info("Seeding progress data...")

    db = next(get_db())

    existing_progress = db.query(Progress).count()
    if existing_progress > 0:
        logger.info(
            f"Found {existing_progress} existing progress records. Skipping seeding."
        )
        return

    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        logger.warning("Admin user not found. Skipping progress seeding.")
        return

    courses = db.query(Course).all()
    if not courses:
        logger.warning("No courses found. Skipping progress seeding.")
        return

    _seed_course_progress(db, admin_user, courses)

    logger.info("Progress data seeding completed successfully")


def _seed_course_progress(db: Session, user: User, courses: List[Course]):
    """
    Seed progress data for each course for the given user.

    Args:
        db: Database session
        user: User to create progress for
        courses: List of courses
    """
    logger.info(f"Creating progress data for user {user.username}...")

    random.shuffle(courses)

    num_courses = len(courses)
    num_to_leave_unstarted = min(
        8, num_courses
    )  # Leave up to 8 courses unstarted, or fewer if not enough courses

    # Define slices ensuring they don't overlap and handle small numbers of courses
    idx_completed_end = min(
        2, num_courses - num_to_leave_unstarted
    )  # Max 2 completed, but leave space for unstarted
    idx_in_progress_end = min(
        idx_completed_end + 3, num_courses - num_to_leave_unstarted
    )  # Max 3 in-progress
    idx_started_end = num_courses - num_to_leave_unstarted

    completed_courses = courses[:idx_completed_end]
    in_progress_courses = courses[idx_completed_end:idx_in_progress_end]
    # Only assign to started_courses if there's a valid range
    started_courses = []
    if idx_in_progress_end < idx_started_end:
        started_courses = courses[idx_in_progress_end:idx_started_end]
        started_courses = started_courses[:1]

    unstarted_course_names = [c.name for c in courses[idx_started_end:]]
    if unstarted_course_names:
        logger.info(
            f"The following courses will be intentionally left unstarted: {', '.join(unstarted_course_names)}"
        )
    else:
        logger.info(
            "No courses will be left unstarted (either too few courses or all assigned progress)."
        )

    for course in completed_courses:
        _create_completed_course_progress(db, user, course)

    for course in in_progress_courses:
        _create_in_progress_course_progress(db, user, course)

    for course in started_courses:
        _create_started_course_progress(db, user, course)

    db.commit()
    logger.info(f"Created progress data for {len(courses)} courses")


def _seed_user_content_activity(
    db: Session, user: User, course: Course, days_ago_max: int, items_to_complete: int
):
    logger.info(
        f"Seeding content activity for user {user.username}, course {course.name}..."
    )
    lessons = db.query(Lesson).filter(Lesson.course_id == course.id).all()
    if not lessons:
        logger.warning(
            f"No lessons found for course {course.name} to seed content activity."
        )
        return

    all_content_items = []
    for lesson in lessons:
        content_items = db.query(Content).filter(Content.lesson_id == lesson.id).all()
        all_content_items.extend(content_items)

    if not all_content_items:
        logger.warning(
            f"No content items found in course {course.name} to seed activity."
        )
        return

    items_to_complete = min(items_to_complete, len(all_content_items))

    course_progress_record = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.course_id == course.id)
        .first()
    )

    if not course_progress_record:
        logger.warning(
            f"No main progress record found for user {user.id} and course {course.id}. Skipping content activity seeding."
        )
        return

    days = list(range(days_ago_max))

    min_per_day = 1
    if items_to_complete >= days_ago_max * min_per_day:
        reserved_items = days_ago_max * min_per_day
        remaining_items = items_to_complete - reserved_items

        day_assignments = {day: min_per_day for day in days}

        weights = [
            1.5 ** ((days_ago_max - day) / 2) for day in days
        ]  # Exponential weights - recent days get higher weight

        if remaining_items > 0:
            additional_assignments = random.choices(
                days, weights=weights, k=remaining_items
            )
            for day in additional_assignments:
                day_assignments[day] = day_assignments.get(day, 0) + 1
    else:
        day_assignments = {day: 0 for day in days}
        assigned_days = random.choices(
            days,
            k=items_to_complete,
            weights=[1.5 ** ((days_ago_max - day) / 2) for day in days],
        )
        for day in assigned_days:
            day_assignments[day] = day_assignments.get(day, 0) + 1

    logger.info(f"Activity distribution plan for {course.name}: {day_assignments}")

    completed_count = 0

    for day, count in day_assignments.items():
        for _ in range(count):
            available_items = []
            for content_item in all_content_items:
                existing_ucp = (
                    db.query(UserContentProgress)
                    .filter(
                        UserContentProgress.user_id == user.id,
                        UserContentProgress.content_id == content_item.id,
                    )
                    .first()
                )

                if not existing_ucp:
                    available_items.append(content_item)

            if not available_items:
                logger.warning(
                    f"No more available content items for user {user.id} in course {course.id}."
                )
                break

            content_item = random.choice(available_items)

            completion_time = datetime.now(timezone.utc) - timedelta(
                days=day, hours=random.randint(0, 23), minutes=random.randint(0, 59)
            )

            ucp = UserContentProgress(
                id=uuid.uuid4(),
                user_id=user.id,
                content_id=content_item.id,
                is_completed=True,
                score=(
                    random.uniform(70, 100)
                    if content_item.content_type in ["assessment", "quiz", "exercise"]
                    else None
                ),
                time_spent=random.randint(5, 30) * 60,  # 5-30 minutes in seconds
                last_interaction=completion_time,
            )

            db.add(ucp)
            completed_count += 1

            all_content_items.remove(content_item)

    if completed_count > 0:
        logger.info(
            f"Seeded {completed_count} content activity items for user {user.username}, course {course.name}."
        )


def _create_completed_course_progress(db: Session, user: User, course: Course):
    """Create progress data for a completed course."""
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id)
        .order_by(Lesson.lesson_order)
        .all()
    )
    if not lessons:
        return

    progress = Progress(
        id=uuid.uuid4(),
        user_id=user.id,
        course_id=course.id,
        current_lesson_id=None,
        total_points_earned=len(lessons) * 100,
        time_spent=len(lessons) * 30,
        progress_percentage=100.0,
        progress_data={
            "completed_lessons": len(lessons),
            "total_lessons": len(lessons),
            "average_score": random.randint(85, 100),
        },
        last_accessed=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7)),
        is_completed=True,
    )
    db.add(progress)

    for i, lesson in enumerate(lessons):
        completed_date = datetime.now(timezone.utc) - timedelta(
            days=random.randint(10, 20) + (len(lessons) - i)
        )
        score = random.randint(80, 100)
        time_spent = random.randint(25, 40)  # Minutes

        completed_lesson = CompletedLesson(
            id=uuid.uuid4(),
            user_id=user.id,
            lesson_id=lesson.id,
            course_id=course.id,
            completed_at=completed_date,
            score=score,
            time_spent=time_spent,
        )
        db.add(completed_lesson)

    completed_course = CompletedCourse(
        id=uuid.uuid4(),
        user_id=user.id,
        course_id=course.id,
        completed_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 5)),
        final_score=float(random.randint(85, 98)),
        total_time_spent=progress.time_spent,
        completed_lessons_count=len(lessons),
        achievements_earned=[str(uuid.uuid4()) for _ in range(random.randint(1, 3))],
        certificate_id=uuid.uuid4(),
    )
    db.add(completed_course)

    _seed_user_content_activity(
        db, user, course, days_ago_max=7, items_to_complete=random.randint(5, 15)
    )


def _create_in_progress_course_progress(db: Session, user: User, course: Course):
    """Create progress data for a course that is in progress (partially completed)."""
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id)
        .order_by(Lesson.lesson_order)
        .all()
    )
    if not lessons:
        return

    if len(lessons) <= 1:
        num_lessons_to_complete = 0
    else:
        num_lessons_to_complete = (
            random.randint(1, len(lessons) - 1) if len(lessons) > 1 else 0
        )

    progress = Progress(
        id=uuid.uuid4(),
        user_id=user.id,
        course_id=course.id,
        current_lesson_id=(
            lessons[num_lessons_to_complete].id
            if num_lessons_to_complete < len(lessons)
            else lessons[-1].id
        ),
        total_points_earned=num_lessons_to_complete * 100,  # 100 points per lesson
        time_spent=num_lessons_to_complete * 30,  # 30 min per lesson
        progress_percentage=round((num_lessons_to_complete / len(lessons)) * 100, 1),
        progress_data={
            "completed_lessons": num_lessons_to_complete,
            "total_lessons": len(lessons),
            "average_score": random.randint(75, 95),
        },
        last_accessed=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 3)),
        is_completed=False,
    )
    db.add(progress)

    days_ago_list = list(range(7))
    random.shuffle(days_ago_list)

    for i, lesson in enumerate(lessons):
        if i < num_lessons_to_complete:

            if i < min(7, num_lessons_to_complete):
                day_offset = days_ago_list[i % len(days_ago_list)]
                completed_at = datetime.now(timezone.utc) - timedelta(
                    days=day_offset,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
            else:
                # Any remaining lessons can be completed at random times (older)
                completed_at = datetime.now(timezone.utc) - timedelta(
                    days=random.randint(8, 20),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )

            completed_lesson = CompletedLesson(
                id=uuid.uuid4(),
                user_id=user.id,
                lesson_id=lesson.id,
                course_id=course.id,
                completed_at=completed_at,
                score=random.randint(70, 100),
                time_spent=random.randint(20, 40),  # Minutes
            )
            db.add(completed_lesson)

    _seed_user_content_activity(
        db, user, course, days_ago_max=7, items_to_complete=random.randint(3, 10)
    )


def _create_started_course_progress(db: Session, user: User, course: Course):
    """Create progress data for a course that has just been started."""
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id)
        .order_by(Lesson.lesson_order)
        .all()
    )
    if not lessons:
        return

    first_lesson = lessons[0]

    progress = Progress(
        id=uuid.uuid4(),
        user_id=user.id,
        course_id=course.id,
        current_lesson_id=first_lesson.id,
        total_points_earned=0,
        time_spent=random.randint(5, 15),  # Just started, minimal time spent
        progress_percentage=round(
            (1 / len(lessons)) * random.uniform(0.1, 0.4) * 100, 1
        ),  # Small percentage
        progress_data={
            "completed_lessons": 0,
            "total_lessons": len(lessons),
            "average_score": None,
        },
        last_accessed=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 2)),
        is_completed=False,
    )
    db.add(progress)

    if random.random() > 0.5:
        content_state = ContentState(
            id=uuid.uuid4(),
            user_id=user.id,
            progress_id=progress.id,
            content_id=uuid.uuid4(),
            state_type="scroll_position",
            numeric_value=random.uniform(0.1, 0.5),
            json_value=None,
            text_value=None,
            updated_at=datetime.now(timezone.utc)
            - timedelta(hours=random.randint(1, 48)),
        )
        db.add(content_state)
