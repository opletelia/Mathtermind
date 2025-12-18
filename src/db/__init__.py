# db/__init__.py
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dependency Injection for SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
