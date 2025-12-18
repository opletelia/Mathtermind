from PyQt5.QtWidgets import QWidget, QGridLayout,QVBoxLayout, QLabel,QSizePolicy
from PyQt5 import QtWidgets, QtCore, QtGui
class Page3(QWidget):    
    def create_card(self, title_text="Назва", labels_text=("TextLabel1", "TextLabel2"), desc_text="Опис"):
        
        card = QtWidgets.QWidget()
        card.setMinimumSize(QtCore.QSize(360, 330))
        card.setMaximumSize(QtCore.QSize(360, 330))
        card.setStyleSheet("QWidget { border-radius: 25px; border: 2px solid #e6e6e6; background-color: rgb(255, 255, 255); }")
        card_layout = QtWidgets.QVBoxLayout(card)
    
        title = QtWidgets.QLabel(title_text)
        title.setStyleSheet("font: 75 14pt 'MS Shell Dlg 2';border-color: rgb(255, 255, 255);")
        # Мітки 
        labels = QtWidgets.QHBoxLayout()
        for text in labels_text:
            lb_subject = QtWidgets.QLabel(text)
            lb_subject.setStyleSheet("border-radius: 25px; background-color: #bbebee; border: 2px solid #bbebee;")
            lb_subject.setMinimumSize(QtCore.QSize(165, 50))
            lb_subject.setMaximumSize(QtCore.QSize(165, 50))
            labels.addWidget(lb_subject)
        
        lb_description = QtWidgets.QLabel(desc_text)
        lb_description.setStyleSheet("font: 75 10pt 'MS Shell Dlg 2';border-color: rgb(255, 255, 255);")
        
        stacked_widget = QtWidgets.QStackedWidget()
        stacked_widget.setMaximumSize(QtCore.QSize(16777215, 75))
        stacked_widget.setStyleSheet("border-color: rgb(255, 255, 255);")

        page_start = QtWidgets.QWidget()
        layout_start = QtWidgets.QGridLayout(page_start)

        btn_start = QtWidgets.QPushButton("Start Course")
        btn_start.setMinimumSize(QtCore.QSize(310, 50))
        btn_start.setStyleSheet("border-radius:25px; background: #516ed9; font: 75 15pt 'Bahnschrift'; color: white;")
        
        layout_start.addWidget(btn_start, 0, 0, 1, 1)

        page_start.setLayout(layout_start)

        page_continue = QtWidgets.QWidget()
        layout_continue = QtWidgets.QGridLayout(page_continue)

        btn_continue = QtWidgets.QPushButton("Continue")
        btn_continue.setMinimumSize(QtCore.QSize(310, 50))
        btn_continue.setStyleSheet("border-radius:25px; background: #516ed9; font: 75 15pt 'Bahnschrift'; color: white;")

        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setMinimumSize(QtCore.QSize(310, 20))
        progress_bar.setStyleSheet("QProgressBar {border-radius: 8px;background-color: #f3f3f3;}")
        progress_bar.setMaximum(100)
        progress_bar.setValue(1)
        
        layout_continue.setContentsMargins(0, 0, 0, 0)
        layout_continue.addWidget(btn_continue, 0, 0, 1, 1)
        layout_continue.addWidget(progress_bar, 1, 0, 1, 1)

        page_continue.setLayout(layout_continue)

        stacked_widget.addWidget(page_start)
        stacked_widget.addWidget(page_continue)

        def switch_to_continue():
                stacked_widget.setCurrentWidget(page_continue)

        btn_start.clicked.connect(switch_to_continue)
        card_layout.addWidget(title)
        card_layout.addLayout(labels)
        card_layout.addWidget(lb_description)
        card_layout.addWidget(stacked_widget)
        return card

    def create_section(self, section_title="Розділ", num_cards=4):
        section_widget = QtWidgets.QWidget()
        section_layout = QtWidgets.QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_label = QtWidgets.QLabel(section_title)
        section_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        section_layout.addWidget(section_label)
        cards_container = QtWidgets.QWidget()
        cards_layout = QtWidgets.QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)  
        cards_layout.setAlignment(QtCore.Qt.AlignLeft) 
        for _ in range(num_cards):
                card = self.create_card()
                cards_layout.addWidget(card)
        spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        cards_layout.addItem(spacer)

        section_layout.addWidget(cards_container)
        return section_widget


    def add_new_tab(self, name="Нова вкладка", sections_data=None):
        new_tab = QtWidgets.QWidget()
        new_tab.setObjectName(name)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_area_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(15)
        if sections_data:
            for section_title, num_cards in sections_data:
                section_widget = self.create_section(section_title, num_cards)
                scroll_layout.addWidget(section_widget)
        scroll_area.setWidget(scroll_area_widget)
        tab_layout = QtWidgets.QVBoxLayout(new_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        self.tabWidget_3.addTab(new_tab, name)


    def __init__(self):
        super().__init__()
        self.pg_lessons = QtWidgets.QWidget()
        self.pg_lessons.setObjectName("pg_lessons")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.pg_lessons)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.lb_lessons = QtWidgets.QLabel(self.pg_lessons)
        self.lb_lessons.setText("Уроки")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_lessons.sizePolicy().hasHeightForWidth())
        self.lb_lessons.setSizePolicy(sizePolicy)
        self.lb_lessons.setMinimumSize(QtCore.QSize(0, 50))
        self.lb_lessons.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.lb_lessons.setFont(font)
        self.lb_lessons.setObjectName("lb_lessons")
        self.gridLayout_9.addWidget(self.lb_lessons, 0, 0, 1, 1)
        self.tabWidget_3 = QtWidgets.QTabWidget(self.pg_lessons)
        self.tabWidget_3.setMinimumSize(QtCore.QSize(660, 300))
        self.tabWidget_3.setObjectName("tabWidget_3")
        
        self.gridLayout_9.addWidget(self.tabWidget_3, 2, 0, 1, 1)
        self.lb_choice = QtWidgets.QLabel(self.pg_lessons)
        self.lb_choice.setText("Виберіть урок:")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_choice.sizePolicy().hasHeightForWidth())
        self.lb_choice.setSizePolicy(sizePolicy)
        self.lb_choice.setMinimumSize(QtCore.QSize(0, 50))
        self.lb_choice.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.lb_choice.setFont(font)
        self.lb_choice.setObjectName("lb_choice")
        self.gridLayout_9.addWidget(self.lb_choice, 1, 0, 1, 1)
        self.add_new_tab("Перша вкладка", [
        ("Розділ 1", 3),  
        ("Розділ 2", 5), 
        ("Розділ 3", 2)   
        ])

        self.add_new_tab("Друга вкладка", [
        ("Розділ 1", 4),
        ("Розділ 2", 3)
        ])
        self.setLayout(self.gridLayout_9)