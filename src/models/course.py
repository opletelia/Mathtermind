from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class Course:
    """Data model representing a course"""

    id: str
    topic: str  # Informatics or Math
    name: str
    description: str
    created_at: datetime
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    is_active: bool = False
    is_completed: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def formatted_created_date(self) -> str:
        """Return formatted date string"""
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted date string (alias for created_date for compatibility)"""
        return self.formatted_created_date

    @property
    def formatted_duration(self) -> str:
        """Return formatted duration string"""
        estimated_time = self.metadata.get("estimated_time", 0)
        hours = estimated_time // 60
        minutes = estimated_time % 60

        if hours > 0 and minutes > 0:
            return f"Тривалість: {hours} год {minutes} хв"
        elif hours > 0:
            return f"Тривалість: {hours} год"
        else:
            return f"Тривалість: {minutes} хв"

    @property
    def difficulty_level(self) -> str:
        """Get the difficulty level from metadata"""
        return self.metadata.get("difficulty_level", "Beginner")

    @property
    def level(self) -> str:
        """Alias for difficulty_level for compatibility"""
        return self.difficulty_level

    @property
    def subject(self) -> str:
        """Alias for topic for compatibility"""
        return self.topic

    @property
    def title(self) -> str:
        """Alias for name for compatibility"""
        return self.name

    @property
    def points_reward(self) -> int:
        """Get points reward from metadata"""
        return self.metadata.get("points_reward", 0)

    @property
    def target_age_group(self) -> str:
        """Get target age group from metadata"""
        return self.metadata.get("target_age_group", "13-14")

    @property
    def duration_hours(self) -> float:
        """Get duration in hours for compatibility"""
        estimated_time = self.metadata.get("estimated_time", 0)
        return estimated_time / 60.0
