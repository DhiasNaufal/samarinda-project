import json
import os
import ee
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider,  QSpacerItem, QSizePolicy
from PyQt6.QtCore import QDate, Qt
from gee.auth import authenticate_and_initialize
from gee.sentinel2_processing import process_sentinel2
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
class SuperResolution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.start_date = QDate.fromString("2024-01-01", "yyyy-MM-dd")
        self.end_date = QDate.fromString("2024-12-01", "yyyy-MM-dd")
        self.max_cloud_prob = 20
        self.s2_clipped = None
        self.initUI()

    def initUI(self):
        """Initialize the second tab (Placeholder for future functionality)."""
        layout = QVBoxLayout()
        form_layout = QVBoxLayout()  # Form layout for buttons

        # Load Image Button
        self.load_image_btn = QPushButton("Load Image")
        self.load_image_btn.clicked.connect(self.load_image)
        form_layout.addWidget(self.load_image_btn)

         # Start Super Resolution Button
        self.super_res_btn = QPushButton("Start Super Resolution")
        self.super_res_btn.clicked.connect(self.start_super_resolution)
        form_layout.addWidget(self.super_res_btn)

        # Web Map View
        self.web_view_tab2 = QWebEngineView()
        self.web_view_tab2.setHtml(self.load_map_html())  # Load map
        self.web_view_tab2.setMinimumHeight(400)  # Adjust height if needed
        
        self.channel_tab2 = QWebChannel()
        self.channel_tab2.registerObject("pyqtChannel", self)  
        self.web_view_tab2.page().setWebChannel(self.channel_tab2)

        # Add widgets in vertical order
        layout.addLayout(form_layout)  # Buttons at the top
        layout.addWidget(self.web_view_tab2)  # Map in the middle
        
        # Add Log and Watermark
        self.log_window_tab2 = self.add_log_and_watermark(layout)  # Separate log for Tab 2

        self.setLayout(layout)
        pass

    
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

    def load_image(self):
        """Browse and load a TIF image."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Image File", "", "TIFF Files (*.tif *.tiff)")

        if file_path:
            print(f"TIFF file selected: {file_path}")
            self.last_loaded_file = file_path  # Store for server directory change
            self.start_server()  # Ensure the server is started

            tiff_dir = os.path.dirname(file_path)
            print(f"📁 Files in {tiff_dir}: {os.listdir(tiff_dir)}")

            # Convert local path to HTTP URL
            file_name = os.path.basename(file_path).replace("\\", "/")
            image_url = f"http://localhost:8000/{file_name}"
            print(f"🌍 Image URL: {image_url}")

            # Pass correct HTTP URL to JavaScript
            js_script = f"updateBeforeLayer('{image_url}');"
            self.web_view_tab2.page().runJavaScript(js_script)
    def start_super_resolution(self):
        """Placeholder function for Super Resolution process."""
        self.log("Super Resolution Started...")
        
    def load_map_html(self):
        """Load map.html content from file."""
        html_file_path = os.path.join(os.getcwd(), "map2.html")
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return html_content
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

        return log_window 