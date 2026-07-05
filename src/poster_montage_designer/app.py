import sys

from PySide6.QtWidgets import QApplication

from poster_montage_designer.windows.main_window import MainWindow


DARK_THEME = """
QMainWindow {
    background-color: #2b2b2b;
}

QWidget {
    background-color: #2b2b2b;
    color: #d6d6d6;
    font-family: Segoe UI;
    font-size: 10pt;
}

QLabel {
    color: #d6d6d6;
}

QPushButton {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #444444;
}

QPushButton:pressed {
    background-color: #2f2f2f;
}
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()