from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QSpacerItem, QSizePolicy
from utils.enum import LogType
from utils.common import get_current_time

class LogWidget(QWidget):
  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)

    self.log_window = QTextEdit()
    self.log_window.setReadOnly(True)
    layout.addWidget(self.log_window, 1)

    spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    layout.addItem(spacer)

    self.setLayout(layout)

  def log_message(
      self, text: str, 
      type: str = LogType.NONE.value
  ):
    if type == LogType.ERROR.value:
      color = "red"
    elif type == LogType.WARNING.value:
      color = "yellow"
    else:
      color = "black"

    text = f"{get_current_time()}: {f'[{type}]' if type else ''} {text}"
    self.log_window.append(f'<span style="color:{color};">{text}</span>')

    
