from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider, QComboBox,QProgressBar,QSizePolicy
from typing import Optional

# from .widgets.text_input_widget import TextInputWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.button_widget import ButtonWidget
from .widgets.log_widget import LogWidget
from .widgets.web_viewer_widget import WebViewWidget

from utils.enum import LogLevel, FileType
from utils.common import get_filename

from logic.classificationBg import ClassificationBgProcess

import json
import os
# from predict import main

os.environ["SM_FRAMEWORK"] = "tf.keras"
class Classification(QWidget):
    def __init__(self, parent : Optional[QWidget] = None) -> None:
        super().__init__(parent)
        os.environ["SM_FRAMEWORK"] = "tf.keras"
        self.initUI()
        self.calculate_temp = 0

    def initUI(self):
        # set main layout
        main_layout = QVBoxLayout(self)

        form_layout = QVBoxLayout()
        self.project_name = QLabel("Klasifikasi Kelapa Sawit")
        form_layout.addWidget(self.project_name)

        self.imageInput = FileInputWidget(
            button_name="Muat Gambar",
            filetype=FileType.TIFF.value,
            file_dialog_title="Pilih Dokumen TIF"
        )

        self.imageInput.path_selected.connect(self.info)
        form_layout.addWidget(self.imageInput)

  
        self.project_name = QLabel("Select Model")
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["U-Net", "MVT", "ResNet"])
        form_layout.addWidget(self.model_dropdown)
        stylesheet = f"""
            QComboBox {{
                {f'margin: 10px;'}
            }}
        """
        self.setStyleSheet(stylesheet)
        self.start_process = ButtonWidget(name="Mulai Proses Klasifikasi")
        self.start_process.clicked.connect(self.startClassification)
        form_layout.addWidget(self.start_process)

        self.progress_bar = QProgressBar()
        form_layout.addWidget(self.progress_bar)
        self.progress_bar.setVisible(False)

        # Map View
        self.web_view = WebViewWidget(map_url="http://localhost:8000/assets/classification_map.html")

        # Content Layout (form and map)
        content_layout = QHBoxLayout()
        content_layout.addLayout(form_layout, 1)
        content_layout.addWidget(self.web_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        main_layout.addWidget(self.log_window)
    
    
    def info(self, filepath: str):
        self.web_view.add_raster(get_filename(filepath))
        self.log_window.log_message("TIF berhasil dimuat!")

    def startClassification(self):
        #start

        self.log_window.log_message('Memulai Klasifikasi')
        # ClassificationBgProcess(self.imageInput.get_value)
        self.GEE_auth_thread = ClassificationBgProcess(self.imageInput.get_value)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        self.progress_bar.setVisible(True)
        # end
        self.GEE_auth_thread.progress.connect(lambda message : self.log_window.log_message(message))
        self.GEE_auth_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.GEE_auth_thread.finished.connect(lambda: self.web_view.add_raster("res.tif"))
        # self.GEE_auth_thread.finished.connect(lambda: self.auth_btn.setEnabled(True))
        # self.GEE_auth_thread.finished.connect(self.GEE_auth_thread.deleteLater)
        self.GEE_auth_thread.start()

        # # self.auth_btn.setEnabled(False)

