import logging

from PyQt5.QtWidgets import QWidget, QGridLayout,QVBoxLayout, QLabel,QSizePolicy
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5 import QtSvg
from src.services.progress_service import ProgressService
from src.services.session_manager import SessionManager
from src.services.achievement_service import AchievementService
from .graphs import MyGraph
import os
from PyQt5.QtWidgets import QScrollArea, QHBoxLayout
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt
from src.services import LessonService, ProgressService, SessionManager, ContentService, CourseService
from src.models.content import TheoryContent, ExerciseContent, AssessmentContent, InteractiveContent
from src.services.session_manager import SessionManager    

logger = logging.getLogger(__name__)


class ClickableLabel(QLabel):
    def __init__(self, *args, on_click=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_click = on_click

    def mousePressEvent(self, event):
        if self._on_click:
            self._on_click()
        super().mousePressEvent(event)


class BadgesTab(QWidget):
    def __init__(self, badges):

        super().__init__()
        self.badges = badges
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        def _load_pixmap(path: str, size: int) -> QtGui.QPixmap:
            if path.lower().endswith(".svg"):
                renderer = QtSvg.QSvgRenderer(path)
                img = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
                painter = QtGui.QPainter(img)
                painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
                painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
                painter.fillRect(img.rect(), QtCore.Qt.transparent)
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                renderer.render(painter, QtCore.QRectF(0, 0, size, size))
                painter.end()
                return QtGui.QPixmap.fromImage(img)
            return QtGui.QPixmap(path)

        def _maybe_grey_pixmap(pixmap: QtGui.QPixmap, earned: bool) -> QtGui.QPixmap:
            if earned:
                return pixmap
            img = QtGui.QImage(pixmap.size(), QtGui.QImage.Format_ARGB32_Premultiplied)
            painter = QtGui.QPainter(img)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
            painter.fillRect(img.rect(), QtCore.Qt.transparent)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(img.rect(), QtGui.QColor(170, 170, 170, 255))
            painter.end()
            return QtGui.QPixmap.fromImage(img)

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_widget.setProperty("type","w_pg")
        scroll_layout = QHBoxLayout()
        scroll_layout.setAlignment(Qt.AlignLeft)
        scroll_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        for badge in self.badges:
            badge_widget = QVBoxLayout()
            description = badge.get("description", "")
            earned = bool(badge.get("earned", True))

            # Іконка бейджу
            pixmap = _maybe_grey_pixmap(_load_pixmap(badge["icon"], 80), earned)
            icon_label = ClickableLabel(on_click=lambda d=description: QtWidgets.QMessageBox.information(self, "Досягнення", d) if d else None)
            icon_label.setProperty("type","lb_description")
            icon_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            if description:
                icon_label.setToolTip(description)
            badge_widget.addWidget(icon_label)

            # Назва бейджу
            name_label = ClickableLabel(badge["name"], on_click=lambda d=description: QtWidgets.QMessageBox.information(self, "Досягнення", d) if d else None)
            name_label.setProperty("type","lb_description")
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            if description:
                name_label.setToolTip(description)
            badge_widget.addWidget(name_label)

            container = QWidget()
            container.setProperty("type","w_pg")
            container.setLayout(badge_widget)
            scroll_layout.addWidget(container)

        scroll_widget.setLayout(scroll_layout)
        scroll_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        layout.addWidget(scroll)
        self.setLayout(layout)


class Progress_page(QWidget):
    
    
    def create_tab_with_grid(self, name, labels, columns=4):
        tab_widget = QtWidgets.QWidget()
        grid_layout = QtWidgets.QGridLayout(tab_widget)
        
        grid_layout.setContentsMargins(5,5,5,5)
        grid_layout.setHorizontalSpacing(30)
        grid_layout.setVerticalSpacing(15)
        grid_layout.setAlignment(QtCore.Qt.AlignTop)

        for idx, (title, description, progress_value, lessons_status) in enumerate(labels):
            row = idx // columns
            col = idx % columns

            container = QtWidgets.QWidget()
            container.setProperty("type","card")
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(5,5,5,5)
            container_layout.setSpacing(5)

            container.setMinimumHeight(150)
            container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

            # Назва курсу
            label_title = QtWidgets.QLabel(title)
            label_title.setProperty("type", "lb_name_lesson")
            label_title.setWordWrap(True)
            container_layout.addWidget(label_title)

            # Індикатори успішності уроків
            status_container = QtWidgets.QWidget()
            status_container.setProperty("type", "w_pg")
            status_layout = QtWidgets.QGridLayout(status_container)
            status_layout.setContentsMargins(0,0,0,0)

            squares_per_row = 5
            for i, status in enumerate(lessons_status):
                r = i // squares_per_row
                c = i % squares_per_row
                square = QtWidgets.QLabel()
                square.setFixedSize(20,20)
                color_map = {
                    "done": "#27AE60",        # Green - Finished
                    "needs_work": "#3498DB",  # Blue - In Progress
                    "not_done": "#95A5A6"     # Gray - Not Started
                }
                color = color_map.get(status, "#95A5A6")
                square.setStyleSheet(f"background-color: {color}; border: 1px solid #34495E; border-radius: 3px;")
                status_layout.addWidget(square, r, c)

            container_layout.addWidget(status_container)

            grid_layout.addWidget(container, row, col)

        for c in range(columns):
            grid_layout.setColumnStretch(c, 1)

        self.tabs_courses_success.addTab(tab_widget, name)
        tab_widget.setProperty("type", "w_pg")




        

    def __init__(self):
        super().__init__()

        self.progress_service = ProgressService()
        self.course_service = CourseService()
        self.lesson_service = LessonService()
        self.session_manager = SessionManager()
        self.achievement_service = AchievementService()
        
        current_user = self.session_manager.get_current_user()
        if isinstance(current_user, dict):
            self.user_id = current_user.get("id")
        else:
            self.user_id = getattr(current_user, "id", None) if current_user else None


        self.pg_progress = QtWidgets.QWidget()
        self.pg_progress.setObjectName("pg_progress")

        base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.main_progress_layout = QtWidgets.QGridLayout(self.pg_progress)
        self.main_progress_layout.setHorizontalSpacing(7)
        self.main_progress_layout.setObjectName("main_progress_layout")
        self.success_widget = QtWidgets.QWidget(self.pg_progress)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        self.success_widget.setSizePolicy(sizePolicy)
        self.success_widget.setMinimumSize(QtCore.QSize(311, 341))
        self.success_widget.setProperty("type","w_pg") 
        self.success_widget.setObjectName("success_widget")
        self.success_layout = QtWidgets.QGridLayout(self.success_widget)
        self.success_layout.setObjectName("success_layout")
        
        self.lb_success = QtWidgets.QLabel(self.success_widget)
        self.lb_success.setText("Ваші бейджі")
        self.lb_success.setProperty("type", "page_section")
        self.lb_success.setMaximumSize(QtCore.QSize(16777215, 50))
        self.lb_success.setObjectName("lb_success")
        self.success_layout.addWidget(self.lb_success, 0, 0, 1, 1)
        

        user_achievements = []
        if self.user_id:
            try:
                earned = self.achievement_service.get_user_achievements(self.user_id)
                earned_ids = {ua.achievement_id for ua in earned}

                for ua in earned:
                    user_achievements.append(
                        {
                            "name": ua.name,
                            "description": ua.description,
                            "icon": os.path.join(base_path, ua.icon),
                            "earned": True,
                        }
                    )

                all_achievements = self.achievement_service.get_all_achievements()
                unearned_added = 0
                for ach in all_achievements:
                    if ach.id in earned_ids:
                        continue
                    if unearned_added >= 5:
                        break
                    user_achievements.append(
                        {
                            "name": ach.name,
                            "description": ach.description,
                            "icon": os.path.join(base_path, ach.icon),
                            "earned": False,
                        }
                    )
                    unearned_added += 1
            except Exception:
                logger.exception("Error loading achievements")
        
        if not user_achievements:
            user_achievements = [{   "name": "Немає досягнень","icon": os.path.join(base_path, "icon/badges/badge1.svg")}]
        
        self.badges_tab = BadgesTab(user_achievements)
        self.success_layout.addWidget(self.badges_tab,1,0,1,1)
        self.main_progress_layout.addWidget(self.success_widget, 1, 2, 3, 1)
        
        self.activity_widget = QtWidgets.QWidget(self.pg_progress)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.activity_widget.setSizePolicy(sizePolicy)
        self.activity_widget.setMinimumSize(QtCore.QSize(311, 341))
        self.activity_widget.setProperty("type","w_pg")
        self.activity_widget.setObjectName("activity_widget")
        self.activity_layout = QtWidgets.QGridLayout(self.activity_widget)
        self.activity_layout.setObjectName("activity_layout")
        

        #АТИВНІСТЬ
        self.lb_activity = QtWidgets.QLabel(self.activity_widget)
        self.lb_activity.setText("Активність")
        self.lb_activity.setProperty("type", "page_section")
        self.lb_activity.setObjectName("lb_activity")
        self.activity_layout.addWidget(self.lb_activity, 0, 0, 1, 1)



        
        
        base_path = os.path.dirname(os.path.abspath(__file__))

        def create_card(icon_path, number_text, description_text):
            card_widget = QtWidgets.QWidget()
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
            card_widget.setSizePolicy(sizePolicy)
            card_widget.setProperty("type", "card")

            card_layout = QtWidgets.QHBoxLayout(card_widget)
            card_layout.setAlignment(QtCore.Qt.AlignCenter)
            card_layout.setSpacing(20)

            from PyQt5.QtSvg import QSvgWidget
            if icon_path.endswith('.svg'):
                icon_container = QtWidgets.QWidget()
                icon_container.setProperty("type","w_pg")
                icon_container.setFixedSize(100, 100)
                icon_container_layout = QtWidgets.QVBoxLayout(icon_container)
                icon_container_layout.setContentsMargins(0, 0, 0, 0)
                
                svg_widget = QSvgWidget(icon_path)
                svg_widget.setFixedSize(100, 100)
                icon_container_layout.addWidget(svg_widget)
                
                card_layout.addWidget(icon_container)
            else:
                icon_label = QtWidgets.QLabel(card_widget)
                pixmap = QtGui.QPixmap(icon_path)
                icon_label.setPixmap(pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                icon_label.setAlignment(QtCore.Qt.AlignCenter)
                icon_label.setProperty("type", "lb_description")
                icon_label.setMinimumSize(100, 100)
                card_layout.addWidget(icon_label)

            text_container = QtWidgets.QWidget()
            text_container.setProperty("type","w_pg")
            text_layout = QtWidgets.QVBoxLayout(text_container)
            text_layout.setSpacing(5)
            text_layout.setContentsMargins(10, 10, 10, 10)

            number_label = QtWidgets.QLabel(number_text, text_container)
            number_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            number_label.setProperty("type", "lb_name_lesson")
            font = QtGui.QFont()
            font.setPointSize(24)
            font.setBold(True)
            number_label.setFont(font)
            text_layout.addWidget(number_label)

            description_label = QtWidgets.QLabel(description_text, text_container)
            description_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            description_label.setProperty("type", "lb_name_lesson")
            description_label.setWordWrap(True)
            text_layout.addWidget(description_label)

            card_layout.addWidget(text_container)

            return card_widget, number_label, description_label

        self.courses_card_widget, self.lb_num_of_courses, self.lb_courses_desc = create_card(
            os.path.join(base_path, "icon/icon_hat.svg"), "8", "Курсів"
        )
        self.lessons_card_widget, self.lb_num_of_lessons, self.lb_lessons_desc = create_card(
            os.path.join(base_path, "icon/icon_book2.svg"), "8", "Уроків"
        )
        self.awards_card_widget, self.lb_num_of_awards, self.lb_awards_desc = create_card(
            os.path.join(base_path, "icon/icon_award.svg"), "8", "Нагород"
        )
        self.tasks_card_widget, self.lb_num_of_tasks, self.lb_tasks_desc = create_card(
            os.path.join(base_path, "icon/icon_tasks.svg"), "8", "Завдань"
        )

        self.activity_layout.addWidget(self.courses_card_widget, 1, 0, 1, 1)
        self.activity_layout.addWidget(self.lessons_card_widget, 1, 1, 1, 1)
        self.activity_layout.addWidget(self.awards_card_widget, 2, 0, 1, 1)
        self.activity_layout.addWidget(self.tasks_card_widget, 2, 1, 1, 1)

        self.main_progress_layout.addWidget(self.activity_widget, 4, 0, 1, 1)
        
        
        self.courses_success_scroll_area = QtWidgets.QScrollArea(self.pg_progress)
        self.courses_success_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.courses_success_scroll_area.setWidgetResizable(True)
        self.courses_success_scroll_area.setObjectName("courses_success_scroll_area")
        self.scroll_courses_success_content = QtWidgets.QWidget()
        self.scroll_courses_success_content.setGeometry(QtCore.QRect(0, 0, 664, 341))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        
        self.scroll_courses_success_content.setSizePolicy(sizePolicy)
        self.scroll_courses_success_content.setObjectName("scroll_courses_success_content")
        self.courses_success_layout = QtWidgets.QGridLayout(self.scroll_courses_success_content)
        self.courses_success_layout.setContentsMargins(0, 0, 0, 0)
        self.courses_success_layout.setObjectName("courses_success_layout")
        self.widget_courses_success = QtWidgets.QWidget(self.scroll_courses_success_content)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_courses_success.sizePolicy().hasHeightForWidth())
        
        self.widget_courses_success.setSizePolicy(sizePolicy)
        self.widget_courses_success.setMinimumSize(QtCore.QSize(311, 341))
        self.widget_courses_success.setProperty("type","w_pg")
        self.widget_courses_success.setObjectName("widget_courses_success")
        
        self.courses_success_layout_inner = QtWidgets.QGridLayout(self.widget_courses_success)
        self.courses_success_layout_inner.setContentsMargins(11, 20, 0, 0)
        self.courses_success_layout_inner.setSpacing(0)
        self.courses_success_layout_inner.setObjectName("courses_success_layout_inner")
        
        self.lb_course_success = QtWidgets.QLabel(self.widget_courses_success)
        self.lb_course_success.setText("Успішність по курсах")
        self.lb_course_success.setProperty("type", "page_section")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_course_success.sizePolicy().hasHeightForWidth())
        self.lb_course_success.setSizePolicy(sizePolicy)
        self.lb_course_success.setObjectName("lb_course_success")
        self.courses_success_layout_inner.addWidget(self.lb_course_success, 0, 0, 1, 1)
        
        self.tabs_courses_success = QtWidgets.QTabWidget(self.widget_courses_success)
        self.tabs_courses_success.setMinimumSize(QtCore.QSize(660, 300))
        self.tabs_courses_success.setLayoutDirection(QtCore.Qt.LeftToRight)        
        self.tabs_courses_success.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabs_courses_success.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabs_courses_success.setObjectName("tabs_courses_success")
        

        self.courses_success_layout_inner.addWidget(self.tabs_courses_success, 1, 0, 1, 1)
        self.courses_success_layout.addWidget(self.widget_courses_success, 0, 0, 1, 1)
        self.courses_success_scroll_area.setWidget(self.scroll_courses_success_content)
        self.main_progress_layout.addWidget(self.courses_success_scroll_area, 4, 2, 1, 1)
        
        self.courses_scroll_area = QtWidgets.QScrollArea(self.pg_progress)
        self.courses_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.courses_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.courses_scroll_area.setWidgetResizable(True)
        self.courses_scroll_area.setObjectName("courses_scroll_area")
        
        self.scroll_courses_content = QtWidgets.QWidget()
        self.scroll_courses_content.setGeometry(QtCore.QRect(0, 0, 685, 341))
        self.scroll_courses_content.setObjectName("scroll_courses_content")
        
        self.courses_layout = QtWidgets.QGridLayout(self.scroll_courses_content)
        self.courses_layout.setContentsMargins(0, 0, 0, 0)
        self.courses_layout.setSpacing(0)
        self.courses_layout.setObjectName("courses_layout")
        
        self.widget_courses_main = QtWidgets.QWidget(self.scroll_courses_content)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_courses_main.sizePolicy().hasHeightForWidth())
        self.widget_courses_main.setSizePolicy(sizePolicy)
        self.widget_courses_main.setMinimumSize(QtCore.QSize(321, 341))
        #self.widget_courses_main.setProperty("type","w_pg")
        self.widget_courses_main.setObjectName("widget_courses_main")
        self.courses_main_layout = QtWidgets.QGridLayout(self.widget_courses_main)
        self.courses_main_layout.setObjectName("courses_main_layout")

        labels_data = [
        ("lb_course_1", "Назва курсу 1", 24),
        ("lb_course_2", "Назва курсу 2", 50),
        ("lb_course_3", "Назва курсу 3", 75),
        ("lb_course_4", "Назва курсу 4", 100),
        ("lb_course_5", "Назва курсу 5", 50),
        ("lb_course_3", "Назва курсу 3", 75),
        ("lb_course_4", "Назва курсу 4", 100),
        ("lb_course_5", "Назва курсу 5", 50),
        ("lb_course_6", "Назва курсу 6", 75)
        ]
      
       
        for title, description, progress_value in labels_data:
            container = QtWidgets.QWidget()
            container.setProperty("type","w_pg")
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(5,5,5,5)
            container_layout.setSpacing(10)

            # Назва курсу
            label_title = QtWidgets.QLabel(title)
            label_title.setProperty("type", "lb_name_lesson")
            label_title.setWordWrap(True)  # перенос рядків, якщо довга назва
            container_layout.addWidget(label_title)

            # Опис курсу
            label_desc = QtWidgets.QLabel(description)
            label_desc.setProperty("type", "lb_small")
            label_desc.setWordWrap(True)
            container_layout.addWidget(label_desc)

            # Прогрес-бар і відсоток
            progress_container = QtWidgets.QWidget()
            progress_layout = QtWidgets.QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(0,0,0,0)

            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setMinimumHeight(20)
            progress_bar.setValue(progress_value)
            progress_bar.setTextVisible(False)
            progress_layout.addWidget(progress_bar)

            lb_percent = QtWidgets.QLabel(f"{progress_value}%")
            lb_percent.setFixedWidth(40)
            lb_percent.setAlignment(QtCore.Qt.AlignCenter)
            lb_percent.setProperty("type", "lb_small")
            progress_layout.addWidget(lb_percent)

            container_layout.addWidget(progress_container)
            
            
            self.courses_layout.addWidget(container)
            spacer = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            self.courses_layout.addItem(spacer)

        self.courses_scroll_area.setWidget(self.scroll_courses_content)
        self.main_progress_layout.addWidget(self.courses_scroll_area, 1, 0, 3, 1)
        labels_informatics = [
            ("Базова математика", "Опис курсу 1", 24, ["done", "not_done", "done", "needs_work", "not_done", "done", "needs_work"]),
            ("Функції", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Вища математика", "Опис курсу 1", 24, ["done", "not_done", "done", "needs_work", "not_done", "done", "needs_work"]),
            ("Статистика та аналіз даних", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Геометрія та топологія", "Опис курсу 1", 24, ["done", "not_done", "done", "needs_work", "not_done", "done", "needs_work"]),
            ("Теорія ймовірностей", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Основи програмування", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Інформатика 1fddfgdfg", "Опис курсу 1", 24, ["done", "not_done", "done", "needs_work", "not_done", "done", "needs_work"]),
            ("Інформатика 2", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Інформатика 1fddfgdfg", "Опис курсу 1", 24, ["done", "not_done", "done", "needs_work", "not_done", "done", "needs_work"]),
            ("Інформатика 2", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Інформатика 3", "Опис курсу 3", 75, ["not_done", "done", "done", "done"])
        ]


        labels_math = [
            ("Базова математика", "Опис курсу 1", 100, ["done", "not_done", "done", "needs_work"]),
            ("Функції", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Статистика та аналіз даних", "Опис курсу 2", 50, ["done", "done", "needs_work", "not_done"]),
            ("Теорія ймовірностей", "Опис курсу 3", 75, ["done", "done", "needs_work", "not_done"])
        ]

        self.create_tab_with_grid("Інформатика", labels_informatics)
        self.create_tab_with_grid("Математика", labels_math)


        self.lb_progress = QtWidgets.QLabel(self.pg_progress)
        self.lb_progress.setText("Успішність")
        self.lb_progress.setProperty("type", "title")
        self.lb_progress.setObjectName("lb_progress")

        self.main_progress_layout.addWidget(self.lb_progress, 0, 0, 1, 1)
        self.setLayout(self.main_progress_layout)
        
        self.load_progress_data()

    def load_progress_data(self):
        """Load real progress data from the database and update widgets."""
        if not self.user_id:
            return
        
        try:
            stats = self.progress_service.get_user_progress_stats(self.user_id)
            achievements_count = 0
            try:
                achievements_count = len(
                    self.achievement_service.get_user_achievements(self.user_id)
                )
            except Exception:
                logger.exception("Error loading achievements for activity cards")
            self.update_activity_cards(stats)
            self.lb_num_of_awards.setText(str(achievements_count))
            
            self.update_course_list_widget()
            
            self.update_course_completion_tabs()
            
        except Exception as e:
            logger.exception("Error loading progress data")

    def update_activity_cards(self, stats):
        """Update the activity cards with real statistics."""
        self.lb_num_of_courses.setText(str(stats['completed_courses']))
        self.lb_num_of_lessons.setText(str(stats['completed_lessons']))
        self.lb_num_of_awards.setText(str(0))
        self.lb_num_of_tasks.setText(str(stats['total_tasks']))

    def update_course_list_widget(self):
        """Update the course list widget with real course progress."""
        if not self.user_id:
            return
        
        courses = self.progress_service.get_course_progress_list(self.user_id)
        
        while self.courses_layout.count():
            child = self.courses_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for course in courses:
            container = QtWidgets.QWidget()
            container.setProperty("type","w_pg")
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(5,5,5,5)
            container_layout.setSpacing(10)

            label_title = QtWidgets.QLabel(course['title'])
            label_title.setProperty("type", "lb_name_lesson")
            label_title.setWordWrap(True)
            container_layout.addWidget(label_title)

            label_desc = QtWidgets.QLabel(course['description'])
            label_desc.setProperty("type", "lb_small")
            label_desc.setWordWrap(True)
            container_layout.addWidget(label_desc)

            progress_container = QtWidgets.QWidget()
            progress_layout = QtWidgets.QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(0,0,0,0)

            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setMinimumHeight(20)
            progress_bar.setValue(int(course['progress_percentage']))
            progress_bar.setTextVisible(False)
            progress_layout.addWidget(progress_bar)

            lb_percent = QtWidgets.QLabel(f"{int(course['progress_percentage'])}%")
            lb_percent.setFixedWidth(40)
            lb_percent.setAlignment(QtCore.Qt.AlignCenter)
            lb_percent.setProperty("type", "lb_small")
            progress_layout.addWidget(lb_percent)

            container_layout.addWidget(progress_container)
            
            self.courses_layout.addWidget(container)
            spacer = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            self.courses_layout.addItem(spacer)

    def update_course_completion_tabs(self):
        """Update the course completion tabs with real data."""
        logger.debug("=== UPDATE COURSE COMPLETION TABS ===")
        if not self.user_id:
            logger.debug("No user_id, returning")
            return
        
        self.tabs_courses_success.clear()
        
        informatics_courses = self.progress_service.get_category_course_progress(self.user_id, 'Інформатика')
        mathematics_courses = self.progress_service.get_category_course_progress(self.user_id, 'Математика')
        
        logger.debug("Інформатика courses: %s", len(informatics_courses))
        logger.debug("Математика courses: %s", len(mathematics_courses))

        if informatics_courses:
            labels_informatics = []
            logger.debug("Processing %s Інформатика courses", len(informatics_courses))
            for i, course in enumerate(informatics_courses):
                logger.debug("%s. %s (ID: %s)", i + 1, course.get('title'), course.get('id'))
                lesson_statuses = self.get_lesson_statuses(course['id'])
                labels_informatics.append((
                    course['title'],
                    f"{course['completed_lessons']}/{course['total_lessons']} уроків",
                    int(course['progress_percentage']),
                    lesson_statuses
                ))
            logger.debug("Creating Інформатика tab with %s courses", len(labels_informatics))
            self.create_tab_with_grid("Інформатика", labels_informatics)
        
        if mathematics_courses:
            labels_math = []
            for course in mathematics_courses:
                lesson_statuses = self.get_lesson_statuses(course['id'])
                labels_math.append((
                    course['title'],
                    f"{course['completed_lessons']}/{course['total_lessons']} уроків",
                    int(course['progress_percentage']),
                    lesson_statuses
                ))
            self.create_tab_with_grid("Математика", labels_math)

    def get_lesson_statuses(self, course_id):
        """Get lesson completion statuses for a course."""
        try:
            completed_lessons = self.progress_service.get_course_completed_lessons(self.user_id, course_id)
            completed_lesson_ids = [str(cl.lesson_id) for cl in completed_lessons]
            
            progress = self.progress_service.get_course_progress(self.user_id, course_id)
            current_lesson_id = str(progress.current_lesson_id) if progress and progress.current_lesson_id else None
            
            lessons = self.lesson_service.get_lessons_by_course_id(course_id)
            
            statuses = []
            for lesson in lessons:
                lesson_id_str = str(lesson.id)
                
                if lesson_id_str in completed_lesson_ids:
                    statuses.append("done")
                elif lesson_id_str == current_lesson_id:
                    statuses.append("needs_work")
                else:
                    statuses.append("not_done")
            
            return statuses
        except Exception as e:
            logger.exception("Error getting lesson statuses")
            return ["not_done"] * 5

