from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineDownloadRequest
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QUrl, QMutex

import json
from typing import Optional
import os
class WebViewWidget(QWidget):
  geojson_generated = pyqtSignal(dict)
  string_received = pyqtSignal(str)

  def __init__(self, map_url: str = "", map_path: str = "", min_height: int = 400, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.map_path = map_path
    self.map_url = map_url
    self.min_height = min_height
    self.init_ui()

  def init_ui(self) -> None:
    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    self.web_view = QWebEngineView()
    if self.map_url:
      self.web_view.setUrl(QUrl(self.map_url))
    elif self.map_path:
      self.web_view.setHtml(self.load_map(self.map_path))

    self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.web_view.setStyleSheet("QWebEngineView { height: 100%; }")
    self.web_view.setMinimumHeight(self.min_height)
    layout.addWidget(self.web_view)

    self.channel = QWebChannel()
    self.channel.registerObject("pyqtChannel", self)
    self.web_view.page().setWebChannel(self.channel)

    # Track handled downloads to avoid duplicate issues
    profile = QWebEngineProfile.defaultProfile()
    profile.downloadRequested.connect(self.handle_download_requested)
  
  def handle_download_requested(self, download: QWebEngineDownloadRequest):
    """Handle download requests from the web view."""
    download.accept()

    # Connect to stateChanged instead of finished
    def on_state_changed(state):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            print("✅ Download finished.")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            print("❌ Download interrupted.")

    download.stateChanged.connect(on_state_changed)

  def load_map(self, map_path: str) -> None:
    """Load map.html content from file."""
    with open(map_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content
  
  @pyqtSlot(str)
  def receiveGeoJSON(self, data: str) -> None:
    """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
    self.data = json.loads(data)
    self.geojson_generated.emit(self.data)

  @pyqtSlot(str)
  def receivedString(self, data: str) -> None:
    """Receive string data from JavaScript."""
    self.string_received.emit(data)

  def add_raster(self, filename: str, path: str = "output"):
    """Send a command to JavaScript to load a new raster file."""
    raster_url = f"http://localhost:8000/{path}/{filename}"
    script = f'window.postMessage({{"type": "addRaster", "url": "{raster_url}", "layerName": "{filename}"}}, "*");'
    self.web_view.page().runJavaScript(script)