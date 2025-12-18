from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow
from .ui import Ui_MainWindow
from .admin_dashboard import AdminDashboard
class UiWrapper(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.setMinimumSize(1700, 865)  
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


class UiAdminWrapper(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.setMinimumSize(1700, 865)  
        self.ui = AdminDashboard()
        self.ui.init_ui()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
