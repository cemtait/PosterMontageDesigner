from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from poster_montage_designer.models import Project
from poster_montage_designer.io.imdb import import_imdb_json
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

        self.workspace = WorkspaceView(self.ui.canvasPanel)
        self.title_list = QListWidget(self.ui.projectPanel)
        self.project_info_label = QLabel(self.ui.projectPanel)

        self._install_splitter()
        self._install_workspace()
        self._install_project_panel_widgets()

        self.ui.newMontageButton.clicked.connect(self.new_montage)
        self.ui.openMontageButton.clicked.connect(self.open_montage)
        self.import_imdb_button.clicked.connect(self.import_imdb_json)
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
        self.ui.projectLayout.insertWidget(5, self.project_info_label)
        self.ui.projectLayout.insertWidget(6, title_list_title)
        self.ui.projectLayout.insertWidget(7, self.title_list, 1)

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
        imdb_id = title.imdb_title_id or "No IMDb ID"

        self.ui.propertiesStatusLabel.setText(
            f"Selected Title\n\n"
            f"{title.title}\n"
            f"{year}\n\n"
            f"{imdb_id}"
        )