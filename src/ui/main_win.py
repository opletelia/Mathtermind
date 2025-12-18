import logging
import sys

logger = logging.getLogger(__name__)
import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from .circular_progress import *
from .graphs import *
from src.services.progress_service import ProgressService
from src.services.session_manager import SessionManager
from src.services.course_service import CourseService
from src.services.lesson_service import LessonService

class ClickFilter(QtCore.QObject):
    clicked = QtCore.pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
        return False 


class Main_page(QWidget):
    def __init__(self, stack=None, lesson_page=None, courses_page=None, lessons_page=None):
        super().__init__()
        self.stack = stack
        self.pg_lesson = lesson_page
        self.pg_courses = courses_page
        self.pg_lessons = lessons_page
        
        self.progress_service = ProgressService()
        
        self.course_service = CourseService()
        self.lesson_service = LessonService()
        
        
        
        self.pg_main = QtWidgets.QWidget(self)
        self.pg_main.setObjectName("pg_main")
        self.main_layout = QtWidgets.QGridLayout(self.pg_main)
        self.main_layout.setObjectName("main_layout")
        self.continue_viewing_section = QtWidgets.QWidget(self.pg_main)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.continue_viewing_section.sizePolicy().hasHeightForWidth())
        self.continue_viewing_section.setSizePolicy(sizePolicy)
        self.continue_viewing_section.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.continue_viewing_section.setObjectName("continue_viewing_section")
        self.continue_viewing_section.setProperty("type", "w_pg")
        self.grid_continue_section = QtWidgets.QGridLayout(self.continue_viewing_section)
        self.grid_continue_section.setObjectName("grid_continue_section")        
        
        self.continue_viewing_label = QtWidgets.QLabel(self.continue_viewing_section)
        self.continue_viewing_label.setText("Продовжити перегляд")
        self.continue_viewing_label.setProperty("type", "page_section")
        
       

        self.continue_viewing_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)        
        self.continue_viewing_label.setMaximumSize(QtCore.QSize(16777215, 50))
        self.continue_viewing_label.setObjectName("continue_viewing_label")
        
        self.continue_viewing_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)  
        header_layout.addWidget(self.continue_viewing_label, alignment=Qt.AlignLeft)
        self.grid_continue_section.addLayout(header_layout, 0, 0, 1, 3)
        self.continue_viewing_scroll_area = QtWidgets.QScrollArea(self.continue_viewing_section)
        self.continue_viewing_scroll_area.setWidgetResizable(True)
        self.continue_viewing_scroll_area.setObjectName("continue_viewing_scroll_area")
        
        self.scroll_area_content_widget = QtWidgets.QWidget()
        self.scroll_area_content_widget .setProperty("type", "w_pg")
        self.scroll_area_content_widget.setGeometry(QtCore.QRect(-329, 0, 1816, 250))
        self.scroll_area_content_widget.setObjectName("scroll_area_content_widget")
        
        self.scroll_area_main_layout = QtWidgets.QHBoxLayout(self.scroll_area_content_widget)
        self.scroll_area_main_layout.setObjectName("scroll_area_main_layout")
        self.continue_viewing_courses_layout = QtWidgets.QHBoxLayout()
        self.continue_viewing_courses_layout.setObjectName("continue_viewing_courses_layout")
        
        self.scroll_area_main_layout.addLayout(self.continue_viewing_courses_layout)
        self.continue_viewing_scroll_area.setWidget(self.scroll_area_content_widget)
        self.grid_continue_section.addWidget(self.continue_viewing_scroll_area, 1, 1, 1, 1)
        self.grid_continue_section.setContentsMargins(8, 8, 8, 8)

        in_progress_lessons = self.get_user_in_progress_lessons()
        
        for i, lesson_data in enumerate(in_progress_lessons[:9], start=1):
            widget = QtWidgets.QWidget(self.scroll_area_content_widget)
            widget.setMinimumSize(QtCore.QSize(250, 0))
            widget.setMaximumSize(QtCore.QSize(250, 16777215))    
            widget.setProperty("type", "card")            
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.setObjectName(f"w_pg1_les{i}")

            vertical_layout = QtWidgets.QVBoxLayout(widget)
            vertical_layout.setObjectName(f"verticalLayout_{i}")

            lesson_name_label = QtWidgets.QLabel(widget)
            lesson_name_label.setProperty("type", "lb_name_lesson")
            lesson_name_label.setObjectName(f"lb_n_les{i}")
            lesson_name_label.setText(lesson_data["lesson"])
            lesson_name_label.setMinimumWidth(225)
            lesson_name_label.setMaximumHeight(100)
            lesson_name_label.setWordWrap(True)
            vertical_layout.addWidget(lesson_name_label)
            
            widget.lesson_label = lesson_name_label
            
            course_name_label = QtWidgets.QLabel(widget)
            course_name_label.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding))
            course_name_label.setMinimumSize(QtCore.QSize(0, 50))
            course_name_label.setMaximumSize(QtCore.QSize(16777215, 50))
            course_name_label.setProperty("type", "lb_name_course")
            course_name_label.setObjectName(f"course_name_label{i}")
            course_name_label.setText(lesson_data["course"])
            vertical_layout.addWidget(course_name_label)

            lesson_description_label = QtWidgets.QLabel(widget)
            lesson_description_label.setProperty("type", "lb_small")
            lesson_description_label.setObjectName(f"lesson_description_label{i}")
            lesson_description_label.setText(lesson_data["desc"])
            vertical_layout.addWidget(lesson_description_label)

            lesson_progress_bar = QtWidgets.QProgressBar(widget)
            lesson_progress_bar.setObjectName(f"lesson_progress_bar{i}")
            lesson_progress_bar.setValue(lesson_data["progress"])
            vertical_layout.addWidget(lesson_progress_bar)
            
            click_filter = ClickFilter(widget)
            widget.installEventFilter(click_filter)
            
            click_filter.clicked.connect(lambda w=widget: self.on_lesson_click(w))

            self.continue_viewing_courses_layout.addWidget(widget)


        self.btn_scroll_next = QtWidgets.QPushButton(self.continue_viewing_section)
        self.btn_scroll_next.setProperty("type", "next_previous")
        icon9 = QtGui.QIcon()
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon9_path = os.path.join(base_path, "icon/next.png")
        icon9.addPixmap(QtGui.QPixmap(icon9_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_scroll_next.setIcon(icon9)
        self.btn_scroll_next.setIconSize(QtCore.QSize(30, 30))
        self.btn_scroll_next.setObjectName("btn_scroll_next")
        self.grid_continue_section.addWidget(self.btn_scroll_next, 1, 2, 1, 1)
        
        self.btn_scroll_prev = QtWidgets.QPushButton(self.continue_viewing_section)
        self.btn_scroll_prev.setProperty("type", "next_previous")
        icon10 = QtGui.QIcon()
        icon10_path = os.path.join(base_path, "icon/previous.png")
        icon10.addPixmap(QtGui.QPixmap(icon10_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_scroll_prev.setIcon(icon10)
        self.btn_scroll_prev.setIconSize(QtCore.QSize(30, 30))
        self.btn_scroll_prev.setObjectName("btn_scroll_prev")
        self.grid_continue_section.addWidget(self.btn_scroll_prev, 1, 0, 1, 1)
        self.main_layout.addWidget(self.continue_viewing_section, 1, 0, 1, 1)
        
        self.courses_section = QtWidgets.QWidget(self.pg_main)
        self.courses_section.setProperty("type", "w_pg")
        self.courses_section.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.courses_layout = QtWidgets.QVBoxLayout(self.courses_section)
        self.courses_layout.setContentsMargins(8, 8, 8, 8)
        self.courses_layout.setSpacing(8)

        self.lb_my_courses = QtWidgets.QLabel("Курси")
        self.lb_my_courses.setProperty("type", "page_section")
        self.lb_my_courses.setFixedHeight(50)
        self.courses_layout.addWidget(self.lb_my_courses)

        self.courses_scroll = QtWidgets.QScrollArea()
        self.courses_scroll.setWidgetResizable(True)
        self.courses_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.courses_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.courses_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.courses_layout.addWidget(self.courses_scroll)

        self.courses_grid_container = QtWidgets.QWidget()
        self.courses_grid_container.setProperty("type", "w_pg")
        self.courses_grid_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout_14 = QtWidgets.QGridLayout(self.courses_grid_container)
        self.gridLayout_14.setContentsMargins(8, 8, 8, 8)
        self.gridLayout_14.setHorizontalSpacing(16)
        self.gridLayout_14.setVerticalSpacing(16)

        cols = 4
        for c in range(cols):
            self.gridLayout_14.setColumnStretch(c, 1)

        courses = self.course_service.get_all_courses()

        for i, course in enumerate(courses[:8], start=1):
            course_widget = QWidget(self.courses_grid_container)
            course_layout = QVBoxLayout(course_widget)
            course_layout.setContentsMargins(8, 8, 8, 8)
            course_layout.setSpacing(6)
            course_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

            course_widget.setMinimumSize(180, 180)
            course_widget.setProperty("type","transparent_widget")

            course_label = QLabel(course.name)
            course_label.setAlignment(Qt.AlignCenter)
            course_label.setProperty("type", "lb_description")
            course_label.setWordWrap(True)
            course_layout.addWidget(course_label)
            course_label.setMinimumHeight(50)

            circular_progress = CircularProgress(course_widget)
            circular_progress.setMinimumSize(140, 140)
            progress_value = self.get_course_progress_for_user(course.id)
            circular_progress.set_value(progress_value)
            course_layout.addWidget(circular_progress)

            row = (i - 1) // cols
            col = (i - 1) % cols
            self.gridLayout_14.addWidget(course_widget, row, col)

        self.courses_scroll.setWidget(self.courses_grid_container)

        self.main_layout.addWidget(self.courses_section, 2, 0, 1, 1)

        self.activity_section = QtWidgets.QWidget(self.pg_main)
        self.activity_section.setSizePolicy(sizePolicy)
        self.activity_section.setMinimumSize(QtCore.QSize(312, 340))
        self.activity_section.setMaximumSize(QtCore.QSize(500, 16777215))
        self.activity_section.setProperty("type", "w_pg")
        self.activity_section.setObjectName("activity_section")
        self.gridLayout_13 = QtWidgets.QGridLayout(self.activity_section)
        self.gridLayout_13.setObjectName("gridLayout_13")
        
        self.lb_activity = QtWidgets.QLabel(self.activity_section)
        self.lb_activity.setMinimumSize(QtCore.QSize(0, 50))
        self.lb_activity.setMaximumSize(QtCore.QSize(16777215, 50))
        self.lb_activity.setText("Активність")
        self.lb_activity.setProperty("type", "page_section")
        self.lb_activity.setObjectName("lb_activity")
        self.gridLayout_13.addWidget(self.lb_activity, 0, 0, 1, 1)
        
        self.activity_graph_widget = QtWidgets.QWidget(self.activity_section)
        self.activity_graph_widget.setObjectName("activity_graph_widget")
        self.activity_graph_widget.setProperty("type", "w_pg")
        self.gridLayout_13.addWidget(self.activity_graph_widget, 1, 0, 1, 1)
        self.main_layout.addWidget(self.activity_section, 2, 1, 1, 1)
        
        self.recommended_section = QtWidgets.QWidget(self.pg_main)
        self.recommended_section.setSizePolicy(sizePolicy)
        self.recommended_section.setMaximumSize(QtCore.QSize(500, 16777215))
        self.recommended_section.setMinimumSize(QtCore.QSize(0, 275))
        self.recommended_section.setProperty("type", "w_pg")
        self.recommended_section.setObjectName("recommended_section")
        self.grid_rec_activity_section = QtWidgets.QGridLayout(self.recommended_section)
        self.grid_rec_activity_section.setObjectName("grid_rec_activity_section")
        
        self.recommended_label = QtWidgets.QLabel(self.recommended_section)
        self.recommended_label.setText("Можливо цікавить")
        self.recommended_label.setProperty("type", "page_section")
        self.recommended_label.setObjectName("recommended_label")
        self.grid_rec_activity_section.addWidget(self.recommended_label, 0, 0, 1, 1)
        
        self.recommended_scroll_area = QtWidgets.QScrollArea(self.recommended_section)
        self.recommended_scroll_area.setWidgetResizable(True)
        self.recommended_scroll_area.setObjectName("recommended_scroll_area")
        
        self.recommended_scroll_content_widget = QtWidgets.QWidget()
        self.recommended_scroll_content_widget.setProperty("type", "w_pg")
        self.recommended_scroll_content_widget.setObjectName("recommended_scroll_content_widget")
        
        self.recommended_cards_layout = QtWidgets.QVBoxLayout(self.recommended_scroll_content_widget)
        self.recommended_cards_layout.setObjectName("recommended_cards_layout")
        self.recommended_cards_layout.setAlignment(Qt.AlignTop)

        self.recommended_scroll_area.setWidget(self.recommended_scroll_content_widget)
        self.grid_rec_activity_section.addWidget(self.recommended_scroll_area, 1, 0, 1, 1)

        self.main_layout.addWidget(self.recommended_section, 1, 1, 1, 1)

        recommended_courses = self.get_recommended_courses()
        
        for i, course in enumerate(recommended_courses, start=1):
            course_widget = QtWidgets.QWidget(self.recommended_scroll_content_widget)
            course_widget.setProperty("type", "card")
            course_widget.setMinimumSize(QtCore.QSize(0, 75))
            
            course_widget.course_id = course.get("id")
            
            course_layout = QVBoxLayout(course_widget)
            
            name_label = QtWidgets.QLabel(course["name"])
            name_label.setProperty("type", "lb_description")
            name_label.setMinimumWidth(330)
            name_label.setMaximumHeight(100)
            name_label.setWordWrap(True)
            name_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

            reason_label = QtWidgets.QLabel(course["reason"])
            reason_label.setProperty("type", "lb_small2")
            
            course_layout.addWidget(name_label)
            course_layout.addWidget(reason_label)
            
            click_filter = ClickFilter(course_widget)
            course_widget.installEventFilter(click_filter)
            click_filter.clicked.connect(lambda w=course_widget: self.on_course_click(w))
            
            self.recommended_cards_layout.addWidget(course_widget)
        
        self.main_layout.addWidget(self.recommended_section, 1, 1, 1, 1)
        
        self.title_main_lb = QtWidgets.QLabel(self.pg_main)
        self.title_main_lb.setText("Головна")
        self.title_main_lb.setProperty("type", "title")
        self.title_main_lb.setObjectName("title_main_lb")
        self.main_layout.addWidget(self.title_main_lb, 0, 0, 1, 1)
        self.setLayout(self.main_layout)
        #графік
        self.layout = QVBoxLayout(self.activity_graph_widget)
        self.plot = pg.PlotWidget() 
        self.layout.addWidget(self.plot)
        chart = MyGraph(self.plot)
        
        activity_data, day_labels = self.get_weekly_activity_data()
        chart.plot_bar_chart(activity_data, day_labels)

        self.btn_scroll_next.clicked.connect(self.scroll_right)
        self.btn_scroll_prev.clicked.connect(self.scroll_left)
        self.continue_viewing_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        QtCore.QTimer.singleShot(0, self.update_scroll_buttons)
        self.continue_viewing_scroll_area.horizontalScrollBar().valueChanged.connect(self.update_scroll_buttons)


    def update_scroll_buttons(self):
        scrollbar = self.continue_viewing_scroll_area.horizontalScrollBar()
        if scrollbar.maximum() == 0:
            self.btn_scroll_prev.hide()
            self.btn_scroll_next.hide()
            return
        self.btn_scroll_prev.setVisible(scrollbar.value() > 0)
        self.btn_scroll_next.setVisible(
            scrollbar.value() < scrollbar.maximum()
        )

    
    
    def scroll_left(self):
        scroll_bar = self.continue_viewing_scroll_area.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() - 150)

    def scroll_right(self):
        scroll_bar = self.continue_viewing_scroll_area.horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() + 150)
    
    def on_lesson_click(self, widget):
        logger.debug("Клік по уроці: %s", widget.lesson_label.text())
        self.pg_lesson.set_lesson_data(widget.lesson_label.text())
        self.stack.setCurrentWidget(self.pg_lesson)

    def get_recommended_courses(self):
        try:
            current_user = SessionManager.get_current_user()
            if not current_user:
                return []
            
            user_id = current_user.get('id')
            if not user_id:
                return []
            
            user_progress = self.progress_service.get_user_progress(user_id)
            user_topics = set()
            user_course_ids = set()
            
            all_courses = self.course_service.get_all_courses()
            course_dict = {str(course.id): course for course in all_courses}
            
            for progress_record in user_progress:
                user_course_ids.add(str(progress_record.course_id))
                course = course_dict.get(str(progress_record.course_id))
                if course:
                    user_topics.add(course.topic)
            
            recommended = []
            for course in all_courses:
                if str(course.id) not in user_course_ids:
                    if course.topic in user_topics:
                        recommended.append({
                            "id": str(course.id),
                            "name": course.name,
                            "topic": str(course.topic),
                            "priority": 1,
                            "reason": f"Схожий з вашими курсами по темі {course.topic}"
                        })
                    elif str(course.topic) == "MATHEMATICS":
                        recommended.append({
                            "id": str(course.id),
                            "name": course.name,
                            "topic": str(course.topic),
                            "priority": 2,
                            "reason": "Рекомендовано для розвитку математичних навичок"
                        })
                    else:
                        recommended.append({
                            "id": str(course.id),
                            "name": course.name,
                            "topic": str(course.topic),
                            "priority": 3,
                            "reason": "Новий курс для розширення знань"
                        })
            
            recommended.sort(key=lambda x: x["priority"])
            return recommended[:5]
            
        except Exception as e:
            logger.exception("Error getting recommended courses")
            return []

    def on_course_click(self, widget):
        try:
            course_id = widget.course_id
            logger.debug("Клік по курсу: %s", course_id)
            
            if course_id and self.pg_lessons and self.stack:
                self.pg_lessons.set_course_id(course_id)
                self.stack.setCurrentWidget(self.pg_lessons)
        except Exception as e:
            logger.exception("Помилка при кліку на курс")

    def get_weekly_activity_data(self):
        UKRAINIAN_DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
        
        try:
            current_user = SessionManager.get_current_user()
            if not current_user:
                return [0] * 7, UKRAINIAN_DAYS
            
            user_id = current_user.get('id')
            if not user_id:
                return [0] * 7, UKRAINIAN_DAYS
            
            user_id = str(user_id).replace('-', '')
            
            from src.db import get_db
            from datetime import datetime, timedelta
            from sqlalchemy import text
            
            db = next(get_db())
            try:
                today = datetime.now().date()
                start_date = today - timedelta(days=6)
                
                query = text("""
                SELECT DATE(completed_at) as date, COUNT(*) as lessons_completed
                FROM completed_lessons 
                WHERE user_id = :user_id AND DATE(completed_at) >= :start_date
                GROUP BY DATE(completed_at)
                ORDER BY date
                """)
                
                result = db.execute(query, {"user_id": user_id, "start_date": start_date}).fetchall()
                
                activity_data = [0] * 7
                day_labels = []
                
                for i in range(7):
                    current_date = start_date + timedelta(days=i)
                    date_str = current_date.strftime('%Y-%m-%d')
                    day_labels.append(UKRAINIAN_DAYS[current_date.weekday()])
                    
                    for row in result:
                        if str(row[0]) == date_str:
                            activity_data[i] = row[1]
                            break
                
                return activity_data, day_labels
            finally:
                db.close()
            
        except Exception as e:
            logger.exception("Error getting weekly activity")
            return [0] * 7, UKRAINIAN_DAYS

    def get_user_in_progress_lessons(self):
        try:
            current_user = SessionManager.get_current_user()
            if not current_user:
                return []
            
            user_id = current_user.get('id')
            if not user_id:
                return []
            
            user_progress = self.progress_service.get_user_progress(user_id)
            in_progress_lessons = []
            
            for progress_record in user_progress:
                if not progress_record.is_completed and progress_record.current_lesson_id:
                    try:
                        lesson = self.lesson_service.get_lesson_by_id(progress_record.current_lesson_id)
                        course = self.course_service.get_course_by_id(progress_record.course_id)
                        
                        if lesson and course:
                                lesson_data = {
                                    "lesson": lesson.title,
                                    "course": course.name,
                                    "desc": f"Прогрес: {progress_record.progress_percentage:.1f}%",
                                    "progress": int(progress_record.progress_percentage)
                                }
                                in_progress_lessons.append(lesson_data)
                    except Exception as e:
                        continue
            
            return in_progress_lessons
            
        except Exception as e:
            return []

    def get_course_progress_for_user(self, course_id):
        try:
            current_user = SessionManager.get_current_user()
            if not current_user:
                return 0
            
            user_id = current_user.get('id')
            if not user_id:
                return 0
            
            course_id_str = str(course_id)
            
            progress = self.progress_service.get_course_progress(user_id, course_id_str)
            if progress:
                progress_value = int(progress.progress_percentage) if hasattr(progress, 'progress_percentage') else 0
                logger.debug("Course %s: Progress = %s%%", course_id_str, progress_value)
                return progress_value
            else:
                logger.debug("Course %s: No progress found", course_id_str)
            return 0
            
        except Exception as e:
            logger.exception("Error getting progress for course %s", course_id)
            return 0