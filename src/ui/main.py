import logging

from PyQt5 import QtWidgets, QtCore, QtGui
from .ui import Ui_MainWindow
from .account_login import*
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMenu, QAction
import sys
from .ui_wrapper import *
from .account_login import LoginPage
from .register_page import RegisterPage
from .admin_dashboard import AdminDashboard
from src.services.session_manager import SessionManager
import os

logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mathtermind")
        self.resize(1400, 900)

        self.font_scale = 0

        icon = QtGui.QIcon()
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "icon/logo.png")
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.main_stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.main_stack)

        self.login_page = LoginPage()
        self.login_page.login_successful.connect(self.show_main_interface)
        self.login_page.goto_register.connect(self.show_register)
        self.main_stack.addWidget(self.login_page)

        self.register_page = RegisterPage()
        self.register_page.back_to_login.connect(self.show_login)
        self.main_stack.addWidget(self.register_page)
        

        self.ui_wrapper = None
        self.ui_page = None
        self.admin_dashboard = None
        self.main_stack.setCurrentWidget(self.login_page)

        self.current_theme = "light"
        self.light_theme_path = os.path.join(base_path, "style.qss")
        self.dark_theme_path = os.path.join(base_path, "style_dark.qss")


    def show_main_interface(self):
        self.ui_wrapper = UiWrapper()
        self.ui_page = self.ui_wrapper.centralWidget()
        
        self.main_stack.addWidget(self.ui_page)

        self.ui_wrapper.ui.btn_user.clicked.connect(self.show_menu)
        self.ui_wrapper.ui.pg_lesson.points_updated.connect(self.on_points_updated)
        self.update_points_display()
        self.main_stack.setCurrentWidget(self.ui_page)

    def update_points_display(self):
        current_user = SessionManager.get_current_user()
        if current_user:
            points = current_user.get("points", 0)
            self.ui_wrapper.ui.lb_points.setText(f"{points:,} балів".replace(",", " "))

    def on_points_updated(self, new_points: int):
        self.ui_wrapper.ui.lb_points.setText(f"{new_points:,} балів".replace(",", " "))


    """def show_admin_interface(self):
        if self.admin_dashboard is None:
            self.admin_dashboard = UiAdminWrapper()
            self.ui_admin_page = self.admin_dashboard.centralWidget()
            self.main_stack.addWidget(self.ui_admin_page)
        
        self.main_stack.setCurrentWidget(self.ui_admin_page)"""
        
    def show_register(self):
        self.main_stack.setCurrentWidget(self.register_page)

    def show_login(self):
        self.main_stack.setCurrentWidget(self.login_page)


    def show_menu(self):
        menu = QMenu(self)
        action1 = QAction("Змінити розмір тексту", self)
        action2 = QAction("Вихід", self)
        action3 = QAction("Змінити тему", self)

        action1.triggered.connect(self.action1_triggered)
        action2.triggered.connect(self.action2_triggered)
        action3.triggered.connect(self.action3_triggered)

        menu.addAction(action1)
        menu.addAction(action3)

        current_user = SessionManager.get_current_user()
        if current_user and current_user.get("role") == "admin":
            action_admin = QAction("Панель адміністратора", self)
            action_admin.triggered.connect(self.open_admin_dashboard)
            menu.addAction(action_admin)

        menu.addAction(action2)

        menu.exec_(self.ui_wrapper.ui.btn_user.mapToGlobal(
            self.ui_wrapper.ui.btn_user.rect().bottomLeft()
        ))

    def action1_triggered(self):
        logger.debug("Вибрана дія 1")
        hint_label = QtWidgets.QLabel("Натискайте + або - для зміни розміру тексту", self)
        hint_label.setStyleSheet("background-color: #5a78ff; border: 1px solid #5a78ff; padding: 10px; font-size:20px; color:white;")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
    
        window_width = self.width()
        window_height = self.height()
        hint_width = 500
        hint_height = 50

        x = (window_width - hint_width) // 2
        y = (window_height - hint_height) // 2

        hint_label.setGeometry(x, y, hint_width, hint_height)
        hint_label.show()       
        QtCore.QTimer.singleShot(5000, hint_label.hide)


    def action2_triggered(self):
        self.main_stack.setCurrentWidget(self.login_page)

    def open_admin_dashboard(self):
        if self.admin_dashboard is None:
            self.admin_dashboard = AdminDashboard()
            self.admin_dashboard.go_to_main.connect(self.show_main_from_admin)
            self.main_stack.addWidget(self.admin_dashboard)
        self.main_stack.setCurrentWidget(self.admin_dashboard)

    def show_main_from_admin(self):
        self.main_stack.setCurrentWidget(self.ui_page)

    def action3_triggered(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"

        self.apply_scaled_stylesheet()


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
        self.main_stack.adjustSize()
        self.repaint()


    def apply_scaled_stylesheet(self):
        theme_file = (
            self.light_theme_path if self.current_theme == "light"
            else self.dark_theme_path
        )

        try:
            with open(theme_file, "r") as file:
                stylesheet = file.read()
            import re
            def repl(match):
                base = int(match.group(1))
                new_size = base + self.font_scale

                if new_size > 28:
                    new_size = 28
                if new_size < 8:
                    new_size = 8

                return f"font-size: {new_size}px;"

            stylesheet = re.sub(r"font-size:\s*(\d+)px", repl, stylesheet)

            QtWidgets.QApplication.instance().setStyleSheet(stylesheet)

        except Exception as e:
            logger.exception("Помилка при оновленні теми")

        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    style_file_path = os.path.join(SCRIPT_DIR, "style.qss")
    try:
        with open(style_file_path, "r") as file:
            style_sheet = file.read()
        app.setStyleSheet(style_sheet)
    except Exception as e:
        logger.warning("Could not load style.qss: %s", e)

   
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
