"""Seed script to populate Basic Math course with comprehensive content."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from src.db import get_db
from src.db.models import (AssessmentContent, Content, Course, ExerciseContent,
                           InteractiveContent, Lesson, Progress, TheoryContent,
                           User)


def seed_math_course():
    """Seed comprehensive basic math course."""
    session = next(get_db())
    try:
        course = (
            session.query(Course).filter(Course.name == "Базова математика").first()
        )
        if not course:
            print("Course 'Базова математика' not found!")
            return

        print(f"Found course: {course.name} (ID: {course.id})")

        course_id_str = str(course.id)
        admin_user = session.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Admin user not found. Skipping admin progress seeding.")
            admin_user_id = None
        else:
            admin_user_id = str(admin_user.id)

        session.query(Content).filter(
            Content.lesson_id.in_(
                session.query(Lesson.id).filter(Lesson.course_id == course.id)
            )
        ).delete(synchronize_session=False)

        session.query(Lesson).filter(Lesson.course_id == course.id).delete()
        session.commit()

        print("Cleared existing lessons and content")

        lessons_data = [
            {
                "title": "Натуральні числа та операції",
                "section": "Арифметика",
                "order": 1,
                "estimated_time": 40,
                "points": 100,
                "content": [
                    {
                        "type": "theory",
                        "title": "Натуральні числа",
                        "order": 1,
                        "data": {
                            "text": """# Натуральні числа та основні операції

## Що таке натуральні числа?

Натуральні числа - це числа, які використовуються для підрахунку: 1, 2, 3, 4, 5, ...

## Основні операції

### Додавання (+)
Об'єднання двох чисел в одне більше число.
```
5 + 3 = 8
12 + 7 = 19
```

### Віднімання (-)
Знаходження різниці між двома числами.
```
10 - 4 = 6
25 - 13 = 12
```

### Множення (×)
Багаторазове додавання однакових чисел.
```
4 × 3 = 12 (це 4 + 4 + 4)
7 × 5 = 35
```

### Ділення (÷)
Розподіл числа на рівні частини.
```
20 ÷ 4 = 5
36 ÷ 6 = 6
```

## Порядок дій

При обчисленні виразів дотримуйтесь порядку:
1. Дужки
2. Множення та ділення (зліва направо)
3. Додавання та віднімання (зліва направо)

**Приклад:** 2 + 3 × 4 = 2 + 12 = 14 (спочатку множення!)"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Додавання",
                        "order": 2,
                        "data": {
                            "question": "Обчисліть: 15 + 27",
                            "solution": "42",
                            "hints": [
                                "Додайте одиниці: 5 + 7 = 12",
                                "Перенесіть 1 до десятків",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Віднімання",
                        "order": 3,
                        "data": {
                            "question": "Обчисліть: 83 - 45",
                            "solution": "38",
                            "hints": [
                                "Віднімайте по розрядах",
                                "83 - 45 = 83 - 40 - 5",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Множення",
                        "order": 4,
                        "data": {
                            "question": "Обчисліть: 7 × 8",
                            "solution": "56",
                            "hints": ["Згадайте таблицю множення", "7 × 8 = 7 × 7 + 7"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Ділення",
                        "order": 5,
                        "data": {
                            "question": "Обчисліть: 72 ÷ 9",
                            "solution": "8",
                            "hints": [
                                "На яке число треба помножити 9, щоб отримати 72?"
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Порядок дій",
                        "order": 6,
                        "data": {
                            "question": "Обчисліть: 5 + 3 × 4",
                            "solution": "17",
                            "hints": ["Спочатку множення!", "3 × 4 = 12, потім 5 + 12"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Перевірка знань",
                        "order": 7,
                        "data": {
                            "questions": [
                                {
                                    "question": "Скільки буде 25 + 17?",
                                    "type": "multiple_choice",
                                    "options": ["32", "42", "52", "41"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Скільки буде 6 × 7?",
                                    "type": "multiple_choice",
                                    "options": ["36", "42", "48", "35"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "100 - 37 = 63",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "8 × 9 = 81",
                                    "type": "true_false",
                                    "correct_answer": False,
                                },
                                {
                                    "question": "Обчисліть: 48 ÷ 6",
                                    "type": "short_answer",
                                    "correct_answer": "8",
                                },
                                {
                                    "question": "Обчисліть: 9 × 9",
                                    "type": "short_answer",
                                    "correct_answer": "81",
                                },
                                {
                                    "question": "15 + 5 × 2 = _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "25",
                                },
                                {
                                    "question": "(10 + 5) × 2 = _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "30",
                                },
                                {
                                    "question": "Співставте операції з результатами",
                                    "type": "drag_drop",
                                    "descriptions": ["5 + 7", "12 - 4", "3 × 4"],
                                    "words": ["12", "8", "12"],
                                    "answers": ["12", "8", "12"],
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Звичайні та десяткові дроби",
                "section": "Дроби",
                "order": 2,
                "estimated_time": 50,
                "points": 150,
                "content": [
                    {
                        "type": "theory",
                        "title": "Звичайні дроби",
                        "order": 1,
                        "data": {
                            "text": """# Дроби

## Що таке дріб?

Дріб - це частина цілого. Записується як **a/b**, де:
- **a** - чисельник (скільки частин взяли)
- **b** - знаменник (на скільки частин поділили)

**Приклад:** 3/4 означає "три чверті" - ціле поділене на 4 частини, взято 3.

## Види дробів

### Правильні дроби
Чисельник менший за знаменник: 1/2, 3/4, 5/8

### Неправильні дроби
Чисельник більший або рівний знаменнику: 5/3, 7/4, 9/9

### Мішані числа
Ціла частина + дріб: 2½, 3¾

## Операції з дробами

### Додавання (однакові знаменники)
```
1/4 + 2/4 = 3/4
```

### Додавання (різні знаменники)
```
1/2 + 1/3 = 3/6 + 2/6 = 5/6
```

### Множення дробів
```
2/3 × 3/4 = 6/12 = 1/2
```

### Ділення дробів
```
2/3 ÷ 1/2 = 2/3 × 2/1 = 4/3
```

## Скорочення дробів

Ділимо чисельник і знаменник на їх спільний дільник:
```
6/8 = 3/4 (поділили на 2)
15/20 = 3/4 (поділили на 5)
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Додавання дробів",
                        "order": 2,
                        "data": {
                            "question": "Обчисліть: 1/4 + 2/4",
                            "solution": "3/4",
                            "hints": [
                                "Знаменники однакові",
                                "Додайте тільки чисельники",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Множення дробів",
                        "order": 3,
                        "data": {
                            "question": "Обчисліть: 1/2 × 2/3",
                            "solution": "1/3",
                            "hints": [
                                "Помножте чисельники: 1 × 2",
                                "Помножте знаменники: 2 × 3",
                                "Скоротіть результат",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Скорочення дробів",
                        "order": 4,
                        "data": {
                            "question": "Скоротіть дріб: 8/12",
                            "solution": "2/3",
                            "hints": [
                                "Знайдіть спільний дільник",
                                "8 і 12 діляться на 4",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Дроби",
                        "order": 5,
                        "data": {
                            "questions": [
                                {
                                    "question": "Яка частина кола зафарбована, якщо зафарбовано 3 з 8 секторів?",
                                    "type": "multiple_choice",
                                    "options": ["3/8", "8/3", "5/8", "3/5"],
                                    "correct_answer": 0,
                                },
                                {
                                    "question": "Скільки буде 2/5 + 1/5?",
                                    "type": "multiple_choice",
                                    "options": ["3/10", "3/5", "2/5", "1/5"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "1/2 більше за 1/3",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "4/8 = 1/2",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "Скоротіть дріб 6/9",
                                    "type": "short_answer",
                                    "correct_answer": "2/3",
                                },
                                {
                                    "question": "1/2 × 1/2 = _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "1/4",
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Відсотки та їх застосування",
                "section": "Відсотки",
                "order": 3,
                "estimated_time": 45,
                "points": 150,
                "content": [
                    {
                        "type": "theory",
                        "title": "Відсотки",
                        "order": 1,
                        "data": {
                            "text": """# Відсотки

## Що таке відсоток?

Відсоток (%) - це одна сота частина числа.
- 1% = 1/100 = 0.01
- 50% = 50/100 = 1/2
- 100% = ціле число

## Як знайти відсоток від числа?

**Формула:** число × (відсоток / 100)

**Приклади:**
```
10% від 200 = 200 × 0.1 = 20
25% від 80 = 80 × 0.25 = 20
50% від 60 = 60 × 0.5 = 30
```

## Як знайти число за його відсотком?

**Формула:** значення / (відсоток / 100)

**Приклад:** 20 - це 25% від якого числа?
```
20 / 0.25 = 80
```

## Практичні застосування

### Знижки
Товар коштує 500 грн, знижка 20%:
```
Знижка = 500 × 0.2 = 100 грн
Нова ціна = 500 - 100 = 400 грн
```

### Відсоткове збільшення
Зарплата 10000 грн, підвищення на 15%:
```
Підвищення = 10000 × 0.15 = 1500 грн
Нова зарплата = 10000 + 1500 = 11500 грн
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Знаходження відсотка",
                        "order": 2,
                        "data": {
                            "question": "Знайдіть 10% від 150",
                            "solution": "15",
                            "hints": ["10% = 0.1", "150 × 0.1 = ?"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Знижка",
                        "order": 3,
                        "data": {
                            "question": "Товар коштує 200 грн. Яка ціна зі знижкою 25%?",
                            "solution": "150",
                            "hints": [
                                "Знайдіть 25% від 200",
                                "Відніміть від початкової ціни",
                            ],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Відсоткове збільшення",
                        "order": 4,
                        "data": {
                            "question": "Ціна зросла на 20% і стала 120 грн. Яка була початкова ціна?",
                            "solution": "100",
                            "hints": ["120 = 100% + 20% = 120%", "120 / 1.2 = ?"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Відсотки",
                        "order": 5,
                        "data": {
                            "questions": [
                                {
                                    "question": "Скільки буде 50% від 80?",
                                    "type": "multiple_choice",
                                    "options": ["20", "30", "40", "50"],
                                    "correct_answer": 2,
                                },
                                {
                                    "question": "25% = 1/4",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "100% від будь-якого числа дорівнює цьому числу",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "Знайдіть 20% від 50",
                                    "type": "short_answer",
                                    "correct_answer": "10",
                                },
                                {
                                    "question": "1% від 300 = _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "3",
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Лінійні рівняння",
                "section": "Рівняння",
                "order": 4,
                "estimated_time": 55,
                "points": 200,
                "content": [
                    {
                        "type": "theory",
                        "title": "Лінійні рівняння",
                        "order": 1,
                        "data": {
                            "text": """# Рівняння

## Що таке рівняння?

Рівняння - це рівність з невідомою величиною (зазвичай x).

**Приклад:** x + 5 = 12

## Розв'язування простих рівнянь

### Правило: що робимо з одним боком, робимо з іншим

**Приклад 1:** x + 5 = 12
```
x + 5 - 5 = 12 - 5
x = 7
```

**Приклад 2:** x - 3 = 10
```
x - 3 + 3 = 10 + 3
x = 13
```

**Приклад 3:** 2x = 14
```
2x / 2 = 14 / 2
x = 7
```

**Приклад 4:** x / 4 = 5
```
x / 4 × 4 = 5 × 4
x = 20
```

## Складніші рівняння

**Приклад:** 3x + 5 = 20
```
3x + 5 - 5 = 20 - 5
3x = 15
x = 15 / 3
x = 5
```

## Перевірка розв'язку

Підставляємо знайдене значення в початкове рівняння:
```
3 × 5 + 5 = 15 + 5 = 20 ✓
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Просте рівняння",
                        "order": 2,
                        "data": {
                            "question": "Розв'яжіть: x + 7 = 15",
                            "solution": "8",
                            "hints": ["Відніміть 7 від обох сторін", "x = 15 - 7"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Рівняння з множенням",
                        "order": 3,
                        "data": {
                            "question": "Розв'яжіть: 4x = 28",
                            "solution": "7",
                            "hints": ["Поділіть обидві сторони на 4", "x = 28 / 4"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Складне рівняння",
                        "order": 4,
                        "data": {
                            "question": "Розв'яжіть: 2x + 6 = 20",
                            "solution": "7",
                            "hints": ["Спочатку відніміть 6", "Потім поділіть на 2"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Рівняння",
                        "order": 5,
                        "data": {
                            "questions": [
                                {
                                    "question": "Розв'яжіть: x - 5 = 10",
                                    "type": "multiple_choice",
                                    "options": ["5", "10", "15", "20"],
                                    "correct_answer": 2,
                                },
                                {
                                    "question": "Розв'яжіть: 3x = 21",
                                    "type": "multiple_choice",
                                    "options": ["6", "7", "8", "9"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Якщо x + 10 = 10, то x = 0",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "Розв'яжіть: x / 5 = 4",
                                    "type": "short_answer",
                                    "correct_answer": "20",
                                },
                                {
                                    "question": "x + 8 = 15, тоді x = _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "7",
                                },
                            ]
                        },
                    },
                    {
                        "type": "interactive",
                        "title": "Графік лінійного рівняння",
                        "order": 6,
                        "data": {
                            "interactive_type": "simulation",
                            "configuration": {
                                "simulation_type": "graph_plot",
                                "initial_state": {
                                    "equations": [
                                        {"equation": "y = x + 2", "color": "#3498db"},
                                        {"equation": "y = 2x - 1", "color": "#e74c3c"},
                                        {"equation": "y = -x + 5", "color": "#2ecc71"},
                                    ],
                                    "domain": [-10, 10],
                                    "range": [-10, 10],
                                },
                                "ui_config": {
                                    "show_grid": True,
                                    "show_axes": True,
                                    "show_labels": True,
                                    "allow_zoom": True,
                                    "allow_pan": True,
                                },
                                "tasks": [
                                    {
                                        "id": "t1",
                                        "description": "Знайдіть точку перетину y = x + 2 з віссю Y",
                                        "expected_answer": "(0, 2)",
                                        "hint": "Підставте x = 0 у рівняння",
                                    },
                                    {
                                        "id": "t2",
                                        "description": "Де графік y = 2x - 1 перетинає вісь X?",
                                        "expected_answer": "(0.5, 0)",
                                        "hint": "Знайдіть x, коли y = 0",
                                    },
                                ],
                            },
                            "instructions": "Досліджуйте графіки лінійних рівнянь. Спостерігайте, як змінюється нахил та положення прямої залежно від коефіцієнтів.",
                        },
                    },
                ],
            },
            {
                "title": "Геометричні фігури",
                "section": "Геометрія",
                "order": 5,
                "estimated_time": 50,
                "points": 200,
                "content": [
                    {
                        "type": "theory",
                        "title": "Основи геометрії",
                        "order": 1,
                        "data": {
                            "text": """# Геометричні фігури

## Основні плоскі фігури

### Трикутник
- Має 3 сторони та 3 кути
- Сума кутів = 180°
- **Площа** = (основа × висота) / 2

### Прямокутник
- Має 4 сторони, протилежні рівні
- Всі кути = 90°
- **Площа** = довжина × ширина
- **Периметр** = 2 × (довжина + ширина)

### Квадрат
- Всі 4 сторони рівні
- Всі кути = 90°
- **Площа** = сторона²
- **Периметр** = 4 × сторона

### Коло
- **Площа** = π × r² (де r - радіус)
- **Довжина кола** = 2 × π × r
- π ≈ 3.14

## Приклади обчислень

### Площа прямокутника
```
Довжина = 8 см, ширина = 5 см
Площа = 8 × 5 = 40 см²
```

### Площа трикутника
```
Основа = 10 см, висота = 6 см
Площа = (10 × 6) / 2 = 30 см²
```

### Площа кола
```
Радіус = 7 см
Площа = 3.14 × 7² = 3.14 × 49 ≈ 154 см²
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Площа прямокутника",
                        "order": 2,
                        "data": {
                            "question": "Знайдіть площу прямокутника зі сторонами 6 см і 9 см",
                            "solution": "54",
                            "hints": ["Площа = довжина × ширина", "6 × 9 = ?"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Периметр квадрата",
                        "order": 3,
                        "data": {
                            "question": "Знайдіть периметр квадрата зі стороною 7 см",
                            "solution": "28",
                            "hints": ["Периметр = 4 × сторона", "4 × 7 = ?"],
                            "answer_type": "text",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Геометрія",
                        "order": 5,
                        "data": {
                            "questions": [
                                {
                                    "question": "Скільки сторін має трикутник?",
                                    "type": "multiple_choice",
                                    "options": ["2", "3", "4", "5"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Яка площа квадрата зі стороною 5 см?",
                                    "type": "multiple_choice",
                                    "options": ["10 см²", "20 см²", "25 см²", "30 см²"],
                                    "correct_answer": 2,
                                },
                                {
                                    "question": "Сума кутів трикутника = 180°",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "Всі сторони прямокутника рівні",
                                    "type": "true_false",
                                    "correct_answer": False,
                                },
                                {
                                    "question": "Периметр квадрата зі стороною 10 см",
                                    "type": "short_answer",
                                    "correct_answer": "40",
                                },
                                {
                                    "question": "Площа прямокутника 4×6 = _____ см²",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "24",
                                },
                                {
                                    "question": "Співставте фігури з кількістю сторін",
                                    "type": "drag_drop",
                                    "descriptions": [
                                        "Трикутник",
                                        "Квадрат",
                                        "П'ятикутник",
                                    ],
                                    "words": ["3", "4", "5"],
                                    "answers": ["3", "4", "5"],
                                },
                            ]
                        },
                    },
                    {
                        "type": "interactive",
                        "title": "Геометричні фігури на координатній площині",
                        "order": 6,
                        "data": {
                            "interactive_type": "visualization",
                            "configuration": {
                                "visualization_type": "geometry",
                                "shapes": [
                                    {
                                        "type": "rectangle",
                                        "points": [[1, 1], [5, 1], [5, 4], [1, 4]],
                                        "color": "#3498db",
                                        "label": "Прямокутник 4×3",
                                    },
                                    {
                                        "type": "triangle",
                                        "points": [[7, 1], [10, 1], [8.5, 4]],
                                        "color": "#e74c3c",
                                        "label": "Трикутник",
                                    },
                                    {
                                        "type": "circle",
                                        "center": [3, 7],
                                        "radius": 2,
                                        "color": "#2ecc71",
                                        "label": "Коло r=2",
                                    },
                                ],
                                "ui_config": {
                                    "show_grid": True,
                                    "show_axes": True,
                                    "show_measurements": True,
                                    "domain": [0, 12],
                                    "range": [0, 10],
                                },
                                "tasks": [
                                    {
                                        "id": "g1",
                                        "description": "Обчисліть площу прямокутника",
                                        "expected_answer": "12",
                                        "hint": "Площа = довжина × ширина",
                                    },
                                    {
                                        "id": "g2",
                                        "description": "Обчисліть периметр прямокутника",
                                        "expected_answer": "14",
                                        "hint": "Периметр = 2 × (довжина + ширина)",
                                    },
                                    {
                                        "id": "g3",
                                        "description": "Обчисліть площу кола (π ≈ 3.14)",
                                        "expected_answer": "12.56",
                                        "hint": "Площа = π × r²",
                                    },
                                ],
                            },
                            "instructions": "Вивчайте геометричні фігури на координатній площині. Обчислюйте їх площі та периметри.",
                        },
                    },
                ],
            },
        ]

        if admin_user_id:
            progress_id = uuid.uuid4()
            progress = Progress(
                id=progress_id,
                user_id=uuid.UUID(admin_user_id),
                course_id=uuid.UUID(course_id_str),
                current_lesson_id=None,
                progress_percentage=0.0,
                total_points_earned=0,
                time_spent=0,
                progress_data={},
            )
            session.add(progress)

        for lesson_data in lessons_data:
            lesson_id = uuid.uuid4()
            lesson = Lesson(
                id=lesson_id,
                course_id=uuid.UUID(course_id_str),
                title=lesson_data["title"],
                section=lesson_data.get("section"),
                lesson_order=lesson_data["order"],
                estimated_time=lesson_data["estimated_time"],
                points_reward=lesson_data["points"],
                created_at=datetime.now(),
            )
            session.add(lesson)
            session.flush()

            for content_data in lesson_data["content"]:
                content_id = uuid.uuid4()

                if content_data["type"] == "theory":
                    content = TheoryContent(
                        id=content_id,
                        lesson_id=lesson_id,
                        title=content_data["title"],
                        order=content_data["order"],
                        content_type="theory",
                        text_content=content_data["data"]["text"],
                    )
                elif content_data["type"] == "exercise":
                    content = ExerciseContent(
                        id=content_id,
                        lesson_id=lesson_id,
                        title=content_data["title"],
                        order=content_data["order"],
                        content_type="exercise",
                        problems=content_data["data"],
                    )
                elif content_data["type"] == "assessment":
                    content = AssessmentContent(
                        id=content_id,
                        lesson_id=lesson_id,
                        title=content_data["title"],
                        order=content_data["order"],
                        content_type="assessment",
                        questions=content_data["data"]["questions"],
                    )
                elif content_data["type"] == "interactive":
                    content = InteractiveContent(
                        id=content_id,
                        lesson_id=lesson_id,
                        title=content_data["title"],
                        order=content_data["order"],
                        content_type="interactive",
                        interactive_type=content_data["data"]["interactive_type"],
                        configuration=content_data["data"]["configuration"],
                        instructions=content_data["data"].get("instructions", ""),
                    )
                else:
                    continue

                session.add(content)
                print(f"  - Added {content_data['type']}: {content_data['title']}")

        session.commit()
        print(
            f"\n✓ Successfully seeded Basic Math course with {len(lessons_data)} lessons!"
        )
        print(f"✓ Total content items: {sum(len(l['content']) for l in lessons_data)}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_math_course()
    print("\nSeeding completed!")
