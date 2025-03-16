from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit
from PyQt6.QtCore import pyqtSignal, QDate, Qt

from utils.enum import LayoutDirection

class DateWidget(QWidget):
  date_changed = pyqtSignal(str)

  def __init__(
      self, 
      label: str = "",
      default_value: str = "",
      layout_direction: LayoutDirection = LayoutDirection.HORIZONTAL.value,
      parent: QWidget | None = None
    ) -> None:
    super().__init__(parent)
    
    self.default_value = QDate.fromString(default_value, "yyyy-MM-dd") if default_value else QDate.currentDate()
    self.layout_direction = layout_direction
    self.label = label

    self.init_ui()

  def init_ui(self) -> None:
    if self.layout_direction == LayoutDirection.VERTICAL.value:
      layout = QVBoxLayout(self)
      layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    else:
      layout = QHBoxLayout(self) 
      layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    
    label = QLabel(self.label)
    layout.addWidget(label)

    self.date = QDateEdit()
    self.date.setCalendarPopup(True)
    self.date.setDate(self.default_value)
    self.date.dateChanged.connect(self.on_date_changed)
    layout.addWidget(self.date)

  def on_date_changed(self, date: QDate) -> None:
    self.date_changed.emit(date.toString("yyyy-MM-dd"))

  def get_date_string(self, format: str = "yyyy-MM-dd") -> str:
    return self.date.date().toString(format)
  
  def get_date(self):
    return self.date.date()


    
