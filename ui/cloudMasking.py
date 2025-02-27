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

from utils.enum import LogType, FileType

class CloudMasking(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        # Initialize attributes
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.max_cloud_prob = 20
        self.s2_clipped = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  
        form_layout = QVBoxLayout()  
        # Project Name
        self.project_name = TextInputWidget("Nama Proyek Google Earth Engine:")
        form_layout.addWidget(self.project_name)

        # Authenticate Button
        self.auth_btn = QPushButton("Autentikasi Akun GEE")
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
        self.cloud_prob_label = QLabel("Probabilitas Awan Maksimum: 20")
        self.cloud_prob_slider = QSlider(Qt.Orientation.Horizontal)
        self.cloud_prob_slider.setMinimum(0)
        self.cloud_prob_slider.setMaximum(100)
        self.cloud_prob_slider.setValue(20)
        self.cloud_prob_slider.setTickInterval(10)
        self.cloud_prob_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.cloud_prob_slider.valueChanged.connect(self.update_cloud_prob)
        form_layout.addWidget(self.cloud_prob_label)
        form_layout.addWidget(self.cloud_prob_slider)

        # Action Buttons
        self.process_btn = QPushButton("Proses Citra Sentinel-2 ")
        self.process_btn.clicked.connect(self.process_geometry)
        form_layout.addWidget(self.process_btn)

        self.map_btn = QPushButton("Buat Peta")
        self.map_btn.clicked.connect(self.generate_map)
        form_layout.addWidget(self.map_btn)

        self.export_btn = QPushButton("Ekspor Gambar")
        self.export_btn.clicked.connect(self.export_image)
        form_layout.addWidget(self.export_btn)

        # Web Map View
        self.web_view = QWebEngineView()
        self.web_view.setHtml(self.load_map_html())

        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  
        self.web_view.setStyleSheet("QWebEngineView { height: 100%; }")
        self.web_view.setMinimumHeight(400)  

        # Web Channel
        self.channel = QWebChannel()
        self.channel.registerObject("pyqtChannel", self) 
        self.web_view.page().setWebChannel(self.channel)


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
        
    @pyqtSlot(str)
    def receiveGeoJSON(self, geojson_str):
        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        import json
        geojson = json.loads(geojson_str)
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log_window.log_message("Polygon Terbentuk!")
    def load_map_html(self):
        """Load map.html content from file."""
        html_file_path = os.path.join(os.getcwd(), "map.html")
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return html_content
    
    def authenticate_gee(self):
        self.project = self.project_name.get_value.strip()

        if not self.project:
            self.log_window.log_message("Tolong Masukan Nama Proyek Google Earth Engine!", LogType.ERROR.value)
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
            self.log_window.log_message("Tolong lakukan autentikasi terlebih dahulu!", LogType.ERROR.value)
            return
        
        if not self.geometry:
            self.log_window.log_message("Tidak ada dokumen GeoJSON yang dibuat!", LogType.ERROR.value)
            return

        project_name = self.project_name.get_value

        if not project_name:
            self.log_window.log_message("Masukan nama proyek terlebih dahulu!", LogType.ERROR.value)
            return

        self.log_window.log_message("Memproses citra Sentinel-2 ...")

        self.s2_clipped = process_sentinel2(
            self.geometry, 
            self.start_date.get_date(), 
            self.end_date.get_date(), 
            self.max_cloud_prob)
        self.log_window.log_message("Proses citra Sentinel-2 berhasil!")
    
    def generate_map(self):
        """Generate and display map with Sentinel-2 imagery."""
        if not self.s2_clipped:
            self.log_window.log_message("Lakukan proses citra Sentinel-2 terlebih dahulu!", LogType.ERROR.value)
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

    def update_cloud_prob(self, value):
        """Update cloud probability value from slider."""
        self.max_cloud_prob = value
        self.cloud_prob_label.setText(f"Probabilitas Awan Maksimum: {value}")

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