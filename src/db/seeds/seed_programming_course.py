"""Seed script to populate Programming Basics course with comprehensive content."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from src.db import get_db
from src.db.models import (Achievement, AssessmentContent, CompletedLesson,
                           Content, Course, ExerciseContent, Lesson, Progress,
                           TheoryContent, User, UserAchievement, UserContentProgress)


def clean_uuid(uuid_str):
    """Ensure UUID string has proper format with hyphens."""
    uuid_str = str(uuid_str).replace("-", "")
    # Format: 8-4-4-4-12
    return f"{uuid_str[0:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:32]}"


def seed_programming_course():
    """Seed comprehensive programming course."""
    session = next(get_db())
    try:
        course = (
            session.query(Course).filter(Course.name == "Основи програмування").first()
        )
        if not course:
            print("Course 'Основи програмування' not found!")
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
                "title": "Вступ до програмування",
                "section": "Основи",
                "order": 1,
                "estimated_time": 45,
                "points": 150,
                "content": [
                    {
                        "type": "theory",
                        "title": "Що таке програмування?",
                        "order": 1,
                        "data": {
                            "text": '''# Що таке програмування?

Програмування - це процес створення комп'ютерних програм за допомогою мов програмування. 

## Основні поняття:

1. **Алгоритм** - покрокова інструкція для розв'язання задачі
2. **Код** - текст програми, написаний мовою програмування
3. **Компілятор/Інтерпретатор** - програма, що перетворює код у виконуваний файл
4. **Синтаксис** - правила написання коду
5. **Семантика** - значення коду

## Чому Python?

Python - одна з найпопулярніших мов програмування завдяки:
- Простому синтаксису
- Великій кількості бібліотек
- Широкому застосуванню (веб, наука, AI, автоматизація)
- Активній спільноті розробників

## Перша програма

```python
print("Hello, World!")
```

Ця програма виводить текст на екран.

## Коментарі в Python

```python
# Це однорядковий коментар
print("Hello")  # Коментар в кінці рядка

"""
Це багаторядковий
коментар
"""
```

## Відступи

Python використовує відступи для визначення блоків коду:

```python
if True:
    print("Цей код всередині блоку")
print("Цей код поза блоком")
```'''
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Виведення тексту",
                        "order": 2,
                        "data": {
                            "question": "Напишіть програму, яка виводить ваше ім'я",
                            "initial_code": "# Напишіть код тут\n",
                            "solution": 'print("Ваше ім\'я")',
                            "test_cases": [
                                {"input": "", "expected_output": "Ваше ім'я"}
                            ],
                            "hints": [
                                "Використайте функцію print()",
                                "Текст має бути в лапках",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Привітання",
                        "order": 3,
                        "data": {
                            "question": 'Напишіть програму, яка виводить "Привіт, світ!" українською',
                            "initial_code": "# Виведіть привітання\n",
                            "solution": 'print("Привіт, світ!")',
                            "test_cases": [
                                {"input": "", "expected_output": "Привіт, світ!"}
                            ],
                            "hints": ["Використайте print()", "Не забудьте лапки"],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Кілька рядків",
                        "order": 4,
                        "data": {
                            "question": "Виведіть три рядки: своє ім'я, вік та місто (кожне на новому рядку)",
                            "initial_code": "# Виведіть три рядки\n",
                            "solution": 'print("Іван")\nprint(25)\nprint("Київ")',
                            "test_cases": [],
                            "hints": [
                                "Використайте print() тричі",
                                "Кожен print() виводить новий рядок",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Коментарі",
                        "order": 5,
                        "data": {
                            "question": 'Додайте коментар перед кодом, що пояснює що він робить, потім виведіть "Python is fun!"',
                            "initial_code": "# Ваш коментар тут\n",
                            "solution": '# Виводимо повідомлення про Python\nprint("Python is fun!")',
                            "test_cases": [
                                {"input": "", "expected_output": "Python is fun!"}
                            ],
                            "hints": [
                                "Коментар починається з #",
                                "Коментар не впливає на виконання",
                            ],
                            "answer_type": "code",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Виправте помилку",
                        "order": 6,
                        "data": {
                            "question": "Виправте синтаксичну помилку в коді",
                            "initial_code": 'print("Hello World)',
                            "solution": 'print("Hello World")',
                            "test_cases": [
                                {"input": "", "expected_output": "Hello World"}
                            ],
                            "hints": [
                                "Перевірте лапки",
                                "Кожна відкрита лапка має бути закрита",
                            ],
                            "answer_type": "fix_error",
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Виправте помилку 2",
                        "order": 7,
                        "data": {
                            "question": "Знайдіть та виправте помилку у виклику функції",
                            "initial_code": 'Print("Привіт")',
                            "solution": 'print("Привіт")',
                            "test_cases": [{"input": "", "expected_output": "Привіт"}],
                            "hints": [
                                "Python чутливий до регістру",
                                "Функції пишуться з малої літери",
                            ],
                            "answer_type": "fix_error",
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Перевірка знань",
                        "order": 8,
                        "data": {
                            "questions": [
                                {
                                    "question": "Що таке алгоритм?",
                                    "type": "multiple_choice",
                                    "options": [
                                        "Покрокова інструкція для розв'язання задачі",
                                        "Мова програмування",
                                        "Комп'ютерна програма",
                                        "Текстовий редактор",
                                    ],
                                    "correct_answer": 0,
                                },
                                {
                                    "question": "Яка функція виводить текст в Python?",
                                    "type": "multiple_choice",
                                    "options": [
                                        "write()",
                                        "print()",
                                        "output()",
                                        "display()",
                                    ],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Python є інтерпретованою мовою програмування",
                                    "type": "true_false",
                                    "correct_answer": True,
                                },
                                {
                                    "question": "В Python відступи не мають значення",
                                    "type": "true_false",
                                    "correct_answer": False,
                                },
                                {
                                    "question": 'Яке значення поверне len("Python")?',
                                    "type": "short_answer",
                                    "correct_answer": "6",
                                },
                                {
                                    "question": "Як називається функція для введення даних з клавіатури?",
                                    "type": "short_answer",
                                    "correct_answer": "input",
                                },
                                {
                                    "question": "Для виведення тексту використовується функція _____()",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "print",
                                },
                                {
                                    "question": "Коментар в Python починається з символу _____",
                                    "type": "fill_blank",
                                    "question_part2": "",
                                    "correct_answer": "#",
                                },
                                {
                                    "question": "Співставте поняття з їх визначеннями",
                                    "type": "drag_drop",
                                    "descriptions": [
                                        "Покрокова інструкція",
                                        "Текст програми",
                                        "Перетворює код",
                                    ],
                                    "words": ["Алгоритм", "Код", "Інтерпретатор"],
                                    "answers": ["Алгоритм", "Код", "Інтерпретатор"],
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Змінні та типи даних",
                "section": "Основи",
                "order": 2,
                "estimated_time": 45,
                "points": 150,
                "content": [
                    {
                        "type": "theory",
                        "title": "Змінні в Python",
                        "order": 1,
                        "data": {
                            "text": """# Змінні та типи даних

## Що таке змінна?

Змінна - це іменоване місце в пам'яті комп'ютера для зберігання даних.

```python
name = "Іван"
age = 25
height = 1.75
is_student = True
```

## Основні типи даних:

1. **int** - цілі числа (1, 42, -10)
2. **float** - дробові числа (3.14, -0.5)
3. **str** - текст ("Hello", 'Python')
4. **bool** - логічні значення (True, False)

## Правила іменування змінних:

- Починається з літери або _
- Може містити літери, цифри, _
- Регістр має значення (age ≠ Age)
- Не використовуйте зарезервовані слова

## Приклади:

```python
# Правильно
user_name = "Олена"
user_age = 30
total_sum = 100.50

# Неправильно
2name = "Error"  # починається з цифри
user-name = "Error"  # містить дефіс
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Створення змінних",
                        "order": 2,
                        "data": {
                            "question": "Створіть три змінні: name (ваше ім'я), age (ваш вік), city (ваше місто) та виведіть їх",
                            "initial_code": "# Створіть змінні\nname = \nage = \ncity = \n\n# Виведіть їх\n",
                            "solution": 'name = "Іван"\nage = 25\ncity = "Київ"\nprint(name)\nprint(age)\nprint(city)',
                            "test_cases": [],
                            "hints": [
                                "Текст має бути в лапках",
                                "Числа без лапок",
                                "Використайте print() для виведення",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Арифметичні операції",
                        "order": 3,
                        "data": {
                            "question": "Обчисліть суму двох чисел: 15 та 27",
                            "initial_code": "# Створіть змінні\na = 15\nb = 27\n\n# Обчисліть суму\nresult = \n\nprint(result)",
                            "solution": "a = 15\nb = 27\nresult = a + b\nprint(result)",
                            "test_cases": [{"input": "", "expected_output": "42"}],
                            "hints": [
                                "Використайте оператор +",
                                "Збережіть результат у змінну result",
                            ],
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Змінні",
                        "order": 4,
                        "data": {
                            "questions": [
                                {
                                    "question": "Який тип даних у змінної x = 3.14?",
                                    "type": "multiple_choice",
                                    "options": ["int", "float", "str", "bool"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Яке ім'я змінної правильне?",
                                    "type": "multiple_choice",
                                    "options": [
                                        "2user",
                                        "user-name",
                                        "user_name",
                                        "user name",
                                    ],
                                    "correct_answer": 2,
                                },
                                {
                                    "question": "Що виведе print(5 + 3)?",
                                    "type": "multiple_choice",
                                    "options": ["53", "8", "5+3", "Error"],
                                    "correct_answer": 1,
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Умовні конструкції",
                "section": "Керування потоком",
                "order": 3,
                "estimated_time": 50,
                "points": 200,
                "content": [
                    {
                        "type": "theory",
                        "title": "Оператор if",
                        "order": 1,
                        "data": {
                            "text": """# Умовні конструкції

## Оператор if

Дозволяє виконувати код залежно від умови.

```python
age = 18

if age >= 18:
    print("Ви повнолітній")
```

## if-else

```python
temperature = 25

if temperature > 30:
    print("Спекотно")
else:
    print("Нормальна температура")
```

## if-elif-else

```python
score = 85

if score >= 90:
    print("Відмінно")
elif score >= 75:
    print("Добре")
elif score >= 60:
    print("Задовільно")
else:
    print("Незадовільно")
```

## Оператори порівняння:

- `==` - дорівнює
- `!=` - не дорівнює
- `>` - більше
- `<` - менше
- `>=` - більше або дорівнює
- `<=` - менше або дорівнює

## Логічні оператори:

- `and` - логічне І
- `or` - логічне АБО
- `not` - логічне НЕ

```python
age = 20
has_license = True

if age >= 18 and has_license:
    print("Можете керувати автомобілем")
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Перевірка віку",
                        "order": 2,
                        "data": {
                            "question": "Напишіть програму, яка перевіряє чи користувач повнолітній (>= 18)",
                            "initial_code": "age = 20\n\n# Напишіть умову\n",
                            "solution": 'age = 20\n\nif age >= 18:\n    print("Повнолітній")\nelse:\n    print("Неповнолітній")',
                            "test_cases": [],
                            "hints": [
                                "Використайте if-else",
                                "Порівняйте age з 18",
                                "Не забудьте про відступи",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Оцінка за тестом",
                        "order": 3,
                        "data": {
                            "question": 'Створіть програму, яка виводить оцінку: 90+ = "A", 80-89 = "B", 70-79 = "C", <70 = "F"',
                            "initial_code": "score = 85\n\n# Напишіть умови\n",
                            "solution": 'score = 85\n\nif score >= 90:\n    print("A")\nelif score >= 80:\n    print("B")\nelif score >= 70:\n    print("C")\nelse:\n    print("F")',
                            "test_cases": [],
                            "hints": [
                                "Використайте if-elif-else",
                                "Перевіряйте від більшого до меншого",
                            ],
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Умови",
                        "order": 4,
                        "data": {
                            "questions": [
                                {
                                    "question": 'Що виведе код: x = 5\nif x > 3:\n    print("Yes")',
                                    "type": "multiple_choice",
                                    "options": ["Yes", "No", "Error", "Нічого"],
                                    "correct_answer": 0,
                                },
                                {
                                    "question": 'Який оператор означає "не дорівнює"?',
                                    "type": "multiple_choice",
                                    "options": ["<>", "!=", "==", "=/="],
                                    "correct_answer": 1,
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Цикли",
                "section": "Керування потоком",
                "order": 4,
                "estimated_time": 60,
                "points": 250,
                "content": [
                    {
                        "type": "theory",
                        "title": "Цикл for та while",
                        "order": 1,
                        "data": {
                            "text": """# Цикли в Python

## Цикл for

Використовується для ітерації по послідовності.

```python
# Цикл від 0 до 4
for i in range(5):
    print(i)

# Цикл по списку
fruits = ["яблуко", "банан", "апельсин"]
for fruit in fruits:
    print(fruit)

# Цикл з кроком
for i in range(0, 10, 2):  # 0, 2, 4, 6, 8
    print(i)
```

## Цикл while

Виконується поки умова істинна.

```python
count = 0
while count < 5:
    print(count)
    count += 1

# Нескінченний цикл з виходом
while True:
    answer = input("Продовжити? (y/n): ")
    if answer == 'n':
        break
```

## Керування циклами:

- `break` - вихід з циклу
- `continue` - перехід до наступної ітерації

```python
# Пропуск парних чисел
for i in range(10):
    if i % 2 == 0:
        continue
    print(i)  # Виведе тільки непарні

# Вихід при знаходженні
for i in range(100):
    if i == 50:
        break
    print(i)  # Виведе 0-49
```"""
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Таблиця множення",
                        "order": 2,
                        "data": {
                            "question": "Виведіть таблицю множення для числа 5 (від 1 до 10)",
                            "initial_code": "number = 5\n\n# Напишіть цикл\n",
                            "solution": 'number = 5\n\nfor i in range(1, 11):\n    print(f"{number} x {i} = {number * i}")',
                            "test_cases": [],
                            "hints": [
                                "Використайте for i in range(1, 11)",
                                "Виведіть number * i",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Сума чисел",
                        "order": 3,
                        "data": {
                            "question": "Обчисліть суму всіх чисел від 1 до 100",
                            "initial_code": "total = 0\n\n# Напишіть цикл\n\nprint(total)",
                            "solution": "total = 0\n\nfor i in range(1, 101):\n    total += i\n\nprint(total)",
                            "test_cases": [{"input": "", "expected_output": "5050"}],
                            "hints": [
                                "Використайте змінну total",
                                "Додавайте кожне число до total",
                            ],
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Цикли",
                        "order": 4,
                        "data": {
                            "questions": [
                                {
                                    "question": "Скільки разів виконається: for i in range(5)?",
                                    "type": "multiple_choice",
                                    "options": ["4", "5", "6", "Нескінченно"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Що робить оператор break?",
                                    "type": "multiple_choice",
                                    "options": [
                                        "Пропускає ітерацію",
                                        "Виходить з циклу",
                                        "Зупиняє програму",
                                        "Нічого",
                                    ],
                                    "correct_answer": 1,
                                },
                            ]
                        },
                    },
                ],
            },
            {
                "title": "Функції",
                "section": "Функції",
                "order": 5,
                "estimated_time": 55,
                "points": 200,
                "content": [
                    {
                        "type": "theory",
                        "title": "Створення функцій",
                        "order": 1,
                        "data": {
                            "text": '''# Функції в Python

## Що таке функція?

Функція - це блок коду, який можна викликати багато разів.

```python
def greet():
    print("Привіт!")

greet()  # Виклик функції
```

## Функції з параметрами

```python
def greet(name):
    print(f"Привіт, {name}!")

greet("Іван")  # Привіт, Іван!
greet("Марія")  # Привіт, Марія!
```

## Повернення значення

```python
def add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8
```

## Параметри за замовчуванням

```python
def greet(name="друже"):
    print(f"Привіт, {name}!")

greet()  # Привіт, друже!
greet("Олена")  # Привіт, Олена!
```

## Документація функції

```python
def calculate_area(width, height):
    """
    Обчислює площу прямокутника.
    
    Args:
        width: ширина
        height: висота
    
    Returns:
        площа прямокутника
    """
    return width * height
```'''
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Функція привітання",
                        "order": 2,
                        "data": {
                            "question": "Створіть функцію say_hello(name), яка виводить привітання",
                            "initial_code": '# Створіть функцію\ndef say_hello(name):\n    # Ваш код\n\n# Викличте функцію\nsay_hello("Іван")',
                            "solution": 'def say_hello(name):\n    print(f"Привіт, {name}!")\n\nsay_hello("Іван")',
                            "test_cases": [],
                            "hints": [
                                "Використайте print()",
                                "Використайте f-string для форматування",
                            ],
                        },
                    },
                    {
                        "type": "exercise",
                        "title": "Функція множення",
                        "order": 3,
                        "data": {
                            "question": "Створіть функцію multiply(a, b), яка повертає добуток двох чисел",
                            "initial_code": "def multiply(a, b):\n    # Ваш код\n\nresult = multiply(6, 7)\nprint(result)",
                            "solution": "def multiply(a, b):\n    return a * b\n\nresult = multiply(6, 7)\nprint(result)",
                            "test_cases": [{"input": "", "expected_output": "42"}],
                            "hints": ["Використайте return", "Поверніть a * b"],
                        },
                    },
                    {
                        "type": "assessment",
                        "title": "Тест: Функції",
                        "order": 4,
                        "data": {
                            "questions": [
                                {
                                    "question": "Яке ключове слово використовується для створення функції?",
                                    "type": "multiple_choice",
                                    "options": ["function", "def", "func", "define"],
                                    "correct_answer": 1,
                                },
                                {
                                    "question": "Що робить оператор return?",
                                    "type": "multiple_choice",
                                    "options": [
                                        "Виводить значення",
                                        "Повертає значення з функції",
                                        "Зупиняє програму",
                                        "Створює змінну",
                                    ],
                                    "correct_answer": 1,
                                },
                            ]
                        },
                    },
                ],
            },
        ]

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
            )
            session.add(lesson)
            session.flush()

            print(f"Created lesson: {lesson.title}")

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
                        problems=content_data[
                            "data"
                        ],  # Store all exercise data as JSON
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

                session.add(content)
                print(f"  - Added {content_data['type']}: {content_data['title']}")

        if admin_user_id:
            progress_id = uuid.uuid4()
            progress = Progress(
                id=progress_id,
                user_id=uuid.UUID(admin_user_id),
                course_id=uuid.UUID(course_id_str),
                current_lesson_id=None,  # Will be set when user starts
                progress_percentage=0.0,
                total_points_earned=0,
                time_spent=0,
                progress_data={},  # Empty dict for now
            )
            session.add(progress)

        achievements_data = [
            {
                "name": "Перші кроки",
                "description": "Ви зробили перший крок у світ програмування! Продовжуйте навчатися, щоб відкрити нові можливості.",
                "category": "Learning",
                "icon": "icon/badges/badge1.svg",
                "points": 10,
                "criteria": {"lessons_started": 1},
            },
            {
                "name": "Швидкий учень",
                "description": "Чудова робота! Ви успішно завершили 3 уроки. Ваша наполегливість вражає!",
                "category": "Engagement",
                "icon": "icon/badges/badge2.svg",
                "points": 50,
                "criteria": {"lessons_completed": 3},
            },
            {
                "name": "Майстер Python",
                "description": 'Вітаємо! Ви повністю опанували курс "Основи програмування" і стали справжнім майстром Python!',
                "category": "Mastery",
                "icon": "icon/badges/badge3.svg",
                "points": 200,
                "criteria": {"course_completed": "Основи програмування"},
            },
            {
                "name": "Дослідник",
                "description": "Ви переглянули всі розділи уроку. Цікавість — ключ до успіху!",
                "category": "Learning",
                "icon": "icon/badges/badge1.svg",
                "points": 15,
                "criteria": {"sections_viewed": 5},
            },
            {
                "name": "Відмінник",
                "description": "Ви отримали 100% за тест! Ваші знання бездоганні.",
                "category": "Mastery",
                "icon": "icon/badges/badge3.svg",
                "points": 100,
                "criteria": {"perfect_score": True},
            },
            {
                "name": "Наполегливий",
                "description": "Ви навчаєтесь 7 днів поспіль! Регулярність — запорука успіху.",
                "category": "Engagement",
                "icon": "icon/badges/badge2.svg",
                "points": 75,
                "criteria": {"streak_days": 7},
            },
            {
                "name": "Перші 10 завдань",
                "description": "Ви виконали 10 завдань з програмування. Гарний темп — рухаємось далі!",
                "category": "Challenge",
                "icon": "icon/badges/badge2.svg",
                "points": 80,
                "criteria": {"code_exercises_completed": 10},
            },
            {
                "name": "Математичний геній",
                "description": "Ви розв'язали 20 математичних задач. Числа підкоряються вам!",
                "category": "Mastery",
                "icon": "icon/badges/badge3.svg",
                "points": 120,
                "criteria": {"math_problems_solved": 20},
            },
        ]

        for ach_data in achievements_data:
            existing = (
                session.query(Achievement)
                .filter(Achievement.title == ach_data["name"])
                .first()
            )
            if not existing:
                achievement = Achievement(
                    id=uuid.uuid4(),
                    title=ach_data["name"],
                    description=ach_data["description"],
                    category=ach_data["category"],
                    icon=ach_data["icon"],
                    criteria=ach_data["criteria"],
                    points=ach_data["points"],
                )
                session.add(achievement)
                print(f"Created achievement: {ach_data['name']}")

        session.commit()
        print(
            f"\n✓ Successfully seeded Programming Basics course with {len(lessons_data)} lessons!"
        )
        print(f"✓ Total content items: {sum(len(l['content']) for l in lessons_data)}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_programming_course()
    print("\nSeeding completed!")
