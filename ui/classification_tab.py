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
from .widgets.frame_widget import FrameWidget
from .widgets.message_box_widget import CustomMessageBox, QMessageBox
from .widgets.dynamic_widget import DynamicWidget

from utils.enum import LogLevel, FileType, FileInputType
from utils.common import get_filename, get_string_date, get_file_extension

from logic.classification.classificationBg import ClassificationBgProcess
from logic.classification.process_result import ProcessResult, save_vector, save_geotiff

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
        self.temp_output_path = None

    def initUI(self):
        # set main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = DynamicWidget()
        form_layout.setFixedWidth(500)

        self.imageInput = FileInputWidget(
            label="Dokumen Gambar",
            button_name="Muat Gambar",
            filetype=FileType.TIFF.value,
            file_dialog_title="Pilih Dokumen TIF"
        )
        self.imageInput.path_selected.connect(self.info)
        form_layout.add_widget(self.imageInput)
  
        self.model_dropdown = DropdownWidget(
            label="Pilih Model",
            dropdown_options=["U-Net", "MVT", "ResNet"]
        )
        form_layout.add_widget(self.model_dropdown)

        self.start_process = ButtonWidget(name="Mulai Proses Klasifikasi")
        self.start_process.clicked.connect(self.startClassification)
        form_layout.add_widget(self.start_process)

        self.progress_bar = ProgressBarWidget()
        self.progress_bar.setVisible(False)
        form_layout.add_widget(self.progress_bar)

        # classification result frame
        result_frame = FrameWidget()
        form_layout.add_widget(result_frame)

        title = QLabel("<h3>Hasil Klasifikasi</h3>")
        result_frame.add_widget(title)
        
        sawit_frame = FrameWidget()
        result_frame.add_widget(sawit_frame.frame)
        sawit_title = QLabel("Luas Kelapa Sawit yang Terdeteksi :")
        sawit_frame.add_widget(sawit_title)
        self.palmoil = QLabel("<h1>- m2</h1>")
        sawit_frame.add_widget(self.palmoil)
        
        hor_layout = QHBoxLayout()
        result_frame.add_layout(hor_layout)
        left_layout = QVBoxLayout()
        hor_layout.addLayout(left_layout)
        self.ground = QLabel("Lahan\t\t- m2 ")
        self.ground.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        left_layout.addWidget(self.ground)
        self.urban = QLabel("Urban\t\t- m2 ")
        self.urban.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        left_layout.addWidget(self.urban)

        right_layout = QVBoxLayout()
        hor_layout.addLayout(right_layout)
        self.hutan = QLabel("Hutan\t\t- m2 ")
        self.hutan.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        right_layout.addWidget(self.hutan)
        self.vegetation = QLabel("Vegetasi\t- m2 ")
        self.vegetation.setStyleSheet("border: 1px solid lightgray; padding: 2px")
        right_layout.addWidget(self.vegetation)

        download_shp = FileInputWidget(
            button_name="Download SHP", 
            filetype=FileType.SHP.value,
            file_input_type=FileInputType.FILENAME.value)
        download_shp.path_selected.connect(lambda path: save_vector(self.result["gdf"], path))
        result_frame.add_widget(download_shp)
        download_tif = FileInputWidget(
            button_name="Download TIFF", 
            filetype=FileType.TIFF.value,
            file_input_type=FileInputType.FILENAME.value)
        download_tif.path_selected.connect(lambda path: save_geotiff(self.result["meta"], self.result["class_array"], path))
        result_frame.add_widget(download_tif)
        download_geojson = FileInputWidget(
            button_name="Download GeoJSON", 
            filetype=FileType.GEOJSON.value,
            file_input_type=FileInputType.FILENAME.value)
        download_geojson.path_selected.connect(lambda path: save_vector(self.result["gdf"], path))
        result_frame.add_widget(download_geojson)
        
        # raster or vector layers
        label = QLabel("Layers")
        form_layout.add_widget(label)
        self.layer = ListWidget()
        # self.layer.setFixedHeight(100)
        self.layer.item_changed.connect(lambda name: self.graphics_view.toggle_layer(name))
        form_layout.add_widget(self.layer)

        # Graphics View (Raster or vector)
        self.graphics_view = GraphicsViewWidget()
        self.graphics_view.setMinimumWidth(500)

        # Content Layout (form and graphics)
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_layout.addWidget(form_layout, 1)
        content_layout.addWidget(self.graphics_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        # self.log_window.setFixedHeight(200)
        main_layout.addWidget(self.log_window)

    def add_image_layer(self, filepath):
        layer_name = get_filename(filepath, ext=False)
        self.layer.add_item(layer_name)

        self.graphics_view.load_raster(filepath)
    
    def remove_image_layer(self, layer_name):
        self.layer.remove_item(layer_name)
        self.graphics_view.remove_raster(layer_name)
    
    def info(self, filepath: str):
        # remove all existing data on the qgraphicsview and layer lists
        self.graphics_view.clear_data()
        self.layer.clear_data()
        self.temp_output_path = None

        # Add new layer
        self.imageInput.set_label(f"Dokumen Gambar : {filepath}")
        self.add_image_layer(filepath)
        self.log_window.log_message("TIF berhasil dimuat!")

    def process_result(self, result):
        self.add_image_layer(self.temp_output_path)

        self.result = result
        for label, area in result["total_area"].items():
            if label == "ground":
                self.ground.setText(f"Lahan\t\t {area:.2f} m2")
            elif label == "hutan":
                self.hutan.setText(f"Hutan\t\t {area:.2f} m2")
            elif label == "urban":
                self.urban.setText(f"Urban\t\t {area:.2f} m2")
            elif label == "vegetation":
                self.vegetation.setText(f"Vegetasi\t {area:.2f} m2")
            elif label == "palmoil":
                self.palmoil.setText(f"<h1>{area:.2f} m2</h1>")

    def startClassification(self):
        if self.imageInput.get_value == "":
            message = CustomMessageBox(
                parent=self,
                title="Warning",
                message="Mohon untuk memilih Gambar terlebih dahulu",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return

        if self.model_dropdown.get_value != "U-Net":
            message = CustomMessageBox(
                parent=self,
                title="Warning",
                message=f"Model {self.model_dropdown.get_value} saat ini belum tersedia",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return
        
        # Remove current result if exists
        if self.temp_output_path is not None:
            name = get_filename(self.temp_output_path, ext=False)
            self.remove_image_layer(name)

        #start
        result_name = f"Hasil - {get_filename(self.imageInput.get_value, ext=False)}-{get_string_date()}.png"
        self.temp_output_path = os.path.join(os.getcwd(), "data", result_name)

        self.log_window.log_message('Memulai Klasifikasi')
        self.classification_thread = ClassificationBgProcess(self.imageInput.get_value, self.temp_output_path, result_name)

        self.classification_thread.started.connect(lambda: self.progress_bar.setVisible(True))
        self.classification_thread.progress.connect(lambda message : self.log_window.log_message(message))
        # self.classification_thread.result.connect(lambda: self.add_image_layer(self.temp_output_path))
        self.classification_thread.result.connect(self.process_result)
        self.classification_thread.finished.connect(self.classification_thread.deleteLater)
        self.classification_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.classification_thread.start()

