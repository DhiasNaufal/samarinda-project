from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLayout
from typing import Optional
from utils.enum import LayoutType

class DynamicWidget(QWidget):
  def __init__(self, layout_type: LayoutType = LayoutType.VERTICAL.value, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui(layout_type)
  
  def init_ui(self, layout_type):
    self.main_layout = QVBoxLayout(self) if layout_type == LayoutType.VERTICAL.value else QHBoxLayout(self)
    self.setLayout(self.main_layout)

  def add_widget(self, widget: QWidget):
    self.main_layout.addWidget(widget)

  def add_layout(self, layout: QLayout):
    self.main_layout.addLayout(layout)

  def clear_widget(self):
    while self.main_layout.count():
      item = self.main_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
    

