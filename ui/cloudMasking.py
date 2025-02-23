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

class CloudMasking(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        # Initialize attributes
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.start_date = QDate.fromString("2024-01-01", "yyyy-MM-dd")
        self.end_date = QDate.fromString("2024-12-01", "yyyy-MM-dd")
        self.max_cloud_prob = 20
        self.s2_clipped = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  
        form_layout = QVBoxLayout()  
        # Project Name
        self.project_label = QLabel("Google Earth Engine Project Name:")
        self.project_input = QLineEdit()
        form_layout.addWidget(self.project_label)
        form_layout.addWidget(self.project_input)

        # Authenticate Button
        self.auth_btn = QPushButton("Authenticate and Initialize GEE")
        self.auth_btn.clicked.connect(self.authenticate_gee)
        form_layout.addWidget(self.auth_btn)

        # Load GeoJSON Button
        self.geojson_label = QLabel("Selected GeoJSON: None")
        self.load_geojson_btn = QPushButton("Load GeoJSON")
        self.load_geojson_btn.clicked.connect(self.load_geojson)
        form_layout.addWidget(self.geojson_label)
        form_layout.addWidget(self.load_geojson_btn)

        # Date Selection
        self.date_layout = QHBoxLayout()
        self.start_date_label = QLabel("Start Date:")
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(self.start_date)
        
        self.end_date_label = QLabel("End Date:")
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        self.date_layout.addWidget(self.start_date_label)
        self.date_layout.addWidget(self.start_date_input)
        self.date_layout.addWidget(self.end_date_label)
        self.date_layout.addWidget(self.end_date_input)
        form_layout.addLayout(self.date_layout)

        # Cloud Probability Slider
        self.cloud_prob_label = QLabel("Max Cloud Probability: 20")
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
        self.process_btn = QPushButton("Process Sentinel-2 Data")
        self.process_btn.clicked.connect(self.process_geometry)
        form_layout.addWidget(self.process_btn)

        self.map_btn = QPushButton("Generate Map")
        self.map_btn.clicked.connect(self.generate_map)
        form_layout.addWidget(self.map_btn)

        self.export_btn = QPushButton("Export Image")
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
        self.log_window = self.add_log_and_watermark(main_layout)
        self.log_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setLayout(main_layout)  
        # Tambahkan web_view ke layout 
        
    @pyqtSlot(str)
    def receiveGeoJSON(self, geojson_str):
        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        import json
        geojson = json.loads(geojson_str)
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log("Polygon received from map and set as geometry!")
        print("Polygon received from map and set as geometry!")
    def load_map_html(self):
        """Load map.html content from file."""
        html_file_path = os.path.join(os.getcwd(), "map.html")
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return html_content
    
    def authenticate_gee(self):
        self.project = self.project_input.text().strip()

        if not self.project:
            self.log("Error: Please enter a project name before authentication!")
            return
        try:
            authenticate_and_initialize(self.project)
            self.log(f"Authenticated with project: {self.project}")
        except Exception as e:
            self.log(f"Authentication failed: {str(e)}")

    def load_geojson(self):
        """Load a GeoJSON file."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select GeoJSON File", "", "GeoJSON Files (*.geojson)")

        if file_path:
            self.geojson_path = file_path
            self.geojson_label.setText(f"Selected GeoJSON: {file_path}")

            with open(file_path, "r") as f:
                geojson = json.load(f)

            if "features" in geojson and len(geojson["features"]) > 0:
                self.geom = geojson["features"][0]["geometry"]
                self.geometry = ee.Geometry(self.geom)
                self.log("GeoJSON loaded successfully!")
            else:
                self.log("Invalid GeoJSON file.")

    def process_geometry(self):
        """Process Sentinel-2 data."""
        if not self.project:
            self.log("Error: Please authenticate first!")
            return
        
        if not self.geometry:
            self.log("Error: No GeoJSON loaded!")
            return

        self.start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        self.end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        project_name = self.project_input.text()

        if not project_name:
            self.log("Error: Enter a project name!")
            return

        self.log("Processing Sentinel-2 imagery...")

        # Load Sentinel-2 dataset
        s2_sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")

        # Cloud mask function
        def mask_clouds(img):
            clouds = ee.Image(img.get("cloud_mask")).select("probability")
            is_not_cloud = clouds.lt(self.max_cloud_prob)
            return img.updateMask(is_not_cloud)

        # Edge masking function
        def mask_edges(s2_img):
            return s2_img.updateMask(
                s2_img.select("B8A").mask().updateMask(s2_img.select("B9").mask())
            )

        # Apply filtering
        criteria = ee.Filter.bounds(self.geometry).And(ee.Filter.date(self.start_date, self.end_date))
        s2_sr_filtered = s2_sr.filter(criteria).map(mask_edges)
        s2_clouds_filtered = s2_clouds.filter(criteria)

        # Join datasets
        join = ee.Join.saveFirst("cloud_mask")
        condition = ee.Filter.equals(leftField="system:index", rightField="system:index")
        s2_sr_with_cloud_mask = join.apply(s2_sr_filtered, s2_clouds_filtered, condition)

        # Apply cloud masking and create a median composite
        self.s2_cloud_masked = ee.ImageCollection(s2_sr_with_cloud_mask).map(mask_clouds).median()

        # Clip the image using the selected geometry
        self.s2_clipped = self.s2_cloud_masked.clip(self.geometry)

        self.log("Sentinel-2 processing complete.")
    
    def generate_map(self):
        """Generate and display map with Sentinel-2 imagery."""
        if not self.s2_clipped:
            self.log("Error: Process Sentinel-2 data first!")
            return

        self.log("Generating map...")

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

        self.log("Map generated successfully.")

    def update_cloud_prob(self, value):
        """Update cloud probability value from slider."""
        self.max_cloud_prob = value
        self.cloud_prob_label.setText(f"Max Cloud Probability: {value}")

    def export_image(self):
        """"Export processed Sentinel-2 image."""
        if not self.s2_clipped:
            self.log("Error: Process Sentinel-2 data first!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.s2_clipped, description="Sentinel2_Export", folder="GEE_Exports",
            scale=10, region=self.geometry, crs="EPSG:4326", fileNamePrefix="Sentinel2_Export", maxPixels=1e13
        )
        
        task.start()
        self.log("Export task started. Check Google Drive.")

    def add_log_and_watermark(self, parent_layout):
        """Adds a log window and watermark label to a given layout."""
        log_window = QTextEdit()
        log_window.setReadOnly(True)
        
        # Vertical layout for log and watermark
        log_layout = QVBoxLayout()
        log_layout.addWidget(log_window, 1)

        watermark = QLabel("© Badan Pertanahan Nasional Kantor Wilayah Kalimantan Timur")
        watermark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        watermark.setStyleSheet("font-size: 10px; color: black;")

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        log_layout.addItem(spacer)  # Pushes watermark to the bottom
        log_layout.addWidget(watermark)

        # Append log layout to the form layout (not main_layout)
        parent_layout.addLayout(log_layout)

        return log_window  # Return log_window to use it in the tab
    def log(self, message):
        """Log messages to all tabs' log windows."""
        if hasattr(self, 'log_window') and self.log_window:
            self.log_window.append(message)  # Log in Tab 1

        if hasattr(self, 'log_window_tab2') and self.log_window_tab2:
            self.log_window_tab2.append(message)  # Log in Tab 2

        if hasattr(self, 'log_window_tab3') and self.log_window_tab3:
            self.log_window_tab3.append(message)  # Log in Tab 3 (if exists)


