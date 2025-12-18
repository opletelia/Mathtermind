from PyQt5 import QtWidgets, QtCore, QtGui
from src.services.auth_service import AuthService
from src.core import get_logger
import os
logger = get_logger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class RegisterPage(QtWidgets.QWidget):
    back_to_login = QtCore.pyqtSignal()  

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()

        self.setObjectName("pg_register")
        self.setMinimumSize(800, 600)
        
        self.label_title = QtWidgets.QLabel("Реєстрація")
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.label_title.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.input_username = QtWidgets.QLineEdit()
        self.input_username.setPlaceholderText("Ім’я користувача")
        self.input_username.setProperty("type", "settings")
        self.input_username.setMinimumSize(QtCore.QSize(200, 50))
        self.input_username.setMaximumSize(QtCore.QSize(400, 50))

        self.input_email = QtWidgets.QLineEdit()
        self.input_email.setPlaceholderText("Електронна адреса користувача")
        self.input_email.setProperty("type", "settings")
        self.input_email.setMinimumSize(QtCore.QSize(200, 50))
        self.input_email.setMaximumSize(QtCore.QSize(400, 50))


        self.input_password = QtWidgets.QLineEdit()
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_password.setProperty("type", "settings")
        self.input_password.setMinimumSize(QtCore.QSize(200, 50))
        self.input_password.setMaximumSize(QtCore.QSize(400, 50))
        self.input_password.setTextMargins(0, 0, 30, 0)

        self.show_password_btn = QtWidgets.QToolButton(self.input_password)
        self.show_password_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg")))
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.show_password_btn.setFixedSize(24, 24)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        self.input_password.textChanged.connect(self.adjust_eye_positions)
        self.input_password.resizeEvent = self.adjust_eye_positions

        self.input_confirm = QtWidgets.QLineEdit()
        self.input_confirm.setPlaceholderText("Повторіть пароль")
        self.input_confirm.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_confirm.setProperty("type", "settings")
        self.input_confirm.setMinimumSize(QtCore.QSize(200, 50))
        self.input_confirm.setMaximumSize(QtCore.QSize(400, 50))
        self.input_confirm.setTextMargins(0, 0, 30, 0)

        self.show_confirm_btn = QtWidgets.QToolButton(self.input_confirm)
        self.show_confirm_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg")))
        self.show_confirm_btn.setCheckable(True)
        self.show_confirm_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.show_confirm_btn.setFixedSize(24, 24)
        self.show_confirm_btn.clicked.connect(self.toggle_confirm_visibility)
        self.input_confirm.textChanged.connect(self.adjust_eye_positions)
        self.input_confirm.resizeEvent = self.adjust_eye_positions


        self.btn_register = QtWidgets.QPushButton("Зареєструватися")
        self.btn_register.setProperty("type", "start_continue")
        self.btn_register.setMinimumSize(QtCore.QSize(200, 50))
        self.btn_register.setMaximumSize(QtCore.QSize(400, 50))
        self.btn_register.clicked.connect(self.register_user)

        self.btn_back = QtWidgets.QPushButton("← Назад до входу")
        self.btn_back.clicked.connect(self.back_to_login.emit)
        self.btn_back.setProperty("type", "register")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(15)
        layout.addWidget(self.label_title)
        layout.addWidget(self.input_username)
        layout.addWidget(self.input_email)
        layout.addWidget(self.input_password)
        layout.addWidget(self.input_confirm)
        layout.addWidget(self.btn_register)
        layout.addWidget(self.btn_back)
        

    def adjust_eye_positions(self,event=None):
        pw = self.input_password.width()
        ph = self.input_password.height()
        btn_w = self.show_password_btn.width()
        btn_h = self.show_password_btn.height()
        self.show_password_btn.move(pw - btn_w - 6, (ph - btn_h) // 2)
        self.show_confirm_btn.move(pw - btn_w - 6, (ph - btn_h) // 2)


    def toggle_password_visibility(self, checked):
        if checked:
            self.input_password.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.show_password_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_open.svg")))
        else:
            self.input_password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.show_password_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg")))

    def toggle_confirm_visibility(self, checked):
        if checked:
            self.input_confirm.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.show_confirm_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_open.svg")))
        else:
            self.input_confirm.setEchoMode(QtWidgets.QLineEdit.Password)
            self.show_confirm_btn.setIcon(QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg")))

    def register_user(self):
        username = self.input_username.text().strip()
        email = self.input_email.text().strip()
        password = self.input_password.text()
        confirm_password = self.input_confirm.text()
        
        if not username or not email or not password or not confirm_password:
            QtWidgets.QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть усі поля")
            return
            
        if password != confirm_password:
            QtWidgets.QMessageBox.warning(self, "Помилка", "Паролі не збігаються")
            return
            
        if len(password) < 6:
            QtWidgets.QMessageBox.warning(self, "Помилка", "Пароль повинен містити щонайменше 6 символів")
            return
            
        try:
            success, message, user_id = self.auth_service.register(
                username=username,
                email=email,
                password=password
            )
            
            if success:
                logger.info(f"User {username} registered successfully")
                QtWidgets.QMessageBox.information(
                    self, 
                    "Успіх", 
                    f"Реєстрація успішна! Ви можете увійти з логіном: {username}"
                )
                self.back_to_login.emit()
            else:
                logger.warning(f"Registration failed for user {username}: {message}")
                QtWidgets.QMessageBox.warning(self, "Помилка", message or "Помилка реєстрації")
        except Exception as e:
            logger.error(f"Registration error for user {username}: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Помилка", f"Помилка реєстрації: {str(e)}")
