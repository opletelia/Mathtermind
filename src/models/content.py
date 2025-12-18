from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Content(ABC):
    """Base data model representing content"""

    id: str
    title: str
    content_type: str
    order: int
    lesson_id: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

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


@dataclass
class TheoryContent(Content):
    """Data model representing theory content"""

    text_content: str = ""
    images: List[str] = field(default_factory=list)
    examples: Dict[str, Any] = field(default_factory=dict)
    references: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        if self.images is None:
            self.images = []
        if self.examples is None:
            self.examples = {}
        if self.references is None:
            self.references = {}
        if not self.text_content:
            raise ValueError("Text content cannot be empty for TheoryContent")


@dataclass
class ExerciseContent(Content):
    """Data model representing exercise content"""

    problem_statement: str = ""
    solution: str = ""
    difficulty: str = ""
    hints: List[str] = field(default_factory=list)
    answer_type: str = "text"
    initial_code: str = ""

    def __post_init__(self):
        super().__post_init__()
        if self.hints is None:
            self.hints = []
        self.content_type = "exercise"
        if not self.problem_statement:
            raise ValueError("Problem statement cannot be empty for ExerciseContent")
        if not self.solution:
            raise ValueError("Solution cannot be empty for ExerciseContent")
        if not self.difficulty:
            raise ValueError("Difficulty cannot be empty for ExerciseContent")


@dataclass
class QuizContent(Content):
    """Data model representing quiz content"""

    questions: List[Dict[str, Any]] = field(default_factory=list)
    passing_score: float = 70.0

    def __post_init__(self):
        super().__post_init__()
        self.content_type = "quiz"
        if not self.questions:
            raise ValueError("Questions cannot be empty for QuizContent")


@dataclass
class AssessmentContent(Content):
    """Data model representing assessment content"""

    questions: List[Dict[str, Any]] = field(default_factory=list)
    passing_score: float = 70.0
    time_limit: Optional[int] = None
    attempts_allowed: int = 3
    is_final: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.content_type = "assessment"
        if not self.questions:
            raise ValueError("Questions cannot be empty for AssessmentContent")


@dataclass
class InteractiveContent(Content):
    """Data model representing interactive content"""

    interaction_type: str = ""
    interaction_data: Dict[str, Any] = field(default_factory=dict)
    instructions: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.content_type = "interactive"
        if not self.interaction_type:
            raise ValueError("Interaction type cannot be empty for InteractiveContent")
        if not self.interaction_data:
            raise ValueError("Interaction data cannot be empty for InteractiveContent")


@dataclass
class ResourceContent(Content):
    """Data model representing resource content"""

    resource_type: str = ""
    resource_url: str = ""
    description: str = ""
    is_required: bool = False
    created_by: Optional[str] = None
    resource_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.content_type = "resource"
        if self.resource_metadata is None:
            self.resource_metadata = {}
        if not self.resource_type:
            raise ValueError("Resource type cannot be empty for ResourceContent")
        if not self.resource_url:
            raise ValueError("Resource URL cannot be empty for ResourceContent")
        if not self.description:
            raise ValueError("Description cannot be empty for ResourceContent")


@dataclass
class ContentState:
    """Data model representing content state for resumption and versioning"""

    id: str
    user_id: str
    content_id: str
    progress_id: str
    state_type: str
    json_value: Optional[Dict[str, Any]] = None
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not any([self.json_value, self.numeric_value, self.text_value]):
            raise ValueError("At least one value field must be provided")

    @property
    def value(self) -> Any:
        """Get the primary value regardless of type"""
        if self.json_value is not None:
            return self.json_value
        elif self.numeric_value is not None:
            return self.numeric_value
        elif self.text_value is not None:
            return self.text_value
        return None
