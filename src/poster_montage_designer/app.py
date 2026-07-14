import sys

from PySide6.QtWidgets import QApplication

from poster_montage_designer.windows.main_window import MainWindow


DARK_THEME = """
QMainWindow { background-color: #2b2b2b; }

QWidget {
    background-color: #2b2b2b;
    color: #d6d6d6;
    font-family: Segoe UI;
    font-size: 10pt;
}

QLabel { color: #d6d6d6; }

QLabel#projectTitleLabel,
QLabel#propertiesTitleLabel {
    font-size: 12pt;
    font-weight: 600;
    color: #f0f0f0;
}

QLabel#titleListTitleLabel,
QLabel#benchListTitleLabel {
    margin-top: 8px;
    font-weight: 600;
    color: #f0f0f0;
}


QLabel#projectSummaryLabel {
    background-color: #232323;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 5px 7px;
    color: #cfcfcf;
    font-size: 9pt;
}

QLabel#posterPreviewLabel {
    background-color: #202020;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}

QPushButton {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover { background-color: #444444; }
QComboBox {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 28px 5px 9px;
}
QComboBox:hover { background-color: #444444; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    color: #d6d6d6;
    border: 1px solid #555555;
    selection-background-color: #4a637a;
}

QPushButton:pressed { background-color: #2f2f2f; }
QPushButton:disabled {
    background-color: #303030;
    color: #777777;
    border-color: #3d3d3d;
}

QSplitter#mainSplitter::handle { background-color: #1f1f1f; }
QSplitter#mainSplitter::handle:horizontal { width: 5px; }
QSplitter#mainSplitter::handle:hover { background-color: #4a637a; }

QListWidget {
    background-color: #111111;
    border: 1px solid #5a5a5a;
    border-radius: 5px;
    padding: 3px;
    outline: none;
}

QListWidget::viewport { background-color: #111111; }

QListWidget::item {
    padding: 1px 6px;
    min-height: 15px;
    border-left: 4px solid transparent;
}

QListWidget::item:hover { background-color: #2a3036; }

QListWidget::item:selected,
QListWidget::item:selected:active,
QListWidget::item:selected:!active {
    background-color: #2d6fa3;
    color: #ffffff;
    border-left: 4px solid #b7ddff;
}

QLabel#progressLabel {
    color: #c8c8c8;
    font-size: 9pt;
}

QLabel#progressLabel[active="false"] { color: transparent; }

QProgressBar#projectProgressBar {
    background-color: #1f1f1f;
    border: 1px solid #444444;
    border-radius: 5px;
    min-height: 18px;
    max-height: 18px;
    text-align: center;
    color: transparent;
}

QProgressBar#projectProgressBar::chunk {
    background-color: #4f7899;
    border-radius: 4px;
}

QProgressBar#projectProgressBar[active="false"] {
    background-color: transparent;
    border-color: transparent;
}

QProgressBar#projectProgressBar[active="false"]::chunk { background-color: transparent; }

QSlider::groove:horizontal {
    height: 5px;
    background: #222222;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #6f91ad;
    border: 1px solid #9bbbd5;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover { background: #83a8c7; }

QScrollBar:vertical {
    background-color: #242424;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover { background-color: #666666; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background-color: #242424;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover { background-color: #666666; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal { background: none; }

QMenuBar {
    background-color: #262626;
    color: #d6d6d6;
}
QMenuBar::item:selected { background-color: #3a3a3a; }
QMenu {
    background-color: #2b2b2b;
    color: #d6d6d6;
    border: 1px solid #444444;
}
QMenu::item:selected { background-color: #4a637a; }
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
