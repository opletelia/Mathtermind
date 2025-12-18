from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Lesson:

    id: str
    title: str
    course_id: str
    lesson_order: int
    estimated_time: int  # in minutes
    points_reward: int
    section: Optional[str] = None
    lesson_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    content: Dict[str, Any] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    topic: Optional[str] = None
    skills_taught: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.content is None:
            self.content = {}
        if self.prerequisites is None:
            self.prerequisites = []
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.skills_taught is None:
            self.skills_taught = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def formatted_duration(self) -> str:
        """Return formatted duration string"""
        hours = self.estimated_time // 60
        minutes = self.estimated_time % 60

        if hours > 0 and minutes > 0:
            return f"Тривалість: {hours} год {minutes} хв"
        elif hours > 0:
            return f"Тривалість: {hours} год"
        else:
            return f"Тривалість: {minutes} хв"

    @property
    def formatted_points(self) -> str:
        """Return formatted points string"""
        return f"Бали: {self.points_reward}"

    @property
    def formatted_created_date(self) -> str:
        """Return formatted creation date"""
        if not self.created_at:
            return "N/A"
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted update date"""
        if not self.updated_at:
            return "N/A"
        return self.updated_at.strftime("%d %B %Y")

    @property
    def lesson_number(self) -> str:
        """Return formatted lesson number"""
        return f"Урок {self.lesson_order}"

    @property
    def has_prerequisites(self) -> bool:
        """Check if lesson has prerequisites"""
        return bool(self.prerequisites and len(self.prerequisites) > 0)
