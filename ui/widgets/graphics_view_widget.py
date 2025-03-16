from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QGraphicsPixmapItem, QComboBox, QGraphicsProxyWidget
from PyQt6.QtGui import QPainter, QPixmap, QImage, QWheelEvent

from typing import Optional
from PIL import Image

import numpy as np

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


  def load_raster(self, path: str, opacity: float = 1.0):
    image = Image.open(path)
    image_arr = np.array(image)
    height, width = image_arr.shape[:2]

    # Handle different image formats
    if len(image_arr.shape) == 2:  # Grayscale
        qimg = QImage(image_arr.data, width, height, width, QImage.Format.Format_Grayscale8)
    elif len(image_arr.shape) == 3 and image_arr.shape[2] == 3:  # RGB
        qimg = QImage(image_arr.data, width, height, width * 3, QImage.Format.Format_RGB888)
    elif len(image_arr.shape) == 3 and image_arr.shape[2] == 4:  # RGBA
        qimg = QImage(image_arr.data, width, height, width * 4, QImage.Format.Format_RGBA8888)
    
    pixmap = QPixmap.fromImage(qimg)

    item = QGraphicsPixmapItem(pixmap)
    item.setOpacity(opacity)

    z_value = self.z_values[-1] + 1 if len(self.z_values) else 1
    self.z_values.append(z_value)
    item.setZValue(z_value)

    layer_name = get_filename(path, ext=False)
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