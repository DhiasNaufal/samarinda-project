from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QIcon
from ui.cloudMasking import CloudMasking
from ui.superResolution import SuperResolution
from PyQt6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Palm Tree Classification")
        self.setWindowIcon(QIcon("assets/img/ugm.png"))
        self.setGeometry(200, 200, 800, 600)
        self.load_stylesheet("assets/css/main.qss")
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(CloudMasking(self), "Sentinel 2 Cloud Mask")
        self.tabs.addTab(SuperResolution(self), "Super Resolution")
        self.tabs.addTab(CloudMasking(self), "Klasifikasi Kelapa Sawit")

        # Footer
        app_footer = QHBoxLayout()
        app_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer_label = QLabel("© Badan Pertanahan Nasional Kantor Wilayah Kalimantan Timur")
        footer_label.setStyleSheet("font-size: 10px; color: black;")

        app_footer.addWidget(footer_label)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addLayout(app_footer)
        self.setLayout(layout)

    def load_stylesheet(self, filename) -> None:
        try:
            with open(filename, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print(f"Warning: File {filename} tidak ditemukan.")