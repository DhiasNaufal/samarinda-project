from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, List

class DropdownWidget(QWidget):
  value_changed = pyqtSignal(str)

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
    self.dropdown.currentTextChanged.connect(self.value_changed)
    layout.addWidget(self.dropdown)
  
  def set_options(self, options: list):
    if not len(options):
      return
    
    self.dropdown.clear()
    self.dropdown.addItems(options)

  @property
  def get_value(self):
    return self.dropdown.currentText()
    