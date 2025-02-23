from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QIcon
from ui.cloudMasking import CloudMasking
# from ui.tab1_sentinel import Tab1Sentinel
# from ui.tab2_super_res import Tab2SuperRes
# from ui.tab3_classification import Tab3Classification

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Palm Tree Classification")
        self.setWindowIcon(QIcon("assets/ugm.png"))
        self.setGeometry(200, 200, 800, 600)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(CloudMasking(self), "Sentinel 2 Cloud Mask")
        # self.tabs.addTab(Tab2SuperRes(self), "Sentinel 2 Super Resolution")
        # self.tabs.addTab(Tab3Classification(self), "Palm Tree Classification")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
