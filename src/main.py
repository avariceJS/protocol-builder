import sys
import os

# Allow running as `python src/main.py` from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Сборщик протокола')
    app.setStyle('Fusion')
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
