from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class User:
    """Data model representing a user"""

    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age_group: str = "15-17"
    role: str = "user"
    points: int = 0
    experience_level: int = 1
    total_study_time: int = 0  # in minutes
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def full_name(self) -> str:
        """Get the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    @property
    def formatted_created_date(self) -> str:
        """Return formatted date string"""
        if not self.created_at:
            return "N/A"
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted date string"""
        if not self.updated_at:
            return "N/A"
        return self.updated_at.strftime("%d %B %Y")

    @property
    def formatted_study_time(self) -> str:
        """Return formatted total study time"""
        hours = self.total_study_time // 60
        minutes = self.total_study_time % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"

    @property
    def has_name(self) -> bool:
        """Check if the user has a name set"""
        return bool(self.first_name or self.last_name)

    @property
    def display_name(self) -> str:
        """Get the name to display for the user"""
        if self.has_name:
            return self.full_name
        return self.username

