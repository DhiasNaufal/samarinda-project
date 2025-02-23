from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QIcon
from ui.cloudMasking import CloudMasking

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Palm Tree Classification")
        self.setWindowIcon(QIcon("assets/ugm.png"))
        self.setGeometry(200, 200, 800, 600)
        self.load_stylesheet("assets/css/main.qss")
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(CloudMasking(self), "Sentinel 2 Cloud Mask")
        self.tabs.addTab(CloudMasking(self), "Super Resolution")
        self.tabs.addTab(CloudMasking(self), "Klasifikasi Kelapa Sawit")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    def load_stylesheet(self, filename):
        try:
            with open(filename, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print(f"Warning: File {filename} tidak ditemukan.")