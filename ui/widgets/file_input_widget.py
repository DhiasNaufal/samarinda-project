from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt

from typing import Optional, List

from .button_widget import ButtonWidget

from utils.enum import FileType, FileInputType, ColorOptions
class FileInputWidget(QWidget):
    path_selected = pyqtSignal(str)

    def __init__(
            self, 
            label: str = "", 
            button_name: str = "Pilih File", 
            button_width: Optional[int] = None, 
            button_font_color: ColorOptions = ColorOptions.BLACK.value, 
            button_color: ColorOptions = ColorOptions.LIGHT_GRAY.value,  
            filetype: List[FileType] = [FileType.ALL_FILES.value],
            file_input_type: FileInputType = FileInputType.FILEPATH.value,
            file_dialog_title: str = "Pilih File",
            default_path: str = "-",
            parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.default_label = label
        self.button_name = button_name
        self.button_width = button_width
        self.button_color = button_color
        self.button_font_color = button_font_color

        # input dialog
        self.file_input_type = file_input_type
        self.filetype = ";;".join(filetype)
        self.file_dialog_title = file_dialog_title

        self.path = default_path

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if self.default_label:
            self.label = QLabel(f"{self.default_label} : {self.path}")
            self.label.setWordWrap(True)
            layout.addWidget(self.label)

        # Button to choose directory
        self.button = ButtonWidget(
            name=self.button_name, 
            button_color=self.button_color, 
            button_font_color=self.button_font_color,
            margin=0,
            fixed_width=self.button_width)
        self.button.clicked.connect(self.on_button_clicked)
        layout.addWidget(self.button)

    def on_button_clicked(self) -> None:
        """
        """
        if self.file_input_type == FileInputType.FILENAME.value:
            # Open a file dialog to choose filepath and set the name
            path, _ = QFileDialog.getSaveFileName(self, self.file_dialog_title, "", self.filetype)

        elif self.file_input_type == FileInputType.DIRECTORY.value:
            # Open file dialog for choosing a directory
            path = QFileDialog.getExistingDirectory(self, self.file_dialog_title)

        else:
            # Open file dialog for choosing a file
            path, _ = QFileDialog.getOpenFileName(self, self.file_dialog_title, "", self.filetype)

        if path:
            # change label name
            # if self.default_label:
            #     self.label.setText(f"{self.default_label} : {path}")

            # emit the signal
            self.path = path
            self.path_selected.emit(path)

    def set_label(self, label: str):
        self.label.setText(label)

    def set_path(self, path: str):
        self.path = path
        label = self.label.text().split(":")
        self.label.setText(f"{label[0]} : {path}")

    @property
    def get_value(self) -> str:
        return self.path


