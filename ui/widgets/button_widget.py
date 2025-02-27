from PyQt6 import QtWidgets, QtCore

class ButtonWidget(QtWidgets.QPushButton):
    def __init__(
            self, 
            name="...", 
            margin=10,
            button_color="#f0f0f0", 
            button_font_color="black", 
            fixed_width=None, 
            parent=None):
        super().__init__(parent)

        self.setText(name)
        stylesheet = f"background-color: {button_color}; color: {button_font_color}; {f'margin-left: {margin}px; margin-right: {margin}px;' if margin else ''}"
        self.setStyleSheet(stylesheet)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        if fixed_width is not None:
            self.setFixedWidth(fixed_width)