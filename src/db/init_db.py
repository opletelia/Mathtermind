from .models import Base
from . import engine
from sqlalchemy import inspect


def init_db():
    """Initialize the database schema."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if (
        "users" in tables
        and "courses" in tables
        and "settings" in tables
        and "progress" in tables
        and "user_answers" in tables
        and "topics" in tables
        and "lessons" in tables
        and "quizzes" in tables
    ):
        print("Database already initialized!")
        return
    else:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully!")
