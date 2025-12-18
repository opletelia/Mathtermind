import logging

from PyQt5.QtWidgets import QWidget, QScrollArea,QGridLayout,QVBoxLayout, QLabel,QSizePolicy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QDrag,QPixmap,QIcon
from .graphs import *
from .tasks import *
from .lesson_content_handler import LessonContentHandler
from src.services.session_manager import SessionManager
from src.services.progress_service import ProgressService

logger = logging.getLogger(__name__)

class LessonItem(QWidget):
    def __init__(self, title, duration, status="incomplete"):
        super().__init__()
        self.setObjectName("cards")

        self.title_label = QLabel(title)
        self.title_label.setProperty("type","lb_small2")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Preferred)
        self.title_label.setMinimumWidth(150)
        self.title_label.setMinimumHeight(50)

        duration_label = QLabel(duration)
        duration_label.setProperty("type","description")
        
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(duration_label)
        text_layout.setSpacing(2)
        
        status_widget = QWidget()
        status_widget.setFixedSize(24, 24)
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel()
        status_label.setAlignment(Qt.AlignCenter)
        
        if status == "done":
            status_label.setText("")
            status_label.setPixmap(QPixmap("blue_icon/check_mark.PNG").scaled(status_widget.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
            status_label.setStyleSheet("background-color: transparent;")
        elif status == "active":
            status_label.setText("")
            status_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")
        else:
            status_label.setText("")
            status_label.setStyleSheet("color: #bdc3c7; font-size: 14px;")
            
        status_layout.addWidget(status_label)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(text_layout)
        main_layout.addStretch()
        main_layout.addWidget(status_widget)
        main_layout.setContentsMargins(12, 8, 12, 8)

        self.setLayout(main_layout)

        bg_color = {
            "done": "#e8f8f5",     
            "active": "#e3f2fd",    
            "incomplete": "#ffffff" 
        }.get(status, "#ffffff")

        border_color = {
            "done": "#27ae60",     
            "active": "#3498db",    
            "incomplete": "#ecf0f1" 
        }.get(status, "#ecf0f1")

        self.setStyleSheet(f"""
            QWidget#card {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                margin: 2px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
            
            QWidget#card:hover {{
                background-color: #f8f9fa;
                border-color: #3498db;
            }}
        """)

class Lesson_page(QWidget):
    points_updated = pyqtSignal(int)

    def __init__(self):

        super().__init__()
        self.pg_lesson = QtWidgets.QWidget()
        self.pg_lesson.setObjectName("pg_lesson")

        self.current_course_id = None
        self.current_user_id = None
        self.progress_service = ProgressService()
        
        self.main_grid_layout = QtWidgets.QGridLayout(self.pg_lesson)
        self.main_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_grid_layout.setObjectName("main_grid_layout")
        
        self.main_scroll_area = QtWidgets.QScrollArea(self.pg_lesson)
        self.main_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.main_scroll_area.setWidgetResizable(True)
        self.main_scroll_area.setObjectName("main_scroll_area")
        self.main_scroll_content = QtWidgets.QWidget()

        self.main_scroll_content.setMinimumSize(QtCore.QSize(1399, 746))
        self.main_scroll_content.setMaximumSize(QtCore.QSize(2000, 2000))

        self.main_scroll_content.setObjectName("main_scroll_content")
        self.main_content_layout = QtWidgets.QGridLayout(self.main_scroll_content)
        self.main_content_layout.setContentsMargins(10, 5, 10, 10)
        self.main_content_layout.setVerticalSpacing(5)
        self.main_content_layout.setRowStretch(2, 1)
        self.main_content_layout.setObjectName("main_content_layout")
        """self.video_widget = QVideoWidget(self.main_scroll_content)
        self.video_widget.setMinimumSize(QtCore.QSize(1000, 350))
        self.video_widget.setMaximumSize(QtCore.QSize(16777215, 350))
        self.video_widget.setProperty("type","w_pg")
        self.video_widget.setObjectName("video_widget")
        self.main_content_layout.addWidget(self.video_widget, 1, 0, 2, 1)"""
        self.main_content_layout.setColumnStretch(0, 3)
        
        self.progress_section_widget = QtWidgets.QWidget(self.main_scroll_content)
        self.progress_section_widget.setMinimumSize(QtCore.QSize(200, 80))
        self.progress_section_widget.setMaximumSize(QtCore.QSize(350, 100))
        self.progress_section_widget.setProperty("type","w_pg")
        self.progress_section_widget.setObjectName("progress_section_widget")
        self.progress_layout = QtWidgets.QGridLayout(self.progress_section_widget)
        self.progress_layout.setContentsMargins(10, 10, 10, 10)
        self.progress_layout.setObjectName("progress_layout")
        
        self.course_title_lb = QtWidgets.QLabel(self.progress_section_widget)
        self.course_title_lb.setObjectName("course_title_lb")
        self.course_title_lb.setProperty("type","page_section")
        self.course_title_lb.setText("")
        self.progress_layout.addWidget(self.course_title_lb, 0, 0, 1, 1)
        
        self.lesson_progress_bar = QtWidgets.QProgressBar(self.progress_section_widget)
        self.lesson_progress_bar.setMinimumSize(QtCore.QSize(0, 25))
        self.lesson_progress_bar.setProperty("value", 24)
        self.lesson_progress_bar.setFormat("")
        self.lesson_progress_bar.setObjectName("lesson_progress_bar")
        self.progress_layout.addWidget(self.lesson_progress_bar, 1, 0, 1, 1)

        self.lesson_result_label = QtWidgets.QLabel("")
        self.lesson_result_label.setObjectName("lesson_result_label")
        self.lesson_result_label.setWordWrap(True)
        self.lesson_result_label.hide()
        self.progress_layout.addWidget(self.lesson_result_label, 2, 0, 1, 1)

        self.main_content_layout.addWidget(self.progress_section_widget, 0, 1, 2, 1)
        
        self.lesson_title_lb = QtWidgets.QLabel(self.main_scroll_content)
        self.lesson_title_lb.setMinimumSize(QtCore.QSize(1000, 20))
        self.lesson_title_lb.setMaximumSize(QtCore.QSize(16777215, 25))
        self.lesson_title_lb.setObjectName("lesson_title_lb")
        self.lesson_title_lb.setProperty("type","page_section")

        self.main_content_layout.addWidget(self.lesson_title_lb, 1, 0, 1, 1)
        
        self.lessons_list_scroll_area = QtWidgets.QScrollArea(self.main_scroll_content)
        self.lessons_list_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.lessons_list_scroll_area.setWidgetResizable(True)
        self.lessons_list_scroll_area.setObjectName("lessons_list_scroll_area")
        
        self.lessons_list_scroll_content = QtWidgets.QWidget()
        self.lessons_list_scroll_content.setMinimumSize(QtCore.QSize(350, 0))
        self.lessons_list_scroll_content.setMaximumSize(QtCore.QSize(450, 16777215))
        self.lessons_list_scroll_content.setGeometry(QtCore.QRect(0, 0, 570, 498))
        self.lessons_list_scroll_content.setObjectName("lessons_list_scroll_content")

        self.lessons_list_scroll_layout = QtWidgets.QGridLayout(self.lessons_list_scroll_content)
        self.lessons_list_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.lessons_list_scroll_layout.setObjectName("lessons_list_scroll_layout")

        self.lessons_list_container = QtWidgets.QWidget(self.lessons_list_scroll_content)
        self.lessons_list_container.setProperty("type","w_pg")
        self.lessons_list_container.setObjectName("lessons_list_container")
        
        self.lessons_list_layout = QtWidgets.QGridLayout(self.lessons_list_container)
        self.lessons_list_layout.setContentsMargins(11, -1, -1, -1)
        self.lessons_list_layout.setObjectName("lessons_list_layout")
        
        self.list_widget = QtWidgets.QListWidget()

        self.list_widget.itemClicked.connect(self.on_item_click)
        self.lessons_list_layout.addWidget(self.list_widget, 0, 0, 1, 1)
        
        self.lessons_list_scroll_layout.addWidget(self.lessons_list_container, 0, 0, 1, 1)
        self.lessons_list_scroll_area.setWidget(self.lessons_list_scroll_content)
        self.main_content_layout.addWidget(self.lessons_list_scroll_area, 2, 1, 1, 1)
        
        self.task_section_scroll_area = QtWidgets.QScrollArea(self.main_scroll_content)
        self.task_section_scroll_area.setMinimumSize(QtCore.QSize(1000, 0))
        self.task_section_scroll_area.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.task_section_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.task_section_scroll_area.setWidgetResizable(True)
        self.task_section_scroll_area.setObjectName("task_section_scroll_area")
        
        self.scroll_task_section_content = QtWidgets.QWidget()
        self.scroll_task_section_content.setGeometry(QtCore.QRect(0, 0, 800, 290))
        self.scroll_task_section_content.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.scroll_task_section_content.setMinimumSize(QtCore.QSize(1000, 0))
        self.scroll_task_section_content.setObjectName("scroll_task_section_content")
        
        self.task_scroll_layout = QtWidgets.QGridLayout(self.scroll_task_section_content)
        self.task_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.task_scroll_layout.setObjectName("task_scroll_layout")
        
        self.tab_container_widget = QtWidgets.QWidget()
        self.tab_container_widget.setMinimumSize(QtCore.QSize(1000, 290))
        self.tab_container_widget.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.tab_container_widget.setProperty("type","w_pg")
        self.tab_container_widget.setObjectName("tab_container_widget")
        
        self.task_tabs_layout = QtWidgets.QGridLayout(self.tab_container_widget)
        self.task_tabs_layout.setObjectName("task_tabs_layout")
        
        self.task_tabs = QtWidgets.QTabWidget(self.tab_container_widget)
        self.task_tabs.setMinimumSize(QtCore.QSize(1000, 290))
        self.task_tabs.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.task_tabs.setObjectName("task_tabs")
        
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tab_container_widget.setProperty("type", "w_pg")

        self.task_tabs_layout.addWidget(self.task_tabs, 0, 0, 1, 1)
        self.task_scroll_layout.addWidget(self.tab_container_widget, 0, 0, 1, 1)
        self.task_section_scroll_area.setWidget(self.scroll_task_section_content)
        self.main_content_layout.addWidget(self.task_section_scroll_area, 2, 0, 1, 1)
        self.title_main_lb = QtWidgets.QLabel(self.main_scroll_content)
        self.title_main_lb.setMinimumSize(QtCore.QSize(1000, 30))
        self.title_main_lb.setMaximumSize(QtCore.QSize(16777215, 30))
        self.title_main_lb.setText("Урок")
        self.title_main_lb.setProperty("type", "title")
        self.title_main_lb.setObjectName("title_main_lb")
        self.main_content_layout.addWidget(self.title_main_lb, 0, 0, 1, 1)
        self.main_scroll_area.setWidget(self.main_scroll_content)
        
        self.main_grid_layout.addWidget(self.main_scroll_area, 0, 0, 1, 1)
        
        self.setLayout(self.main_grid_layout)


    def createScrollableTab(self, inner_widget):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(inner_widget)
        inner_widget.setProperty("type", "w_pg")
        return scroll_area

    def set_lesson_data(self, lesson_name):
        logger.info("Завантажуємо урок: %s", lesson_name)
        if hasattr(self, 'lessons_by_title'):
            if lesson_name in self.lessons_by_title:
                logger.debug("Lesson found in current course")
            else:
                self._find_and_load_course_for_lesson(lesson_name)
                return
        else:
            self._find_and_load_course_for_lesson(lesson_name)
            return
        
        found_item = None
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if widget.title_label.text() == lesson_name:
                found_item = item
                break

        if found_item:
            self.list_widget.setCurrentItem(found_item)
            self.update_lesson_content(found_item)
            self.update_task_tabs()
        else:
            logger.warning("Урок з назвою '%s' не знайдено у списку.", lesson_name)

    def update_task_tabs(self):
        self.task_tabs.clear() 
        self.task_tabs.addTab(self.createScrollableTab(self.task_window.create_theory()), "Теорія")
        self.task_tabs.addTab(self.createScrollableTab(self.task_window.create_tasks_tab()), "Всі завдання")

    def update_lesson_content(self, item):
        if isinstance(item, QtWidgets.QListWidgetItem):
            selected_lesson_widget = self.list_widget.itemWidget(item)
            if selected_lesson_widget:
                lesson_title = selected_lesson_widget.title_label.text()
                self.lesson_title_lb.setText(lesson_title)
                self.task_window = TaskWindow()
                self.task_window.points_updated.connect(self.points_updated.emit)
                self.task_window.lesson_completed.connect(self._on_lesson_completed)
                lesson_id = None
                if hasattr(self, 'lessons_by_title'):
                    lesson_id = self.lessons_by_title.get(lesson_title)
                self.task_window.set_context(
                    user_id=self.current_user_id,
                    course_id=self.current_course_id,
                    lesson_id=lesson_id
                )
                
                self.task_window.set_progress_callback(self._on_task_window_progress)

                self._show_lesson_result_if_completed(lesson_id)
                
                if hasattr(self, 'lesson_content_data') and lesson_title in self.lesson_content_data:
                    self.task_window.update_content(self.lesson_content_data[lesson_title])
                    logger.debug("Завантажено реальний контент для уроку: %s", lesson_title)
                else:
                    logger.warning("Урок з назвою '%s' не знайдено в завантажених даних.", lesson_title)
                    logger.debug(
                        "Доступні уроки: %s",
                        list(self.lesson_content_data.keys()) if hasattr(self, 'lesson_content_data') else 'No data',
                    )
                    default_content = {
                        "theory": f"Теоретичний матеріал для уроку: {lesson_title}\n\nКонтент буде додано незабаром.",
                        "test_questions": [],
                        "true_false_questions": [],
                        "input_questions": [],
                        "blank_questions": [],
                        "code_questions": [],
                        "fix_error_questions": [],
                        "drag_and_drop_questions": [],
                        "interactive_tasks": [],
                    }
                    self.task_window.update_content(default_content)
                self.update_task_tabs()             
            else:
                logger.warning("не вдалося отримати віджет")
        else:
            logger.warning("не є в списку ")
    
    def _on_task_window_progress(self, **kwargs):
        """Callback from TaskWindow to update progress display.
        
        Receives:
            - answered: number of questions answered
            - total: total number of questions
            - percentage: completion percentage (0-100)
            - correct: number of correct answers
            - lesson_completed: (optional) True if lesson was completed
        """
        answered = kwargs.get('answered', 0)
        total = kwargs.get('total', 0)
        percentage = kwargs.get('percentage', 0)
        correct = kwargs.get('correct', 0)
        lesson_completed = kwargs.get('lesson_completed', False)
        
        self.lesson_progress_bar.setMaximum(100)
        self.lesson_progress_bar.setValue(percentage)
        
        if total > 0:
            tooltip = f"Прогрес: {percentage}% ({answered}/{total} запитань, {correct} правильних)"
        else:
            tooltip = f"Прогрес: {percentage}%"
        
        self.lesson_progress_bar.setToolTip(tooltip)
        
        if lesson_completed and self.current_course_id:
            try:
                self.set_course_id(self.current_course_id)
            except Exception as e:
                logger.exception("Error refreshing course after completion")

    def set_course_id(self, course_id):
        """Set the course ID and load lessons from database."""
        logger.debug("set_course_id called with: %s", course_id)
        try:
            self.current_course_id = course_id
            current_user = SessionManager.get_current_user()
            self.current_user_id = current_user.get('id') if current_user else None

            if not hasattr(self, 'content_handler'):
                self.content_handler = LessonContentHandler()
            
            data = self.content_handler.load_course_lessons(course_id)
            
            if 'course_title' in data:
                self.course_title_lb.setText(data['course_title'])
            elif 'course' in data and 'title' in data['course']:
                self.course_title_lb.setText(data['course']['title'])
            else:
                self.course_title_lb.setText("Курс")
            self.lessons_by_title = data['lessons_by_title']
            self.lesson_content_data = data['content']
            
            logger.info("Завантажено %s уроків з БД", len(data['lessons']))
            
            self.list_widget.clear()
            
            completed_ids = set()
            if self.current_user_id:
                try:
                    completed = self.progress_service.get_course_completed_lessons(
                        self.current_user_id,
                        course_id
                    )
                    completed_ids = {cl.lesson_id for cl in completed}
                except Exception as e:
                    logger.exception("Failed to load completed lessons for progress")

            total_lessons = len(data['lessons'])
            completed_count = 0

            for i, lesson in enumerate(data['lessons']):
                status = "incomplete"
                if lesson['id'] in completed_ids:
                    status = "done"
                    completed_count += 1
                elif lesson['order'] == 1 and completed_count == 0:
                    status = "active"
                
                item = QtWidgets.QListWidgetItem()
                widget = LessonItem(lesson['title'], lesson['duration'], status)
                item.setSizeHint(widget.sizeHint())
                
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)

            if total_lessons > 0:
                percentage = int(round((completed_count / total_lessons) * 100))
            else:
                percentage = 0
            self.lesson_progress_bar.setMaximum(100)
            self.lesson_progress_bar.setValue(percentage)
            self.lesson_progress_bar.setToolTip(
                f"Завершено уроків: {completed_count} з {total_lessons} ({percentage}%)"
            )
            
            logger.debug("Loaded lessons: %s", list(self.lessons_by_title.keys()))
            
        except Exception as e:
            logger.exception("Помилка завантаження уроків")

    def _find_and_load_course_for_lesson(self, lesson_name):
        """Find which course contains the lesson and load that course"""
        try:
            if not hasattr(self, 'content_handler'):
                self.content_handler = LessonContentHandler()
            
            course_id = self.content_handler.find_course_for_lesson(lesson_name)
            
            if course_id:
                self.set_course_id(course_id)
                self.set_lesson_data(lesson_name)
            else:
                logger.debug("Lesson '%s' not found in any course", lesson_name)
            
        except Exception as e:
            logger.exception("Error finding course for lesson")

    def on_item_click(self, item):
        index = self.list_widget.indexFromItem(item)
        item_text = self.list_widget.itemWidget(item).title_label.text()
        self.lesson_title_lb.setText(item_text)
        self.lesson_result_label.hide()
        self.set_lesson_data(item_text)

    def _on_lesson_completed(self, correct: int, total: int, percentage: int):
        """Handle lesson completion - show result and refresh lesson list."""
        self.lesson_result_label.setText(
            f"Результат: {correct}/{total} ({percentage}%)"
        )
        self.lesson_result_label.setStyleSheet(
            "color: #27ae60; font-weight: bold;" if percentage >= 70 else "color: #e74c3c; font-weight: bold;"
        )
        self.lesson_result_label.show()

        if self.current_course_id:
            self.set_course_id(self.current_course_id)

    def _show_lesson_result_if_completed(self, lesson_id: str):
        """Show lesson result if the lesson was already completed."""
        if not lesson_id or not self.current_user_id:
            self.lesson_result_label.hide()
            return

        try:
            completed = self.progress_service.get_lesson_completion(
                self.current_user_id, lesson_id
            )
            if completed:
                if completed.score is not None:
                    score = int(completed.score)
                    self.lesson_result_label.setText(
                        f"Попередній результат: {score}%"
                    )
                    self.lesson_result_label.setStyleSheet(
                        "color: #27ae60; font-weight: bold;" if score >= 70 else "color: #e74c3c; font-weight: bold;"
                    )
                else:
                    self.lesson_result_label.setText("Урок завершено")
                    self.lesson_result_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.lesson_result_label.show()
            else:
                self.lesson_result_label.hide()
        except Exception as e:
            logger.exception("Error checking lesson completion")
            self.lesson_result_label.hide()
    