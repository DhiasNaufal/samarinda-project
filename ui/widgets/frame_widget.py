from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLayout
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

    main_layout = QVBoxLayout(self)
    main_layout.addWidget(self.frame)

  def add_widget(self, widget: QWidget):
    self.frame_layout.addWidget(widget)

  def add_layout(self, layout: QLayout):
    self.frame_layout.addLayout(layout)

  def set_frame_size(self, width, height):
    self.frame.setFixedSize(width, height)