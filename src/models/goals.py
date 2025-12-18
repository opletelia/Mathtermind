from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LearningGoal:
    """Data model representing a user learning goal"""

    id: str
    user_id: str
    goal_type: str  # Daily, Weekly, Course, Topic
    title: str
    description: Optional[str] = None
    target: int = 0  # Minutes, points, or lessons depending on type
    target_unit: str = "Minutes"  # Minutes, Points, Lessons, Exercises
    current_progress: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_completed: bool = False
    is_recurring: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_start_date(self) -> str:
        """Return formatted start date"""
        if not self.start_date:
            return "N/A"
        return self.start_date.strftime("%d %B %Y")

    @property
    def formatted_end_date(self) -> str:
        """Return formatted end date"""
        if not self.end_date:
            return "Continuing"
        return self.end_date.strftime("%d %B %Y")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.target <= 0:
            return 0.0
        return min(100.0, (self.current_progress / self.target) * 100)

    @property
    def formatted_progress(self) -> str:
        """Return formatted progress"""
        return (
            f"{self.current_progress}/{self.target} ({self.progress_percentage:.1f}%)"
        )

    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.end_date or self.is_completed:
            return False
        return datetime.now() > self.end_date

    @property
    def time_remaining_days(self) -> Optional[int]:
        """Calculate remaining days until deadline"""
        if not self.end_date:
            return None
        delta = self.end_date - datetime.now()
        return max(0, delta.days)


@dataclass
class PersonalBest:
    """Data model representing a personal best performance"""

    id: str
    user_id: str
    metric_type: str  # Score, Time, Streak, Accuracy, etc.
    value: float
    context_id: Optional[str] = None  # Content ID, Lesson ID, etc.
    context_type: Optional[str] = None  # "lesson", "content", "course", etc.
    achieved_at: Optional[datetime] = None
    previous_best: Optional[float] = None
    improvement: Optional[float] = None  # Percentage or absolute improvement
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_achieved_date(self) -> str:
        """Return formatted achieved date"""
        if not self.achieved_at:
            return "N/A"
        return self.achieved_at.strftime("%d %B %Y, %H:%M")

    @property
    def formatted_value(self) -> str:
        """Return formatted value based on metric type"""
        if self.metric_type.lower() == "score":
            return f"{self.value:.1f} балів"
        elif self.metric_type.lower() == "time":
            minutes = int(self.value // 60)
            seconds = int(self.value % 60)
            return f"{minutes}:{seconds:02d}"
        elif self.metric_type.lower() == "accuracy":
            return f"{self.value:.1f}%"
        else:
            return str(self.value)

    @property
    def formatted_improvement(self) -> str:
        """Return formatted improvement"""
        if self.improvement is None:
            return "N/A"
        if self.improvement > 0:
            return f"+{self.improvement:.1f}"
        return f"{self.improvement:.1f}"

