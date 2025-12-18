from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ContentArea(QWidget):
    """A dynamic content area for displaying different pages."""

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)

        self.label = QLabel("Welcome to the Learning Platform!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.label)

    def update_content(self, page_name: str):
        """Update the content label to reflect the current page."""
        self.label.setText(f"Currently Viewing: {page_name}")
