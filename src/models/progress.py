from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Progress:
    """Data model representing user progress in a course"""

    id: str
    user_id: str
    course_id: str
    current_lesson_id: Optional[str] = None
    total_points_earned: int = 0
    time_spent: int = 0  # in minutes
    progress_percentage: float = 0.0
    progress_data: Dict[str, Any] = None
    last_accessed: Optional[datetime] = None
    is_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.progress_data is None:
            self.progress_data = {}

    @property
    def formatted_last_accessed(self) -> str:
        """Return formatted last accessed date"""
        if not self.last_accessed:
            return "N/A"
        return self.last_accessed.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_time_spent(self) -> str:
        """Return formatted time spent"""
        hours = self.time_spent // 60
        minutes = self.time_spent % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"

    @property
    def formatted_progress(self) -> str:
        """Return formatted progress percentage"""
        return f"{self.progress_percentage:.1f}%"


@dataclass
class ContentState:
    """Data model representing the state of a content item"""

    id: str
    user_id: str
    progress_id: str
    content_id: str
    state_type: str
    numeric_value: Optional[float] = None
    json_value: Optional[Dict[str, Any]] = None
    text_value: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @property
    def formatted_updated_date(self) -> str:
        """Return formatted updated date"""
        if not self.updated_at:
            return "N/A"
        return self.updated_at.strftime("%d %B %Y, %H:%M")

    @property
    def value(self) -> Any:
        """Return the appropriate value based on state type"""
        if self.numeric_value is not None:
            return self.numeric_value
        elif self.json_value is not None:
            return self.json_value
        elif self.text_value is not None:
            return self.text_value
        return None


@dataclass
class UserContentProgress:
    """Data model representing user progress on a specific content item"""

    id: str
    user_id: str
    content_id: str
    lesson_id: str
    progress_id: str
    status: str = "not_started"  # not_started, in_progress, completed
    score: Optional[float] = None
    time_spent: int = 0  # in seconds
    last_interaction: Optional[datetime] = None
    custom_data: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.custom_data is None:
            self.custom_data = {}

    @property
    def formatted_last_interaction(self) -> str:
        """Return formatted last interaction date"""
        if not self.last_interaction:
            return "N/A"
        return self.last_interaction.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_time_spent(self) -> str:
        """Return formatted time spent"""
        minutes = self.time_spent // 60
        seconds = self.time_spent % 60

        if minutes > 0:
            return f"{minutes}:{seconds:02d}"
        else:
            return f"{seconds} с"

    @property
    def formatted_score(self) -> str:
        """Return formatted score"""
        if self.score is None:
            return "N/A"
        return f"{self.score:.1f}"

    @property
    def is_completed(self) -> bool:
        """Check if the content is completed"""
        return self.status == "completed"


@dataclass
class CompletedLesson:
    """Data model representing a completed lesson"""

    id: str
    user_id: str
    lesson_id: str
    course_id: str
    completed_at: datetime
    score: Optional[float] = None
    time_spent: int = 0  # in minutes
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_completed_date(self) -> str:
        """Return formatted completion date"""
        return self.completed_at.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_time_spent(self) -> str:
        """Return formatted time spent"""
        hours = self.time_spent // 60
        minutes = self.time_spent % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"

    @property
    def formatted_score(self) -> str:
        """Return formatted score"""
        if self.score is None:
            return "N/A"
        return f"{self.score:.1f}"


@dataclass
class CompletedCourse:
    """Data model representing a completed course"""

    id: str
    user_id: str
    course_id: str
    completed_at: datetime
    final_score: Optional[float] = None
    total_time_spent: int = 0  # in minutes
    completed_lessons_count: int = 0
    achievements_earned: List[str] = None
    certificate_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.achievements_earned is None:
            self.achievements_earned = []

    @property
    def formatted_completed_date(self) -> str:
        """Return formatted completion date"""
        return self.completed_at.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_time_spent(self) -> str:
        """Return formatted time spent"""
        hours = self.total_time_spent // 60
        minutes = self.total_time_spent % 60

        if hours > 0 and minutes > 0:
            return f"{hours} год {minutes} хв"
        elif hours > 0:
            return f"{hours} год"
        else:
            return f"{minutes} хв"

    @property
    def formatted_score(self) -> str:
        """Return formatted score"""
        if self.final_score is None:
            return "N/A"
        return f"{self.final_score:.1f}"

    @property
    def has_certificate(self) -> bool:
        """Check if a certificate was issued"""
        return self.certificate_id is not None

