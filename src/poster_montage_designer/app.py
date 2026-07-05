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

QLabel#projectTitleLabel,
QLabel#propertiesTitleLabel {
    font-size: 12pt;
    font-weight: 600;
    color: #f0f0f0;
}

QLabel#filmListTitleLabel {
    margin-top: 8px;
    font-weight: 600;
    color: #f0f0f0;
}

QLabel#projectInfoLabel {
    color: #bdbdbd;
    line-height: 130%;
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

QListWidget#filmListWidget {
    background-color: #242424;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}

QListWidget#filmListWidget::item {
    padding: 5px 6px;
    border-radius: 3px;
}

QListWidget#filmListWidget::item:hover {
    background-color: #333333;
}

QListWidget#filmListWidget::item:selected {
    background-color: #4a637a;
    color: #ffffff;
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