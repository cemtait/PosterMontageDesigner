from pathlib import Path

from PySide6.QtCore import QObject, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from poster_montage_designer.models import Film, Project
from poster_montage_designer.widgets.workspace import WorkspaceView


class MainWindow:
    def __init__(self) -> None:
        ui_path = Path(__file__).parent.parent / "ui" / "main_window.ui"

        loader = QUiLoader()
        self.window = loader.load(str(ui_path))

        if self.window is None:
            raise RuntimeError(f"Could not load UI file: {ui_path}")

        self.project = Project()

        self.window.resize(1200, 750)

        self.new_button = self._find(QPushButton, "newMontageButton")
        self.open_button = self._find(QPushButton, "openMontageButton")
        self.status_label = self._find(QLabel, "projectStatusLabel")
        self.properties_status_label = self._find(QLabel, "propertiesStatusLabel")

        self.project_panel = self._find(QWidget, "projectPanel")
        self.canvas_panel = self._find(QWidget, "canvasPanel")

        self.workspace = WorkspaceView(self.canvas_panel)
        self.film_list = QListWidget(self.project_panel)
        self.project_info_label = QLabel(self.project_panel)

        self._install_workspace()
        self._install_project_panel_widgets()

        self.new_button.clicked.connect(self.new_montage)
        self.open_button.clicked.connect(self.open_montage)
        self.film_list.currentItemChanged.connect(self._film_selection_changed)

        self._refresh_project_panel()
        self._refresh_properties_panel()

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

    def _install_project_panel_widgets(self) -> None:
        layout = self.project_panel.layout()

        if not isinstance(layout, QVBoxLayout):
            raise RuntimeError("projectPanel must have a QVBoxLayout.")

        self.project_info_label.setObjectName("projectInfoLabel")
        self.project_info_label.setWordWrap(True)

        film_list_title = QLabel("Film List", self.project_panel)
        film_list_title.setObjectName("filmListTitleLabel")

        self.film_list.setObjectName("filmListWidget")
        self.film_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.film_list.setAlternatingRowColors(False)

        layout.insertWidget(4, self.project_info_label)
        layout.insertWidget(5, film_list_title)
        layout.insertWidget(6, self.film_list, 1)

    def new_montage(self) -> None:
        self.project = Project()
        self.workspace.set_page_size(27.0 * 25.4, 40.0 * 25.4)

        # Temporary sample films so the permanent list can be judged visually.
        # This gets replaced by real IMDb import in the next slice.
        self.project.films = [
            Film("King Kong", 2005),
            Film("Avatar", 2009),
            Film("The Hobbit: An Unexpected Journey", 2012),
            Film("The Hobbit: The Desolation of Smaug", 2013),
            Film("Guardians of the Galaxy Vol. 2", 2017),
            Film("Avengers: Infinity War", 2018),
            Film("The Falcon and the Winter Soldier", 2021),
        ]

        self._refresh_project_panel()
        self._refresh_properties_panel()

    def open_montage(self) -> None:
        self.status_label.setText("Open montage is not implemented yet.")

    def _refresh_project_panel(self) -> None:
        self.status_label.setText(self.project.name)

        self.project_info_label.setText(
            f"Current Project\n"
            f"{self.project.name}\n\n"
            f"Source\n"
            f"{self.project.source}\n\n"
            f"Films\n"
            f"{self.project.film_count}"
        )

        self.film_list.clear()

        if not self.project.films:
            empty_item = QListWidgetItem("(empty)")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.film_list.addItem(empty_item)
            return

        for film in self.project.films:
            label = film.title if film.year is None else f"{film.title} ({film.year})"
            self.film_list.addItem(QListWidgetItem(label))

    def _refresh_properties_panel(self) -> None:
        self.properties_status_label.setText("Poster: 27 × 40 inch one-sheet")

    def _film_selection_changed(self, current, previous) -> None:
        if current is None or not self.project.films:
            self.properties_status_label.setText("Nothing selected.")
            return

        row = self.film_list.row(current)

        if row < 0 or row >= len(self.project.films):
            self.properties_status_label.setText("Nothing selected.")
            return

        film = self.project.films[row]
        year = "Unknown year" if film.year is None else str(film.year)

        self.properties_status_label.setText(
            f"Selected Film\n\n"
            f"{film.title}\n"
            f"{year}"
        )

    def show(self) -> None:
        self.window.show()