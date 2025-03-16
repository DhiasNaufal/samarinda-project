from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider, QComboBox,QProgressBar,QSizePolicy
from PyQt6.QtCore import Qt
from typing import Optional

# from .widgets.text_input_widget import TextInputWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.button_widget import ButtonWidget
from .widgets.log_widget import LogWidget
from .widgets.web_viewer_widget import WebViewWidget
from .widgets.dropdown_widget import DropdownWidget
from .widgets.progress_bar_widget import ProgressBarWidget

from utils.enum import LogLevel, FileType
from utils.common import get_filename, get_string_date, get_file_extension

from logic.classification.classificationBg import ClassificationBgProcess

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
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.project_name = QLabel("Klasifikasi Kelapa Sawit")
        stylesheet = f"""
            QLabel {{
                {f'margin: 10px;'}
            }}
        """
        self.project_name.setStyleSheet(stylesheet)
        form_layout.addWidget(self.project_name)

        self.imageInput = FileInputWidget(
            # label="Klasifikasi Kelapa Sawit",
            button_name="Muat Gambar",
            filetype=FileType.TIFF.value,
            file_dialog_title="Pilih Dokumen TIF"
        )

        self.imageInput.path_selected.connect(self.info)
        form_layout.addWidget(self.imageInput)
  
        self.model_dropdown = DropdownWidget(
            label="Pilih Model",
            dropdown_options=["U-Net", "MVT", "ResNet"]
        )
        # self.label = QLabel("Select Model")
        # form_layout.addWidget(self.label)
        # self.model_dropdown = QComboBox()
        # self.model_dropdown.addItems(["U-Net", "MVT", "ResNet"])
        form_layout.addWidget(self.model_dropdown)
        # stylesheet = f"""
        #     QComboBox {{
        #         {f'margin: 10px;'}
        #     }}
        # """
        # self.setStyleSheet(stylesheet)

        self.start_process = ButtonWidget(name="Mulai Proses Klasifikasi")
        self.start_process.clicked.connect(self.startClassification)
        form_layout.addWidget(self.start_process)

        self.progress_bar2 = QProgressBar()
        form_layout.addWidget(self.progress_bar2, stretch=1)
        self.progress_bar2.setVisible(False)

        self.progress_bar = ProgressBarWidget(self)
        self.progress_bar.setVisible(True)
        form_layout.addWidget(self.progress_bar)

        # Map View
        self.web_view = WebViewWidget(map_url="http://localhost:8000/assets/classification_map.html")

        # Content Layout (form and map)
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(form_layout, 1)
        content_layout.addWidget(self.web_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        main_layout.addWidget(self.log_window)
    
    
    def info(self, filepath: str):
        self.web_view.add_raster(get_filename(filepath), path="data")
        self.log_window.log_message("TIF berhasil dimuat!")

    def startClassification(self):
        #start
        result_name = f"{get_filename(self.imageInput.get_value, ext=False)}-{get_string_date()}.{get_file_extension()}"

        self.log_window.log_message('Memulai Klasifikasi')
        # ClassificationBgProcess(self.imageInput.get_value)
        self.classification_thread = ClassificationBgProcess(self.imageInput.get_value, result_name)
        self.progress_bar2.setMinimum(0)
        self.progress_bar2.setMaximum(0)  # Indeterminate mode
        self.progress_bar2.setVisible(True)
        # end
        self.classification_thread.progress.connect(lambda message : self.log_window.log_message(message))
        self.classification_thread.finished.connect(lambda: self.progress_bar2.setVisible(False))
        self.classification_thread.finished.connect(lambda: self.web_view.add_raster(result_name))
        # self.classification_thread.finished.connect(lambda: self.auth_btn.setEnabled(True))
        self.classification_thread.finished.connect(self.classification_thread.deleteLater)
        self.classification_thread.start()

        # # self.auth_btn.setEnabled(False)

