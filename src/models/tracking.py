from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LearningSession:
    """Data model representing a learning session"""

    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in minutes
    session_data: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}

    @property
    def formatted_start_time(self) -> str:
        """Return formatted start time"""
        return self.start_time.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_end_time(self) -> str:
        """Return formatted end time"""
        if not self.end_time:
            return "Active"
        return self.end_time.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_duration(self) -> str:
        """Return formatted duration"""
        duration = self.duration
        if not duration and self.end_time:
            minutes = int((self.end_time - self.start_time).total_seconds() / 60)
            duration = minutes

        if not duration:
            return "In progress"

        hours = duration // 60
        minutes = duration % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"

    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.end_time is None


@dataclass
class ErrorLog:
    """Data model representing a student error log"""

    id: str
    user_id: str
    lesson_id: Optional[str] = None
    error_data: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.error_data is None:
            self.error_data = {}

    @property
    def formatted_created_date(self) -> str:
        """Return formatted created date"""
        if not self.created_at:
            return "N/A"
        return self.created_at.strftime("%d %B %Y, %H:%M")

    @property
    def error_type(self) -> str:
        """Return the error type"""
        return self.error_data.get("error_type", "Unknown")

    @property
    def topic(self) -> str:
        """Return the topic where error occurred"""
        return self.error_data.get("topic", "Unknown")

    @property
    def student_answer(self) -> str:
        """Return the student's incorrect answer"""
        return self.error_data.get("student_answer", "")

    @property
    def correct_answer(self) -> str:
        """Return the correct answer"""
        return self.error_data.get("correct_answer", "")


@dataclass
class StudyStreak:
    """Data model representing a study streak"""

    id: str
    user_id: str
    current_streak: int = 0
    longest_streak: int = 0
    last_study_date: Optional[datetime] = None
    streak_data: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.streak_data is None:
            self.streak_data = {}

    @property
    def formatted_last_study_date(self) -> str:
        """Return formatted last study date"""
        if not self.last_study_date:
            return "N/A"
        return self.last_study_date.strftime("%d %B %Y")

    @property
    def is_active_today(self) -> bool:
        """Check if the user has studied today"""
        if not self.last_study_date:
            return False
        today = datetime.now().date()
        return self.last_study_date.date() == today

    @property
    def formatted_current_streak(self) -> str:
        """Return formatted current streak"""
        if self.current_streak == 1:
            return "1 день"
        return f"{self.current_streak} днів"

    @property
    def formatted_longest_streak(self) -> str:
        """Return formatted longest streak"""
        if self.longest_streak == 1:
            return "1 день"
        return f"{self.longest_streak} днів"

    @property
    def weekly_total_time(self) -> int:
        """Return total study time this week in minutes"""
        return self.streak_data.get("weekly_summary", {}).get("total_time", 0)

    @property
    def formatted_weekly_time(self) -> str:
        """Return formatted weekly study time"""
        total_minutes = self.weekly_total_time
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"
