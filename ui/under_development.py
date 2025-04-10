from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from typing import Optional
from utils.common import resource_path

import os
class UnderDevelopment(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0) 
       
        image_layout = QHBoxLayout()

        # Load Image
        pixmap = QPixmap(resource_path(os.path.join("assets", "img", "under_dev.png"))) 
        image_label = QLabel(self)

        if pixmap.isNull():
            image_label.setText("Image not found!") 
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            resized_pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(resized_pixmap)
        image_layout.addStretch()  
        image_layout.addWidget(image_label)
        image_layout.addStretch()  
        main_layout.addLayout(image_layout)
        self.setLayout(main_layout)
