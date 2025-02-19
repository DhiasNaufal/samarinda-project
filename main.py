import sys
import ee
import json
import folium
import webbrowser
from shapely.geometry import shape
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QLineEdit, QDateEdit, QSlider, QTextEdit, QHBoxLayout,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import pyqtSlot

# Authenticate and Initialize Google Earth Engine
def authenticate_and_initialize(project):
    """Authenticate and initialize the Google Earth Engine."""
    ee.Authenticate()
    ee.Initialize(project=project)
    print("GEE Authentication Successful")

class Sentinel2App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("ugm.png"))
        self.setWindowTitle("Palm Tree Classification")
        self.setGeometry(200, 200, 500, 400)

        # Initialize attributes
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.start_date = QDate.fromString("2024-01-01", "yyyy-MM-dd")
        self.end_date = QDate.fromString("2024-12-01", "yyyy-MM-dd")
        self.max_cloud_prob = 20
        self.s2_clipped = None

        # Create tab widget
        self.tabs = QTabWidget(self)

        # First tab (Main UI)
        self.tab1 = QWidget()
        self.initTab1()
        self.tabs.addTab(self.tab1, "Sentinel 2 Cloud Mask")

        # Second tab (Placeholder)
        self.tab2 = QWidget()
        self.initTab2()
        self.tabs.addTab(self.tab2, "Sentinel 2 Super Resolution")

        # Third tab (Placeholder)
        self.tab3 = QWidget()
        self.initTab3()
        self.tabs.addTab(self.tab3, "Palm Tree Classification")

        # Layout for main window
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # # Tambahkan QWebChannel
        # self.channel = QWebChannel()
        # self.channel.registerObject("pyqtChannel", self)
        # self.web_view.page().setWebChannel(self.channel)
        
    @pyqtSlot(str)
    def receiveGeoJSON(self, geojson_str):
        """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
        import json
        geojson = json.loads(geojson_str)
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log("Polygon received from map and set as geometry!")
        print("Polygon received from map and set as geometry!")

    def initTab1(self):
        """Initialize the first tab (existing UI) with a side-by-side map."""
        main_layout = QHBoxLayout()  # Mengatur tata letak secara horizontal
        form_layout = QVBoxLayout()  # Untuk elemen UI sebelumnya

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
        self.start_date_input.setDate(QDate.currentDate())
        
        self.end_date_label = QLabel("End Date:")
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate().addDays(30))

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

        # Log Window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        form_layout.addWidget(self.log_window)

        # Web Map View
        self.web_view = QWebEngineView()
        self.web_view.setHtml(self.get_map_html())
        self.web_view.setMinimumWidth(400)  # Atur lebar minimal peta agar tampak proporsional
        self.channel = QWebChannel()
        self.channel.registerObject("pyqtChannel", self)  # Daftarkan objek Python ke Web Channel
        # Set Web Channel ke Web View
        self.web_view.page().setWebChannel(self.channel)
        # Gabungkan form dan peta dalam layout utama
        main_layout.addLayout(form_layout, 1)  # UI sebelumnya (form) - lebih kecil
        main_layout.addWidget(self.web_view, 2)  # Map - lebih besar

        self.tab1.setLayout(main_layout)  # Terapkan tata letak pada tab1


    def get_map_html(self):
        """Return the HTML content for displaying the map with LeafletJS."""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Leaflet Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet-draw/dist/leaflet.draw.js"></script>
            <link rel="stylesheet" href="https://unpkg.com/leaflet-draw/dist/leaflet.draw.css" />
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="map" style="width: 100%; height: 400px;"></div>
            <script>
                var map = L.map('map').setView([-0.4827527195626835, 117.18218840574627], 12);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);

                var drawnItems = new L.FeatureGroup();
                map.addLayer(drawnItems);
                var drawControl = new L.Control.Draw({
                    edit: {
                        featureGroup: drawnItems
                    },
                    draw: {
                        polygon: true,
                        marker: false,
                        circle: false,
                        circlemarker: false,
                        rectangle: true,
                        polyline: false
                    }
                });
                map.addControl(drawControl);

                map.on('draw:created', function (e) {
                    var layer = e.layer;
                    drawnItems.addLayer(layer);
                    var geojson = layer.toGeoJSON();
                    if (window.pyqtChannel) {
                        window.pyqtChannel.receiveGeoJSON(JSON.stringify(geojson));
                    }
                    console.log(JSON.stringify(layer.toGeoJSON()));
                });
                new QWebChannel(qt.webChannelTransport, function (channel) {
                    window.pyqtChannel = channel.objects.pyqtChannel;  // Pastikan channel terhubung
                });
            </script>
        </body>
        </html>
        '''

    def initTab2(self):
        """Initialize the second tab (Placeholder for future functionality)."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is the second tab."))
        self.tab2.setLayout(layout)

        # Load Image Button
        self.load_image_btn = QPushButton("Load Image")
        self.load_image_btn.clicked.connect(self.load_image)
        layout.addWidget(self.load_image_btn)

         # Start Super Resolution Button
        self.super_res_btn = QPushButton("Start Super Resolution")
        self.super_res_btn.clicked.connect(self.start_super_resolution)
        layout.addWidget(self.super_res_btn)

        # Add Log and Watermark
        self.log_window_tab2 = self.add_log_and_watermark(layout)  # Separate log for Tab 2

        self.tab2.setLayout(layout)

    def initTab3(self):
        """Initialize the third tab (Placeholder for future functionality)."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is the third tab."))
        self.tab3.setLayout(layout)

       # Load Image Button
        self.load_image_btn_tab3 = QPushButton("Load Image")
        self.load_image_btn_tab3.clicked.connect(self.load_image_tab3)
        layout.addWidget(self.load_image_btn_tab3)

        # Select Model Text
        self.model_label = QLabel("Select Model")
        layout.addWidget(self.model_label)

        # Model Selection Dropdown
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["U-Net", "MVT", "ResNet"])
        layout.addWidget(self.model_dropdown)

        # Start Processing Button
        self.start_processing_btn = QPushButton("Start Processing")
        self.start_processing_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_processing_btn)

        self.log_window_tab3 = self.add_log_and_watermark(layout)  # Separate log for Tab 2

        self.tab3.setLayout(layout)

    def log(self, message):
        """Log messages to all tabs' log windows."""
        if hasattr(self, 'log_window') and self.log_window:
            self.log_window.append(message)  # Log in Tab 1

        if hasattr(self, 'log_window_tab2') and self.log_window_tab2:
            self.log_window_tab2.append(message)  # Log in Tab 2

        if hasattr(self, 'log_window_tab3') and self.log_window_tab3:
            self.log_window_tab3.append(message)  # Log in Tab 3 (if exists)

    def add_log_and_watermark(self, layout):
        """Adds a log window and watermark label to a given layout."""
        log_window = QTextEdit()
        log_window.setReadOnly(True)
        layout.addWidget(log_window)

        watermark = QLabel("© Department of Geodetic Engineering FT UGM")
        watermark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        watermark.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(watermark)

        return log_window  # Return log_window to use it in the tab
    
    def authenticate_gee(self):
        """Authenticate and initialize Google Earth Engine after entering project name."""
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

    def update_cloud_prob(self, value):
        """Update cloud probability value from slider."""
        self.max_cloud_prob = value
        self.cloud_prob_label.setText(f"Max Cloud Probability: {value}")

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

    def load_image(self):
        """Browse and load a TIF image."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "TIFF Files (*.tif *.tiff)")

        if file_path:
            self.log(f"Image loaded: {file_path}")

    def start_super_resolution(self):
        """Placeholder function for Super Resolution process."""
        self.log("Super Resolution Started...")

    def load_image_tab3(self):
        """Open file dialog to load an image and display its path."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Image File", "", "TIF Files (*.tif);;All Files (*)")

        if file_path:
            self.log(f"Image loaded: {file_path}")  # Log message in all tabs

    def start_processing(self):
        """Start the processing based on selected model."""
        selected_model = self.model_dropdown.currentText()
        self.log(f"Processing started using {selected_model} model...")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Sentinel2App()
    window.show()
    sys.exit(app.exec())