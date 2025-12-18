"""
Seed script for populating lesson content in the database.

This script adds detailed content to existing lessons.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.core import get_logger
from src.core.error_handling import handle_db_errors
from src.db import get_db
from src.db.models import (AssessmentContent, ExerciseContent,
                           InteractiveContent, Lesson, TheoryContent)
from src.db.models.enums import ContentType

logger = get_logger(__name__)


@handle_db_errors(operation="seed_lesson_content")
def seed_lesson_content():
    """
    Add detailed content to existing lessons.
    """
    logger.info("Seeding lesson content...")

    db = next(get_db())

    lesson = (
        db.query(Lesson)
        .filter(Lesson.title.like("%Числа та арифметичні операції%"))
        .first()
    )

    if not lesson:
        logger.warning(
            "Lesson 'Числа та арифметичні операції' not found. Skipping content seeding."
        )
        return

    logger.info(f"Found lesson: {lesson.title} with ID: {lesson.id}")

    from src.db.models import Content

    deleted_count = db.query(Content).filter(Content.lesson_id == lesson.id).delete()
    if deleted_count > 0:
        logger.info(
            f"Deleted {deleted_count} existing content items for lesson '{lesson.title}'."
        )

    content_count = db.query(Content).filter(Content.lesson_id == lesson.id).count()

    if content_count > 0:
        logger.info(
            f"Lesson already has {content_count} content items. Skipping content seeding."
        )
        return

    theory = TheoryContent(
        id=uuid.uuid4(),
        lesson_id=lesson.id,
        title="Числові системи та базові операції",
        description="Основи чисел та арифметичних операцій",
        order=1,
        content_type=ContentType.THEORY,
        text_content="""
# Числа та арифметичні операції

## Вступ
Числа є фундаментальними в математиці. Вони використовуються для підрахунку, вимірювання та порівняння величин.

## Числові системи
1. **Натуральні числа** (N): 1, 2, 3, 4, ...
2. **Цілі числа** (Z): ..., -3, -2, -1, 0, 1, 2, 3, ...
3. **Раціональні числа** (Q): числа, які можна представити у вигляді дробу m/n, де m і n - цілі числа, а n ≠ 0
4. **Дійсні числа** (R): включають раціональні та ірраціональні числа

## Основні арифметичні операції

### Додавання (+)
Операція об'єднання двох чисел для отримання їх суми.
**Приклад**: 5 + 3 = 8

### Віднімання (-)
Операція знаходження різниці між двома числами.
**Приклад**: 9 - 4 = 5

### Множення (×, ·, *)
Операція додавання числа до самого себе певну кількість разів.
**Приклад**: 6 × 7 = 42

### Ділення (÷, /)
Операція знаходження, скільки разів одне число міститься в іншому.
**Приклад**: 15 ÷ 3 = 5

### Властивості арифметичних операцій
1. **Комутативність**: a + b = b + a, a × b = b × a
2. **Асоціативність**: (a + b) + c = a + (b + c), (a × b) × c = a × (b × c)
3. **Дистрибутивність**: a × (b + c) = a × b + a × c

## Порядок операцій (ДМВП)
1. Дужки
2. Множення та ділення (зліва направо)
3. Віднімання та додавання (зліва направо)

**Приклад**: 2 + 3 × 4 = 2 + 12 = 14
**Приклад**: (2 + 3) × 4 = 5 × 4 = 20
""",
        examples={
            "1": {
                "question": "Обчисліть: 15 + 7 × 2 - 3",
                "solution": "За порядком операцій, спочатку виконуємо множення: 7 × 2 = 14.\nПотім додавання та віднімання зліва направо: 15 + 14 - 3 = 29 - 3 = 26.",
            },
            "2": {
                "question": "Розв'яжіть рівняння: 5x + 10 = 35",
                "solution": "5x + 10 = 35\n5x = 35 - 10\n5x = 25\nx = 25 ÷ 5\nx = 5",
            },
        },
        references={
            "books": ["Математика для чайників", "Основи арифметики"],
            "websites": ["https://www.mathsisfun.com/", "https://www.khanacademy.org/"],
        },
        created_at=datetime.now(timezone.utc),
    )
    db.add(theory)

    exercise = ExerciseContent(
        id=uuid.uuid4(),
        lesson_id=lesson.id,
        title="Практичні вправи з арифметики",
        description="Вправи для закріплення матеріалу",
        order=2,
        content_type=ContentType.EXERCISE,
        problems={
            "exercises": [
                {
                    "id": "e1",
                    "type": "computation",
                    "question": "Обчисліть: 25 - 8 + 12",
                    "answer": "29",
                },
                {
                    "id": "e2",
                    "type": "computation",
                    "question": "Обчисліть: 7 × 9 - 14",
                    "answer": "49",
                },
                {
                    "id": "e3",
                    "type": "computation",
                    "question": "Обчисліть: 36 ÷ 4 + 17",
                    "answer": "26",
                },
                {
                    "id": "e4",
                    "type": "computation",
                    "question": "Обчисліть: 3 × (10 + 5) - 12",
                    "answer": "33",
                },
                {
                    "id": "e5",
                    "type": "word_problem",
                    "question": "У Марії було 35 яблук. Вона віддала 12 яблук своїм друзям, а потім купила ще 8 яблук. Скільки яблук у неї залишилося?",
                    "answer": "31",
                },
            ]
        },
        estimated_time=15,
        created_at=datetime.now(timezone.utc),
    )
    db.add(exercise)

    assessment = AssessmentContent(
        id=uuid.uuid4(),
        lesson_id=lesson.id,
        title="Контрольний тест",
        description="Перевірка розуміння матеріалу",
        order=3,
        content_type=ContentType.ASSESSMENT,
        questions={
            "questions": [
                {
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "Який результат виразу: 8 + 4 × (6 - 2) ÷ 2?",
                    "options": ["16", "24", "12", "20"],
                    "correct_answer": "16",
                    "explanation": "За порядком операцій: спочатку дужки (6 - 2 = 4), потім множення і ділення зліва направо (4 × 4 = 16, 16 ÷ 2 = 8), нарешті додавання (8 + 8 = 16).",
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "question": "Яка з нижченаведених властивостей НЕ виконується для операції віднімання?",
                    "options": [
                        "Комутативність",
                        "Асоціативність",
                        "Дистрибутивність",
                        "Всі властивості не виконуються",
                    ],
                    "correct_answer": "Комутативність",
                    "explanation": "Віднімання не є комутативною операцією, тобто a - b ≠ b - a. Наприклад, 5 - 3 = 2, але 3 - 5 = -2.",
                },
                {
                    "id": "q3",
                    "type": "true_false",
                    "question": "Вираз (a + b)² завжди дорівнює a² + b².",
                    "correct_answer": "Хибно",
                    "explanation": "(a + b)² = a² + 2ab + b², а не просто a² + b².",
                },
                {
                    "id": "q4",
                    "type": "fill_in_blank",
                    "question": "Якщо 3x - 7 = 20, то x = ___.",
                    "correct_answer": "9",
                    "explanation": "3x - 7 = 20\n3x = 27\nx = 9",
                },
                {
                    "id": "q5",
                    "type": "multiple_choice",
                    "question": "Скільки натуральних чисел знаходиться між 15 та 31?",
                    "options": ["13", "14", "15", "16"],
                    "correct_answer": "15",
                    "explanation": "Натуральні числа між 15 та 31: 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30. Всього 15 чисел.",
                },
            ]
        },
        time_limit=20,
        passing_score=70.0,
        attempts_allowed=3,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assessment)

    db.commit()
    logger.info(f"Added 3 content items to the lesson: {lesson.title}")


if __name__ == "__main__":
    seed_lesson_content()

