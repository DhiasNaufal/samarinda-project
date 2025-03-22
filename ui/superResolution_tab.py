import json
import os
import ee
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt6.QtCore import QDate
from typing import Optional

from logic.gee.sentinel2_processing import process_sentinel2

from .widgets.log_widget import LogWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.button_widget import ButtonWidget
from .widgets.web_viewer_widget import WebViewWidget
from .widgets.message_box_widget import CustomMessageBox, QMessageBox

from utils.enum import FileType
class SuperResolution(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.start_date = QDate.fromString("2024-01-01", "yyyy-MM-dd")
        self.end_date = QDate.fromString("2024-12-01", "yyyy-MM-dd")
        self.max_cloud_prob = 20
        self.s2_clipped = None
        self.initUI()

    def initUI(self) -> None:
        """Initialize the second tab (Placeholder for future functionality)."""
        layout = QVBoxLayout()
        form_layout = QVBoxLayout()  # Form layout for buttons

        # Load Image Button
        self.image = FileInputWidget(
            button_name="Muat Gambar",
            file_dialog_title="Select Image File",
            filetype=[FileType.TIFF.value]
        )
        self.image.path_selected.connect(self.on_image_selected)
        self.image.setEnabled(False)
        form_layout.addWidget(self.image)

         # Start Super Resolution Button
        self.super_res_btn = ButtonWidget("Start Super Resolution")
        self.super_res_btn.clicked.connect(self.start_super_resolution)
        form_layout.addWidget(self.super_res_btn)

        # Web Map View
        self.web_view = WebViewWidget(map_path=os.path.join(os.getcwd(), "assets", "super_resolution_map.html"))
        # self.web_view = WebViewWidget(map_url="http://localhost:8000/assets/super_resolution_map.html")
        self.web_view.geojson_generated.connect(self.on_received_geojson)

        # Add widgets in vertical order
        layout.addLayout(form_layout)  # Buttons at the top
        layout.addWidget(self.web_view)  # Map in the middle
        
        # Add Log and Watermark
        self.log_window = LogWidget()
        self.log_window.setFixedHeight(200)
        layout.addWidget(self.log_window)

        self.setLayout(layout)
        pass

    def on_received_geojson(self, geojson: dict) -> None:
        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
    
    def authenticate_gee(self) -> None:
        self.project = self.project_input.text().strip()

        if not self.project:
            self.log("Error: Please enter a project name before authentication!")
            return
        try:
            authenticate_and_initialize(self.project)
            self.log(f"Authenticated with project: {self.project}")
        except Exception as e:
            self.log(f"Authentication failed: {str(e)}")

    def load_geojson(self) -> None:
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

    def on_image_selected(self, file_path: str) -> None:
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
            
    def start_super_resolution(self) -> None:
        message = CustomMessageBox(
            message="Fitur ini masih dalam tahap pengembangan",
            icon=QMessageBox.Icon.Warning
        )
        message.show()
        return
        """Placeholder function for Super Resolution process."""
        self.log("Super Resolution Started...")
        
    def load_map_html(self) -> None:
        """Load map.html content from file."""
        html_file_path = os.path.join(os.getcwd(), "assets", "map2.html")
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return 