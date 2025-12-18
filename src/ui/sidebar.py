from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from functools import partial

LOGO_ICON_PATH = "src/ui/assets/icons/white_logo.svg"
PROFILE_ICON_PATH = "src/ui/assets/icons/profile.svg"
SIDEBAR_ICON_SIZE = QSize(24, 24)
LOGO_SIZE = QSize(64, 64)
LOGO_ICON_SIZE = QSize(96, 96)
BUTTON_SIZE = QSize(64, 64)
BUTTON_SPACING = 0
BUTTON_TOP_MARGIN = 80
BUTTON_BOTTOM_MARGIN = 80

ICON_PATHS = {
    "Dashboard": "src/ui/assets/icons/dashboard.svg",
    "Courses": "src/ui/assets/icons/courses.svg",
    "Quiz": "src/ui/assets/icons/quiz.svg"
}

class Sidebar(QWidget):
    def __init__(self, on_button_clicked):
        super().__init__()
        self.on_button_clicked = on_button_clicked
        self._setup_ui()

    def _setup_ui(self):
        """Setup the sidebar layout."""
        self.setLayout(self._create_main_layout())

    def _create_main_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self._create_logo_layout())
        layout.addWidget(self._create_separator())
        layout.addLayout(self._create_button_layout())
        layout.addStretch()
        layout.addLayout(self._create_profile_btn_layout())
        return layout

    def _create_logo_layout(self):
        app_logo = QPushButton()
        app_logo.setIcon(QIcon(LOGO_ICON_PATH))
        app_logo.setIconSize(LOGO_ICON_SIZE)
        app_logo.setFixedSize(LOGO_SIZE)

        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        logo_layout.addWidget(app_logo)
        logo_layout.addStretch()
        return logo_layout
    
    def _create_profile_btn_layout(self):
        profile_btn = QPushButton()
        profile_btn.setIcon(QIcon(PROFILE_ICON_PATH))
        profile_btn.setIconSize(SIDEBAR_ICON_SIZE)
        profile_btn.setFixedSize(BUTTON_SIZE)

        profile_btn_layout = QVBoxLayout()
        profile_btn_layout.addStretch()
        profile_btn_layout.addWidget(profile_btn)
        return profile_btn_layout

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def _create_button_layout(self):
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(BUTTON_SPACING)
        button_layout.setContentsMargins(0, BUTTON_TOP_MARGIN, 0, BUTTON_BOTTOM_MARGIN)

        self.buttons = {}
        for name, icon_path in ICON_PATHS.items():
            button = QPushButton()
            button.setIcon(QIcon(icon_path))
            button.setIconSize(SIDEBAR_ICON_SIZE)
            button.setFixedSize(BUTTON_SIZE)
            button.clicked.connect(partial(self.on_button_clicked, name))
            self.buttons[name] = button
            button_layout.addWidget(button)

        return button_layout
