from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import Optional

class SatelitImage(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    label = QLabel("<h1> Fitur ini masih dalam tahap pengembangan </h1>")
    layout.addWidget(label)
