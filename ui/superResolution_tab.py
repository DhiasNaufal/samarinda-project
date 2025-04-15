import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from typing import Optional

from .widgets.log_widget import LogWidget
from .widgets.button_widget import ButtonWidget
from .widgets.web_viewer_widget import WebViewWidget
from .widgets.message_box_widget import CustomMessageBox, QMessageBox
from .widgets.date_widget import DateWidget
from .widgets.frame_widget import FrameWidget

from utils.common import resource_path
from utils.logger import setup_logger

logger = setup_logger()
class SuperResolution(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.coordinates = None

        self.initUI()

    def initUI(self) -> None:
        """Initialize the second tab (Placeholder for future functionality)."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Web Map View
        self.web_view = WebViewWidget(map_path=resource_path(os.path.join("assets", "super_resolution_map.html")))
        self.web_view.string_received.connect(self.on_coordinate_received)
        layout.addWidget(self.web_view)

        frame = FrameWidget()
        layout.addWidget(frame)

        # Date Widgets
        self.date = DateWidget(label="Pilih Tanggal")
        frame.add_widget(self.date)

        button = ButtonWidget("Mulai")
        button.clicked.connect(self.start_super_resolution)
        frame.add_widget(button)
        
        # Add Log and Watermark
        self.log_window = LogWidget()
        self.log_window.setMinimumHeight(100)
        layout.addWidget(self.log_window)

        pass

    def on_coordinate_received(self, coordinates: str) -> None:
        """Receive coordinates from JavaScript."""
        self.coordinates = coordinates
        logger.info(f"Coordinates received: {self.coordinates}")

    def start_super_resolution(self) -> None:
        """Start the super resolution process."""
        message = CustomMessageBox(
            icon=QMessageBox.Icon.Warning
        )

        if not self.coordinates:
            message.set_message("Silahkan pilih area terlebih dahulu")
            message.show()
            return

        if not self.date.get_date_string():
            message.set_message("Silahkan pilih tanggal terlebih dahulu")
            message.show()
            return

        self.log_window.log_message("Memulai proses super resolusi...")

        self.log_window.log_message(f"Coordinates : {self.coordinates}")
        self.log_window.log_message(f"Date : {self.date.get_date_string()}")