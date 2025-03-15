from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider, QComboBox,QProgressBar,QSizePolicy
from PyQt6.QtCore import Qt
from typing import Optional

from .widgets.file_input_widget import FileInputWidget
from .widgets.button_widget import ButtonWidget
from .widgets.log_widget import LogWidget
from .widgets.dropdown_widget import DropdownWidget
from .widgets.progress_bar_widget import ProgressBarWidget
from .widgets.graphics_view_widget import GraphicsViewWidget
from .widgets.list_widget import ListWidget
from .widgets.frame_widget import FrameWdiget

from utils.enum import LogLevel, FileType
from utils.common import get_filename, get_string_date, get_file_extension

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
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.imageInput = FileInputWidget(
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
        form_layout.addWidget(self.model_dropdown)

        self.start_process = ButtonWidget(name="Mulai Proses Klasifikasi")
        self.start_process.clicked.connect(self.startClassification)
        form_layout.addWidget(self.start_process)


        # classification result frame
        result_frame = FrameWdiget()
        form_layout.addWidget(result_frame)

        title = QLabel("<h3>Hasil Klasifikasi</h3>")
        result_frame.add_widget(title)
        
        sawit_frame = FrameWdiget()
        result_frame.add_widget(sawit_frame.frame)
        sawit_title = QLabel("Luas Kelapa Sawit yang Terdeteksi :")
        sawit_frame.add_widget(sawit_title)
        sawit_total = QLabel("<h1>- Ha</h1>")
        sawit_frame.add_widget(sawit_total)
        
        hor_layout = QHBoxLayout()
        result_frame.add_layout(hor_layout)
        left_layout = QVBoxLayout()
        hor_layout.addLayout(left_layout)
        self.lahan = QLabel("Lahan\t\t- Ha ")
        self.lahan.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        left_layout.addWidget(self.lahan)
        self.urban = QLabel("Urban\t\t- Ha ")
        self.urban.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        left_layout.addWidget(self.urban)

        right_layout = QVBoxLayout()
        hor_layout.addLayout(right_layout)
        self.hutan = QLabel("Hutan\t\t- Ha ")
        self.hutan.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        right_layout.addWidget(self.hutan)
        self.vegetasi = QLabel("Vegetasi\t- Ha ")
        self.vegetasi.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        right_layout.addWidget(self.vegetasi)

        download_shp = ButtonWidget("Download SHP", margin=0)
        result_frame.add_widget(download_shp)
        download_tif = ButtonWidget("Download TIFF", margin=0)
        result_frame.add_widget(download_tif)
        
        # raster or vector layers
        label = QLabel("Layers")
        form_layout.addWidget(label)
        self.layer = ListWidget()
        self.layer.setMinimumHeight(100)
        self.layer.item_changed.connect(lambda name: self.graphics_view.toggle_layer(name))
        form_layout.addWidget(self.layer)

        # Graphics View (Raster or vector)
        self.graphics_view = GraphicsViewWidget()

        # Content Layout (form and graphics)
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(form_layout, 1)
        content_layout.addWidget(self.graphics_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        main_layout.addWidget(self.log_window)

    def add_image_layer(self, filepath):
        layer_name = get_filename(filepath, ext=False)
        self.layer.add_item(layer_name)

        self.graphics_view.load_raster(filepath)
    
    def info(self, filepath: str):
        self.add_image_layer(filepath)
        self.log_window.log_message("TIF berhasil dimuat!")

    def startClassification(self):
        #start
        result_name = f"Hasil - {get_filename(self.imageInput.get_value, ext=False)}-{get_string_date()}.{get_file_extension()}"
        output_path = os.path.join(os.getcwd(), "output", result_name)

        self.log_window.log_message('Memulai Klasifikasi')
        self.classification_thread = ClassificationBgProcess(self.imageInput.get_value, output_path, result_name)

        self.classification_thread.progress.connect(lambda message : self.log_window.log_message(message))
        self.classification_thread.finished.connect(lambda: self.progress_bar2.setVisible(False))
        self.classification_thread.finished.connect(lambda: self.add_image_layer(output_path))
        self.classification_thread.finished.connect(self.classification_thread.deleteLater)
        self.classification_thread.start()

