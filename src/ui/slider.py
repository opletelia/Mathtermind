import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFontMetrics

class RangeSlider(QWidget):
    def __init__(self, min_value=0, max_value=100, start_min=20, start_max=80):
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value
        self._lower_value = start_min
        self._upper_value = start_max
        self._handle_width = 10  # Ширина 
        self._padding = 10       # Відступ 
        self._dragging_handle = None # Яку ручку перетягуємо 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Координати для малювання
        y = self.height() // 2
        x_start = self._padding
        x_end = self.width() - self._padding
        slider_length = x_end - x_start

        # Функція для перетворення значення на координату x
        def value_to_x(value):
            return x_start + slider_length * (value - self.min_value) / (self.max_value - self.min_value)

        lower_x = value_to_x(self._lower_value)
        upper_x = value_to_x(self._upper_value)

        # Малюємо фон повзунка
        track_rect = QRect(x_start, y - 2, slider_length, 4)
        painter.fillRect(track_rect, QBrush(QColor(200, 200, 200)))

        # Малюємо вибраний діапазон
        selected_rect = QRect(int(lower_x), y - 3, int(upper_x - lower_x), 6)
        painter.fillRect(selected_rect, QBrush(QColor(100, 149, 237))) # Cornflower Blue

        # Малюємо нижню ручку
        lower_handle_rect = QRect(int(lower_x - self._handle_width // 2), y - 8, self._handle_width, 16)
        painter.fillRect(lower_handle_rect, QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.drawRect(lower_handle_rect)

        # Малюємо верхню ручку
        upper_handle_rect = QRect(int(upper_x - self._handle_width // 2), y - 8, self._handle_width, 16)
        painter.fillRect(upper_handle_rect, QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.drawRect(upper_handle_rect)

        # Малюємо значення над ручками (опціонально)
        painter.setPen(QPen(Qt.black))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        fm = QFontMetrics(font)

        lower_text = str(self._lower_value)
        lower_text_width = fm.width(lower_text)
        painter.drawText(int(lower_x - lower_text_width // 2), y - 15, lower_text)

        upper_text = str(self._upper_value)
        upper_text_width = fm.width(upper_text)
        painter.drawText(int(upper_x - upper_text_width // 2), y - 15, upper_text)

    def mousePressEvent(self, event):
        y = self.height() // 2
        x_start = self._padding
        x_end = self.width() - self._padding
        slider_length = x_end - x_start

        def value_to_x(value):
            return x_start + slider_length * (value - self.min_value) / (self.max_value - self.min_value)

        lower_x = value_to_x(self._lower_value)
        upper_x = value_to_x(self._upper_value)

        lower_handle_rect = QRect(int(lower_x - self._handle_width // 2), y - 8, self._handle_width, 16)
        upper_handle_rect = QRect(int(upper_x - self._handle_width // 2), y - 8, self._handle_width, 16)

        if lower_handle_rect.contains(event.pos()):
            self._dragging_handle = 'lower'
        elif upper_handle_rect.contains(event.pos()):
            self._dragging_handle = 'upper'
        else:
            self._dragging_handle = None

    def mouseMoveEvent(self, event):
        if self._dragging_handle:
            x = event.pos().x()
            x_start = self._padding
            x_end = self.width() - self._padding
            slider_length = x_end - x_start

            # Перетворення координати x на значення
            def x_to_value(x_pos):
                if x_pos <= x_start:
                    return self.min_value
                elif x_pos >= x_end:
                    return self.max_value
                return self.min_value + (self.max_value - self.min_value) * (x_pos - x_start) / slider_length

            new_value = int(x_to_value(x))

            if self._dragging_handle == 'lower':
                if new_value <= self._upper_value:
                    self._lower_value = new_value
                    self.update()
                    self.valueChanged.emit(self._lower_value, self._upper_value)
            elif self._dragging_handle == 'upper':
                if new_value >= self._lower_value:
                    self._upper_value = new_value
                    self.update()
                    self.valueChanged.emit(self._lower_value, self._upper_value)

    def mouseReleaseEvent(self, event):
        self._dragging_handle = None

    def sizeHint(self):
        return QSize(200, 50)

    def getLowerValue(self):
        return self._lower_value

    def setLowerValue(self, value):
        self._lower_value = max(self.min_value, min(value, self._upper_value))
        self.update()

    def getUpperValue(self):
        return self._upper_value

    def setUpperValue(self, value):
        self._upper_value = min(self.max_value, max(value, self._lower_value))
        self.update()

    valueChanged = pyqtSignal(int, int)

