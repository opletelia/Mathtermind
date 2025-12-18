"""
Pytest configuration file for Mathtermind tests.

This module provides fixtures and configuration for pytest to support
Test-Driven Development in the Mathtermind project.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base, Course, Lesson, Tag, User
from src.db.models.achievement import Achievement, UserAchievement
from src.db.models.content import (AssessmentContent, Content, ExerciseContent,
                                   InteractiveContent, TheoryContent)
from src.db.models.enums import (AgeGroup, AnswerType, Category, ContentType,
                                 DifficultyLevel, FontSize,
                                 InformaticsToolType, InteractiveType,
                                 MathToolType, MetricType, PreferredSubject,
                                 ResourceType, ThemeType, Topic)
from src.db.models.progress import Progress, UserContentProgress
from src.db.models.tools import (InformaticsTool, LearningTool, MathTool,
                                 UserToolUsage)
from src.services.cs_tools_service import CSToolsService
from src.services.math_tools_service import MathToolsService


@pytest.fixture(scope="function")
def test_db():
    """Fixture for creating a temporary SQLite database in memory.

    This fixture creates a new in-memory SQLite database for each test,
    ensuring test isolation.

    Returns:
        SQLAlchemy session: A database session for testing.
    """
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_db():
    """Fixture for creating a mock database session.

    This fixture creates a mock database session that can be used
    for unit tests that don't need a real database.

    Returns:
        MagicMock: A mock database session.
    """
    mock = MagicMock(spec=Session)

    mock.query.return_value = mock
    mock.filter.return_value = mock
    mock.filter_by.return_value = mock
    mock.first.return_value = None
    mock.all.return_value = []
    mock.count.return_value = 0

    return mock


@pytest.fixture
def mock_db_context():
    """Fixture for creating a mock database context.

    This fixture creates a mock database context that can be used
    to patch the get_db function in tests.

    Returns:
        tuple: A tuple containing the mock database session and the patcher.
    """
    mock_db = MagicMock(spec=Session)

    mock_db.query.return_value = mock_db
    mock_db.filter.return_value = mock_db
    mock_db.filter_by.return_value = mock_db
    mock_db.first.return_value = None
    mock_db.all.return_value = []
    mock_db.count.return_value = 0

    patcher = patch("src.db.get_db")
    mock_get_db = patcher.start()
    mock_get_db.return_value = iter([mock_db])

    yield mock_db, patcher

    patcher.stop()


@pytest.fixture
def test_user(test_db):
    """Fixture for creating a test user.

    Args:
        test_db: The test database session.

    Returns:
        User: A test user instance.
    """
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="testuser@example.com",
        password_hash="hashed_password",
        age_group=AgeGroup.FIFTEEN_TO_SEVENTEEN,
        points=0,
        experience_level=1,
        total_study_time=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_users(test_db):
    """Fixture for creating multiple test users.

    Args:
        test_db: The test database session.

    Returns:
        list: A list of test user instances.
    """
    users = [
        User(
            id=uuid.uuid4(),
            username=f"testuser{i}",
            email=f"testuser{i}@example.com",
            password_hash=f"hashed_password{i}",
            age_group=AgeGroup.FIFTEEN_TO_SEVENTEEN,
            points=i * 100,
            experience_level=i,
            total_study_time=i * 60,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(1, 4)
    ]

    for user in users:
        test_db.add(user)

    test_db.commit()

    for user in users:
        test_db.refresh(user)

    return users


@pytest.fixture
def test_course(test_db):
    """Fixture for creating a test course.

    Args:
        test_db: The test database session.

    Returns:
        Course: A test course instance.
    """
    course = Course(
        id=uuid.uuid4(),
        topic=Topic.MATHEMATICS,
        name="Test Course",
        description="A test course for unit testing",
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture
def test_courses(test_db):
    """Fixture for creating multiple test courses.

    Args:
        test_db: The test database session.

    Returns:
        list: A list of test course instances.
    """
    courses = [
        Course(
            id=uuid.uuid4(),
            topic=Topic.MATHEMATICS,
            name="Math Course",
            description="A math course for unit testing",
            created_at=datetime.now(timezone.utc),
        ),
        Course(
            id=uuid.uuid4(),
            topic=Topic.INFORMATICS,
            name="Informatics Course",
            description="An informatics course for unit testing",
            created_at=datetime.now(timezone.utc),
        ),
    ]

    for course in courses:
        test_db.add(course)

    test_db.commit()

    for course in courses:
        test_db.refresh(course)

    return courses


@pytest.fixture
def test_lesson(test_db, test_course):
    """Fixture for creating a test lesson.

    Args:
        test_db: The test database session.
        test_course: A test course instance.

    Returns:
        Lesson: A test lesson instance.
    """
    lesson = Lesson(
        id=uuid.uuid4(),
        course_id=test_course.id,
        title="Test Lesson",
        description="A test lesson for unit testing",
        order=1,
        lesson_type=ContentType.THEORY,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(lesson)
    test_db.commit()
    test_db.refresh(lesson)
    return lesson


@pytest.fixture
def test_lessons(test_db, test_course):
    """Fixture for creating multiple test lessons.

    Args:
        test_db: The test database session.
        test_course: A test course instance.

    Returns:
        list: A list of test lesson instances.
    """
    lessons = [
        Lesson(
            id=uuid.uuid4(),
            course_id=test_course.id,
            title=f"Test Lesson {i}",
            description=f"A test lesson {i} for unit testing",
            order=i,
            lesson_type=lesson_type,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i, lesson_type in enumerate(
            [
                ContentType.THEORY,
                ContentType.EXERCISE,
                ContentType.ASSESSMENT,
                ContentType.INTERACTIVE,
            ],
            1,
        )
    ]

    for lesson in lessons:
        test_db.add(lesson)

    test_db.commit()

    for lesson in lessons:
        test_db.refresh(lesson)

    return lessons


@pytest.fixture
def test_tag(test_db):
    """Fixture for creating a test tag.

    Args:
        test_db: The test database session.

    Returns:
        Tag: A test tag instance.
    """
    tag = Tag(
        id=uuid.uuid4(),
        name="Test Tag",
        category=Category.TOPIC,
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture
def test_tags(test_db):
    """Fixture for creating multiple test tags.

    Args:
        test_db: The test database session.

    Returns:
        list: A list of test tag instances.
    """
    tags = [
        Tag(
            id=uuid.uuid4(),
            name=f"Test Tag {i}",
            category=category,
            created_at=datetime.now(timezone.utc),
        )
        for i, category in enumerate(
            [Category.TOPIC, Category.SKILL, Category.DIFFICULTY, Category.AGE], 1
        )
    ]

    for tag in tags:
        test_db.add(tag)

    test_db.commit()

    for tag in tags:
        test_db.refresh(tag)

    return tags


@pytest.fixture
def test_theory_content(test_db, test_lesson):
    """Fixture for creating a test theory content.

    Args:
        test_db: The test database session.
        test_lesson: A test lesson instance.

    Returns:
        TheoryContent: A test theory content instance.
    """
    content = TheoryContent(
        id=uuid.uuid4(),
        lesson_id=test_lesson.id,
        title="Test Theory Content",
        content_type=ContentType.THEORY,
        text_content="This is a test theory content for unit testing.",
        media_urls=json.dumps(["https://example.com/image.jpg"]),
        order=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


@pytest.fixture
def test_exercise_content(test_db, test_lesson):
    """Fixture for creating a test exercise content.

    Args:
        test_db: The test database session.
        test_lesson: A test lesson instance.

    Returns:
        ExerciseContent: A test exercise content instance.
    """
    content = ExerciseContent(
        id=uuid.uuid4(),
        lesson_id=test_lesson.id,
        title="Test Exercise Content",
        content_type=ContentType.EXERCISE,
        problem_statement="Solve this problem.",
        hints=json.dumps(["Hint 1", "Hint 2"]),
        solution="The solution is X.",
        difficulty=DifficultyLevel.INTERMEDIATE,
        order=2,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


@pytest.fixture
def test_achievement(test_db):
    """Fixture for creating a test achievement.

    Args:
        test_db: The test database session.

    Returns:
        Achievement: A test achievement instance.
    """
    achievement = Achievement(
        id=uuid.uuid4(),
        title="Test Achievement",
        description="A test achievement for unit testing",
        icon="trophy",
        category="Learning",
        criteria=json.dumps(
            {
                "type": "points",
                "requirements": {"points_required": 100},
                "progress_tracking": {
                    "count_type": "cumulative",
                    "reset_period": "never",
                },
            }
        ),
        points=50,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(achievement)
    test_db.commit()
    test_db.refresh(achievement)
    return achievement


@pytest.fixture
def test_user_achievement(test_db, test_user, test_achievement):
    """Fixture for creating a test user achievement.

    Args:
        test_db: The test database session.
        test_user: A test user instance.
        test_achievement: A test achievement instance.

    Returns:
        UserAchievement: A test user achievement instance.
    """
    user_achievement = UserAchievement(
        id=uuid.uuid4(),
        user_id=test_user.id,
        achievement_id=test_achievement.id,
        achieved_at=datetime.now(timezone.utc),
        notification_sent=False,
    )
    test_db.add(user_achievement)
    test_db.commit()
    test_db.refresh(user_achievement)
    return user_achievement


@pytest.fixture
def test_math_tool(test_db):
    """Fixture for creating a test math tool.

    Args:
        test_db: The test database session.

    Returns:
        MathTool: A test math tool instance.
    """
    learning_tool = LearningTool(
        id=uuid.uuid4(),
        name="Test Math Tool",
        description="A test math tool for unit testing",
        tool_category="Math",
        tool_type="math_tool",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(learning_tool)
    test_db.commit()
    test_db.refresh(learning_tool)

    math_tool = MathTool(
        id=learning_tool.id,
        math_tool_type=MathToolType.GRAPHING,
        capabilities=json.dumps(
            {
                "functions": ["add", "subtract", "multiply", "divide"],
                "input_types": ["integer", "float"],
                "output_formats": ["decimal", "fraction"],
                "limitations": ["no complex numbers"],
            }
        ),
        default_config=json.dumps(
            {
                "initial_state": {},
                "ui_settings": {"theme": "light"},
                "computation_settings": {"precision": 2},
            }
        ),
    )
    test_db.add(math_tool)
    test_db.commit()
    test_db.refresh(math_tool)
    return math_tool


@pytest.fixture
def test_informatics_tool(test_db):
    """Fixture for creating a test informatics tool.

    Args:
        test_db: The test database session.

    Returns:
        InformaticsTool: A test informatics tool instance.
    """
    learning_tool = LearningTool(
        id=uuid.uuid4(),
        name="Test Informatics Tool",
        description="A test informatics tool for unit testing",
        tool_category="Informatics",
        tool_type="informatics_tool",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(learning_tool)
    test_db.commit()
    test_db.refresh(learning_tool)

    informatics_tool = InformaticsTool(
        id=learning_tool.id,
        informatics_tool_type=InformaticsToolType.CODE_EDITOR,
        capabilities=json.dumps(
            {
                "languages": ["python", "javascript"],
                "features": ["syntax highlighting", "code completion"],
                "input_types": ["text"],
                "output_types": ["console", "visualization"],
                "limitations": ["no debugging"],
            }
        ),
        default_config=json.dumps(
            {
                "initial_state": {},
                "ui_settings": {"theme": "dark"},
                "execution_settings": {"timeout": 5000},
            }
        ),
    )
    test_db.add(informatics_tool)
    test_db.commit()
    test_db.refresh(informatics_tool)
    return informatics_tool


@pytest.fixture
def test_progress(test_db, test_user, test_course):
    """Fixture for creating a test progress.

    Args:
        test_db: The test database session.
        test_user: A test user instance.
        test_course: A test course instance.

    Returns:
        Progress: A test progress instance.
    """
    progress = Progress(
        id=uuid.uuid4(),
        user_id=test_user.id,
        course_id=test_course.id,
        status="in_progress",
        completion_percentage=50,
        last_accessed=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(progress)
    test_db.commit()
    test_db.refresh(progress)
    return progress


@pytest.fixture
def test_user_content_progress(test_db, test_user, test_theory_content):
    """Fixture for creating a test user content progress.

    Args:
        test_db: The test database session.
        test_user: A test user instance.
        test_theory_content: A test theory content instance.

    Returns:
        UserContentProgress: A test user content progress instance.
    """
    user_content_progress = UserContentProgress(
        id=uuid.uuid4(),
        user_id=test_user.id,
        content_id=test_theory_content.id,
        status="completed",
        score=90,
        time_spent=300,  # in seconds
        completed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(user_content_progress)
    test_db.commit()
    test_db.refresh(user_content_progress)
    return user_content_progress


@pytest.fixture
def test_learning_goal(test_db, test_user):
    """Fixture for creating a test learning goal.

    Args:
        test_db: The test database session.
        test_user: A test user instance.

    Returns:
        LearningGoal: A test learning goal instance.
    """
    learning_goal = LearningGoal(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Learning Goal",
        description="A test learning goal for unit testing",
        goal_type="daily",
        target_value=60,  # 60 minutes
        current_value=30,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(learning_goal)
    test_db.commit()
    test_db.refresh(learning_goal)
    return learning_goal


@pytest.fixture
def test_personal_best(test_db, test_user):
    """Fixture for creating a test personal best.

    Args:
        test_db: The test database session.
        test_user: A test user instance.

    Returns:
        PersonalBest: A test personal best instance.
    """
    personal_best = PersonalBest(
        id=uuid.uuid4(),
        user_id=test_user.id,
        metric_type=MetricType.SCORE,
        value=95,
        context_type="quiz",
        context_id=str(uuid.uuid4()),
        achieved_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(personal_best)
    test_db.commit()
    test_db.refresh(personal_best)
    return personal_best


@pytest.fixture
def test_learning_session(test_db, test_user):
    """Fixture for creating a test learning session.

    Args:
        test_db: The test database session.
        test_user: A test user instance.

    Returns:
        LearningSession: A test learning session instance.
    """
    learning_session = LearningSession(
        id=uuid.uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        duration=3600,  # 1 hour in seconds
        activity_summary=json.dumps(
            {
                "courses_accessed": [str(uuid.uuid4())],
                "lessons_completed": 2,
                "exercises_attempted": 5,
                "points_earned": 100,
            }
        ),
        created_at=datetime.now(timezone.utc),
    )
    test_db.add(learning_session)
    test_db.commit()
    test_db.refresh(learning_session)
    return learning_session


@pytest.fixture
def test_study_streak(test_db, test_user):
    """Fixture for creating a test study streak.

    Args:
        test_db: The test database session.
        test_user: A test user instance.

    Returns:
        StudyStreak: A test study streak instance.
    """
    study_streak = StudyStreak(
        id=uuid.uuid4(),
        user_id=test_user.id,
        current_streak=5,
        longest_streak=10,
        last_study_date=datetime.now(timezone.utc).date(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(study_streak)
    test_db.commit()
    test_db.refresh(study_streak)
    return study_streak


@pytest.fixture
def cs_tools_service():
    """Create a test instance of CSToolsService with mocked dependencies."""
    service = CSToolsService()
    service.tracking_service = MagicMock()
    service.db = MagicMock()
    return service


@pytest.fixture
def math_tools_service():
    """Create a test instance of MathToolsService with mocked dependencies."""
    service = MathToolsService()
    service.tracking_service = MagicMock()
    service.db = MagicMock()
    return service
