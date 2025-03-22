from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QSizePolicy
from typing import Optional

class ProgressBarWidget(QWidget):
  def __init__(self, parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    self.progress_bar = QProgressBar(self)
    self.progress_bar.setMinimum(0)
    self.progress_bar.setMaximum(100)
    
    # for indeterminate progress bar
    self.progress_bar.setTextVisible(False)

    layout.addWidget(self.progress_bar)

  def set_progress_range(self, min: int = 0, max: int = 0):
    self.progress_bar.setMinimum(min)
    self.progress_bar.setMaximum(max)
