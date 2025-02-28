from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from utils.enum import LogLevel, ColorOptions
from utils.common import get_current_time

class LogWidget(QWidget):
  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)

    self.log_window = QTextEdit()
    self.log_window.setReadOnly(True)
    layout.addWidget(self.log_window, 1)

    self.setLayout(layout)

  def log_message(
      self, text: str, 
      type: str = LogLevel.NONE.value
  ):
    if type == LogLevel.ERROR.value:
      color = ColorOptions.RED.value
    elif type == LogLevel.WARNING.value:
      color = ColorOptions.Yellow.value
    else:
      color = ColorOptions.BLACK.value

    text = f"{get_current_time()}: {f'[{type}]' if type else ''} {text}"
    self.log_window.append(f'<span style="color:{color};">{text}</span>')

    
