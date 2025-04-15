from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt

from typing import Optional, Union

from utils.enum import TextType
class TextInputWidget(QWidget):
    def __init__(
            self, 
            label: str = "", 
            defaultValue: TextType = "", 
            type: TextType = TextType.STRING.value, 
            parent: Optional[QWidget] = None
        ) -> None:
        super().__init__(parent)

        self.label = label
        self.type = type
        self.defaultValue = defaultValue if defaultValue else None

        self.init_ui()
    
    def set_label(self, label: str = "") -> None:
        self.label_widget.setText(label)

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label_widget = QLabel(self.label)
        layout.addWidget(self.label_widget)

        self.input = QLineEdit() 
        if self.defaultValue:
            self.input.setText(str(self.defaultValue))
        layout.addWidget(self.input)

    def set_read_only(self, read_only: bool = True):
        self.input.setReadOnly(read_only)
    
    @property
    def is_read_only(self) -> bool:
        return self.input.isReadOnly()

    def set_value(self, val: str) -> None:
        self.input.setText(val)

    @property
    def get_value(self) -> Union[float, int, str]:
        if self.type == TextType.FLOAT.value:
            return float(self.input.text())
        elif self.type == TextType.INT.value:
            return int(self.input.text())
        else:
            return self.input.text()