import logging

from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QFormLayout, QHBoxLayout,
    QGridLayout, QSizePolicy, QFrame, QScrollArea, QPushButton, QVBoxLayout)
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from src.services.session_manager import SessionManager
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

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



class Settings_page(QWidget):
    def __init__(self):
        super().__init__()
        self.user_data = None
        self.user_service = UserService()
        self.session_manager = SessionManager()
        self.name_field = None
        self.email_field = None
        self.phone_field = None
        self.birthday_field = None
        self.lb_username = None
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)


        self.title_label = QLabel("Налаштування профілю")
        self.title_label.setProperty("type", "title")
        self.title_label.setAlignment(Qt.AlignLeft)
        #self.title_label.setContentsMargins(0, 10, 0, 20)
        #self.layout_settings_form.addRow(title_label)
        self.main_layout.addWidget(self.title_label)#, 0, 0, 1, 1)
        self.setLayout(self.main_layout)


        self.pg_settings = QWidget(self)
        self.pg_settings.setObjectName("pg_settings")
        self.main_layout.addWidget(self.pg_settings)
        self.layout_settings_main = QGridLayout(self.pg_settings)
        


        # Create scroll area
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


        # Add instructions
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
        
        self.name_field = self.add_form_field("Повне ім'я", "Олександр Петренко", "le_name")
        self.email_field = self.add_form_field("Електронна адреса", "oleksandr.petrenko@example.com", "le_email")
        self.phone_field = self.add_form_field("Телефон", "+380501234567", "le_phone")
        self.birthday_field = self.add_form_field("Дата народження", "12.05.2005", "le_birthday")

        # Add another separator
        separator2 = QFrame(self.widget_settings_content)
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #dde2f6;")
        separator2.setFixedHeight(2)
        self.layout_settings_form.addRow(separator2)
        
        # Add section label
        security_label = QLabel("Безпека", self.widget_settings_content)
        security_label.setProperty("type", "page_section")
        security_label.setContentsMargins(0, 10, 0, 10)
        self.layout_settings_form.addRow(security_label)
        
        self.password_field = self.add_password_field("Пароль", "admin123", "le_password")
        
        # Add status message label (hidden by default)
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
        
        # Add space to center the save button
        buttons_layout.addStretch()

        self.btn_save = QPushButton("Зберегти", self.widget_settings_content)
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setMinimumSize(QtCore.QSize(300, 50))
        self.btn_save.setMaximumSize(QtCore.QSize(300, 50))
        self.btn_save.setProperty("type","start_continue")
        self.layout_settings_form.addRow(self.btn_save)

        #self.layout_settings_main.addWidget(self.widget_settings_content)
        self.btn_save.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.btn_save)
        
        # Add space to center the save button
        buttons_layout.addStretch()
        
        self.layout_settings_form.addRow(buttons_widget)
        
        # Set the content widget as the scroll area's widget
        self.scroll_area.setWidget(self.widget_settings_content)
        
        # Add the scroll area to the main layout
        self.layout_settings_main.addWidget(self.scroll_area)
        
        # Try to retrieve real user data
        #self.refresh_user_data()

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
        original_pixmap = QPixmap("icon/icon_users.PNG") #зображення 
        round_pixmap = make_round_pixmap(original_pixmap, QSize(50, 50))
        lb_image.setPixmap(round_pixmap)
        lb_image.setAlignment(Qt.AlignCenter)
        layout_user_greeting.addWidget(lb_image)

        lb_welcome = QLabel("Вітаємо,", widget_user_greeting)
        lb_welcome.setProperty("type", "page_section")
        lb_welcome.setMinimumSize(100, 50)
        lb_welcome.setMaximumSize(100, 50)
        layout_user_greeting.addWidget(lb_welcome)

        self.lb_username = QLabel("Олександр", widget_user_greeting)
        self.lb_username.setProperty("type", "page_section")
        layout_user_greeting.addWidget(self.lb_username)

        self.layout_settings_form.addRow(widget_user_greeting)

    def add_form_field(self, label_text, placeholder_text, obj_name):
        form_group_widget = QWidget(self.widget_settings_content)
        form_group_layout = QHBoxLayout(form_group_widget)
        form_group_layout.setContentsMargins(0, 0, 0, 0)
        form_group_layout.setSpacing(10)
        
        input_field = QLineEdit(self.widget_settings_content)
        input_field.setPlaceholderText(placeholder_text)
        input_field.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        input_field.setFixedHeight(40)  # однакова висота для всіх полів
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

    def _get_value(self, source, key, default=""):
        if not source:
            return default
        if isinstance(source, dict):
            value = source.get(key, default)
        else:
            value = getattr(source, key, default)
        return value if value is not None else default

    def _get_metadata_value(self, source, key):
        metadata = None
        if isinstance(source, dict):
            metadata = source.get("metadata")
        else:
            metadata = getattr(source, "metadata", None)
        if isinstance(metadata, dict):
            return metadata.get(key, "") or ""
        return ""

    def _update_form_fields(self, data):
        if not self.name_field:
            return
        first_name = self._get_value(data, "first_name")
        last_name = self._get_value(data, "last_name")
        username = self._get_value(data, "username")
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()
        if not full_name:
            full_name = username
        email = self._get_value(data, "email")
        phone = self._get_value(data, "phone")
        birthday = self._get_value(data, "birthday")
        if not phone:
            phone = self._get_metadata_value(data, "phone")
        if not birthday:
            birthday = self._get_metadata_value(data, "birthday")
        self.name_field.setText(full_name or "")
        self.email_field.setText(email or "")
        self.phone_field.setText(phone or "")
        self.birthday_field.setText(birthday or "")
        if self.lb_username is not None:
            self.lb_username.setText(full_name or username or "Користувач")

    def refresh_user_data(self):
        try:
            current_user = SessionManager.get_current_user()
            if not current_user:
                self.user_data = None
                self._update_form_fields(None)
                return
            user_id = self._get_value(current_user, "id")
            detailed_user = None
            if user_id:
                try:
                    detailed_user = self.user_service.get_user_by_id(user_id)
                except Exception as e:
                    logger.exception("Помилка отримання даних користувача")
            self.user_data = detailed_user or current_user
            self._update_form_fields(self.user_data)
        except Exception as e:
            logger.exception("Помилка оновлення даних користувача")
            self.user_data = None
            self._update_form_fields(None)

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
        name = self.name_field.text()
        email = self.email_field.text()
        phone = self.phone_field.text()
        birthday = self.birthday_field.text()
        password = self.password_field.text()
        
        if self.user_data and isinstance(self.user_data, dict) and "id" in self.user_data:
            try:
                self.status_label.setText("Налаштування успішно збережено!")
                self.status_label.setStyleSheet("color: #32CD32; font-weight: bold;")
                self.status_label.setVisible(True)
                
                self.password_field.clear()
                
                QtCore.QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
            except Exception as e:
                self.status_label.setText(f"Помилка: {str(e)}")
                self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
                self.status_label.setVisible(True)
                
                QtCore.QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
        else:
            self.status_label.setText("Увійдіть для збереження налаштувань")
            self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            self.status_label.setVisible(True)
            
            QtCore.QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))

    def showEvent(self, event):
        super().showEvent(event)
        logger.debug("Settings page is now visible - refreshing user data")
        
        old_user_data = self.user_data
        self.refresh_user_data()
        
        if old_user_data != self.user_data and self.user_data:
            self.status_label.setText("Дані оновлено")
            self.status_label.setStyleSheet("color: #32CD32; font-weight: bold;")
            self.status_label.setVisible(True)

            QtCore.QTimer.singleShot(2000, lambda: self.status_label.setVisible(False))
