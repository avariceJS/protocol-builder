import sys
import os

# Allow running as `python src/main.py` from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.ui.styles import APP_STYLE
from src.utils.assets import app_icon_path


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Сборщик протокола')
    icon = QIcon(app_icon_path())
    if not icon.isNull():
        app.setWindowIcon(icon)
    app.setStyle('Fusion')
    app.setStyleSheet(APP_STYLE)

    if sys.platform == 'win32':
        from src.ui.install_prompt import maybe_offer_install
        if maybe_offer_install(app):
            sys.exit(0)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
