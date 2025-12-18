import logging

from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout
from PyQt5 import QtWidgets, QtCore, QtGui
from .ui import*
from .lesson_win import Lesson_page
from src.services.course_service import CourseService
from src.services.lesson_service import LessonService
from src.services.progress_service import ProgressService
from src.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

class Lessons_page(QWidget):    
    def __init__(self,stack=None, lesson_page=None):
        super().__init__()
        self.stack = None
        self.pg_lesson = None
        self.stack = stack
        self.pg_lesson = lesson_page
        self.current_course_id = None

        self.pg_lessons = QtWidgets.QWidget()
        self.pg_lessons.setObjectName("pg_lessons")
        self.main_lessons_layout = QtWidgets.QGridLayout(self.pg_lessons)
        self.main_lessons_layout.setObjectName("main_lessons_layout")
        
        self.lb_lessons = QtWidgets.QLabel(self.pg_lessons)
        self.lb_lessons.setText("Уроки")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.lb_lessons.setSizePolicy(sizePolicy)
        self.lb_lessons.setMinimumSize(QtCore.QSize(0, 50))
        self.lb_lessons.setMaximumSize(QtCore.QSize(16777215, 50))
        self.lb_lessons.setProperty("type", "title")
        
        self.lb_lessons.setObjectName("lb_lessons")
        self.main_lessons_layout.addWidget(self.lb_lessons, 0, 0, 1, 1)
        self.lessons_tab_widget = QtWidgets.QTabWidget(self.pg_lessons)
        self.lessons_tab_widget.setMinimumSize(QtCore.QSize(660, 300))
        self.lessons_tab_widget.setObjectName("lessons_tab_widget")
        self.lessons_tab_widget.tabBar().setVisible(False)
        
        self.main_lessons_layout.addWidget(self.lessons_tab_widget, 3, 0, 1, 1)
        self.lb_choice = QtWidgets.QLabel(self.pg_lessons)
        self.lb_choice.setText("Виберіть урок:")
        self.lb_choice.setSizePolicy(sizePolicy)
        self.lb_choice.setMinimumSize(QtCore.QSize(0, 30))
        self.lb_choice.setMaximumSize(QtCore.QSize(16777215, 30))
        self.lb_choice.setProperty("type", "page_section")
        self.lb_choice.setObjectName("lb_choice")
        self.main_lessons_layout.addWidget(self.lb_choice, 1, 0, 1, 1)

        self.setLayout(self.main_lessons_layout)
        
        self.course_service = CourseService()
        self.progress_service = ProgressService()
        self.course_buttons = []

    def load_started_courses(self):
        current_user = SessionManager.get_current_user()
        if not current_user:
            return
        
        user_id = current_user.get('id')
        if not user_id:
            return
        
        for btn in self.course_buttons:
            btn.deleteLater()
        self.course_buttons.clear()
        
        try:
            started_courses = self.progress_service.get_user_started_courses(user_id)
            for course_data in started_courses:
                name = course_data['name']
                max_length = 20
                display_name = name if len(name) <= max_length else name[:max_length-3] + "..."
                
                btn = QtWidgets.QPushButton(display_name)
                btn.setToolTip(name)
                btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                
                is_current = self.current_course_id and course_data['id'] == self.current_course_id
                if is_current:
                    btn.setStyleSheet("""
                        QPushButton {
                            border-radius: 20px;
                            min-height: 40px;
                            padding: 5px 15px;
                            background-color: rgb(230, 230, 230);
                            color: #516ed9;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: rgb(210, 210, 210);
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            border-radius: 20px;
                            min-height: 40px;
                            padding: 5px 15px;
                            background: #516ed9;
                            color: white;
                        }
                        QPushButton:hover {
                            background: #8fb4ff;
                        }
                    """)
                
                course_id = course_data['id']
                btn.clicked.connect(lambda checked, cid=course_id: self.switch_to_course(cid))
                
                self.course_buttons_layout.addWidget(btn)
                self.course_buttons.append(btn)
        except Exception as e:
            logger.exception("Error loading started courses")

    def switch_to_course(self, course_id):
        self.set_course_id(course_id)
        self.load_started_courses()


    def create_card(self, title_text="Назва", labels_text=("TextLabel1", "TextLabel2"), desc_text="Опис", progress_percent=0, lesson_score=None):
        card = QtWidgets.QWidget()
        card.setFixedSize(QtCore.QSize(360, 330))
        card.setProperty("type", "card")
        card_layout = QtWidgets.QVBoxLayout(card)
        title = QtWidgets.QLabel(title_text)
        title.setProperty("type","lb_name_lesson")
        title.setMinimumWidth(330)
        title.setMaximumHeight(100)
        title.setWordWrap(True)

        labels = QtWidgets.QHBoxLayout()
        for text in labels_text:
            lb_subject = QtWidgets.QLabel(text)
            lb_subject.setProperty("type","lb_name_course")
            lb_subject.setMinimumSize(QtCore.QSize(165, 50))
            lb_subject.setMaximumSize(QtCore.QSize(165, 50))
            labels.addWidget(lb_subject)
        
        lb_description = QtWidgets.QLabel(desc_text)
        lb_description.setProperty("type","lb_description")
        lb_description.setMinimumWidth(330)
        lb_description.setMaximumHeight(100)
        lb_description.setWordWrap(True)
        
        stacked_widget = QtWidgets.QStackedWidget()
        stacked_widget.setMaximumSize(QtCore.QSize(16777215, 75))
        stacked_widget.setProperty("type","w_pg")

        page_start = QtWidgets.QWidget()
        page_start.setProperty("type","w_pg")
        layout_start = QtWidgets.QGridLayout(page_start)

        btn_start = QtWidgets.QPushButton("Розпочати урок")
        btn_start.setMinimumSize(QtCore.QSize(310, 50))
        btn_start.setProperty("type","start_continue")
        
        layout_start.addWidget(btn_start, 0, 0, 1, 1)

        page_start.setLayout(layout_start)

        page_continue = QtWidgets.QWidget()
        layout_continue = QtWidgets.QGridLayout(page_continue)

        btn_continue = QtWidgets.QPushButton("Продовжити")
        btn_continue.setMinimumSize(QtCore.QSize(310, 50))
        btn_continue.setProperty("type","start_continue")

        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setMinimumSize(QtCore.QSize(310, 20))
        progress_bar.setMaximum(100)
        if lesson_score is not None:
            progress_bar.setValue(lesson_score)
            if lesson_score >= 100:
                progress_bar.setFormat("Завершено")
            else:
                progress_bar.setFormat(f"Результат: {lesson_score}%")
        else:
            progress_bar.setValue(0)
            progress_bar.setFormat("")
        
        layout_continue.setContentsMargins(0, 0, 0, 0)
        layout_continue.addWidget(btn_continue, 0, 0, 1, 1)
        layout_continue.addWidget(progress_bar, 1, 0, 1, 1)

        page_continue.setLayout(layout_continue)
        page_continue.setProperty("type","w_pg")

        stacked_widget.addWidget(page_start)
        stacked_widget.addWidget(page_continue)

        def switch_to_continue():
            stacked_widget.setCurrentWidget(page_continue)

        def open_lesson_page():
            logger.debug("Клік по уроці: %s", title_text)
            self.pg_lesson.set_lesson_data(title_text)
            self.stack.setCurrentWidget(self.pg_lesson)
        
        btn_start.clicked.connect(switch_to_continue)
        btn_continue.clicked.connect(open_lesson_page)

        card_layout.addWidget(title)
        card_layout.addLayout(labels)
        card_layout.addWidget(lb_description)
        card_layout.addWidget(stacked_widget)
        return card

    def create_section(self, section_title="Розділ", cards_data=None, progress_percent=0, lesson_scores=None):
        section_widget = QtWidgets.QWidget()
        section_layout = QtWidgets.QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        
        section_label = QtWidgets.QLabel(section_title)
        section_label.setProperty("type", "page_section")
        section_layout.addWidget(section_label)

        cards_container = QtWidgets.QWidget()
        cards_layout = QtWidgets.QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)  
        cards_layout.setAlignment(QtCore.Qt.AlignLeft) 

        if cards_data:
            for card_info in cards_data:
                title = card_info.get("title", "Назва")
                labels = card_info.get("labels", ("Label1", "Label2"))
                desc = card_info.get("description", "Опис")
                lesson_score = None
                if lesson_scores and title in lesson_scores:
                    lesson_score = lesson_scores[title]
                card = self.create_card(title, labels, desc, progress_percent, lesson_score)
                cards_layout.addWidget(card)

        spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        cards_layout.addItem(spacer)

        section_layout.addWidget(cards_container)
        return section_widget

    def add_new_tab(self, name="Нова вкладка", sections_data=None, progress_percent=0, lesson_scores=None):
        new_tab = QtWidgets.QWidget()
        new_tab.setObjectName(name)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_area_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)
        if sections_data:
            for section_title, num_cards in sections_data:
                section_widget = self.create_section(section_title, num_cards, progress_percent, lesson_scores)
                scroll_layout.addWidget(section_widget)
        scroll_area.setWidget(scroll_area_widget)
        tab_layout = QtWidgets.QVBoxLayout(new_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        self.lessons_tab_widget.addTab(new_tab, name)
    
    def set_course_id(self, course_id):
        try:
            logger.info("Завантаження уроків для курсу: %s", course_id)
            
            self.lessons_tab_widget.clear()
            self.current_course_id = course_id
            
            self.course_service = CourseService()
            self.lesson_service = LessonService()
            
            course = self.course_service.get_course_by_id(course_id)
            if not course:
                logger.warning("Курс не знайдено: %s", course_id)
                return
            
            lessons = self.lesson_service.get_lessons_by_course_id(course.id)
            if not lessons:
                logger.warning("Уроки не знайдено для курсу: %s", course_id)
                return

            progress_percent = 0
            lesson_scores = {}
            current_user = SessionManager.get_current_user()
            if current_user:
                user_id = current_user.get('id')
                if user_id:
                    try:
                        completed = self.progress_service.get_course_completed_lessons(user_id, course_id)
                        if lessons:
                            progress_percent = int((len(completed) / len(lessons)) * 100)
                        for cl in completed:
                            for lesson in lessons:
                                if str(lesson.id) == str(cl.lesson_id):
                                    if cl.score is not None:
                                        lesson_scores[lesson.title] = int(cl.score)
                                    else:
                                        lesson_scores[lesson.title] = 100
                                    break
                    except Exception as e:
                        logger.exception("Error calculating course progress")
            
            sections = {}
            for lesson in lessons:
                section_key = lesson.section if lesson.section else "Загальне"
                if section_key not in sections:
                    sections[section_key] = []
                sections[section_key].append({
                    "title": lesson.title,
                    "labels": (str(course.topic), "Урок"),
                    "description": lesson.content.get('description', f"Опис уроку {lesson.title}") if lesson.content else f"Опис уроку {lesson.title}"
                })
            
            sections_data = [(section_name, lessons_list) for section_name, lessons_list in sections.items()]
            self.add_new_tab(course.name, sections_data, progress_percent, lesson_scores)
            
            logger.info("Завантажено %s уроків для курсу %s", len(lessons), course.name)
            
            if self.pg_lesson:
                self.pg_lesson.set_course_id(course.id)
            else:
                logger.debug("No lesson_page reference available")
            
        except Exception as e:
            logger.exception("Помилка завантаження уроків для курсу %s", course_id)

    def set_lesson_tab_by_name(self, lesson_name):
        logger.debug("Пошук уроку у вкладках: %s", lesson_name)
        tab_count = self.lessons_tab_widget.count()
        found_index = -1
        for i in range(tab_count):
            tab_label = self.lessons_tab_widget.tabText(i)
            if isinstance(tab_label, str):
                if tab_label.lower() == lesson_name.lower():
                    found_index = i
                    break
        if found_index != -1:
            self.lessons_tab_widget.setCurrentIndex(found_index)
        else:
            logger.warning("Вкладку не знайдено")

