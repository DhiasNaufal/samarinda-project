from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QGraphicsPixmapItem, QComboBox, QGraphicsProxyWidget
from PyQt6.QtGui import QPainter, QPixmap, QImage, QWheelEvent

from typing import Optional
from PIL import Image

import numpy as np
import rasterio

from utils.common import get_filename

class GraphicsViewWidget(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.layer_items = {}
    self.z_values = []

    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()
    self.setLayout(layout)

    self.scene = QGraphicsScene(self)
    self.view = GraphicsView(self.scene)
    self.view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    layout.addWidget(self.view)

  def normalize(self, band):
    band = band.astype(np.float32)
    band = (band - band.min()) / (band.max() - band.min() + 1e-5)
    return (band * 255).astype(np.uint8)

  def read_image(self, path: str):
    with rasterio.open(path) as src:
      count = src.count

      if count == 1: # Grayscale
          image = self.normalize(src.read(1))
      elif count == 3: # RGB
          r, g, b = src.read(1), src.read(2), src.read(3)
          image = np.stack([self.normalize(r), self.normalize(g), self.normalize(b)], axis=-1)
      elif count == 4: # RGBA
          r, g, b, a = src.read(1), src.read(2), src.read(3), src.read(4)
          image = np.stack([self.normalize(r), self.normalize(g), self.normalize(b), self.normalize(a)], axis=-1)
      elif count >= 10: # Sentinel-2: use bands 4 (R), 3 (G), 2 (B)
          r, g, b = src.read(4), src.read(3), src.read(2)
          image = np.stack([self.normalize(r), self.normalize(g), self.normalize(b)], axis=-1)
      else:
          raise ValueError(f"Unsupported band count: {count}")

      return image


  def load_raster(self, path: str = None, cv_image: np.ndarray = None, layer: str = "", opacity: float = 1.0):
    if path is not None:
      # image = Image.open(path)
      # image_arr = np.array(image)
      image_arr = self.read_image(path)
      layer_name = get_filename(path, ext=False)
    else:
       image_arr = cv_image
       layer_name = layer
       
    height, width = image_arr.shape[:2]

    # Handle different image formats
    if len(image_arr.shape) == 2:  # Grayscale
        qimg = QImage(image_arr.tobytes(), width, height, width, QImage.Format.Format_Grayscale8)
    elif len(image_arr.shape) == 3 and image_arr.shape[2] == 3:  # RGB
        qimg = QImage(image_arr.tobytes(), width, height, width * 3, QImage.Format.Format_RGB888)
    elif len(image_arr.shape) == 3 and image_arr.shape[2] == 4:  # RGBA
        qimg = QImage(image_arr.tobytes(), width, height, width * 4, QImage.Format.Format_RGBA8888)
    
    pixmap = QPixmap.fromImage(qimg)

    item = QGraphicsPixmapItem(pixmap)
    item.setOpacity(opacity)

    z_value = self.z_values[-1] + 1 if len(self.z_values) else 1
    self.z_values.append(z_value)
    item.setZValue(z_value)

    self.layer_items[layer_name] = item

    self.scene.addItem(item)
        
  def toggle_layer(self, name):
    item: QGraphicsPixmapItem = self.layer_items.get(name)
    if item:
       item.setVisible(not item.isVisible())

  def remove_raster(self, name):
     item: QGraphicsPixmapItem = self.layer_items.get(name)
     self.scene.removeItem(item)
     del self.layer_items[name]
  
  def clear_data(self):
     self.z_values = []
     self.layer_items = {}
     self.scene.clear()

class GraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Enable panning
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale_factor = 1.15  # Zoom in/out factor

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out when scrolling."""
        zoom_in = event.angleDelta().y() > 0
        if zoom_in:
            self.scale(self.scale_factor, self.scale_factor)
        else:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)