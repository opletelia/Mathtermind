import enum

# TODO: translate all enums to ukrainian


class AgeGroup(str, enum.Enum):
    """Age groups for users."""

    TEN_TO_TWELVE = "10-12"
    THIRTEEN_TO_FOURTEEN = "13-14"
    FIFTEEN_TO_SEVENTEEN = "15-17"


class AnswerType(str, enum.Enum):
    """Types of answers for questions."""

    MULTIPLE_CHOICE = "Множинний вибір"
    OPEN_ENDED = "Відкрита відповідь"
    CODE = "Код"
    MATHEMATICAL = "Математична формула"
    MATCHING = "Відповідність"
    TRUE_FALSE = "Істина/Хиба"


class InteractiveType(str, enum.Enum):
    """Types of interactive content."""

    SIMULATION = "Симуляція"
    TOOL = "Інструмент"
    GAME = "Гра"
    VISUALIZATION = "Візуалізація"


class MathToolType(str, enum.Enum):
    """Types of mathematical tools."""

    GRAPHING = "Графік"
    GEOMETRY = "Геометрія"
    EQUATION_SOLVER = "Рівняння"
    STATISTICS = "Статистика"
    PROBABILITY = "Ймовірність"
    MATRIX = "Матриця"


class InformaticsToolType(str, enum.Enum):
    """Types of informatics tools."""

    CODE_EDITOR = "Редактор коду"
    ALGORITHM_VISUALIZER = "Алгоритмічний візуалізатор"
    DATA_STRUCTURE_VISUALIZER = "Структура даних візуалізатор"
    LOGIC_CIRCUIT = "Логічний пристрій"
    DATABASE_DESIGNER = "Дизайнер бази даних"
    NETWORK_SIMULATOR = "Симулятор мережі"


class MetricType(str, enum.Enum):
    """Types of metrics for personal bests."""

    SCORE = "Оцінка"
    TIME = "Час"
    STREAK = "Безперервність"
    ACCURACY = "Точність"
    PROBLEMS_SOLVED = "Вирішені завдання"
    CONSECUTIVE_CORRECT = "Послідовні правильні відповіді"


class Category(str, enum.Enum):
    """Categories for tags."""

    TOPIC = "Тема"
    SKILL = "Навичка"
    DIFFICULTY = "Складність"
    AGE = "Вік"
    OTHER = "Інше"


class ResourceType(str, enum.Enum):
    """Types of resources."""

    VIDEO = "Відео"
    TEXT = "Текст"
    IMAGE = "Зображення"
    AUDIO = "Аудіо"
    LINK = "Посилання"


class Topic(str, enum.Enum):
    """Topics for courses."""

    INFORMATICS = "Інформатика"
    MATHEMATICS = "Математика"


class DifficultyLevel(str, enum.Enum):
    """Difficulty levels for lessons."""

    BEGINNER = "Початковий"
    INTERMEDIATE = "Середній"
    ADVANCED = "Досвідчений"


class ContentType(str, enum.Enum):
    """Types of content."""

    THEORY = "theory"
    EXERCISE = "exercise"
    ASSESSMENT = "assessment"
    INTERACTIVE = "interactive"
    RESOURCE = "resource"


class LessonType(str, enum.Enum):
    """Types of lessons."""

    THEORY = "Теорія"
    EXERCISE = "Завдання"
    ASSESSMENT = "Оцінювання"
    INTERACTIVE = "Інтерактивне завдання"
    RESOURCE = "Ресурс"


class ThemeType(str, enum.Enum):
    """User interface theme options."""

    LIGHT = "Світла"
    DARK = "Темна"


class FontSize(str, enum.Enum):
    """Font size options for accessibility."""

    SMALL = "Маленький"
    MEDIUM = "Середній"
    LARGE = "Великий"


class PreferredSubject(str, enum.Enum):
    """User's preferred subject for study."""

    MATH = "Математика"
    INFORMATICS = "Інформатика"

