import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from ui.main_window import MainWindow
from utils.common import resource_path
import os
import sys

if not sys.stdout:
    sys.stdout = open(os.devnull, 'w')
if not sys.stderr:
    sys.stderr = open(os.devnull, 'w')

def show_main_window():
    window.show()
    splash.finish(window)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Splash Screen
    splash_pixmap = QPixmap(resource_path(os.path.join("assets", "img", "ugm.png")))
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.setMask(splash_pixmap.mask())
    splash.setWindowOpacity(0.9)
    splash.show()
    
    window = MainWindow()

    # Delay showing the main window by 2 seconds (non-blocking)
    QTimer.singleShot(2000, show_main_window)
    
    sys.exit(app.exec())
