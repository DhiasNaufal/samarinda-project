from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
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
from logic.classification.save_worker import SaveWorker
from logic.sentinel_classification.sentinel_image_classification import SentinelImageClassification
from logic.sentinel_classification.save_worker import SentinelImageSaveWorker

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
            filetype=[FileType.TIFF.value],
            file_dialog_title="Pilih Dokumen TIF"
        )
        self.imageInput.path_selected.connect(self.info)
        form_layout.add_widget(self.imageInput)
  
        self.model_dropdown = DropdownWidget(
            label="Sumber Gambar",
            dropdown_options=["Citra Satelit", "Sentinel 2", "UAV"]
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
            filetype=[FileType.SHP.value],
            file_input_type=FileInputType.FILENAME.value)
        download_shp.path_selected.connect(self.download_shp)
        
        result_frame.add_widget(download_shp)
        download_tif = FileInputWidget(
            button_name="Download TIFF", 
            filetype=[FileType.TIFF.value],
            file_input_type=FileInputType.FILENAME.value)
        download_tif.path_selected.connect(self.download_tif)
        result_frame.add_widget(download_tif)
        # download_geojson = FileInputWidget(
        #     button_name="Download GeoJSON", 
        #     filetype=[FileType.GEOJSON.value],
        #     file_input_type=FileInputType.FILENAME.value)
        # download_geojson.path_selected.connect(
        #     lambda path: self._start_worker(worker_type="download", mode="vector", output_path=path, gdf=self.result["gdf"]))
        # result_frame.add_widget(download_geojson)
        
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

    def disable_except(self, exceptions: list[QWidget] = []) -> None:
        def is_in_exception_tree(widget: QWidget) -> bool:
            for ex in exceptions:
                current = widget
                while current is not None:
                    if current is ex:
                        return True
                    current = current.parentWidget()
            return False

        for child in self.findChildren(QWidget):
            if not is_in_exception_tree(child):
                child.setDisabled(True)

    def enable_all(self) -> None:
        for child in self.findChildren(QWidget):
            child.setEnabled(True)

    def default_area(self):
        self.ground.setText("Lahan\t\t - m2")   
        self.hutan.setText("Hutan\t\t - m2")
        self.urban.setText("Urban\t\t - m2")
        self.vegetation.setText("Vegetasi\t - m2")
        self.palmoil.setText("<h1>- m2</h1>")

    def add_image_layer(self, filepath: str = "", **kwargs):
        if filepath:
            layer_name = get_filename(filepath, ext=False)
            self.layer.add_item(layer_name)

            self.graphics_view.load_raster(path=filepath)
        else:
            self.layer.add_item(kwargs.get("layer_name"))
            self.graphics_view.load_raster(cv_image=kwargs.get("image"), layer=kwargs.get("layer_name"))

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

        # set all area to -
        self.default_area()

    def download_shp(self, path):
        if self.model_dropdown.get_value == "Citra Satelit":
            self._start_worker(
                worker_type="download", 
                mode="vector", 
                output_path=path, 
                gdf=self.result["gdf"])
        elif self.model_dropdown.get_value == "Sentinel 2":
            self._start_worker(
                worker_type="download", 
                mode="vector", 
                output_path=path, 
                reference_tif=self.imageInput.get_value,  
                class_array=self.result["class_array"])
    
    def download_tif(self, path):
        if self.model_dropdown.get_value == "Citra Satelit":
            self._start_worker(
                worker_type="download", 
                mode="raster", 
                output_path=path, 
                meta=self.result["meta"], 
                class_array=self.result["class_array"])
        elif self.model_dropdown.get_value == "Sentinel 2":
            self._start_worker(
                worker_type="download", 
                mode="raster", 
                output_path=path, 
                reference_tif=self.imageInput.get_value,  
                class_array=self.result["class_array"])

    def process_result(self, result):
        params = {
            "layer_name": get_filename(self.temp_output_path, ext=False),
            "image": result["image"]
        }
        self.add_image_layer(**params)

        self.result = result
        if result["total_area"] is None:
            return
        
        # set area to label
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

        if self.model_dropdown.get_value == "UAV":
            message = CustomMessageBox(
                parent=self,
                title="Warning",
                message=f"Model untuk sumber gambar {self.model_dropdown.get_value} saat ini belum tersedia",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return
        
        # Remove current result if exists
        if self.temp_output_path is not None:
            name = get_filename(self.temp_output_path, ext=False)
            self.remove_image_layer(name)

        # set all area to -
        self.default_area()

        # set output path
        output_path = os.path.join(os.getcwd(), "data")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        result_name = f"Hasil - {get_filename(self.imageInput.get_value, ext=False)}-{get_string_date()}.png"
        self.temp_output_path = os.path.join(output_path, result_name)

        self.log_window.log_message('Memulai Klasifikasi')

        # start classification process
        if self.model_dropdown.get_value == "Citra Satelit":
            self._start_worker(worker_type="classification", image_path = self.imageInput.get_value, output_path = self.temp_output_path, result_name = result_name)
        elif self.model_dropdown.get_value == "Sentinel 2":
            self._start_worker(worker_type="classification", image_path = self.imageInput.get_value)   
 
    def _start_worker(self, worker_type="", **kwargs):
        if worker_type == "classification":
            if self.model_dropdown.get_value == "Citra Satelit":
                self.qthread = ClassificationBgProcess(**kwargs)
            elif self.model_dropdown.get_value == "Sentinel 2":
                self.qthread = SentinelImageClassification(**kwargs)
        elif worker_type == "download":
            if self.model_dropdown.get_value == "Citra Satelit":
                self.qthread = SaveWorker(**kwargs)
            elif self.model_dropdown.get_value == "Sentinel 2":
                self.qthread = SentinelImageSaveWorker(**kwargs)
        else:
            self.log_window.log_message("Invalid worker type")
            return
        
        self.qthread.started.connect(lambda: self.progress_bar.setVisible(True))
        self.qthread.started.connect(lambda: self.progress_bar.set_progress_range())
        self.qthread.started.connect(lambda: self.disable_except([self.log_window]))

        if worker_type == "classification":
            self.qthread.progress.connect(lambda message : self.log_window.log_message(message))
            self.qthread.result.connect(self.process_result)

        self.qthread.error.connect(lambda error_msg: self.log_window.log_message(f"Error : {error_msg}", level=LogLevel.ERROR.value))
        
        self.qthread.finished.connect(self.qthread.deleteLater)
        self.qthread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.qthread.finished.connect(lambda: self.enable_all())
        self.qthread.start()