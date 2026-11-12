"""Entry point:  python main.py"""

import sys

from PyQt6.QtWidgets import QApplication

from database import StudentDB
from main_window import MainWindow
from styles import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")            # consistent base on every OS; QSS is layered on top
    app.setStyleSheet(STYLESHEET)

    db = StudentDB()
    db.seed_if_empty()                # sample data on first run only

    window = MainWindow(db)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
