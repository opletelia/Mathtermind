import os

from PyQt5 import QtCore, QtGui, QtWidgets

from src.core import get_logger
from src.services.auth_service import AuthService

logger = get_logger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class LoginPage(QtWidgets.QWidget):
    login_successful = QtCore.pyqtSignal()
    goto_register = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()

        self.setObjectName("pg_login")
        self.setMinimumSize(800, 600)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        self.widget = QtWidgets.QWidget()
        self.widget.setMinimumSize(QtCore.QSize(1600, 865))
        self.widget.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.widget.setProperty("type", "continue_viewing")

        self.label_title = QtWidgets.QLabel("Вхід до системи")
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.label_title.setProperty("type", "title")

        self.input_login = QtWidgets.QLineEdit()
        self.input_login.setPlaceholderText("Логін")
        self.input_login.setProperty("type", "settings")
        self.input_login.setMinimumSize(QtCore.QSize(200, 50))
        self.input_login.setMaximumSize(QtCore.QSize(400, 50))

        self.input_password = QtWidgets.QLineEdit()
        self.input_password.setPlaceholderText("Пароль")
        self.input_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_password.setProperty("type", "settings")
        self.input_password.setFixedSize(QtCore.QSize(200, 50))
        self.input_password.setMaximumSize(QtCore.QSize(400, 50))

        self.show_password_btn = QtWidgets.QToolButton(self.input_password)
        self.show_password_btn.setIcon(
            QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg"))
        )
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.show_password_btn.setFixedSize(24, 24)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)

        self.input_password.textChanged.connect(self.adjust_eye_position)
        self.input_password.resizeEvent = self.adjust_eye_position

        self.btn_login = QtWidgets.QPushButton("Увійти")
        self.btn_login.clicked.connect(self.check_credentials)
        self.btn_login.setProperty("type", "start_continue")
        self.btn_login.setMinimumSize(QtCore.QSize(200, 50))
        self.btn_login.setMaximumSize(QtCore.QSize(400, 2000))

        self.btn_register = QtWidgets.QPushButton("Зареєструватися")
        self.btn_register.setProperty("type", "register")
        self.btn_register.clicked.connect(self.goto_register.emit)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)
        layout.addWidget(self.label_title)
        layout.addWidget(self.input_login)
        layout.addWidget(self.input_password)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_register)

        self.checkbox_remember = QtWidgets.QCheckBox("Запам'ятати мене")
        self.checkbox_remember.setChecked(False)
        layout.addWidget(self.checkbox_remember, alignment=QtCore.Qt.AlignHCenter)

        self.load_saved_credentials()

    def check_credentials(self):
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not login or not password:
            QtWidgets.QMessageBox.warning(
                self, "Помилка", "Будь ласка, введіть логін та пароль"
            )
            return

        try:
            success, message, user_data = self.auth_service.login(login, password)
            if success:
                logger.info(f"User {login} logged in successfully")

                if self.checkbox_remember.isChecked():
                    self.save_credentials(login, password)
                else:
                    self.clear_saved_credentials()

                self.login_successful.emit()
            else:
                logger.warning(f"Login failed for user {login}: {message}")
                QtWidgets.QMessageBox.warning(
                    self, "Помилка", message or "Невірний логін або пароль"
                )
        except Exception as e:
            logger.error(f"Login error for user {login}: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Помилка", f"Помилка входу: {str(e)}")

    def save_credentials(self, login, password):
        """Save credentials to a simple config file for auto-login"""
        try:
            import json
            import os

            config_dir = os.path.expanduser("~/.mathtermind")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "login_config.json")

            with open(config_file, "w") as f:
                json.dump({"login": login, "password": password, "remember": True}, f)
            logger.info(f"Saved credentials for user {login}")
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}")

    def load_saved_credentials(self):
        """Load saved credentials and auto-login if available"""
        try:
            import json
            import os

            config_file = os.path.expanduser("~/.mathtermind/login_config.json")

            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)
                    if config.get("remember"):
                        self.input_login.setText(config["login"])
                        self.input_password.setText(config["password"])
                        self.checkbox_remember.setChecked(True)
                        QtCore.QTimer.singleShot(500, self.auto_login)
                        logger.info(
                            f"Loaded saved credentials for user {config['login']}"
                        )
        except Exception as e:
            logger.error(f"Failed to load saved credentials: {str(e)}")

    def auto_login(self):
        """Perform automatic login with saved credentials"""
        if self.checkbox_remember.isChecked() and self.input_login.text():
            self.check_credentials()

    def clear_saved_credentials(self):
        """Clear saved credentials"""
        try:
            import os

            config_file = os.path.expanduser("~/.mathtermind/login_config.json")
            if os.path.exists(config_file):
                os.remove(config_file)
                logger.info("Cleared saved credentials")
        except Exception as e:
            logger.error(f"Failed to clear saved credentials: {str(e)}")

    def adjust_eye_position(self, event=None):
        pw = self.input_password.width()
        ph = self.input_password.height()
        btn_w = self.show_password_btn.width()
        btn_h = self.show_password_btn.height()
        self.show_password_btn.move(pw - btn_w - 6, (ph - btn_h) // 2)

    def toggle_password_visibility(self, checked):
        if checked:
            self.input_password.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.show_password_btn.setIcon(
                QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_open.svg"))
            )
        else:
            self.input_password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.show_password_btn.setIcon(
                QtGui.QIcon(os.path.join(SCRIPT_DIR, "icon/eye_closed.svg"))
            )
