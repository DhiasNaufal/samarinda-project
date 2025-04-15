from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from typing import Optional

class FrameWidget(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.frame = QFrame(self)
    self.frame.setStyleSheet("QFrame#mainFrame { border: 1px solid lightgray; }")
    self.frame.setObjectName("mainFrame")
    self.frame.setFrameShape(QFrame.Shape.Box)

    # define a layout for the frame to hold widgets
    self.frame_layout = QVBoxLayout(self.frame)
    self.frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    main_layout = QVBoxLayout(self)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(self.frame)
  
  @property
  def add_spacer_item(self):
    spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
    self.frame_layout.addSpacerItem(spacer)

  def add_widget(self, widget: QWidget):
    self.add_spacer_item
    self.frame_layout.addWidget(widget)

  def add_layout(self, layout: QLayout):
    self.add_spacer_item
    self.frame_layout.addLayout(layout)

  def set_frame_size(self, width, height):
    self.frame.setFixedSize(width, height)