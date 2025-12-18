"""
Seed script for populating the database with sample course data.

This script creates sample courses and lessons in the database for development
and testing purposes.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db import get_db
from src.db.models import Course, Lesson
from src.db.models.enums import Topic

logger = get_logger(__name__)


@handle_db_errors(operation="seed_courses")
def seed_courses():
    """
    Seed the database with sample course data.
    """
    logger.info("Seeding courses...")

    db = next(get_db())

    existing_courses = db.query(Course).count()
    if existing_courses > 0:
        logger.info(f"Found {existing_courses} existing courses. Skipping seeding.")
        return

    courses = [
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Базова математика",
            "description": "Курс з основ математики: числа, дії, дроби та відсотки для учнів 5-6 класів",
            "duration": 120,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Алгебра 7 клас",
            "description": "Вивчення виразів, рівнянь та функцій для учнів 7 класу",
            "duration": 180,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Геометрія 7-8 клас",
            "description": "Планіметрія: трикутники, чотирикутники, коло та їх властивості",
            "duration": 200,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Алгебра 8 клас",
            "description": "Квадратні рівняння, нерівності та квадратний корінь",
            "duration": 180,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Математика для НМТ",
            "description": "Підготовка до НМТ з математики: теорія та практичні завдання",
            "duration": 300,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Цікава математика",
            "description": "Логічні задачі, головоломки та математичні ігри для розвитку мислення",
            "duration": 90,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Основи програмування",
            "description": "Перші кроки у програмуванні: алгоритми, блок-схеми та Python для початківців",
            "duration": 150,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Scratch для дітей",
            "description": "Візуальне програмування у Scratch: створюємо ігри та анімації",
            "duration": 120,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Python для школярів",
            "description": "Вивчення Python через цікаві проєкти: ігри, малювання та автоматизація",
            "duration": 180,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Комп'ютерна грамотність",
            "description": "Основи роботи з комп'ютером: файли, папки, текстові редактори та презентації",
            "duration": 90,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Безпека в Інтернеті",
            "description": "Як безпечно користуватися Інтернетом: паролі, приватність та кібербулінг",
            "duration": 60,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Створення веб-сторінок",
            "description": "Основи HTML та CSS: створюємо власну веб-сторінку крок за кроком",
            "duration": 150,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Інформатика 9 клас",
            "description": "Шкільний курс інформатики: електронні таблиці, бази даних та презентації",
            "duration": 180,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Дроби та відсотки",
            "description": "Все про дроби: звичайні, десяткові, відсотки та їх застосування",
            "duration": 120,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.MATHEMATICS,
            "name": "Текстові задачі",
            "description": "Як розв'язувати текстові задачі: на рух, роботу, суміші та відсотки",
            "duration": 150,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.uuid4(),
            "topic": Topic.INFORMATICS,
            "name": "Алгоритми та логіка",
            "description": "Розвиток алгоритмічного мислення через задачі та головоломки",
            "duration": 120,
            "created_at": datetime.now(timezone.utc),
        },
    ]

    course_objects = []
    for course_data in courses:
        course = Course(**course_data)
        db.add(course)
        course_objects.append(course)

    db.commit()
    logger.info(f"Created {len(courses)} sample courses")

    _seed_lessons(db, course_objects)

    logger.info("Course and lesson seeding completed successfully")


def _seed_lessons(db: Session, courses: List[Course]):
    """
    Seed the database with sample lessons for each course.

    Args:
        db: The database session
        courses: List of course objects to create lessons for
    """
    logger.info("Seeding lessons for courses...")

    course_lessons_with_sections = {
        "Базова математика": [
            ("Арифметика", ["Числа та їх властивості", "Додавання та віднімання", "Множення та ділення"]),
            ("Дроби", ["Звичайні дроби", "Десяткові дроби", "Операції з дробами"]),
            ("Відсотки", ["Поняття відсотка", "Задачі на відсотки"]),
        ],
        "Геометрія 7-8 клас": [
            ("Трикутники", ["Види трикутників", "Властивості трикутників", "Площа трикутника"]),
            ("Чотирикутники", ["Паралелограм", "Прямокутник та квадрат", "Трапеція"]),
            ("Коло", ["Властивості кола", "Дуги та хорди", "Площа круга"]),
        ],
        "Алгебра 7 клас": [
            ("Вирази", ["Числові вирази", "Буквені вирази", "Спрощення виразів"]),
            ("Рівняння", ["Лінійні рівняння", "Розв'язування рівнянь"]),
            ("Функції", ["Поняття функції", "Графіки функцій"]),
        ],
        "Алгебра 8 клас": [
            ("Квадратні рівняння", ["Неповні квадратні рівняння", "Формула коренів", "Теорема Вієта"]),
            ("Нерівності", ["Числові нерівності", "Лінійні нерівності", "Системи нерівностей"]),
            ("Квадратний корінь", ["Властивості кореня", "Операції з коренями"]),
        ],
        "Основи програмування": [
            ("Алгоритми", ["Що таке алгоритм", "Блок-схеми", "Типи алгоритмів"]),
            ("Python: Основи", ["Змінні та типи даних", "Введення та виведення", "Умовні оператори"]),
            ("Python: Цикли", ["Цикл while", "Цикл for", "Вкладені цикли"]),
        ],
        "Scratch для дітей": [
            ("Знайомство", ["Інтерфейс Scratch", "Спрайти та сцени"]),
            ("Рух та анімація", ["Команди руху", "Костюми та анімація", "Звуки"]),
            ("Ігри", ["Керування персонажем", "Створення простої гри"]),
        ],
        "Python для школярів": [
            ("Основи", ["Встановлення Python", "Перша програма", "Типи даних"]),
            ("Структури даних", ["Списки", "Словники", "Кортежі"]),
            ("Функції", ["Створення функцій", "Параметри та повернення", "Модулі"]),
        ],
        "Безпека в Інтернеті": [
            ("Основи безпеки", ["Основи кібербезпеки", "Надійні паролі"]),
            ("Захист даних", ["Захист особистих даних", "Кібербулінг та як з ним боротися"]),
        ],
        "Інформатика 9 клас": [
            ("Електронні таблиці", ["Основи Excel", "Формули та функції", "Діаграми та графіки"]),
            ("Бази даних", ["Поняття БД", "Запити до БД"]),
            ("Презентації", ["Створення презентацій", "Анімація та ефекти"]),
        ],
        "Дроби та відсотки": [
            ("Дроби", ["Звичайні дроби", "Десяткові дроби", "Порівняння дробів"]),
            ("Відсотки", ["Поняття відсотка", "Задачі на відсотки"]),
        ],
        "Цікава математика": [
            ("Головоломки", ["Математичні головоломки", "Логічні задачі"]),
            ("Ребуси", ["Геометричні ребуси", "Числові послідовності"]),
            ("Фокуси", ["Математичні фокуси"]),
        ],
        "Текстові задачі": [
            ("Задачі на рух", ["Рівномірний рух", "Зустрічний рух", "Рух вздогін"]),
            ("Задачі на роботу", ["Спільна робота", "Продуктивність"]),
            ("Задачі на суміші", ["Концентрація", "Сплави та розчини"]),
        ],
        "Математика для НМТ": [
            ("Алгебра", ["Рівняння та нерівності", "Функції та графіки", "Прогресії"]),
            ("Геометрія", ["Планіметрія", "Стереометрія", "Координати"]),
            ("Підготовка", ["Типові завдання НМТ", "Стратегії розв'язування"]),
        ],
        "Комп'ютерна грамотність": [
            ("Основи роботи", ["Знайомство з комп'ютером", "Файли та папки", "Робочий стіл"]),
            ("Текстові редактори", ["Microsoft Word", "Форматування тексту", "Таблиці та зображення"]),
            ("Презентації", ["PowerPoint основи", "Створення слайдів", "Анімація"]),
        ],
        "Створення веб-сторінок": [
            ("HTML", ["Структура HTML", "Теги та атрибути", "Посилання та зображення"]),
            ("CSS", ["Селектори", "Кольори та шрифти", "Блокова модель"]),
            ("Практика", ["Створення сторінки", "Адаптивний дизайн"]),
        ],
        "Алгоритми та логіка": [
            ("Логічне мислення", ["Логічні задачі", "Умовиводи", "Парадокси"]),
            ("Алгоритми", ["Послідовність дій", "Розгалуження", "Повторення"]),
            ("Практика", ["Задачі на алгоритми", "Оптимізація"]),
        ],
    }

    lessons_count = 0

    for course in courses:
        lesson_order = 1
        
        if course.name in course_lessons_with_sections:
            sections = course_lessons_with_sections[course.name]
            for section_name, lesson_titles in sections:
                for title in lesson_titles:
                    lesson = Lesson(
                        id=uuid.uuid4(),
                        course_id=course.id,
                        title=title,
                        section=section_name,
                        lesson_order=lesson_order,
                        estimated_time=30,
                        points_reward=100,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(lesson)
                    lessons_count += 1
                    lesson_order += 1
        else:
            default_sections = [
                ("Вступ", ["Огляд курсу", "Основні поняття"]),
                ("Основний матеріал", ["Теорія", "Приклади", "Практика"]),
                ("Закріплення", ["Підсумки", "Тестування"]),
            ]
            for section_name, lesson_titles in default_sections:
                for title in lesson_titles:
                    lesson = Lesson(
                        id=uuid.uuid4(),
                        course_id=course.id,
                        title=title,
                        section=section_name,
                        lesson_order=lesson_order,
                        estimated_time=30,
                        points_reward=100,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(lesson)
                    lessons_count += 1
                    lesson_order += 1

    db.commit()
    logger.info(f"Created {lessons_count} sample lessons")


def _get_lesson_title(topic: Topic, lesson_number: int, level: int) -> str:
    """
    Generate a relevant lesson title based on the course topic and lesson number.

    Args:
        topic: The course topic
        lesson_number: The lesson number
        level: Difficulty level (0: beginner, 1: intermediate, 2: advanced)

    Returns:
        A lesson title
    """
    math_lessons = {
        0: [  # Beginner
            "Числа та арифметичні операції",
            "Дроби та відсотки",
            "Геометричні фігури",
            "Основи алгебри",
            "Розв'язування простих рівнянь",
            "Пропорції та відношення",
            "Вимірювання та одиниці виміру",
            "Основи теорії множин",
        ],
        1: [  # Intermediate
            "Лінійні рівняння",
            "Функції та графіки",
            "Квадратні рівняння",
            "Системи рівнянь",
            "Тригонометричні функції",
            "Вектори та матриці",
            "Логарифми та експоненти",
            "Статистичні методи",
        ],
        2: [  # Advanced
            "Тригонометрія",
            "Похідні функцій",
            "Інтеграли",
            "Диференціальні рівняння",
            "Комплексні числа",
            "Аналітична геометрія",
            "Теорія груп",
            "Числові ряди",
        ],
    }

    info_lessons = {
        0: [  # Beginner
            "Алгоритми та блок-схеми",
            "Змінні та типи даних",
            "Умови та цикли",
            "Основи функцій",
            "Робота з файлами",
            "Масиви та списки",
            "Основи об'єктно-орієнтованого програмування",
            "Введення та виведення даних",
        ],
        1: [  # Intermediate
            "Масиви та списки",
            "Функції та методи",
            "Хеш-таблиці",
            "Графи та дерева",
            "Рекурсивні алгоритми",
            "Обробка винятків",
            "Основи мережевого програмування",
            "Робота з базами даних",
        ],
        2: [  # Advanced
            "HTML, CSS, JavaScript",
            "Фреймворки та бібліотеки",
            "Бази даних",
            "Серверна частина",
            "Розгортання додатків",
            "Безпека веб-додатків",
            "RESTful API",
            "Мікросервісна архітектура",
        ],
    }

    if lesson_number <= 0:
        return "Вступ до курсу"

    if topic == Topic.MATHEMATICS:
        lessons = math_lessons.get(level, [])
    else:
        lessons = info_lessons.get(level, [])

    if lesson_number <= len(lessons):
        return lessons[lesson_number - 1]
    else:
        return f"Додатковий матеріал {lesson_number - len(lessons)}"
