import logging

from PyQt5 import QtWidgets, QtCore, QtGui
from .main_win import Main_page
from .course_win import Course_page
from .lessons_list_win import Lessons_page
from .progress_win import Progress_page
from .settings_win import Settings_page
from .lesson_win import Lesson_page
import sys
import os

logger = logging.getLogger(__name__)
class Ui_MainWindow(object):
    def open_lesson_page(self, widget):
        lesson_page = Lesson_page()
        lesson_page.setObjectName("pg_lesson")
        self.stackedWidget.addWidget(lesson_page)
        self.stackedWidget.setCurrentWidget(lesson_page)
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1742, 865)


        self.main_stacked_widget = QtWidgets.QStackedWidget(MainWindow)
        self.main_stacked_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.centralwidget = QtWidgets.QWidget()
        
        self.centralwidget.setObjectName("centralwidget")
        self.main_layout = QtWidgets.QGridLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("main_layout")
        
        self.sidebar_main_layout = QtWidgets.QVBoxLayout()
        self.sidebar_main_layout.setSpacing(0)
        self.sidebar_main_layout.setObjectName("sidebar_main_layout")
        self.sidebar_widget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sidebar_widget.sizePolicy().hasHeightForWidth())
        self.sidebar_widget.setSizePolicy(sizePolicy)
        self.sidebar_widget.setMinimumSize(QtCore.QSize(200, 50))
        self.sidebar_widget.setMaximumSize(QtCore.QSize(250, 2000))
        self.sidebar_widget.setObjectName("sidebar_widget")
        self.sidebar_inner_layout = QtWidgets.QHBoxLayout(self.sidebar_widget)
        self.sidebar_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_inner_layout.setSpacing(0)
        self.sidebar_inner_layout.setObjectName("sidebar_inner_layout")
        self.sidebar_buttons_layout = QtWidgets.QVBoxLayout()
        self.sidebar_buttons_layout.setSpacing(0)
        self.sidebar_buttons_layout.setObjectName("sidebar_buttons_layout")
        self.sidebar_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_logo = QtWidgets.QLabel(self.sidebar_widget)
        self.sidebar_logo.setText("")
        base_path = os.path.dirname(os.path.abspath(__file__))
        sidebar_logo_path = os.path.join(base_path, "icon/logo.png")
        self.sidebar_logo.setPixmap(QtGui.QPixmap(sidebar_logo_path))
        
        self.sidebar_logo.setObjectName("sidebar_logo")
        self.sidebar_logo.setFixedSize(50, 50)  
        self.sidebar_buttons_layout.addWidget(self.sidebar_logo)
        self.menu_buttons = [
        {"name": "btn_main", "icon_normal": "gray_icon/gray_home.PNG", "icon_active": "blue_icon/blue_home.PNG", "text": "Головна"},
        {"name": "btn_courses", "icon_normal": "gray_icon/gray_courses.PNG", "icon_active": "blue_icon/blue_course.PNG", "text": "Курси"},
        {"name": "btn_lessons", "icon_normal": "gray_icon/gray_lessons.PNG", "icon_active": "blue_icon/blue_lessons.PNG", "text": "Уроки"},
        {"name": "btn_progress", "icon_normal": "gray_icon/gray_progress.PNG", "icon_active": "blue_icon/blue_progress.PNG", "text": "Успішність"},
        {"name": "btn_settings", "icon_normal": "gray_icon/gray_settings.PNG", "icon_active": "blue_icon/blue_settings.PNG", "text": "Налаштування"},
        ]

        self.buttons_dict = {}
        def update_buttons(clicked_button):
                for name, btn in self.buttons_dict.items():
                        if btn == clicked_button:
                                icon_path = next(item for item in self.menu_buttons if item["name"] == name)["icon_active"]
                                btn.setIcon(QtGui.QIcon(icon_path))
                                btn.setChecked(True)
                        else:
                                icon_path = next(item for item in self.menu_buttons if item["name"] == name)["icon_normal"]
                        icon_path_abs = os.path.join(base_path, icon_path)
                        btn.setIcon(QtGui.QIcon(icon_path_abs))
                        btn.setChecked(btn == clicked_button)

        for button_config in self.menu_buttons:
                icon_normal_abs = os.path.join(base_path, button_config["icon_normal"])
                icon_active_abs = os.path.join(base_path, button_config["icon_active"])

                logger.debug("Перевірка іконок: %s -> Існує? %s", icon_normal_abs, os.path.exists(icon_normal_abs))
                logger.debug("Перевірка іконок: %s -> Існує? %s", icon_active_abs, os.path.exists(icon_active_abs))

                button = QtWidgets.QPushButton(self.sidebar_widget)

                button.setLayoutDirection(QtCore.Qt.LeftToRight)
                button.setProperty("type", "main")

                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(icon_normal_abs), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                icon.addPixmap(QtGui.QPixmap(icon_active_abs), QtGui.QIcon.Active, QtGui.QIcon.On)
                button.setIcon(icon)

                button.setText(button_config["text"])
                button.setIconSize(QtCore.QSize(30, 30))
                button.setCheckable(True)
                button.setObjectName(button_config["name"])
                self.buttons_dict[button_config["name"]] = button
                self.sidebar_buttons_layout.addWidget(button)
                button.clicked.connect(lambda checked, btn=button, page=button_config["name"]: (
                                update_buttons(btn),
                                self.stackedWidget.setCurrentWidget(getattr(self, f"pg_{page.split('_')[1]}"))  
                        ))
        
        
        spacerItem = QtWidgets.QSpacerItem(20, 328, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.sidebar_buttons_layout.addItem(spacerItem)
        self.btn_exit = QtWidgets.QPushButton(self.sidebar_widget)
        self.btn_exit.setProperty("type", "main")
        
        icon_exit = QtGui.QIcon()
        icon_exit_path = os.path.join(base_path, "icon/icon_exit.png")
        icon_exit.addPixmap(QtGui.QPixmap(icon_exit_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_exit.setIcon(icon_exit)
        self.btn_exit.setIconSize(QtCore.QSize(30, 30))
        self.btn_exit.setCheckable(True)
        self.btn_exit.setObjectName("btn_exit")
        self.sidebar_buttons_layout.addWidget(self.btn_exit)
        self.sidebar_inner_layout.addLayout(self.sidebar_buttons_layout)
        self.sidebar_main_layout.addWidget(self.sidebar_widget)
        self.main_layout.addLayout(self.sidebar_main_layout, 0, 0, 1, 1)
        self.content_widget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.content_widget.sizePolicy().hasHeightForWidth())
        self.content_widget.setSizePolicy(sizePolicy)
        self.content_widget.setMinimumSize(QtCore.QSize(1421, 850))
        self.content_widget.setObjectName("content_widget")
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, -1, 0, -1)
        self.content_layout.setSpacing(0)
        self.content_layout.setObjectName("content_layout")
        self.topbar_widget = QtWidgets.QWidget(self.content_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.topbar_widget.sizePolicy().hasHeightForWidth())
        self.topbar_widget.setSizePolicy(sizePolicy)
        self.topbar_widget.setMaximumSize(QtCore.QSize(1700, 75))
        self.topbar_widget.setObjectName("topbar_widget")
        self.topbar_layout = QtWidgets.QHBoxLayout(self.topbar_widget)
        self.topbar_layout.setObjectName("topbar_layout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.topbar_layout.addItem(spacerItem1)
        self.topbar_search_layout = QtWidgets.QHBoxLayout()
        self.topbar_search_layout.setObjectName("topbar_search_layout")
        self.le_search = QtWidgets.QLineEdit(self.topbar_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(50)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.le_search.sizePolicy().hasHeightForWidth())
        self.le_search.setSizePolicy(sizePolicy)
        self.le_search.setMinimumSize(QtCore.QSize(600, 50))
        self.le_search.setMaximumSize(QtCore.QSize(16777215, 100))
        self.le_search.setProperty("type","search")
        self.le_search.setProperty("class", "search")
        self.le_search.setObjectName("le_search")
        self.topbar_search_layout.addWidget(self.le_search)
        self.btn_search = QtWidgets.QPushButton(self.topbar_widget)
        self.btn_search.setMinimumSize(QtCore.QSize(50, 50))
        self.btn_search.setMaximumSize(QtCore.QSize(200, 100))
        self.btn_search.setObjectName("btn_user")
        self.btn_search.setText("")
        icon6 = QtGui.QIcon()
        icon6_path = os.path.join(base_path, "icon/icon_search.png")
        icon6.addPixmap(QtGui.QPixmap(icon6_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_search.setIcon(icon6)
        self.btn_search.setCheckable(True)
        self.topbar_search_layout.addWidget(self.btn_search)
        
        self.topbar_layout.addLayout(self.topbar_search_layout)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.topbar_layout.addItem(spacerItem2)
        self.btn_points = QtWidgets.QPushButton(self.topbar_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_points.sizePolicy().hasHeightForWidth())
        self.btn_points.setSizePolicy(sizePolicy)
        self.btn_points.setMaximumSize(QtCore.QSize(50, 100))

        self.btn_points.setText("")
        icon7 = QtGui.QIcon()
        icon7_path = os.path.join(base_path, "icon/point.PNG")
        icon7.addPixmap(QtGui.QPixmap(icon7_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_points.setIcon(icon7)
        self.btn_points.setIconSize(QtCore.QSize(50, 50))
        self.btn_points.setCheckable(True)
        self.btn_points.setObjectName("btn_points")
        self.topbar_layout.addWidget(self.btn_points)
        self.lb_points = QtWidgets.QLabel(self.topbar_widget)
        self.lb_points.setObjectName("lb_points")
        self.lb_points.setText("1 250 балів")
        self.lb_points.setProperty("type", "lb_description")
        self.topbar_layout.addWidget(self.lb_points)
        self.btn_user = QtWidgets.QPushButton(self.topbar_widget)
        self.btn_user.setMinimumSize(QtCore.QSize(50, 50))
        self.btn_user.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        icon8 = QtGui.QIcon()
        icon8_path = os.path.join(base_path, "icon/icon_users.png")
        icon8.addPixmap(QtGui.QPixmap(icon8_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_user.setIcon(icon8)
        self.btn_user.setIconSize(QtCore.QSize(30, 30))
        self.btn_user.setCheckable(True)
        self.btn_user.setObjectName("btn_user")
        self.topbar_layout.addWidget(self.btn_user)
        self.content_layout.addWidget(self.topbar_widget)
        self.scrollArea = QtWidgets.QScrollArea(self.content_widget)
        self.scrollArea.setMaximumSize(QtCore.QSize(1700, 16777215))
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1421, 768))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.main_content_layout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.main_content_layout.setObjectName("main_content_layout")
        self.stackedWidget = QtWidgets.QStackedWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setMinimumSize(QtCore.QSize(500, 600))
        self.stackedWidget.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.stackedWidget.setObjectName("stackedWidget")
        self.pg_lesson=Lesson_page()
        self.pg_lesson.setObjectName("pg_lesson")
        
        self.pg_lessons = Lessons_page(self.stackedWidget, self.pg_lesson)
        self.pg_lessons.setObjectName("pg_lessons")
        self.stackedWidget.addWidget(self.pg_lessons)
        self.pg_courses = Course_page(self.stackedWidget, self.pg_lessons)
        self.pg_courses.setObjectName("pg_courses")
        self.stackedWidget.addWidget(self.pg_courses)
        
        self.pg_settings = Settings_page()
        self.pg_settings.setObjectName("pg_settings")
        self.stackedWidget.addWidget(self.pg_settings)
        
        self.pg_progress = Progress_page()
        self.pg_progress.setObjectName("pg_progress")
        self.stackedWidget.addWidget(self.pg_progress)
        
        self.stackedWidget.addWidget(self.pg_lesson)
        
        self.pg_main = Main_page(self.stackedWidget, self.pg_lesson, self.pg_courses, self.pg_lessons)
        
        self.stackedWidget.addWidget(self.pg_main)
        
        self.main_content_layout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.content_layout.addWidget(self.scrollArea)
        self.main_layout.addWidget(self.content_widget, 0, 1, 1, 1)
        
        self.main_stacked_widget.addWidget(self.centralwidget)
        MainWindow.setCentralWidget(self.main_stacked_widget) 

        
        self.stackedWidget.setCurrentWidget(self.pg_main)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        