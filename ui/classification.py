import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QHBoxLayout, QDateEdit, QTextEdit, QSlider, QComboBox,QProgressBar,QSizePolicy
# from .widgets.text_input_widget import TextInputWidget
from .widgets.file_input_widget import FileInputWidget
from .widgets.button_widget import ButtonWidget
from utils.enum import LogLevel, FileType
from .widgets.log_widget import LogWidget
from typing import Optional
# from predict import main
from logic.classificationBg import ClassificationBgProcess
os.environ["SM_FRAMEWORK"] = "tf.keras"
class Classification(QWidget):
    def __init__(self, parent : Optional[QWidget] = None) -> None:
        super().__init__(parent)
        os.environ["SM_FRAMEWORK"] = "tf.keras"
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.project_name = QLabel("Klasifikasi Kelapa Sawit")
        main_layout.addWidget(self.project_name)

        self.imageInput = FileInputWidget(
            button_name="Muat Gambar",
            filetype=FileType.TIFF.value,
            file_dialog_title="Pilih Dokumen TIF"
        )

        self.imageInput.path_selected.connect(self.info)
        main_layout.addWidget(self.imageInput)

  
        self.project_name = QLabel("Select Model")
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["U-Net", "MVT", "ResNet"])
        main_layout.addWidget(self.model_dropdown)
        stylesheet = f"""
            QComboBox {{
                {f'margin: 10px;'}
            }}
        """
        self.setStyleSheet(stylesheet)
        self.start_process = ButtonWidget(name="Mulai Proses Klasifikasi")
        self.start_process.clicked.connect(self.startClassification)
        main_layout.addWidget(self.start_process)
      

        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        self.progress_bar.setVisible(False)
        self.log_window = LogWidget()
        main_layout.addWidget(self.log_window)
        self.setLayout(main_layout) 
        pass
    
    def info(self, data):
        self.log_window.log_message("TIF berhasil dimuat!")

    def startClassification(self):
        #start

        self.log_window.log_message('Memulai Klasifikasi')
        # ClassificationBgProcess(self.imageInput.get_value)
        self.GEE_auth_thread = ClassificationBgProcess(self.imageInput.get_value)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        self.progress_bar.setVisible(True)
        # end
        self.GEE_auth_thread.progress.connect(lambda message : self.log_window.log_message(message))
        self.GEE_auth_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        # self.GEE_auth_thread.finished.connect(lambda: self.auth_btn.setEnabled(True))
        # self.GEE_auth_thread.finished.connect(self.GEE_auth_thread.deleteLater)
        self.GEE_auth_thread.start()

        # self.auth_btn.setEnabled(False)

