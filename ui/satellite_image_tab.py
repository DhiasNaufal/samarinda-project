from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import Optional
from shapely import Polygon
from datetime import datetime
import geopandas as gpd

from .widgets.web_viewer_widget import WebViewWidget
from .widgets.button_widget import ButtonWidget
from .widgets.frame_widget import FrameWidget
from .widgets.dropdown_widget import DropdownWidget
from .widgets.file_input_widget import FileInputWidget, FileInputType, FileType
from .widgets.message_box_widget import CustomMessageBox, QMessageBox
from .widgets.progress_bar_widget import ProgressBarWidget

from logic.satellite_image.download_tiles import DownloadTiles
from logic.satellite_image.tile_providers import TILE_PROVIDERS

from utils.common import get_string_date, calculate_time_diff, is_default_filename

import os

class SatelliteImage(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)
    self.polygon = None

    self.init_ui()
    self.message_box = CustomMessageBox(
          parent=self,
          title="Info",
          icon=QMessageBox.Icon.Information
      )

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
      label="Tentukan output file",
      filetype=[FileType.TIFF.value, FileType.PNG.value, FileType.JPG.value],
      file_input_type=FileInputType.FILENAME.value,
      default_path="(dibuat otomatis oleh sistem)"
    )
    self.output_path.path_selected.connect(lambda path: self.output_path.set_label(f"Tentukan output file : {path}"))
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

  def on_download_finished(self):
    self.progress_bar.set_progress_range(max=100)
    self.download_tile_thread.deleteLater

    end = datetime.now()
    processing_time = calculate_time_diff(self.start, end)

    self.message_box.set_message("Gambar peta telah berhasil di download")
    self.message_box.set_informative_message(f"Selesai dalam waktu : {processing_time}\nTersimpan di : {self.output_path.get_value}.")
    self.message_box.show()

  def handle_error(self, message):
    self.message_box.set_icon(QMessageBox.Icon.Critical)
    self.message_box.set_title("Error")
    self.message_box.set_message(message)
    self.message_box.show()
    self.message_box.set_title("Info")
    self.message_box.set_icon(QMessageBox.Icon.Information)

  def download_image(self):    
    if self.polygon is None:
      self.message_box.set_message("Pilih Area yang ingin di download terlebih dahulu")
      self.message_box.show()
      return

    if not self.output_path.get_value or \
        self.output_path.get_value == "(dibuat otomatis oleh sistem)" or \
        is_default_filename(self.output_path.get_value, "result"):
      self.output_path.set_path(os.path.join(os.getcwd(), "output", f"result {get_string_date()}.tif"))

    self.download_tile_thread = DownloadTiles(
      tile_provider=self.tile_provider.get_value,
      zoom_level=int(self.zoom_level.get_value),
      polygon=self.polygon,
      output_path=self.output_path.get_value
    )
    self.download_tile_thread.started.connect(lambda: self.progress_bar.set_progress_range())
    self.download_tile_thread.started.connect(lambda: setattr(self, "start", datetime.now()))
    self.download_tile_thread.error_signal.connect(self.handle_error)
    self.download_tile_thread.finish_signal.connect(self.on_download_finished)
    self.download_tile_thread.start()
    