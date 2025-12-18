from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtProperty
from PyQt5.QtGui import QPainter, QPen, QFont, QColor

class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self._textColor = QColor(Qt.black)  # дефолтний колір

    def set_value(self, value):
        self.value = max(0, min(100, value))
        self.update()

    def getTextColor(self):
        return self._textColor

    def setTextColor(self, color):
        if isinstance(color, (QColor, Qt.GlobalColor)):
            self._textColor = QColor(color)
        else:  # якщо рядок з QSS
            self._textColor = QColor(color)
        self.update()  # перерисувати при зміні

    textColor = pyqtProperty(QColor, getTextColor, setTextColor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outer_rect = self.rect().adjusted(10, 10, -10, -10)
        side = min(outer_rect.width(), outer_rect.height())
        rect = outer_rect
        rect.setWidth(side)
        rect.setHeight(side)
        rect.moveCenter(outer_rect.center())
        center = rect.center()
        radius = side // 2

        # Коло фону
        pen = QPen(QColor(234, 235, 239), 10)
        painter.setPen(pen)
        painter.drawEllipse(center, radius, radius)

        # Дуга прогресу
        if self.value <= 25:
            pen.setColor(QColor(255, 33, 34))
        elif self.value <= 50:
            pen.setColor(QColor(255, 214, 15))
        elif self.value <= 75:
            pen.setColor(QColor(22, 210, 222))
        else:
            pen.setColor(QColor(4, 214, 87))
        painter.setPen(pen)
        painter.drawArc(
            rect,
            -90 * 16,
            int(-self.value * 3.6 * 16)
        )

        # Текст із кольором з QSS
        painter.setPen(QPen(self._textColor))
        painter.setFont(QFont("MS Shell Dlg 2", 16, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{self.value}%")
