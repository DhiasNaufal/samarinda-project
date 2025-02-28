from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal

import json

class WebViewWidget(QWidget):
  geojson_generated = pyqtSignal(dict)

  def __init__(self, map_path: str, parent=None):
    super().__init__(parent)

    self.init_ui(map_path)

  def init_ui(self, map_path: str):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    
    self.web_view = QWebEngineView()
    self.web_view.setHtml(self.load_map(map_path))

    self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.web_view.setStyleSheet("QWebEngineView { height: 100%; }")
    self.web_view.setMinimumHeight(400)
    layout.addWidget(self.web_view)

    self.channel = QWebChannel()
    self.channel.registerObject("pyqtChannel", self)
    self.web_view.page().setWebChannel(self.channel)

  def load_map(self, map_path: str):
    """Load map.html content from file."""
    with open(map_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content
  
  @pyqtSlot(str)
  def receiveGeoJSON(self, data: str):
    """Receive GeoJSON data from JavaScript and convert it to EE Geometry."""
    self.data = json.loads(data)
    self.geojson_generated.emit(self.data)