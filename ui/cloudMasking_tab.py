import json
import os
import ee
import folium

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from shapely.geometry import shape
from typing import Optional

from logic.gee.auth import GEEAuth
from logic.gee.sentinel2_processing import process_sentinel2

from .widgets.log_widget import LogWidget
from .widgets.text_input_widget import TextInputWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.date_widget import DateWidget
from .widgets.slider_widget import SliderWidget
from .widgets.button_widget import ButtonWidget
from .widgets.web_viewer_widget import WebViewWidget
from .widgets.progress_bar_widget import ProgressBarWidget
from .widgets.dynamic_widget import DynamicWidget
from .widgets.message_box_widget import CustomMessageBox, QMessageBox

from utils.enum import LogLevel, FileType, ColorOptions, LayoutDirection
from utils.common import resource_path

from logic.map import Map

class CloudMasking(QWidget):
    def __init__(self, parent : Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # Initialize attributes
        self.geojson_path = None
        self.geometry = None
        self.s2_clipped = None
        self.initUI()
        self.is_authenticated = False

    def initUI(self) -> None:
        main_layout = QVBoxLayout()  
        form_widget = DynamicWidget() 
        form_widget.setFixedWidth(500)
        # form_widget.set 
        # Project Name
        self.project_name = TextInputWidget("Nama Proyek Google Earth Engine:")
        form_widget.add_widget(self.project_name)

        # Authenticate Button
        self.auth_btn = ButtonWidget(name="Autentikasi Akun GEE")
        self.auth_btn.clicked.connect(self.authenticate_gee)
        form_widget.add_widget(self.auth_btn)

        # Load GeoJSON Button
        self.geojson = FileInputWidget(
            label="Dokumen GeoJSON",
            button_name="Muat GeoJSON",
            layout_direction=LayoutDirection.HORIZONTAL.value,
            filetype=[FileType.GEOJSON.value],
            file_dialog_title="Pilih Dokumen GeoJSON"
        )
        self.geojson.path_selected.connect(self.on_geojson_selected)
        form_widget.add_widget(self.geojson)

        # Date Selection
        self.date_layout = QHBoxLayout()
        form_widget.add_layout(self.date_layout)

        self.start_date = DateWidget(
            label="Tanggal Awal:",
            default_value="2024-01-01",
        )
        self.date_layout.addWidget(self.start_date)

        self.end_date = DateWidget(label="Tanggal Akhir:")
        self.date_layout.addWidget(self.end_date)

        # Cloud Probability Slider
        self.max_cloud_prob = SliderWidget(
            label="Probabilitas Awan Maksimum: ",
            default_value=20
        )
        form_widget.add_widget(self.max_cloud_prob)

        progress_bar = ProgressBarWidget()
        progress_bar.setVisible(False)
        form_widget.add_widget(progress_bar)

        # Action Buttons
        self.process_btn = ButtonWidget("Proses Citra Sentinel-2")
        self.process_btn.clicked.connect(self.process_geometry)
        form_widget.add_widget(self.process_btn)

        self.map_btn = ButtonWidget(
            name="Buat Peta", 
            button_color=ColorOptions.LIGHT_GRAY.value,
            button_hover_color=ColorOptions.MEDIUM_GRAY.value,
            button_font_color=ColorOptions.MEDIUM_BLUE.value)
        self.map_btn.clicked.connect(self.generate_map)
        form_widget.add_widget(self.map_btn)

        self.export_btn = ButtonWidget("Ekspor Gambar")
        self.export_btn.clicked.connect(self.export_image)
        form_widget.add_widget(self.export_btn)

        # Web Map View
        self.web_view = WebViewWidget(map_path=resource_path(os.path.join("assets", "cloud_mask_map.html")))
        # self.web_view = WebViewWidget(map_url="http://localhost:8000/assets/cloud_mask_map.html")
        self.web_view.setMinimumWidth(500)
        self.web_view.geojson_generated.connect(self.on_received_geojson)

        # Set Web Channel ke Web View
        content_layout = QHBoxLayout()
        content_layout.addWidget(form_widget, 1)
        content_layout.addWidget(self.web_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        self.log_window.setMinimumHeight(100)
        self.log_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.log_window)
        
        # set layout
        self.setLayout(main_layout)  
        # Tambahkan web_view ke layout 
        
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

    def on_received_geojson(self, geojson: dict) -> None:
        if not self.is_authenticated:
            message = CustomMessageBox(
                message="Data gagal dimuat. Mohon lakukan \"Autentikasi Akun GEE\" terlebih dahulu dan hapus Polygon yang telah dibuat pada Peta",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return

        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log_window.log_message("Polygon Terbentuk!")

    def on_geojson_selected(self, file_path: str) -> None:
        if not self.is_authenticated:
            message = CustomMessageBox(
                message="Data gagal dimuat. Mohon lakukan \"Autentikasi Akun GEE\" terlebih dahulu",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return
        
        if file_path:
            self.geojson_path = file_path

            with open(file_path, "r") as f:
                geojson = json.load(f)

            if "features" in geojson and len(geojson["features"]) > 0:
                self.geom = geojson["features"][0]["geometry"]
                self.geometry = ee.Geometry(self.geom)
                self.log_window.log_message("GeoJSON berhasil dimuat!")
            else:
                self.log_window.log_message("Dokumen bukan merupakan file GeoJson")
    
    def handle_auth_finished(self, message, log_level):
        self.log_window.log_message(message, log_level)
        if log_level == LogLevel.NONE.value:
            self.is_authenticated = True

    def authenticate_gee(self) -> None:
        project_name = self.project_name.get_value.strip()

        if not project_name:
            mesage = CustomMessageBox(
                message="Mohon Masukan Nama Proyek Google Earth Engine!",
                icon=QMessageBox.Icon.Warning
            )
            mesage.show()
            return
        
        self.GEE_auth_thread = GEEAuth(project_name)
        self.GEE_auth_thread.started.connect(self.disable_except) # disable all widgets
        self.GEE_auth_thread.finished.connect(self.handle_auth_finished)
        self.GEE_auth_thread.finished.connect(self.GEE_auth_thread.deleteLater)
        self.GEE_auth_thread.finished.connect(self.enable_all)
        self.GEE_auth_thread.start()

    def process_geometry(self) -> None:
        """Process Sentinel-2 data."""
        message = CustomMessageBox(
            icon=QMessageBox.Icon.Warning
        )
        if not self.project_name.get_value:
            message.set_message("Mohon lakukan \"Autentikasi Akun GEE\" terlebih dahulu!")
            message.show()
            return
        
        if not self.geometry:
            message.set_message("Tidak ada dokumen GeoJSON yang dibuat!")
            message.show()
            return

        if not self.project_name.get_value:
            message.set_message("Masukan nama proyek terlebih dahulu!")
            message.show()
            return
        
        if self.start_date.get_date() > self.end_date.get_date():
            message.set_message("Tanggal tidak valid. Tanggal akhir harus lebih baru daripada tanggal awal")
            message.show()
            return

        self.log_window.log_message("Memproses citra Sentinel-2 ...")

        self.s2_clipped = process_sentinel2(
            self.geometry, 
            self.start_date.get_date_string(), 
            self.end_date.get_date_string(), 
            self.max_cloud_prob.get_value)
        self.log_window.log_message("Proses citra Sentinel-2 berhasil!")
    
    def generate_map(self) -> None:
        """Generate and display map with Sentinel-2 imagery."""
        if not self.s2_clipped:
            message = CustomMessageBox(
                message="Proses Citra Sentinel-2 terlebih dahulu!",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return

        self.log_window.log_message("Membuat Peta...")

        # Calculate center of ROI
        shapely_geom = shape(self.geom)
        minx, miny, maxx, maxy = shapely_geom.bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]

        # Create Map
        self.map = Map(location=center)
        self.map.add_ee_layer(self.s2_clipped)
        self.map.add_roi_layer(self.geom)
        self.map.save_and_open_map("sentinel_map.html")

        self.log_window.log_message("Peta berhasil dibuat!")

    def export_image(self) -> None:
        """"Export processed Sentinel-2 image."""
        if not self.s2_clipped:
            message = CustomMessageBox(
                message="Proses Citra Sentinel-2 terlebih dahulu!",
                icon=QMessageBox.Icon.Warning
            )
            message.show()
            return

        task = ee.batch.Export.image.toDrive(
            image=self.s2_clipped, description="Sentinel2_Export", folder="GEE_Exports",
            scale=10, region=self.geometry, crs="EPSG:4326", fileNamePrefix="Sentinel2_Export", maxPixels=1e13
        )
        
        task.start()
        self.log_window.log_message("Proses Ekspor dimulai. Silahkan periksa Drive Google anda.")
