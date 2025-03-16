import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
    QListWidget, QListWidgetItem, QPushButton, QGraphicsProxyWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List

class ListWidget(QListWidget):
    item_changed = pyqtSignal(str)
    """Custom QListWidget with checkable items."""
    def __init__(self, options: List[str] = [], parent=None):
        super().__init__(parent)

        # Add checkable items
        for item_text in options:
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.addItem(item)

        self.itemChanged.connect(self.on_item_changed)
    
    def on_item_changed(self, item: QListWidgetItem):
        self.item_changed.emit(item.text())

    def add_item(self, option: str):
        item = QListWidgetItem(option)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        self.addItem(item)
    
    def clear_data(self):
        self.clear()

    def get_checked_items(self):
        """Return a list of checked options."""
        return [self.item(i).text() for i in range(self.count())
                if self.item(i).checkState() == Qt.CheckState.Checked]

    def get_unchecked_items(self):
        """Return a list of unchecked options."""
        return [self.item(i).text() for i in range(self.count())
                if self.item(i).checkState() == Qt.CheckState.Unchecked]