from PyQt5 import QtWidgets, QtCore
from utils.common import outline_stylesheet

class DropdownComponent(QtWidgets.QWidget):
    on_changed = QtCore.pyqtSignal(str)

    def init(self, label="", options=[], dropdown_name="", parent = None) -> None:
        super().init(parent)

        self.label = label
        self.options = options

        self.dropdown_name = dropdown_name

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel(self.label)
        layout.addWidget(label)


        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setMinimumHeight(25)
        self.combo_box.setObjectName(self.dropdown_name)
        self.combo_box.setStyleSheet(outline_stylesheet)

        for option in self.options:
            self.combo_box.addItem(option)

        layout.addWidget(self.combo_box)

        self.combo_box.currentIndexChanged.connect(lambda: self.on_changed.emit(self.combo_box.currentText()))

    @property
    def get_selected_item(self):
        return self.combo_box.currentText()