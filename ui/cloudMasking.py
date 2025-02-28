import json
import os
import ee
import webbrowser
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QDate, Qt
from gee.auth import authenticate_and_initialize
from gee.sentinel2_processing import process_sentinel2
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import folium
from shapely.geometry import shape
from PyQt6.QtCore import pyqtSlot
from gee.auth import authenticate_gee

from .widgets.log_widget import LogWidget
from .widgets.text_input_widget import TextInputWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.date_widget import DateWidget
from .widgets.slider_widget import SliderWidget
from .widgets.button_widget import ButtonWidget
from .widgets.web_viewer_widget import WebViewWidget

from utils.enum import LogLevel, FileType

class CloudMasking(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        # Initialize attributes
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.s2_clipped = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  
        form_layout = QVBoxLayout()  
        # Project Name
        self.project_name = TextInputWidget("Nama Proyek Google Earth Engine:")
        form_layout.addWidget(self.project_name)

        # Authenticate Button
        self.auth_btn = ButtonWidget("Autentikasi Akun GEE")
        self.auth_btn.clicked.connect(self.authenticate_gee)
        form_layout.addWidget(self.auth_btn)

        # Load GeoJSON Button
        self.geojson = FileInputWidget(
            label="Dokumen GeoJSON",
            button_name="Muat GeoJSON",
            filetype=FileType.GEOJSON.value,
            file_dialog_title="Pilih Dokumen GeoJSON"
        )
        self.geojson.path_selected.connect(self.on_geojson_selected)
        form_layout.addWidget(self.geojson)

        # Date Selection
        self.date_layout = QHBoxLayout()
        form_layout.addLayout(self.date_layout)

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
        form_layout.addWidget(self.max_cloud_prob)

        # Action Buttons
        self.process_btn = ButtonWidget("Proses Citra Sentinel-2")
        self.process_btn.clicked.connect(self.process_geometry)
        form_layout.addWidget(self.process_btn)

        self.map_btn = ButtonWidget("Buat Peta")
        self.map_btn.clicked.connect(self.generate_map)
        form_layout.addWidget(self.map_btn)

        self.export_btn = ButtonWidget("Ekspor Gambar")
        self.export_btn.clicked.connect(self.export_image)
        form_layout.addWidget(self.export_btn)

        # Web Map View
        self.web_view = WebViewWidget(map_path=os.path.join(os.getcwd(), "map.html"))
        self.web_view.geojson_generated.connect(self.on_received_geojson)

        # Set Web Channel ke Web View
        content_layout = QHBoxLayout()
        content_layout.addLayout(form_layout, 1)
        content_layout.addWidget(self.web_view, 2)
        main_layout.addLayout(content_layout)

        self.log_window = LogWidget()
        self.log_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.log_window)
        
        # set layout
        self.setLayout(main_layout)  
        # Tambahkan web_view ke layout 
        
    def on_received_geojson(self, geojson: dict):
        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log_window.log_message("Polygon Terbentuk!")
    
    def authenticate_gee(self):
        self.project = self.project_name.get_value.strip()

        if not self.project:
            self.log_window.log_message("Tolong Masukan Nama Proyek Google Earth Engine!", LogLevel.ERROR.value)
            return
        try:
            authenticate_and_initialize(self.project)
            self.log_window.log_message(f"Terautentikasi dengan projek: {self.project}")
        except Exception as e:
            self.log_window.log_message(f"Autentikasi gagal: {str(e)}")

    def on_geojson_selected(self, file_path: str):
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

    def process_geometry(self):
        """Process Sentinel-2 data."""
        if not self.project:
            self.log_window.log_message("Tolong lakukan autentikasi terlebih dahulu!", LogLevel.ERROR.value)
            return
        
        if not self.geometry:
            self.log_window.log_message("Tidak ada dokumen GeoJSON yang dibuat!", LogLevel.ERROR.value)
            return

        project_name = self.project_name.get_value

        if not project_name:
            self.log_window.log_message("Masukan nama proyek terlebih dahulu!", LogLevel.ERROR.value)
            return

        self.log_window.log_message("Memproses citra Sentinel-2 ...")

        self.s2_clipped = process_sentinel2(
            self.geometry, 
            self.start_date.get_date(), 
            self.end_date.get_date(), 
            self.max_cloud_prob.get_value)
        self.log_window.log_message("Proses citra Sentinel-2 berhasil!")
    
    def generate_map(self):
        """Generate and display map with Sentinel-2 imagery."""
        if not self.s2_clipped:
            self.log_window.log_message("Lakukan proses citra Sentinel-2 terlebih dahulu!", LogLevel.ERROR.value)
            return

        self.log_window.log_message("Membuat Peta...")

        # Calculate center of ROI
        shapely_geom = shape(self.geom)
        minx, miny, maxx, maxy = shapely_geom.bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]

        lat, lon = center

        m = folium.Map(location=[lat, lon], zoom_start=12)
        
        # Visualization parameters for Sentinel-2
        rgb_vis = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
        
        # Add Sentinel-2 image layer
        self.add_ee_layer(m, self.s2_clipped, rgb_vis, 'Sentinel 2 Masked')

        # Add ROI overlay
        folium.GeoJson(self.geom, name="ROI").add_to(m)

        # Add layer control
        m.add_child(folium.LayerControl())

        # Save and open map
        map_path = "sentinel_map.html"
        m.save(map_path)
        webbrowser.open(map_path)

        self.log_window.log_message("Peta berhsail dibuat!")

    def export_image(self):
        """"Export processed Sentinel-2 image."""
        if not self.s2_clipped:
            self.log_window.log_message("Proses citra Sentinel-2 terlebih dahulu!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.s2_clipped, description="Sentinel2_Export", folder="GEE_Exports",
            scale=10, region=self.geometry, crs="EPSG:4326", fileNamePrefix="Sentinel2_Export", maxPixels=1e13
        )
        
        task.start()
        self.log_window.log_message("Proses Ekspor dimulai. Silahkan periksa Drive Google anda.")


    def add_ee_layer(self, map_object, ee_image_object, vis_params, name):
        """Adds a method for displaying Earth Engine image tiles to folium map."""
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)

        # Print tile URL for debugging
        print(f"Tile URL for {name}: {map_id_dict['tile_fetcher'].url_format}")

        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
            name=name,
            overlay=True,
            control=True
        ).add_to(map_object)