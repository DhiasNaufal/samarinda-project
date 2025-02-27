from PyQt6 import QtWidgets, QtCore

class Button(QtWidgets.QPushButton):
    def __init__(self, name="...", button_color="#f0f0f0", button_font_color="black", fixed_width=None, parent=None):
        super().__init__(parent)

        self.setText(name)
        stylesheet = f"background-color: {button_color}; color: {button_font_color};"
        self.setStyleSheet(stylesheet)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        if fixed_width is not None:
            self.setFixedWidth(fixed_width)