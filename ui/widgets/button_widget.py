from PyQt6 import QtWidgets, QtCore
from typing import Optional

from utils.enum import ColorOptions

class ButtonWidget(QtWidgets.QPushButton):
    def __init__(
            self, 
            name: str = "...", 
            margin: int = 10,
            button_color: ColorOptions = ColorOptions.LIGHT_GRAY.value, 
            button_hover_color: ColorOptions = ColorOptions.MEDIUM_GRAY.value,
            button_font_color: ColorOptions = ColorOptions.BLACK.value, 
            fixed_width: int = None, 
            parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.setText(name)
        stylesheet = f"""
            QPushButton {{
                background-color: {button_color};
                color: {button_font_color};
                border: none;
                padding: 8px;
                border-radius: 5px;
                {f'margin-left: {margin}px; margin-right: {margin}px;' if margin else ''}
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """
        self.setStyleSheet(stylesheet)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        if fixed_width is not None:
            self.setFixedWidth(fixed_width)