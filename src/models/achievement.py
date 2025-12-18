from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Achievement:
    """Data model representing an achievement"""

    id: str
    name: str
    description: str
    criteria: Dict[str, Any]
    category: str
    icon: str
    points: int = 0
    is_hidden: bool = False
    tier: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_created_date(self) -> str:
        """Return formatted date string"""
        if not self.created_at:
            return "N/A"
        return self.created_at.strftime("%d %B %Y")

    @property
    def formatted_points(self) -> str:
        """Return formatted points"""
        return f"{self.points} балів"

    @property
    def tier_display(self) -> str:
        """Return a display name for the tier"""
        if not self.tier:
            return ""
        return self.tier.capitalize()


@dataclass
class UserAchievement:
    """Data model representing an achievement earned by a user"""

    id: str
    user_id: str
    achievement_id: str
    achievement: Optional[Achievement] = None
    earned_at: Optional[datetime] = None
    progress_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.progress_data is None:
            self.progress_data = {}

    @property
    def formatted_earned_date(self) -> str:
        """Return formatted earned date"""
        if not self.earned_at:
            return "N/A"
        return self.earned_at.strftime("%d %B %Y, %H:%M")

    @property
    def name(self) -> str:
        """Return the achievement name"""
        if self.achievement:
            return self.achievement.name
        return "Unknown Achievement"

    @property
    def description(self) -> str:
        """Return the achievement description"""
        if self.achievement:
            return self.achievement.description
        return ""

    @property
    def icon(self) -> str:
        """Return the achievement icon"""
        if self.achievement:
            return self.achievement.icon
        return ""

    @property
    def points(self) -> int:
        """Return the achievement points"""
        if self.achievement:
            return self.achievement.points
        return 0

    @property
    def category(self) -> str:
        """Return the achievement category"""
        if self.achievement:
            return self.achievement.category
        return ""

    @property
    def tier(self) -> Optional[str]:
        """Return the achievement tier"""
        if self.achievement:
            return self.achievement.tier
        return None

