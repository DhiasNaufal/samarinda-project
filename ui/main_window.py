from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QIcon
from ui.cloudMasking_tab import CloudMasking
from ui.satellite_image_tab import SatelliteImage
from ui.superResolution_tab import SuperResolution
from ui.classification_tab import Classification
from ui.under_development import UnderDevelopment
from PyQt6.QtCore import Qt
import os

from utils.common import resource_path
from utils.logger import setup_logger

logger = setup_logger()
class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Palm Tree Classification")
        self.setWindowIcon(QIcon(resource_path(os.path.join("assets", "img", "ugm.png"))))
        self.setGeometry(200, 30, 1000, 400)
        self.load_stylesheet(resource_path(os.path.join("assets", "css", "main.qss")))
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(CloudMasking(self), "Sentinel 2 Cloud Mask")
        self.tabs.addTab(SatelliteImage(self), "Citra Satelit")
        self.tabs.addTab(SuperResolution(self), "Super Resolution")
        self.tabs.addTab(Classification(self), "Klasifikasi Kelapa Sawit")
        layout.addWidget(self.tabs)
        # self.tabs.setCurrentIndex(3)

        # add tabs event handler
        self.tabs.tabBarClicked.connect(self.handle_clicked_tab)
		# Define stylesheets for individual tab buttons (adjust colors as needed)
        self.tabs.tabBar().setStyleSheet("""
            QTabBar::tab {
                background-color: #B6B6B6;
                color: black
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #017FA7;
                color: white;
                border: none;
            }
        """)

        # Footer
        app_footer = QHBoxLayout()
        app_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(app_footer)

        footer_label = QLabel("© Badan Pertanahan Nasional Kantor Wilayah Kalimantan Timur")
        footer_label.setStyleSheet("font-size: 10px; color: black;")

        app_footer.addWidget(footer_label)

        # self.setLayout(layout)

    def handle_clicked_tab(self, index):
        # Get the currently selected tab index
        selected_tab_index = self.tabs.currentIndex()

        # Define stylesheets for different tab states (adjust colors as needed)
        default_style = "background-color: white;"
        selected_style = "background-color: lightblue;"  # Color for selected tab

        # Set the stylesheet based on selected tab index
        if selected_tab_index == index:
            self.tabs.setStyleSheet(selected_style)
        else:
            self.tabs.setStyleSheet(default_style)

    def load_stylesheet(self, filename) -> None:
        try:
            with open(filename, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            logger.warning(f"Warning: File {filename} tidak ditemukan.")
        except PermissionError:
            logger.critical(f"Error: Akses dibatasi untuk file : {filename}")
