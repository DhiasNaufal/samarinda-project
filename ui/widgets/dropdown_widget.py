from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt
from typing import Optional, List

class DropdownWidget(QWidget):
  def __init__(
      self, 
      label: str = "",
      dropdown_options: List[str] = List,
      parent: Optional[QWidget] = None) -> None:
    super().__init__(parent)

    self.init_ui(label, dropdown_options)

  def init_ui(self, label_name: str, options: List):
    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    label = QLabel(label_name)
    layout.addWidget(label)

    self.dropdown = QComboBox()
    self.dropdown.addItems(options)
    layout.addWidget(self.dropdown)

  @property
  def get_value(self):
    return self.dropdown.currentText()
    