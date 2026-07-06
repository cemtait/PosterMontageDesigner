from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
)

from poster_montage_designer.io.imdb import import_imdb_json
from poster_montage_designer.layouts.grid import calculate_grid_layout
from poster_montage_designer.models import Project
from poster_montage_designer.services.posters import get_poster
from poster_montage_designer.ui.ui_main_window import Ui_MainWindow
from poster_montage_designer.widgets.workspace import WorkspaceView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.project = Project()

        self.import_imdb_button = QPushButton("Import IMDb JSON...", self.ui.projectPanel)
        self.import_imdb_button.setObjectName("importImdbJsonButton")

        self.load_posters_button = QPushButton("Load Posters", self.ui.projectPanel)
        self.load_posters_button.setObjectName("loadPostersButton")

        self.workspace = WorkspaceView(self.ui.canvasPanel)
        self.title_list = QListWidget(self.ui.projectPanel)
        self.project_info_label = QLabel(self.ui.projectPanel)

        self._install_splitter()
        self._install_workspace()
        self._install_project_panel_widgets()

        self.ui.newMontageButton.clicked.connect(self.new_montage)
        self.ui.openMontageButton.clicked.connect(self.open_montage)
        self.import_imdb_button.clicked.connect(self.import_imdb_json)
        self.load_posters_button.clicked.connect(self.load_posters)
        self.title_list.currentItemChanged.connect(self._title_selection_changed)

        self._refresh_project_panel()
        self._refresh_properties_panel()

    def _install_splitter(self) -> None:
        self.ui.mainLayout.removeWidget(self.ui.projectPanel)
        self.ui.mainLayout.removeWidget(self.ui.canvasPanel)
        self.ui.mainLayout.removeWidget(self.ui.propertiesPanel)

        self.ui.projectPanel.setMinimumWidth(260)
        self.ui.projectPanel.setMaximumWidth(650)
        self.ui.projectPanel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

        self.ui.canvasPanel.setMinimumWidth(420)
        self.ui.canvasPanel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.ui.propertiesPanel.setMinimumWidth(260)
        self.ui.propertiesPanel.setMaximumWidth(420)
        self.ui.propertiesPanel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.ui.centralwidget)
        self.splitter.setObjectName("mainSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.ui.projectPanel)
        self.splitter.addWidget(self.ui.canvasPanel)
        self.splitter.addWidget(self.ui.propertiesPanel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.splitter.setSizes([360, 620, 300])

        self.ui.mainLayout.addWidget(self.splitter)

    def _install_workspace(self) -> None:
        if not isinstance(self.ui.canvasLayout, QVBoxLayout):
            raise RuntimeError("canvasPanel must have a QVBoxLayout.")

        self.ui.canvasLayout.removeWidget(self.ui.canvasPlaceholderLabel)
        self.ui.canvasPlaceholderLabel.deleteLater()

        self.ui.canvasLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.canvasLayout.setSpacing(0)
        self.ui.canvasLayout.addWidget(self.workspace)

    def _install_project_panel_widgets(self) -> None:
        if not isinstance(self.ui.projectLayout, QVBoxLayout):
            raise RuntimeError("projectPanel must have a QVBoxLayout.")

        self.project_info_label.setObjectName("projectInfoLabel")
        self.project_info_label.setWordWrap(True)

        title_list_title = QLabel("Title List", self.ui.projectPanel)
        title_list_title.setObjectName("titleListTitleLabel")

        self.title_list.setObjectName("titleListWidget")
        self.title_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.title_list.setAlternatingRowColors(False)
        self.title_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.title_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.ui.projectLayout.insertWidget(3, self.import_imdb_button)
        self.ui.projectLayout.insertWidget(4, self.load_posters_button)
        self.ui.projectLayout.insertWidget(6, self.project_info_label)
        self.ui.projectLayout.insertWidget(7, title_list_title)
        self.ui.projectLayout.insertWidget(8, self.title_list, 1)

    def new_montage(self) -> None:
        self.project = Project()
        self.workspace.set_page_size(27.0 * 25.4, 40.0 * 25.4)
        self._refresh_project_panel()
        self._refresh_properties_panel()

    def open_montage(self) -> None:
        self.ui.projectStatusLabel.setText("Open montage is not implemented yet.")

    def import_imdb_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import IMDb JSON",
            "projects",
            "JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        titles = import_imdb_json(file_path)

        self.project.titles = titles
        self.project.source = str(Path(file_path).name)
        self.project.dirty = True

        if self.project.name == "Untitled Montage":
            self.project.name = "IMDb Montage"

        self._refresh_project_panel()
        self._refresh_properties_panel()

    def load_posters(self) -> None:
        if not self.project.titles:
            self.ui.projectStatusLabel.setText("Import titles first.")
            return

        poster_paths: list[Path] = []
        total = len(self.project.titles)

        self.load_posters_button.setEnabled(False)

        try:
            for index, title in enumerate(self.project.titles, start=1):
                self.ui.projectStatusLabel.setText(
                    f"Loading posters {index} / {total}: {title.title}"
                )
                QApplication.processEvents()

                if not title.imdb_title_id:
                    continue

                poster_path = get_poster(title.imdb_title_id, size="w500")
                if poster_path is None:
                    continue

                title.poster_path = poster_path
                poster_paths.append(poster_path)

            layout = calculate_grid_layout(
                len(poster_paths),
                27.0 * 25.4,
                40.0 * 25.4,
            )

            self.workspace.show_poster_grid(poster_paths, layout)

            self.ui.projectStatusLabel.setText(
                f"Loaded {len(poster_paths)} / {total} posters."
            )

            self.ui.propertiesStatusLabel.setText(
                f"Grid\n\n"
                f"{layout.rows} rows × {layout.columns} columns\n"
                f"Using {layout.used_count} of {len(poster_paths)} posters\n"
                f"Omitting {layout.omitted_count}"
            )

        finally:
            self.load_posters_button.setEnabled(True)

    def _refresh_project_panel(self) -> None:
        self.ui.projectStatusLabel.setText(self.project.name)

        self.project_info_label.setText(
            f"Current Project\n"
            f"{self.project.name}\n\n"
            f"Source\n"
            f"{self.project.source}\n\n"
            f"Titles\n"
            f"{self.project.title_count}"
        )

        self.title_list.clear()

        if not self.project.titles:
            empty_item = QListWidgetItem("(empty)")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.title_list.addItem(empty_item)
            return

        for title in self.project.titles:
            label = title.title
            if title.year is not None:
                label += f" ({title.year})"

            item = QListWidgetItem(label)
            item.setToolTip(label)
            self.title_list.addItem(item)

    def _refresh_properties_panel(self) -> None:
        self.ui.propertiesStatusLabel.setText("Poster: 27 × 40 inch one-sheet")

    def _title_selection_changed(self, current, previous) -> None:
        if current is None or not self.project.titles:
            self.ui.propertiesStatusLabel.setText("Nothing selected.")
            return

        row = self.title_list.row(current)

        if row < 0 or row >= len(self.project.titles):
            self.ui.propertiesStatusLabel.setText("Nothing selected.")
            return

        title = self.project.titles[row]
        year = "Unknown year" if title.year is None else str(title.year)

        self.ui.propertiesStatusLabel.setText(
            f"{title.title}\n"
            f"{year}"
        )