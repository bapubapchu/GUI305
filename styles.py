"""Qt stylesheet (QSS) so the app does not look like the default skin."""

from pathlib import Path

_ASSETS = Path(__file__).resolve().parent / "assets"

_QSS = """
QMainWindow, QWidget#central { background: #f4f1ea; }
QWidget { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 13px; color: #243238; }

QMenuBar { background: #1f4e5f; color: #ffffff; }
QMenuBar::item:selected { background: #2d6a7f; }
QMenu { background: #ffffff; border: 1px solid #c9c4b8; }
QMenu::item:selected { background: #d7e8ec; color: #243238; }

QGroupBox {
    background: #ffffff; border: 1px solid #d8d3c6; border-radius: 8px;
    margin-top: 14px; padding: 12px 10px 10px 10px; font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #1f4e5f; }

QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: #ffffff; border: 1px solid #b9b3a4; border-radius: 5px; padding: 4px 6px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #1f4e5f; }
QLineEdit[invalid="true"], QComboBox[invalid="true"], QSpinBox[invalid="true"] {
    border: 1px solid #c0392b; background: #fdeeee;
}

/* Custom borders remove Qt's built-in arrows, so the arrow sub-controls are styled explicitly. */
QSpinBox { padding-right: 24px; }
QComboBox { padding-right: 26px; }

QComboBox QLineEdit { border: none; background: transparent; padding: 0; }
QComboBox::drop-down {
    subcontrol-origin: padding; subcontrol-position: top right; width: 24px;
    border-left: 1px solid #b9b3a4; background: #e3ede9;
    border-top-right-radius: 5px; border-bottom-right-radius: 5px;
}
QComboBox::down-arrow { image: url("@ARROW_DOWN@"); width: 10px; height: 6px; }
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid #b9b3a4;
    selection-background-color: #d7e8ec; selection-color: #243238;
}

QSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right; width: 22px;
    border-left: 1px solid #b9b3a4; border-bottom: 1px solid #b9b3a4; background: #e3ede9;
    border-top-right-radius: 5px;
}
QSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right; width: 22px;
    border-left: 1px solid #b9b3a4; background: #e3ede9;
    border-bottom-right-radius: 5px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #cfe1dc; }
QSpinBox::up-arrow { image: url("@ARROW_UP@"); width: 10px; height: 6px; }
QSpinBox::down-arrow { image: url("@ARROW_DOWN@"); width: 10px; height: 6px; }

QPushButton {
    background: #1f4e5f; color: #ffffff; border: none; border-radius: 5px;
    padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { background: #2d6a7f; }
QPushButton:pressed { background: #163b48; }
QPushButton:disabled { background: #b9c4c8; color: #eef1f2; }
QPushButton#deleteButton { background: #b5483a; }
QPushButton#deleteButton:hover { background: #cf5a4a; }
QPushButton#clearButton { background: #8a8577; }
QPushButton#clearButton:hover { background: #9d9889; }

QLabel#errorLabel { color: #c0392b; font-weight: 600; }
QLabel#previewLabel { color: #1f4e5f; font-weight: 600; }
QLabel#summaryLabel { color: #5b6b72; }

QTableWidget {
    background: #ffffff; alternate-background-color: #f1f6f7;
    border: 1px solid #d8d3c6; border-radius: 6px; gridline-color: #e6e2d7;
    selection-background-color: #1f4e5f; selection-color: #ffffff;
}
QHeaderView::section {
    background: #e3ede9; color: #1f4e5f; padding: 6px; border: none;
    border-right: 1px solid #d8d3c6; font-weight: 700;
}

QProgressBar {
    border: 1px solid #b9b3a4; border-radius: 5px; background: #ffffff;
    text-align: center; height: 16px;
}
QProgressBar::chunk { background: #4e9a7b; border-radius: 4px; }

QSlider::groove:horizontal { height: 6px; background: #d8d3c6; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #1f4e5f; width: 16px; margin: -6px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal { background: #4e9a7b; border-radius: 3px; }

QStatusBar { background: #e9e5da; color: #3d4a50; }
"""

# Absolute paths (built at runtime, forward slashes) so the arrows load from any working folder.
STYLESHEET = (_QSS
              .replace("@ARROW_DOWN@", (_ASSETS / "arrow_down.png").as_posix())
              .replace("@ARROW_UP@", (_ASSETS / "arrow_up.png").as_posix()))
