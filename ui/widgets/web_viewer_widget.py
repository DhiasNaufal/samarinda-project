from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QUrl

import json
from typing import Optional
class WebViewWidget(QWidget):
  geojson_generated = pyqtSignal(dict)

  def __init__(self, map_url: str = "", map_path: str = "", parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.map_path = map_path
    self.map_url = map_url
    self.init_ui()

  def init_ui(self) -> None:
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    self.web_view = QWebEngineView()
    if self.map_url:
      self.web_view.setUrl(QUrl(self.map_url))
    elif self.map_path:
      self.web_view.setHtml(self.load_map(self.map_path))

    self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.web_view.setStyleSheet("QWebEngineView { height: 100%; }")
    self.web_view.setMinimumHeight(400)
    layout.addWidget(self.web_view)

    self.channel = QWebChannel()
    self.channel.registerObject("pyqtChannel", self)
    self.web_view.page().setWebChannel(self.channel)

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

  def add_raster(self, filename: str, path: str = "output"):
    """Send a command to JavaScript to load a new raster file."""
    raster_url = f"http://localhost:8000/{path}/{filename}"
    script = f'window.postMessage({{"type": "addRaster", "url": "{raster_url}", "layerName": "{filename}"}}, "*");'
    self.web_view.page().runJavaScript(script)