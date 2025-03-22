from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import Optional
from shapely import Polygon

from .widgets.web_viewer_widget import WebViewWidget
from .widgets.button_widget import ButtonWidget
from .widgets.frame_widget import FrameWidget
from .widgets.dropdown_widget import DropdownWidget
from .widgets.file_input_widget import FileInputWidget, FileInputType, FileType
from .widgets.message_box_widget import CustomMessageBox, QMessageBox
from .widgets.progress_bar_widget import ProgressBarWidget

from logic.satellite_image.download_tiles import DownloadTiles
from logic.satellite_image.tile_providers import TILE_PROVIDERS

from utils.common import get_string_date

import os

class SatelliteImage(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    self.web_view = WebViewWidget(map_path=os.path.join(os.getcwd(), "assets", "satellite_image_map.html"))
    self.web_view.geojson_generated.connect(self.on_received_geojson)
    layout.addWidget(self.web_view)

    frame = FrameWidget()
    layout.addWidget(frame)
    form_layout = QHBoxLayout()
    frame.add_layout(form_layout)

    tile_provider_options = [tile_provider["name"] for tile_provider in TILE_PROVIDERS]
    self.tile_provider = DropdownWidget(
        label="Pilih Tile Provider",
        dropdown_options=tile_provider_options
      )
    self.tile_provider.value_changed.connect(self.on_tile_provider_changed)
    form_layout.addWidget(self.tile_provider)

    zoom_level_options = TILE_PROVIDERS[0]["zoom_level"]
    self.zoom_level = DropdownWidget(
        label="Pilih Zoom Level",
        dropdown_options=zoom_level_options
      )
    form_layout.addWidget(self.zoom_level)

    self.output_path = FileInputWidget(
      label="Tentukan nama file dan directory",
      filetype=FileType.PNG.value,
      file_input_type=FileInputType.FILENAME.value,
      default_path=os.path.join(os.getcwd(), "output", f"result {get_string_date()}.png")
    )
    frame.add_widget(self.output_path)

    download_btn = ButtonWidget("Download")
    download_btn.clicked.connect(self.download_image)
    frame.add_widget(download_btn)

    self.progress_bar = ProgressBarWidget(self)
    frame.add_widget(self.progress_bar)
  
  def on_tile_provider_changed(self, val: str):
    zoom_level_options = next((tile_provider["zoom_level"] for tile_provider in TILE_PROVIDERS if tile_provider["name"] == val), None)
    self.zoom_level.set_options(zoom_level_options)

  def on_received_geojson(self, geojson: dict) -> None:
    geom = geojson["geometry"]
    self.polygon = Polygon(geom["coordinates"][0])

  def download_image(self):
    message = CustomMessageBox(
          parent=self,
          title="Info",
          message="Gambar peta telah berhasil di download",
          icon=QMessageBox.Icon.Information
      )
    
    self.download_tile_thread = DownloadTiles(
      tile_provider=self.tile_provider.get_value,
      zoom_level=int(self.zoom_level.get_value),
      polygon=self.polygon,
      output_path=self.output_path.get_value
    )
    self.download_tile_thread.finished.connect(lambda: message.show())
    self.download_tile_thread.finished.connect(self.download_tile_thread.deleteLater)
    self.download_tile_thread.finished.connect(lambda: self.progress_bar.set_progress_range(max=100))
    self.download_tile_thread.started.connect(lambda: self.progress_bar.set_progress_range())
    self.download_tile_thread.start()
    