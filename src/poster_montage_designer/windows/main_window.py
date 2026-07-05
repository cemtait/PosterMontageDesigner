from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from poster_montage_designer.widgets.workspace import WorkspaceView


class MainWindow:
    def __init__(self) -> None:
        ui_path = Path(__file__).parent.parent / "ui" / "main_window.ui"

        loader = QUiLoader()
        self.window = loader.load(str(ui_path))

        if self.window is None:
            raise RuntimeError(f"Could not load UI file: {ui_path}")

        self.window.resize(1200, 750)

        self.new_button = self._find(QPushButton, "newMontageButton")
        self.open_button = self._find(QPushButton, "openMontageButton")
        self.status_label = self._find(QLabel, "projectStatusLabel")
        self.properties_status_label = self._find(QLabel, "propertiesStatusLabel")

        self.canvas_panel = self._find(QWidget, "canvasPanel")
        self.workspace = WorkspaceView(self.canvas_panel)
        self._install_workspace()

        self.new_button.clicked.connect(self.new_montage)
        self.open_button.clicked.connect(self.open_montage)

    def _find(self, widget_type: type, object_name: str) -> QObject:
        widget = self.window.findChild(widget_type, object_name)

        if widget is None:
            raise RuntimeError(f"Could not find widget named: {object_name}")

        return widget

    def _install_workspace(self) -> None:
        layout = self.canvas_panel.layout()

        if not isinstance(layout, QVBoxLayout):
            raise RuntimeError("canvasPanel must have a QVBoxLayout.")

        placeholder = self.window.findChild(QLabel, "canvasPlaceholderLabel")
        if placeholder is not None:
            layout.removeWidget(placeholder)
            placeholder.deleteLater()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.workspace)

    def new_montage(self) -> None:
        self.status_label.setText("Untitled montage")
        self.properties_status_label.setText("Poster: 27 × 40 inch one-sheet")
        self.workspace.set_page_size(27.0 * 25.4, 40.0 * 25.4)

    def open_montage(self) -> None:
        self.status_label.setText("Open montage is not implemented yet.")

    def show(self) -> None:
        self.window.show()