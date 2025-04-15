from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLayout, QSpacerItem, QSizePolicy
from typing import Optional
from utils.enum import LayoutType

class DynamicWidget(QWidget):
  def __init__(self, layout_type: LayoutType = LayoutType.VERTICAL.value, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui(layout_type)
  
  def init_ui(self, layout_type):
    if layout_type == LayoutType.VERTICAL.value:
      self.main_layout = QVBoxLayout(self)
      self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    else:
      self.main_layout = QHBoxLayout(self)
      self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    self.setLayout(self.main_layout)
  
  @property
  def add_spacer_item(self):
    spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
    self.main_layout.addSpacerItem(spacer)

  def add_widget(self, widget: QWidget):
    self.add_spacer_item
    self.main_layout.addWidget(widget)

  def add_layout(self, layout: QLayout):
    self.add_spacer_item
    self.main_layout.addLayout(layout)

  def clear_widget(self):
    while self.main_layout.count():
      item = self.main_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()
    

