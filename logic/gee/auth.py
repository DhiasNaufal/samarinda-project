import ee
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from utils.enum import LogLevel

class GEEAuth(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, project_name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.project_name = project_name

    def run(self):
        try:
            """Authenticate and initialize the Google Earth Engine."""
            ee.Authenticate()
            ee.Initialize(project=self.project_name)
            self.finished.emit(f"Terautentikasi dengan projek: {self.project_name}", LogLevel.NONE.value)
        except Exception as e:
            self.finished.emit(f"Autentikasi gagal: {str(e)}", LogLevel.ERROR.value)