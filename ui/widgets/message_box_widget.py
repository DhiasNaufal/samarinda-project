from PyQt6.QtWidgets import QMessageBox, QWidget
from utils.enum import MessageBoxType

class CustomMessageBox():
  def __init__(
    self, 
    title: str = "", 
    message: str = "", 
    parent: QWidget = None, 
    informative_message: str = "", 
    icon=QMessageBox.Icon.Information, 
    buttons=QMessageBox.StandardButton.Ok
  ) -> None:
    self.parent = parent
    self.title = title
    self.icon = icon
    self.buttons = buttons
    self.message = message
    self.informative_message = informative_message

  def show(self): 
    message_box = QMessageBox(self.parent)
    
    message_box.setWindowTitle(self.title)
    message_box.setIcon(self.icon)
    message_box.setText(self.message)
    message_box.setInformativeText(self.informative_message)
    message_box.setStandardButtons(self.buttons)

    return message_box.exec()
