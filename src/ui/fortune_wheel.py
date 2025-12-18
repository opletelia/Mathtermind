
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QTransform
import random
import os


class FortuneWheel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Колесо фортуни")
        self.setFixedSize(400, 550)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Натисни, щоб крутити колесо!")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.label)

        base_path = os.path.dirname(os.path.abspath(__file__))
        wheel_path = os.path.join(base_path, "icon/wheel2.png")

        self.pixmap_original = QPixmap(wheel_path)
        self.angle = 0 

        self.wheel_label = QLabel()
        self.wheel_label.setFixedSize(300, 300)
        self.wheel_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wheel_label)

        self.update_wheel()

        self.spin_btn = QPushButton("Крутити колесо")
        self.spin_btn.setProperty("type", "start_continue")
        self.spin_btn.setFixedSize(200, 50)
        self.spin_btn.clicked.connect(self.spin)
        layout.addWidget(self.spin_btn, alignment=Qt.AlignCenter)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px; color: #6c9dfd;")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_step)
        self.speed = 0
        self.rewards = ["+5 балів", "+10 монет",
                        "Бейдж 'Молодець!'", "Нічого :(",
                        "+1 підказка", "Додаткове життя"]

    def update_wheel(self):
        transform = QTransform().rotate(self.angle)
        rotated = self.pixmap_original.transformed(transform, Qt.SmoothTransformation)
        self.wheel_label.setPixmap(
            rotated.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def spin(self):
        self.spin_btn.setEnabled(False)
        self.speed = random.uniform(20, 35)  

        self.timer.start(30) 

    def rotate_step(self):
        self.angle = (self.angle + self.speed) % 360
        self.update_wheel()

        self.speed *= 0.97  

        if self.speed < 0.2:  
            self.timer.stop()
            self.finish_spin()

    def finish_spin(self):
        sector_angle = 360 / len(self.rewards)
        index = int(self.angle // sector_angle)
        result = self.rewards[index]

        self.label.setText(result)
        self.result_label.setText(f"Виграш: {result}")

        QMessageBox.information(self, "Результат", f"Тобі випало: {result}")

        self.spin_btn.setEnabled(True)
