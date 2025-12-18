import sys, os
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QFormLayout, QHBoxLayout,
    QGridLayout, QSizePolicy, QFrame, QScrollArea, QPushButton, QVBoxLayout, QMenu, QAction)
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QSize, pyqtSignal
import logging

logger = logging.getLogger(__name__)

from PyQt5 import QtWidgets, QtCore, QtGui

from src.services.user_service import UserService
from src.services.session_manager import SessionManager
from src.services.lesson_service import LessonService
from src.services.course_service import CourseService 
from src.services.progress_service import ProgressService 
from src.models.course import Course

from src.models.lesson import Lesson
from src.models.user import User
from src.models.progress import Progress

from passlib.hash import bcrypt 
import bcrypt
import uuid
from datetime import datetime
import json 
from src.db import get_db
from sqlalchemy.exc import SQLAlchemyError
from src.core.error_handling.exceptions import (
    AuthenticationError,
    DatabaseError,
    MathtermindError,
    SecurityError,
    ServiceError,
    UIError,
    ValidationError,
)
class AddEditCourseDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, course: Course = None):
        super().__init__(parent)
        self.course = course
        self.setWindowTitle("Додати курс" if course is None else "Редагувати курс")
        self.setup_ui()

        if course:
            self.fill_from_course(course)

    def setup_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.topic_edit = QtWidgets.QComboBox()
        self.topic_edit.addItems(["Інформатика", "Математика"])
        self.topic_edit.setProperty("type", "input_field")

        self.name_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QPlainTextEdit()

        self.duration_edit = QtWidgets.QSpinBox()
        self.duration_edit.setMaximum(20000)
        self.duration_edit.setSuffix(" хв")

        self.topic_edit.setProperty("type", "update")
        self.name_edit.setProperty("type", "update")
        self.description_edit.setProperty("type", "update")

        layout.addRow("Тема курсу:", self.topic_edit)
        layout.addRow("Назва курсу:", self.name_edit)
        layout.addRow("Опис:", self.description_edit)
        layout.addRow("Тривалість (хв):", self.duration_edit)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(btn_box)

        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    def fill_from_course(self, c: Course):
        self.topic_edit.setCurrentText(c.topic)
        self.name_edit.setText(c.name)
        self.description_edit.setPlainText(c.description)
        
        metadata = getattr(c, "metadata", {})
        if not isinstance(metadata, dict):
            if hasattr(metadata, "__dict__"):
                metadata = vars(metadata)
            else:
                metadata = {}

        estimated_time = metadata.get("estimated_time", 0)
        self.duration_edit.setValue(int(estimated_time))


    
    def get_course_data_dict(self):
        return {
            "topic": self.topic_edit.currentText() or "MATHEMATICS",
            "name": self.name_edit.text().strip() or "Новий курс",
            "description": self.description_edit.toPlainText().strip() or "Опис відсутній",
            "duration": self.duration_edit.value() or 0,
        }

    def get_course_object(self):
        from src.db.models import Course
        return Course(
            topic=self.topic_edit.currentText() or "MATHEMATICS",
            name=self.name_edit.text().strip() or "Новий курс",
            description=self.description_edit.toPlainText().strip() or "Опис відсутній",
            duration=self.duration_edit.value() or 0,
            metadata={"duration": self.duration_edit.value()},
        )


    def get_updated_fields(self):
        return {
            "topic": self.topic_edit.currentText(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "duration": self.duration_edit.value(),
            "metadata": {"duration": self.duration_edit.value()}
        }
    

class AddEditLessonDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, lesson: Lesson = None, available_courses=None):
        super().__init__(parent)
        self.lesson = lesson
        self.available_courses = available_courses or []
        self.setWindowTitle("Додати урок" if lesson is None else "Редагувати урок")
        self.setup_ui()
        if lesson:
            self.fill_from_lesson(lesson)

    def setup_ui(self):
        self.resize(640, 520)
        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        tab_main = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab_main)
        self.title_edit = QtWidgets.QLineEdit()
        
        self.section_edit = QtWidgets.QLineEdit()
        self.section_edit.setPlaceholderText("Наприклад: Арифметика, Дроби, Геометрія...")
        
        self.course_combo = QtWidgets.QComboBox()
        self.order_spin=QtWidgets.QSpinBox()
        self.order_spin.setRange(0, 30)
        self.course_combo.addItems([c.title for c in self.available_courses] or ["(Немає курсів)"])
        self.duration_spin = QtWidgets.QSpinBox()
        self.duration_spin.setRange(0, 300)

        self.points_spin=QtWidgets.QSpinBox()
        self.points_spin.setRange(0, 30)

        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["Чернетка", "Опубліковано", "Приховано"])
        self.title_edit.setProperty("type", "update")
        self.section_edit.setProperty("type", "update")
        #self.description_edit = QtWidgets.QPlainTextEdit()
        form.addRow("Назва уроку:", self.title_edit)
        form.addRow("Розділ:", self.section_edit)
        form.addRow("Курс:", self.course_combo)
        form.addRow("Порядок:", self.order_spin)
        form.addRow("Тривалість (хв):", self.duration_spin)
        form.addRow("Можливі бали:", self.points_spin)
        form.addRow("Статус:", self.status_combo)
        #form.addRow("Опис:", self.description_edit)
        self.tabs.addTab(tab_main, "Основне")

        tab_theory = QtWidgets.QWidget()
        self.theory_edit = QtWidgets.QPlainTextEdit()
        QtWidgets.QVBoxLayout(tab_theory).addWidget(self.theory_edit)
        self.tabs.addTab(tab_theory, "Теорія")

        tab_tasks = QtWidgets.QWidget()
        self.tasks_edit = QtWidgets.QPlainTextEdit()
        QtWidgets.QVBoxLayout(tab_tasks).addWidget(self.tasks_edit)
        self.tabs.addTab(tab_tasks, "Завдання")

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)


        self.theory_edit.setProperty("type","task_edit")
        self.tasks_edit.setProperty("type","task_edit")
        #self.description_edit.setProperty("type","update")

    def fill_from_lesson(self, lesson: Lesson):
        self.title_edit.setText(lesson.title or "")
        self.section_edit.setText(getattr(lesson, 'section', None) or "")
        if self.available_courses:
            for i, c in enumerate(self.available_courses):
                if str(c.id) == str(lesson.course_id):
                    self.course_combo.setCurrentIndex(i)
                    break

        self.order_spin.setValue(lesson.lesson_order or 0)
        self.duration_spin.setValue(getattr(lesson, "estimated_time", 0) or 0)
        self.points_spin.setValue(getattr(lesson, "points_reward", 0) or 0)
        
        status = getattr(lesson, "status", "Чернетка")
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        try:
            content = self.parent().lesson_service.get_lesson_content(lesson.id)
        except Exception:
            content = {}

        self.theory_edit.setPlainText(content.get("theory", ""))
        tasks = content.get("tasks", [])
        self.tasks_edit.setPlainText(json.dumps(tasks, ensure_ascii=False, indent=2) if tasks else "")





    def get_lesson(self) -> Lesson:
        selected_course_index = self.course_combo.currentIndex()
        selected_course = self.available_courses[selected_course_index] if self.available_courses else None
        course_id = selected_course.id if selected_course else None

        return Lesson(
            id=str(uuid.uuid4()),  
            title=self.title_edit.text().strip() or "Без назви",
            course_id=course_id,
            lesson_order=self.order_spin.value(),  
            estimated_time=self.duration_spin.value(),
            points_reward=self.points_spin.value() or 0,
            content={
                "description": self.description_edit.toPlainText().strip(),
                "theory": self.theory_edit.toPlainText().strip(),
                "tasks": self.tasks_edit.toPlainText().strip()
            },
            
            
            #prerequisites={},
            #learning_objectives=[],

            created_at=datetime.now()
        )



    
    def get_lesson_data_dict(self):
        selected_course = self.available_courses[self.course_combo.currentIndex()]
        section = self.section_edit.text().strip() or None

        return {
            "course_id": selected_course.id,
            "title": self.title_edit.text().strip(),
            "section": section,
            "lesson_order": self.order_spin.value(),
            "estimated_time": self.duration_spin.value(),
            "points_reward": self.points_spin.value(),
        }




    def get_theory_text(self) -> str:
        return self.theory_edit.toPlainText().strip()

    def get_tasks_json(self):
        raw = self.tasks_edit.toPlainText().strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.warning(self, "Помилка JSON", "Невірний формат JSON у вкладці 'Завдання'.")
            return None
        
    def get_tasks_list(self) -> list:
        
        raw = self.tasks_edit.toPlainText().strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Помилка даних",
                            f"Завдання №{i+1} має неправильний формат. Має бути словник."
                        )
                        return []
                return data
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Помилка даних",
                    "Завдання повинні бути масивом JSON-об'єктів."
                )
                return []
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.warning(
                self, "Помилка JSON", "Невірний формат JSON у вкладці 'Завдання'."
            )
            return []


class AddEditStudentDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, user: User = None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Додати користувача" if user is None else "Редагувати користувача")
        self.setup_ui()

        if user:
            self.fill(user)

    def setup_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.username_edit = QtWidgets.QLineEdit()
        self.email_edit = QtWidgets.QLineEdit()
        self.first_name_edit = QtWidgets.QLineEdit()
        self.last_name_edit = QtWidgets.QLineEdit()
        self.age_group_combo = QtWidgets.QComboBox()
        self.phone_edit = QtWidgets.QLineEdit()
        self.bdate_edit = QtWidgets.QLineEdit()

        self.age_group_combo.addItems(["THIRTEEN_TO_FOURTEEN", "FIFTEEN_TO_SEVENTEEN", "TEN_TO_TWELVE"])

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        if self.user:  
            self.password_edit.setPlaceholderText("Залиште порожнім, щоб не змінювати")
        for e in [self.username_edit, self.email_edit, self.first_name_edit, self.last_name_edit, self.password_edit, self.phone_edit,self.bdate_edit]:
            e.setProperty("type","update")
        layout.addRow("Логін:", self.username_edit)
        layout.addRow("Пошта:", self.email_edit)
        layout.addRow("Ім'я:", self.first_name_edit)
        layout.addRow("Прізвище:", self.last_name_edit)
        layout.addRow("Вікова група:", self.age_group_combo)
        layout.addRow("Пароль:", self.password_edit)
        layout.addRow("Телефон:", self.phone_edit)
        layout.addRow("Дата народження:", self.bdate_edit)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        layout.addWidget(btn_box)

    def fill(self, u: User):
        pass
    

    

    def accept(self):
        password = self.password_edit.text()  
        data = {
        "username": self.username_edit.text(),
        "email": self.email_edit.text(),
        #"password_hash": self.password_edit.text(),
        
        "password_hash": password,
        
        "first_name": self.first_name_edit.text(),
        "last_name": self.last_name_edit.text(),
        "age_group": self.age_group_combo.currentText(),
        "phone": self.phone_edit.text(),
        "bdate": self.bdate_edit.text(),
        }

        try:
            db = next(get_db())  
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Помилка", f"Не вдалося підключитися до БД: {e}")
            return
        try:
            user = self.parent().user_service.user_repo.create_user(
                db=db,
                email=f"{data['email']}@example.com",
                username=data["username"],
                password_hash=data["password_hash"],
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                #is_active=True,
                #is_admin=False,
                age_group=data["age_group"],
                profile_data={"phone_number": data.get("phone"),"date_of_birth": data.get("bdate")}
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Помилка", f"[DB_ERROR] Database error during create: {e}")
            return
        finally:
            db.close()

        super().accept()
    
    
    
    def get_data(self):
        return {
            "username": self.username_edit.text(),
            "email": f"{self.username_edit.text()}@example.com",
            "password_hash": self.password_edit.text(),  
            "first_name": self.first_name_edit.text(),
            "last_name": self.last_name_edit.text(),
            "age_group": self.age_group_combo.currentText(),
            "profile_data": {
                "phone_number": self.phone_edit.text(),
                "date_of_birth": self.bdate_edit.text(),
            }
        }


    def populate_fields(self):
        if self.user:
            self.username_edit.setText(self.user.username or "")
            self.email_edit.setText(self.user.email or "")
            self.first_name_edit.setText(self.user.first_name or "")
            self.last_name_edit.setText(self.user.last_name or "")
            profile = getattr(self.user, "metadata", {})
            self.phone_edit.setText(profile.get("phone_number", ""))
            self.bdate_edit.setText(profile.get("date_of_birth"),"" )


class CoursesPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.pg_courses = QtWidgets.QWidget()
        self.pg_courses.setObjectName("pg_courses")
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.main_layout = QtWidgets.QGridLayout(self.pg_courses)
        self.main_layout.setHorizontalSpacing(10)
        self.main_layout.setObjectName("main_layout")

        self.lb_courses = QtWidgets.QLabel(self.pg_courses)
        self.lb_courses.setText("Курси")
        self.lb_courses.setProperty("type", "title")
        self.main_layout.addWidget(self.lb_courses, 0, 0, 1, 2)  

        self.scroll_area = QtWidgets.QScrollArea(self.pg_courses)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scroll_area")

        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)

        self.widget_table = QtWidgets.QWidget(self.scroll_content)
        self.widget_table.setProperty("type", "w_pg")
        self.widget_table.setObjectName("widget_table")
        self.widget_table_layout = QtWidgets.QVBoxLayout(self.widget_table)

        self.lb_table_title = QtWidgets.QLabel("Список курсів")
        self.lb_table_title.setProperty("type", "page_section")
        self.widget_table_layout.addWidget(self.lb_table_title)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Предмет", "Назва", "Опис", "Тривалість (години)", "Оновлено", "ID", "Створено"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.widget_table_layout.addWidget(self.table)

        btn_container = QtWidgets.QWidget()
        btn_container.setProperty("type","transparent_widget")
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 5, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_add = QtWidgets.QPushButton("Додати")
        self.btn_edit = QtWidgets.QPushButton("Редагувати")
        
        self.btn_delete = QtWidgets.QPushButton("Видалити")

        for b in (self.btn_add, self.btn_edit, self.btn_delete):
            b.setProperty("type", "admin_ok")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        self.widget_table_layout.addWidget(btn_container)

        self.scroll_layout.addWidget(self.widget_table)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area, 1, 0, 1, 1)

        self.filters_widget = QtWidgets.QWidget()
        self.filters_widget.setProperty("type", "w_pg")
        self.filters_widget.setFixedWidth(300)
        self.filters_layout = QtWidgets.QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(10, 10, 10, 10)
        self.filters_layout.setSpacing(10)

        lb_filters = QtWidgets.QLabel("Фільтри")
        lb_filters.setProperty("type", "page_section")
        self.filters_layout.addWidget(lb_filters)

        self.filter_subject = QtWidgets.QComboBox()
        self.filter_subject.addItems(["Всі предмети", "Інформатика", "Математика"])
        self.filter_subject.setProperty("type", "input_field")

        self.filter_courses = QtWidgets.QComboBox()
        self.filter_courses.addItems(["Всі статуси", "Активний", "Неактивний"])
        self.filter_courses.setProperty("type", "input_field")

        self.filter_courses = QtWidgets.QComboBox()
        self.filter_courses.setProperty("type", "input_field")

        self.filter_courses.addItem("Всі курси")  
        self.course_service = CourseService()
        courses_list = self.course_service.get_all_courses() 

        for course in courses_list:
            self.filter_courses.addItem(course.name)
        
        self.filter_level = QtWidgets.QComboBox()
        self.filter_level.addItems(["Всі рівні", "Початковий", "Середній", "Просунутий"])
        self.filter_level.setProperty("type", "input_field")        

        self.btn_apply_filters = QtWidgets.QPushButton("Застосувати")
        self.btn_apply_filters.setProperty("type", "admin_ok")
        
        self.subject=QtWidgets.QLabel("Предмет:")
        self.subject.setProperty("type", "lb_description")
        self.filters_layout.addWidget(self.subject)
        self.filters_layout.addWidget(self.filter_subject)

        self.status=QtWidgets.QLabel("Курс:")
        self.status.setProperty("type", "lb_description")
        
        self.filters_layout.addWidget(self.status)
        self.filters_layout.addWidget(self.filter_courses)
        self.level=QtWidgets.QLabel("Рівень:")
        self.level.setProperty("type", "lb_description")
        self.filters_layout.addWidget(self.level)
        
        self.filters_layout.addWidget(self.filter_level)
        self.filters_layout.addSpacing(10)
        self.filters_layout.addWidget(self.btn_apply_filters)
        self.filters_layout.addStretch()

        self.main_layout.addWidget(self.filters_widget, 1, 1, 1, 1)

        self.setLayout(self.main_layout)
        
        self.course_service = CourseService()
        self.load_courses_from_db()
        
        self.update_table()

        self.btn_add.clicked.connect(self.add_course)
        self.btn_edit.clicked.connect(self.edit_course)
        self.btn_delete.clicked.connect(self.delete_course)
        self.btn_apply_filters.clicked.connect(self.apply_filters)


    def add_course(self):
        dialog = AddEditCourseDialog(self)
        if dialog.exec_():
            data = dialog.get_course_data_dict()
            created = self.course_service.create_course(**data)
            self.courses.append(created)
            self.update_table()

        

    def edit_course(self):
        row = self.table.currentRow()
        if row < 0:
            return

        course_to_edit = self.courses[row]
        dlg = AddEditCourseDialog(self, course_to_edit)
        if dlg.exec_():
            data = dlg.get_course_data_dict()  
            db = next(get_db())
            try:
                updated_course = self.course_service.update_course(
                    db=db,
                    course_id=str(course_to_edit.id),
                    topic=data.get("topic"),
                    name=data.get("name"),
                    description=data.get("description"),
                    duration=data.get("duration")
                )

                if updated_course:
                    self.courses[row] = updated_course
                    self.update_table()
            finally:
                db.close()

    
    def delete_course(self):
        row = self.table.currentRow()
        if row < 0:
            return

        if QtWidgets.QMessageBox.question(
            self,
            "Видалити курс",
            "Підтвердити видалення?"
        ) == QtWidgets.QMessageBox.Yes:

            course_id = self.courses[row].id  

            try:
                self.course_service.delete_course(course_id) 
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Помилка", str(e))
                return

            del self.courses[row]
            self.update_table()


    def update_table(self, filtered=None):
        data = filtered if filtered else self.courses
        self.table.setRowCount(len(data))

        for i, c in enumerate(data):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(c.topic))       
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(c.name))        
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(c.description)) 
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(c.formatted_duration))) 
            self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(c.formatted_updated_date))
            self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(str(c.id)))
            self.table.setItem(i, 6, QtWidgets.QTableWidgetItem(c.formatted_created_date))




    def apply_filters(self):
        subject = self.filter_subject.currentText()
        level = self.filter_level.currentText()
        name = self.filter_courses.currentText()

        filtered = []
        for c in self.courses:
            if (subject == "Всі предмети" or c.subject == subject) and \
               (level == "Всі рівні" or c.level == level) and \
               (name == "Всі курси" or c.name == name):
                filtered.append(c)
        self.update_table(filtered)

    
    def load_courses_from_db(self):
        courses_data = self.course_service.get_all_courses() 
        self.courses = courses_data  
        self.update_table()


class LessonsPage(QtWidgets.QWidget):
    def __init__(self, courses_page):
        super().__init__()
        self.courses_page = courses_page
        self.lessons = []
        self.pg_lessons = QtWidgets.QWidget()
        self.pg_lessons.setObjectName("pg_lessons")

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.main_layout = QtWidgets.QGridLayout(self.pg_lessons)
        self.main_layout.setHorizontalSpacing(10)
        self.main_layout.setObjectName("main_layout")

        self.lb_lessons = QtWidgets.QLabel(self.pg_lessons)
        self.lb_lessons.setText("Уроки")
        self.lb_lessons.setProperty("type", "title")
        self.main_layout.addWidget(self.lb_lessons, 0, 0, 1, 2)

        self.scroll_area = QtWidgets.QScrollArea(self.pg_lessons)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scroll_area")

        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)

        self.widget_table = QtWidgets.QWidget(self.scroll_content)
        self.widget_table.setProperty("type", "w_pg")
        self.widget_table.setObjectName("widget_table")
        self.widget_table_layout = QtWidgets.QVBoxLayout(self.widget_table)

        self.lb_table_title = QtWidgets.QLabel("Список уроків")
        self.lb_table_title.setProperty("type", "page_section")
        self.widget_table_layout.addWidget(self.lb_table_title)

        self.table = QtWidgets.QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Назва", "Розділ", "Курс", "Порядок", "Тривалість", "Бали", "Створено", "Оновлено"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.widget_table_layout.addWidget(self.table)

        btn_container = QtWidgets.QWidget()
        btn_container.setProperty("type","transparent_widget")
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 5, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_add = QtWidgets.QPushButton("Додати")
        self.btn_edit = QtWidgets.QPushButton("Редагувати")
        self.btn_delete = QtWidgets.QPushButton("Видалити")

        for b in (self.btn_add, self.btn_edit, self.btn_delete):
            b.setProperty("type", "admin_ok")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        self.widget_table_layout.addWidget(btn_container)

        self.scroll_layout.addWidget(self.widget_table)
        self.scroll_area.setWidget(self.scroll_content)

        self.main_layout.addWidget(self.scroll_area, 1, 0, 1, 1)

        self.filters_widget = QtWidgets.QWidget()
        self.filters_widget.setProperty("type", "w_pg")
        self.filters_widget.setFixedWidth(300)
        self.filters_layout = QtWidgets.QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(10, 10, 10, 10)
        self.filters_layout.setSpacing(10)

        lb_filters = QtWidgets.QLabel("Фільтри")
        lb_filters.setProperty("type", "page_section")
        self.filters_layout.addWidget(lb_filters)

        self.cb_course = QtWidgets.QComboBox()
        self.cb_course.setProperty("type", "input_field")
        self.cb_course.addItems(["Всі предмети", "Інформатика", "Математика"])


        self.filter_courses=QtWidgets.QComboBox()
        self.filter_courses.addItem("Всі курси")  
        self.course_service = CourseService()
        courses_list = self.course_service.get_all_courses() 

        for course in courses_list:
            self.filter_courses.addItem(course.name)
        
        self.filter_subject = QtWidgets.QComboBox()
        self.filter_subject.addItems(["Всі предмети", "Інформатика", "Математика"])
        self.filter_subject.setProperty("type", "input_field")



        #self.filter_status = QtWidgets.QComboBox()
        #self.filter_status.addItems(["Всі статуси", "Активний", "Неактивний"])
        #self.filter_status.setProperty("type", "input_field")


        self.btn_apply_filters = QtWidgets.QPushButton("Застосувати")
        self.btn_apply_filters.setProperty("type", "admin_ok")
        
        self.subject = QtWidgets.QLabel("Предмет:")
        self.subject.setProperty("type", "lb_description")
        self.filters_layout.addWidget(self.subject)
        self.filters_layout.addWidget(self.filter_subject)

        self.courses = QtWidgets.QLabel("Курс:")
        self.courses.setProperty("type", "lb_description")
        self.filters_layout.addWidget(self.courses)
        self.filters_layout.addWidget(self.filter_courses)


        #self.status = QtWidgets.QLabel("Статус:")
        #self.status.setProperty("type", "lb_description")
        #self.filters_layout.addWidget(self.status)
        #self.filters_layout.addWidget(self.filter_status)

        self.filters_layout.addSpacing(10)
        self.filters_layout.addWidget(self.btn_apply_filters)
        self.filters_layout.addStretch()

        self.main_layout.addWidget(self.filters_widget, 1, 1, 1, 1)

        self.setLayout(self.main_layout)

        self.lesson_service = LessonService()
        self.load_lessons_from_db()
        
        self.update_table()

        self.btn_add.clicked.connect(self.add_lesson)
        self.btn_edit.clicked.connect(self.edit_lesson)
        self.btn_delete.clicked.connect(self.delete_lesson)
        self.btn_apply_filters.clicked.connect(self.apply_filters)

    def load_lessons_from_db(self):
        lessons_data = self.lesson_service.get_all_lessons() 
        courses = self.courses_page.courses
        course_map = {c.id: c.name for c in courses} 
        
        self.lessons = []

        for l in lessons_data:
            l.course_name = course_map.get(l.course_id, "Невідомий курс")
            self.lessons.append(l)

        self.update_table()



    def add_lesson(self):
        dialog = AddEditLessonDialog(
            self,
            available_courses=self.courses_page.courses
        )

        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        try:
            lesson = self.lesson_service.create_lesson(
                **dialog.get_lesson_data_dict()
            )
            

            theory_text = dialog.get_theory_text()
            if theory_text:
                self.lesson_service.add_theory_content(
                    lesson_id=lesson.id,
                    text=theory_text
                )

            tasks = dialog.get_tasks_list()  
            for task in tasks:
                self.lesson_service.add_exercise_content(
                    lesson_id=lesson.id,
                    problems=task
                )

            self.lessons.append(lesson)
            self.update_table()

            QtWidgets.QMessageBox.information(
                self, "Успіх", "Урок створено"
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Помилка", str(e)
            )



    def edit_lesson(self):
        row = self.table.currentRow()
        if row < 0:
            return

        lesson = self.lessons[row]
        dlg = AddEditLessonDialog(self, lesson, available_courses=self.courses_page.courses)

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        updated_data = dlg.get_lesson_data_dict()
        updated_data.pop("course_id", None)
        try:
            updated_lesson = self.lesson_service.update_lesson(
                lesson_id=str(lesson.id),
                **updated_data
            )

            theory_text = dlg.get_theory_text()
            if theory_text:
                self.lesson_service.add_theory_content(
                    lesson_id=str(lesson.id),
                    text=theory_text
                )

            tasks = dlg.get_tasks_list()
            self.lesson_service.upsert_exercises(lesson.id, tasks)

            self.lessons[row] = updated_lesson
            self.update_table()
            QtWidgets.QMessageBox.information(self, "Успіх", "Урок оновлено")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Помилка", f"Не вдалося оновити урок:\n{str(e)}")


    def delete_lesson(self):
        row = self.table.currentRow()
        if row < 0:
            return

        if QtWidgets.QMessageBox.question(
            self, "Видалити урок", "Підтвердити видалення?") == QtWidgets.QMessageBox.Yes:
            lesson = self.lessons[row]
            try:
                self.lesson_service.delete_lesson(lesson.id)
                del self.lessons[row]
                self.update_table()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Помилка", f"Не вдалося видалити урок:\n{str(e)}")



    def update_table(self, lessons=None):
        if lessons is None:
            lessons = self.lessons

        self.table.setRowCount(0)
        course_map = {c.id: c.title for c in self.courses_page.courses}

        for l in lessons:
            row = self.table.rowCount()
            self.table.insertRow(row)
            course_name = course_map.get(str(l.course_id), "Невідомий курс")
            section = getattr(l, 'section', None) or "—"
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(l.id)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(l.title))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(section))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(course_name)))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(l.lesson_order)))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(l.estimated_time)))
            self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(str(l.points_reward)))
            self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(l.formatted_created_date))
            self.table.setItem(row, 8, QtWidgets.QTableWidgetItem(l.formatted_updated_date))

    
    def apply_filters(self):
        selected_subject = self.filter_subject.currentText()
        selected_course_name = self.filter_courses.currentText()

        filtered = []
        course_dict = {c.id: c for c in self.courses_page.courses}

        for lesson in self.lessons:
            course = course_dict.get(lesson.course_id)
            if not course:
                continue  

            if selected_subject != "Всі предмети" and course.subject != selected_subject:
                continue

            if selected_course_name != "Всі курси" and course.name != selected_course_name:
                continue

            filtered.append(lesson)

        self.update_table(filtered)


from PyQt5 import QtWidgets
from src.services import UserService
from src.models import User
import os

class StudentsPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.pg_users = QtWidgets.QWidget()
        self.pg_users.setObjectName("pg_users")

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.main_layout = QtWidgets.QGridLayout(self.pg_users)
        self.main_layout.setHorizontalSpacing(10)
        self.main_layout.setObjectName("main_layout")

        self.lb_users = QtWidgets.QLabel("Користувачі")
        self.lb_users.setProperty("type", "title")
        self.main_layout.addWidget(self.lb_users, 0, 0, 1, 2)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)

        self.widget_table = QtWidgets.QWidget()
        self.widget_table.setProperty("type", "w_pg")
        self.widget_table_layout = QtWidgets.QVBoxLayout(self.widget_table)

        


        self.lb_table_title = QtWidgets.QLabel("Список користувачів")
        self.lb_table_title.setProperty("type", "page_section")
        self.widget_table_layout.addWidget(self.lb_table_title)
        
        
        search_container = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Пошук за ім'ям користувача...")
        self.search_input.setProperty("type", "settings")

        self.btn_search = QtWidgets.QPushButton("Пошук")
        self.btn_search.setProperty("type", "admin_ok")
        self.btn_search.setFixedWidth(60)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)

        self.widget_table_layout.addWidget(search_container)



        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Логін", "Пароль", "Ім'я", "Прізвище",
            "Вік", "Створено", "Оновлено"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.widget_table_layout.addWidget(self.table)

        btn_container = QtWidgets.QWidget()
        btn_container.setProperty("type","transparent_widget")
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 5, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_add = QtWidgets.QPushButton("Додати")
        self.btn_edit = QtWidgets.QPushButton("Редагувати")
        self.btn_delete = QtWidgets.QPushButton("Видалити")

        for b in (self.btn_add, self.btn_edit, self.btn_delete):
            b.setProperty("type", "admin_ok")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        self.widget_table_layout.addWidget(btn_container)

        self.scroll_layout.addWidget(self.widget_table)
        self.scroll_area.setWidget(self.scroll_content)

        self.main_layout.addWidget(self.scroll_area, 1, 0, 1, 1)

        self.filters_widget = QtWidgets.QWidget()
        self.filters_widget.setProperty("type", "w_pg")
        self.filters_widget.setFixedWidth(300)
        self.filters_layout = QtWidgets.QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(10, 10, 10, 10)
        self.filters_layout.setSpacing(10)

        lb_filters = QtWidgets.QLabel("Фільтри")
        lb_filters.setProperty("type", "page_section")
        self.filters_layout.addWidget(lb_filters)

        self.filter_age = QtWidgets.QComboBox()
        self.filter_age.addItems(["Всі вікові групи", "10-12", "13-14", "15-17"])
        self.filter_age.setProperty("type", "input_field")

        self.filter_status = QtWidgets.QComboBox()
        self.filter_status.addItems(["Всі статуси", "Активний", "Неактивний"])
        self.filter_status.setProperty("type", "input_field")

        self.btn_apply_filters = QtWidgets.QPushButton("Застосувати")
        self.btn_apply_filters.setProperty("type", "admin_ok")
        
        self.filter_age_text=QtWidgets.QLabel("Вікова група:")
        self.filters_layout.addWidget(self.filter_age_text)
        self.filter_age_text.setProperty("type", "lb_description")
        self.filters_layout.addWidget(self.filter_age)
        #self.filters_layout.addWidget(QtWidgets.QLabel("Статус:"))
        #self.filters_layout.addWidget(self.filter_status)
        self.filters_layout.addSpacing(10)
        self.filters_layout.addWidget(self.btn_apply_filters)
        self.filters_layout.addStretch()

        self.main_layout.addWidget(self.filters_widget, 1, 1, 1, 1)

        self.setLayout(self.main_layout)

        self.user_service = UserService()
        self.load_users_from_db()

        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_delete.clicked.connect(self.delete_user)
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.btn_search.clicked.connect(self.search_users)


    def load_users_from_db(self):
        users_data = self.user_service.get_all_users()  
        self.users = users_data
        self.update_table()

    def update_table(self, filtered=None):
        data = filtered if filtered is not None else self.users
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))
        for i, u in enumerate(data):
            age_group_map = {
                "AgeGroup.TEN_TO_TWELVE": "10-12",
                "AgeGroup.THIRTEEN_TO_FOURTEEN": "13-14",
                "AgeGroup.FIFTEEN_TO_SEVENTEEN": "15-17"
            }
            age_text = age_group_map.get(str(u.age_group), "-")

            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(u.id))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(u.username))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(u.password if hasattr(u, 'password') else ""))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(u.first_name if u.first_name else ""))
            self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(u.last_name if u.last_name else ""))
            self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(age_text))
            self.table.setItem(i, 6, QtWidgets.QTableWidgetItem(u.formatted_created_date))
            self.table.setItem(i, 7, QtWidgets.QTableWidgetItem(u.formatted_updated_date))



    def apply_filters(self):
        age_group = self.filter_age.currentText()
        status = self.filter_status.currentText()

        age_group_map = {
            "AgeGroup.TEN_TO_TWELVE": "10-12",
            "AgeGroup.THIRTEEN_TO_FOURTEEN": "13-14",
            "AgeGroup.FIFTEEN_TO_SEVENTEEN": "15-17"
        }

        filtered = []
        for u in self.users:
            user_age_text = age_group_map.get(str(u.age_group), "-")
            age_ok = (age_group == "Всі вікові групи" or user_age_text == age_group)
            status_ok = (
                status == "Всі статуси" or
                (u.is_active and status == "Активний") or
                (not u.is_active and status == "Неактивний")
            )
            if age_ok and status_ok:
                filtered.append(u)

        self.update_table(filtered)


    def add_user(self):
        dialog = AddEditStudentDialog(self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        data = dialog.get_data()

        # validation
        required = ["username", "email", "password_hash"]
        errors = {f: ["Обовʼязкове поле"] for f in required if not data.get(f)}
        if errors:
            QtWidgets.QMessageBox.warning(
                self, "Помилка", "\n".join(errors.keys())
            )
            return

        # bcrypt
        password_hash = bcrypt.hashpw(
            data["password_hash"].encode(),
            bcrypt.gensalt()
        ).decode()

        try:
            new_user = self.user_service.create_user(
                username=data["username"],
                email=data["email"],
                password_hash=password_hash,
                first_name=data["first_name"],
                last_name=data["last_name"],
                age_group=data["age_group"],
                profile_data=data["profile_data"]
            )

            self.load_users_from_db()
            QtWidgets.QMessageBox.information(self, "Успіх", "Користувача додано")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Помилка", str(e))



    def edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            return

        user = self.users[row]
        dialog = AddEditStudentDialog(self)

        dialog.username_edit.setText(user.username or "")
        dialog.email_edit.setText(user.email or "")
        dialog.first_name_edit.setText(user.first_name or "")
        dialog.last_name_edit.setText(user.last_name or "")
        profile = getattr(user, "profile_data", {})
        dialog.phone_edit.setText(profile.get("phone_number", ""))
        dialog.bdate_edit.setText(profile.get("date_of_birth", ""))

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()

            if data.get("password_hash"):
                password_bytes = data["password_hash"].encode('utf-8')
                data["password_hash"] = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            else:
                data["password_hash"] = user.password_hash

            updates = {}
            for key in ["username", "email", "first_name", "last_name", "password_hash"]:
                if key in data and data[key] != getattr(user, key):
                    updates[key] = data[key]

            profile_updates = {}
            phone = data.get("phone_number", "")
            bdate = data.get("date_of_birth", "")
            if phone != profile.get("phone_number", ""):
                profile_updates["phone_number"] = phone
            if bdate != profile.get("date_of_birth", ""):
                profile_updates["date_of_birth"] = bdate
            if profile_updates:
                updates["profile_data"] = {**profile, **profile_updates}

            if not updates:
                QtWidgets.QMessageBox.information(self, "Увага", "Змін не виявлено")
                return

            try:
                updated_user = self.user_service.update_user(user.id, updates)
                self.users[row] = updated_user
                self.update_table()
                QtWidgets.QMessageBox.information(self, "Успіх", "Дані користувача оновлено")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Помилка", f"Не вдалося оновити користувача: {e}")




    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            return         
        user = self.users[row]
        reply = QtWidgets.QMessageBox.question(
            self,
            "Видалити користувача",
            f"Підтвердити видалення користувача {user.username}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.user_service.delete_user(user.id)
                del self.users[row]
                self.update_table()

                QtWidgets.QMessageBox.information(self, "Успіх", "Користувача видалено")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Помилка", f"Не вдалося видалити користувача: {e}")


    def search_users(self):
        query = self.search_input.text().lower().strip()
        if not query:
            self.update_table()
            return

        filtered = [u for u in self.users if query in (u.username or "").lower()]
        self.update_table(filtered)




class ProgressPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.outer_layout = QtWidgets.QVBoxLayout(self)
        self.outer_layout.setContentsMargins(20, 10, 20, 10)

        self.title = QtWidgets.QLabel("Успішність")
        self.title.setProperty("type", "title")
        self.outer_layout.addWidget(self.title)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(15)
        self.outer_layout.addLayout(self.main_layout)

        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setProperty("type", "w_pg")
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(10, 10, 10, 10)

        self.lb_table_title = QtWidgets.QLabel("Список прогресу")
        self.lb_table_title.setProperty("type", "page_section")
        self.left_layout.addWidget(self.lb_table_title)

        search_container = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Пошук за ім'ям користувача...")
        self.search_input.setProperty("type", "settings")

        self.btn_search = QtWidgets.QPushButton("Пошук")
        self.btn_search.setProperty("type", "admin_ok")
        self.btn_search.setFixedWidth(60)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)

        self.left_layout.addWidget(search_container)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Логін", "Ім'я", "Прізвище", "Вік",
            "Бали", "Час (хв)", "Прогрес %"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.left_layout.addWidget(self.table)

        self.main_layout.addWidget(self.left_widget, 3)

        self.filters_widget = QtWidgets.QWidget()
        self.filters_widget.setProperty("type", "w_pg")
        self.filters_widget.setFixedWidth(300)

        self.filters_layout = QtWidgets.QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(10, 10, 10, 10)
        self.filters_layout.setSpacing(10)

        lb_filters = QtWidgets.QLabel("Фільтри")
        lb_filters.setProperty("type", "page_section")
        self.filters_layout.addWidget(lb_filters)

        self.filter_course = QtWidgets.QComboBox()
        self.filter_course.setProperty("type", "input_field")
        self.filter_course.addItem("Всі курси")

        self.filter_user = QtWidgets.QComboBox()
        self.filter_user.setProperty("type", "input_field")
        self.filter_user.addItem("Всі користувачі")

        self.filter_completion = QtWidgets.QComboBox()
        self.filter_completion.setProperty("type", "input_field")
        self.filter_completion.addItems(["Всі", "Завершені", "В процесі"])

        self.btn_apply = QtWidgets.QPushButton("Застосувати")
        self.btn_apply.setProperty("type", "admin_ok")


        self.course_text= QtWidgets.QLabel("Курс:")
        self.course_text.setProperty("type","lb_description")
        self.filters_layout.addWidget(self.course_text)
        self.filters_layout.addWidget(self.filter_course)

        self.user_text=QtWidgets.QLabel("Користувач:")
        self.user_text.setProperty("type","lb_description")
        self.filters_layout.addWidget(self.user_text)
        self.filters_layout.addWidget(self.filter_user)

        
        self.filters_layout.addWidget(self.btn_apply)
        self.filters_layout.addStretch()
        self.main_layout.addWidget(self.filters_widget, 1)

        self.progress_service = ProgressService()
        self.user_service = UserService()
        self.course_service = CourseService()

        self.load_filters()
        self.load_progress()
        self.btn_apply.clicked.connect(self.apply_filters)
        self.btn_search.clicked.connect(self.search_users)




    def update_table(self, progress_list=None):
        self.table.setRowCount(0)
        progress_list = progress_list or self.all_progress

        
        for p in progress_list:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            user_id_raw = getattr(p, "user_id", "").replace("-", "")
            if user_id_raw == "34fcf40722b547748cb459487ff7aa0f":  
                continue
            user = self.user_service.get_user_by_id(user_id_raw)
            user_name = getattr(user, "username", "Н/Д") if user else "Н/Д"
            first_name = getattr(user, "first_name", "Н/Д") if user else "Н/Д"
            last_name = getattr(user, "last_name", "Н/Д") if user else "Н/Д"
            age_group = getattr(user, "age_group", "-") if user else "-"

            points = str(getattr(p, "total_points_earned", 0))
            time_spent = str(getattr(p, "time_spent", 0))
            progress_percent = str(getattr(p, "progress_percentage", 0))

            self.table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(user_name))
            self.table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(first_name))
            self.table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(last_name))
            self.table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(age_group))
            self.table.setItem(row_position, 4, QtWidgets.QTableWidgetItem(points))
            self.table.setItem(row_position, 5, QtWidgets.QTableWidgetItem(time_spent))
            self.table.setItem(row_position, 6, QtWidgets.QTableWidgetItem(progress_percent))






    def load_filters(self):
        for c in self.course_service.get_all_courses():
            self.filter_course.addItem(c.title, c.id)

        for u in self.user_service.get_all_users():
            full_name = f"{u.first_name} {u.last_name}".strip()
            self.filter_user.addItem(full_name if full_name else u.username, u.id)

    def load_progress(self):
        self.all_progress = self.progress_service.get_all_progress()
        logger.debug("Отримано прогресу: %s", len(self.all_progress))
        for p in self.all_progress:
            logger.debug("%s", p.__dict__ if hasattr(p, '__dict__') else p)
        self.update_table()




    def apply_filters(self):
        course = self.filter_course.currentData()
        user = self.filter_user.currentData()
        completion = self.filter_completion.currentText()
        search = self.search_input.text().lower()

        filtered = []

        for p in self.all_progress:
            if search and search not in p.user_name.lower():
                continue
            if course and course != p.course_id:
                continue
            if user and user != p.user_id:
                continue
            if completion == "Завершені" and not p.is_completed:
                continue
            if completion == "В процесі" and p.is_completed:
                continue
            filtered.append(p)

        self.update_table(filtered)

    
    def search_users(self):
        pass




class SettingsPage(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)


        self.title_label = QLabel("Налаштування профілю")
        self.title_label.setProperty("type", "title")
        self.title_label.setAlignment(Qt.AlignLeft)

        self.main_layout.addWidget(self.title_label)
        self.setLayout(self.main_layout)


        self.pg_settings = QWidget(self)
        self.pg_settings.setObjectName("pg_settings")
        self.main_layout.addWidget(self.pg_settings)
        self.layout_settings_main = QGridLayout(self.pg_settings)
        


        self.scroll_area = QScrollArea(self.pg_settings)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("settings_scroll_area")
        




        self.widget_settings_content = QWidget(self.pg_settings)
        self.apply_size_policy(self.widget_settings_content, min_width=600)
        self.widget_settings_content.setProperty("type", "w_pg")

        self.layout_settings_form = QFormLayout(self.widget_settings_content)
        self.layout_settings_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout_settings_form.setContentsMargins(30, 20, 30, 20)
        self.layout_settings_form.setHorizontalSpacing(12)
        self.layout_settings_form.setVerticalSpacing(8)


        instructions_label = QLabel("Тут ви можете змінити свої особисті дані", self.widget_settings_content)
        instructions_label.setProperty("type", "lb_description")
        instructions_label.setAlignment(Qt.AlignLeft)
        instructions_label.setContentsMargins(0, 0, 0, 20)
        self.layout_settings_form.addRow(instructions_label)


        self.add_user_greeting()
        separator = QFrame(self.widget_settings_content)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #dde2f6;")
        separator.setFixedHeight(2)
        self.layout_settings_form.addRow(separator)
        

        personal_info_label = QLabel("Особиста інформація", self.widget_settings_content)
        personal_info_label.setProperty("type", "page_section")
        personal_info_label.setContentsMargins(0, 10, 0, 10)
        self.layout_settings_form.addRow(personal_info_label)
        
        self.add_form_field("Повне ім'я", "Олександр Петренко", "le_name")
        self.add_form_field("Електронна адреса", "oleksandr.petrenko@example.com", "le_email")
        self.add_form_field("Телефон", "+380501234567", "le_phone")
        self.add_form_field("Дата народження", "12.05.2005", "le_birthday")

        separator2 = QFrame(self.widget_settings_content)
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #dde2f6;")
        separator2.setFixedHeight(2)
        self.layout_settings_form.addRow(separator2)
        
        security_label = QLabel("Безпека", self.widget_settings_content)
        security_label.setProperty("type", "page_section")
        security_label.setContentsMargins(0, 10, 0, 10)
        self.layout_settings_form.addRow(security_label)
        
        self.password_field = self.add_password_field("Пароль", "admin123", "le_password")
        
        self.status_label = QLabel("", self.widget_settings_content)
        self.status_label.setProperty("type", "lb_description")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setContentsMargins(0, 10, 0, 10)
        self.status_label.setStyleSheet("color: #516ed9; font-weight: bold;")
        self.status_label.setVisible(False)
        self.layout_settings_form.addRow(self.status_label)



        buttons_widget = QWidget(self.widget_settings_content)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_widget.setProperty("type","w_pg")
        buttons_layout.setContentsMargins(0, 10, 0, 10)
        
        buttons_layout.addStretch()

        self.btn_save = QPushButton("Зберегти", self.widget_settings_content)
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setMinimumSize(QtCore.QSize(300, 50))
        self.btn_save.setMaximumSize(QtCore.QSize(300, 50))
        self.btn_save.setProperty("type","start_continue")
        self.layout_settings_form.addRow(self.btn_save)

        self.btn_save.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.btn_save)
        
        buttons_layout.addStretch()
        
        self.layout_settings_form.addRow(buttons_widget)
        
        self.scroll_area.setWidget(self.widget_settings_content)
        self.layout_settings_main.addWidget(self.scroll_area)
        
    def apply_size_policy(self, widget, min_width=0, max_width=16777215, min_height=0, max_height=16777215):
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(size_policy)
        widget.setMinimumSize(min_width, min_height)
        widget.setMaximumSize(max_width, max_height)

    def add_user_greeting(self):
        widget_user_greeting = QWidget(self.widget_settings_content)
        widget_user_greeting.setProperty("type", "w_pg")
        self.apply_size_policy(widget_user_greeting, min_width=500, max_width=500, min_height=100, max_height=100)

        layout_user_greeting = QHBoxLayout(widget_user_greeting)
        layout_user_greeting.setContentsMargins(0, 20, 0, 0)

        lb_image = QLabel(widget_user_greeting)
        lb_image.setMinimumSize(50, 50)
        lb_image.setMaximumSize(50, 50)
        lb_image.setScaledContents(True)
        original_pixmap = QPixmap("icon/icon_users.PNG")  
        round_pixmap = make_round_pixmap(original_pixmap, QSize(50, 50))
        lb_image.setPixmap(round_pixmap)
        lb_image.setAlignment(Qt.AlignCenter)
        layout_user_greeting.addWidget(lb_image)

        lb_welcome = QLabel("Вітаємо,", widget_user_greeting)
        lb_welcome.setProperty("type", "page_section")
        lb_welcome.setMinimumSize(100, 50)
        lb_welcome.setMaximumSize(100, 50)
        layout_user_greeting.addWidget(lb_welcome)

        lb_username = QLabel("Олександр", widget_user_greeting)
        lb_username.setProperty("type", "page_section")
        layout_user_greeting.addWidget(lb_username)

        self.layout_settings_form.addRow(widget_user_greeting)

    def add_form_field(self, label_text, placeholder_text, obj_name):
        form_group_widget = QWidget(self.widget_settings_content)
        form_group_layout = QHBoxLayout(form_group_widget)
        form_group_layout.setContentsMargins(0, 0, 0, 0)
        form_group_layout.setSpacing(10)
        
        input_field = QLineEdit(self.widget_settings_content)
        input_field.setPlaceholderText(placeholder_text)
        input_field.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        input_field.setFixedHeight(40)  
        input_field.setObjectName(obj_name)
        input_field.setProperty("type", "settings2")
        

        label = QLabel(label_text, form_group_widget)
        label.setProperty("type", "lb_description")
        label.setMinimumWidth(150) 
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        

        form_group_layout.addWidget(label)
        form_group_layout.addWidget(input_field)
        self.layout_settings_form.addRow(form_group_widget)
        return input_field

    def add_password_field(self, label_text, placeholder_text, obj_name):
        form_group_widget = QWidget(self.widget_settings_content)
        form_group_layout = QHBoxLayout(form_group_widget)
        form_group_layout.setContentsMargins(0, 0, 0, 0)
        form_group_layout.setSpacing(10)
        
        input_field = QLineEdit(self.widget_settings_content)
        input_field.setPlaceholderText(placeholder_text)
        input_field.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        input_field.setEchoMode(QLineEdit.Password)
        input_field.setFixedHeight(40)
        input_field.setObjectName(obj_name)
        input_field.setProperty("type", "settings2")
        
        label = QLabel(label_text, form_group_widget)
        label.setProperty("type", "lb_description")
        label.setMinimumWidth(150)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        

        form_group_layout.addWidget(label)
        form_group_layout.addWidget(input_field)
        self.layout_settings_form.addRow(form_group_widget)
        return input_field



    
    def save_settings(self):
        pass

    def showEvent(self, event):
        pass


class AdminDashboard(QtWidgets.QWidget):
    go_to_main = pyqtSignal()
    theme_changed = QtCore.pyqtSignal(str)
    font_size_changed = QtCore.pyqtSignal(int)


    def __init__(self):
        super().__init__()
        self.font_scale = 0
        self.current_theme = "light"

        self.setWindowTitle("Mathtermind")
        self.resize(1400, 850)
        self.init_ui()
        icon = QtGui.QIcon()
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "icon/logo.png")
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.btn_user.clicked.connect(self.show_menu)

    def init_ui(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QtWidgets.QWidget()
        sidebar.setObjectName("sidebar_widget")
        sidebar.setFixedWidth(230)
        
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 15)
        sidebar_layout.setSpacing(10)

        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        topbar = QtWidgets.QFrame()
        topbar.setFixedHeight(70)
        
        topbar_layout = QtWidgets.QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(15, 10, 15, 10)
        topbar_layout.setSpacing(15)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        topbar_layout.addItem(spacerItem1)
        self.le_search = QtWidgets.QLineEdit()
        self.le_search.setPlaceholderText("Пошук...")
        self.le_search.setMinimumSize(QtCore.QSize(600, 50))
        self.le_search.setMaximumSize(QtCore.QSize(16777215, 100))
        self.le_search.setProperty("type", "search")
        topbar_layout.addWidget(self.le_search)

        self.btn_search = QtWidgets.QPushButton()
        self.btn_search.setIcon(QtGui.QIcon(os.path.join(base_path, "icon/icon_search.png")))
        self.btn_search.setFixedSize(45, 45)
        self.btn_search.setObjectName("btn_user")
        topbar_layout.addWidget(self.btn_search)

        topbar_layout.addStretch()

        self.btn_user = QtWidgets.QPushButton()
        self.btn_user.setIcon(QtGui.QIcon(os.path.join(base_path, "icon/icon_users.png")))
        self.btn_user.setIconSize(QtCore.QSize(32, 32))
        self.btn_user.setFixedSize(50, 50)
        self.btn_user.setObjectName("btn_user")
        topbar_layout.addWidget(self.btn_user)

        content_layout.addWidget(topbar)

        self.stack = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.stack)

        self.sidebar_logo = QtWidgets.QLabel(sidebar)
        self.sidebar_logo.setText("")
        self.sidebar_logo.setObjectName("sidebar_logo")
        self.sidebar_logo.setFixedSize(50, 50)  
        sidebar_layout.addWidget(self.sidebar_logo)

        base_path = os.path.dirname(os.path.abspath(__file__))
        sidebar_logo_path = os.path.join(base_path, "icon/logo.png")
        self.sidebar_logo.setPixmap(QtGui.QPixmap(sidebar_logo_path))

        self.courses_page = CoursesPage()
        self.lessons_page = LessonsPage(self.courses_page)
        self.students_page = StudentsPage()
        self.progress_page = ProgressPage()
        self.settings_page = SettingsPage()

        self.menu_buttons = [
            {"name": "btn_courses", "icon_normal": "gray_icon/gray_courses.PNG", "icon_active": "blue_icon/blue_course.PNG", "text": "Курси"},
            {"name": "btn_lessons", "icon_normal": "gray_icon/gray_lessons.PNG", "icon_active": "blue_icon/blue_lessons.PNG", "text": "Уроки"},
            {"name": "btn_students", "icon_normal": "gray_icon/gray_students.PNG", "icon_active": "blue_icon/blue_students.PNG", "text": "Учні"},
            {"name": "btn_progress", "icon_normal": "gray_icon/gray_progress.PNG", "icon_active": "blue_icon/blue_progress.PNG", "text": "Успішність"},
            {"name": "btn_settings", "icon_normal": "gray_icon/gray_settings.PNG", "icon_active": "blue_icon/blue_settings.PNG", "text": "Налаштування"},
        ]

        self.pages = [
            self.courses_page,
            self.lessons_page,
            self.students_page,
            self.progress_page,
            self.settings_page
        ]

        self.sidebar_buttons = []
        for i, item in enumerate(self.menu_buttons):
            btn = QtWidgets.QPushButton(item["text"])
            btn.setCheckable(True)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setIcon(QtGui.QIcon(os.path.join(base_path, item["icon_normal"])))
            btn.setIconSize(QtCore.QSize(28, 28))
            btn.setProperty("type", "main")
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
            self.stack.addWidget(self.pages[i])

        sidebar_layout.addStretch()
        spacerItem = QtWidgets.QSpacerItem(20, 328, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sidebar_layout.addItem(spacerItem)
        self.btn_exit = QtWidgets.QPushButton(sidebar)
        self.btn_exit.setProperty("type", "main")
        icon_exit = QtGui.QIcon()
        icon_exit_path = os.path.join(base_path, "icon/icon_exit.png")
        icon_exit.addPixmap(QtGui.QPixmap(icon_exit_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.btn_exit.setIcon(icon_exit)
        self.btn_exit.setIconSize(QtCore.QSize(30, 30))
        self.btn_exit.setCheckable(True)
        self.btn_exit.setObjectName("btn_exit")
        sidebar_layout.addWidget(self.btn_exit)

        main_layout.addWidget(sidebar)
        main_layout.addLayout(content_layout)

        self.switch_page(0)




    
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        base_path = os.path.dirname(os.path.abspath(__file__))
        for i, (btn, data) in enumerate(zip(self.sidebar_buttons, self.menu_buttons)):
            icon_path = data["icon_active"] if i == index else data["icon_normal"]
            btn.setChecked(i == index)
            btn.setIcon(QtGui.QIcon(os.path.join(base_path, icon_path)))

    def show_menu(self):
        menu = QMenu(self)
        action_main = QAction("Головна сторінка", self)
        action_main.triggered.connect(self.go_to_main.emit)
        menu.addAction(action_main)

        action_font = QAction("Змінити розмір тексту", self)
        action_theme = QAction("Змінити тему", self)
        action_exit = QAction("Вихід", self)

        action_font.triggered.connect(self.show_font_hint)
        action_theme.triggered.connect(self.toggle_theme)
        action_exit.triggered.connect(lambda: self.go_to_main.emit())

        menu.addAction(action_font)
        menu.addAction(action_theme)
        menu.addAction(action_exit)
        menu.exec_(self.btn_user.mapToGlobal(self.btn_user.rect().bottomLeft()))
        
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_scaled_stylesheet()

    def show_font_hint(self):
        hint_label = QtWidgets.QLabel(
            "Натискайте + або - для зміни розміру тексту", self
        )
        hint_label.setStyleSheet(
            "background-color: #5a78ff; border: 1px solid #5a78ff; padding: 10px; font-size:20px; color:white;"
        )
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setGeometry((self.width()-500)//2, (self.height()-50)//2, 500, 50)
        hint_label.show()
        QtCore.QTimer.singleShot(5000, hint_label.hide)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
            self.change_font_size(1)
        elif event.key() == QtCore.Qt.Key_Minus:
            self.change_font_size(-1)

    def change_font_size(self, delta):
        self.font_scale += delta
        if self.font_scale > 4:
            self.font_scale = 4
        if self.font_scale < -2:
            self.font_scale = -2
        self.apply_scaled_stylesheet()

    def apply_scaled_stylesheet(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        theme_file = os.path.join(base_path, "style.qss") if self.current_theme == "light" else os.path.join(base_path, "style_dark.qss")
        try:
            with open(theme_file, "r") as f:
                stylesheet = f.read()

            import re
            def repl(match):
                base = int(match.group(1))
                new_size = base + self.font_scale
                new_size = max(8, min(new_size, 28))
                return f"font-size: {new_size}px;"

            stylesheet = re.sub(r"font-size:\s*(\d+)px", repl, stylesheet)
            QtWidgets.QApplication.instance().setStyleSheet(stylesheet)
        except Exception as e:
            print("Помилка застосування стилю:", e)

def make_round_pixmap(pixmap, size):
    pixmap = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    rounded = QPixmap(size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size.width(), size.height())
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded


def main():
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    current_theme = "light"  
    light_theme_path = os.path.join(SCRIPT_DIR, "style.qss")
    dark_theme_path = os.path.join(SCRIPT_DIR, "style_dark.qss")
    
    app = QtWidgets.QApplication(sys.argv)
    win = AdminDashboard()
    
    with open(light_theme_path, "r") as file:
            style_sheet = file.read()
    app.setStyleSheet(style_sheet)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
