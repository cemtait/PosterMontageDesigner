from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFontDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QSlider,
    QSplitter,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from poster_montage_designer.config import AppConfig, load_config, save_config
from poster_montage_designer.io.imdb import import_imdb_json
from poster_montage_designer.layouts.grid import GridLayout, calculate_grid_layout
from poster_montage_designer.models import Project, Title
from poster_montage_designer.services.posters import (
    get_poster,
    get_poster_candidate_count,
)
from poster_montage_designer.services.tmdb import lookup_imdb_id
from poster_montage_designer.ui.ui_main_window import Ui_MainWindow
from poster_montage_designer.widgets.workspace import WorkspaceView


MM_PER_INCH = 25.4
DEFAULT_PAGE_WIDTH_MM = 27.0 * MM_PER_INCH
DEFAULT_PAGE_HEIGHT_MM = 40.0 * MM_PER_INCH

CANVAS_PRESETS: dict[str, tuple[float, float]] = {
    "One Sheet 27 × 40 in": (27.0 * MM_PER_INCH, 40.0 * MM_PER_INCH),
    "A3 Portrait": (297.0, 420.0),
    "A3 Landscape": (420.0, 297.0),
    "A2 Portrait": (420.0, 594.0),
    "A2 Landscape": (594.0, 420.0),
    "16:9 Projection": (1016.0, 571.5),
    "4:3 Projection": (1016.0, 762.0),
    "2.39:1 CinemaScope": (1016.0, 425.1),
    "1:1 Square": (800.0, 800.0),
    "Custom": (DEFAULT_PAGE_WIDTH_MM, DEFAULT_PAGE_HEIGHT_MM),
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)

        self.config = load_config()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.tmdb_token_edit = QLineEdit(self)
        self.tmdb_token_edit.setText(self.config.tmdb_read_token)
        self.tmdb_token_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.export_width_edit = QLineEdit(self)
        self.export_width_edit.setText("4961")

        self.export_note_label = QLabel(
            "Export resolution controls will become active when final rendering is implemented.",
            self,
        )
        self.export_note_label.setWordWrap(True)

        form.addRow("TMDb read token", self.tmdb_token_edit)
        form.addRow("Target export width", self.export_width_edit)

        buttons = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel", self)
        self.save_button = QPushButton("Save", self)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout.addLayout(form)
        layout.addWidget(self.export_note_label)
        layout.addStretch(1)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save)

    def _save(self) -> None:
        save_config(
            AppConfig(
                tmdb_read_token=self.tmdb_token_edit.text().strip(),
            )
        )
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.project = Project()
        self.poster_entries: list[tuple[str, Path]] = []
        self.missing_poster_titles: list[str] = []
        self.omitted_layout_titles: list[str] = []
        self.current_layout: GridLayout | None = None
        self._updating_canvas_controls = False
        self.undo_stack: list[Project] = []
        self._restoring_undo = False

        self.create_from_imdb_button = QPushButton("Create from IMDb JSON...", self.ui.projectPanel)
        self.create_from_imdb_button.setObjectName("createFromImdbButton")

        self.chronological_button = QPushButton("Chronological", self.ui.projectPanel)
        self.chronological_button.setObjectName("chronologicalButton")

        self.box_office_button = QPushButton("Box Office", self.ui.projectPanel)
        self.box_office_button.setObjectName("boxOfficeButton")
        self.box_office_button.setToolTip("Sort by cached/downloaded TMDb box office revenue where available.")

        self.shuffle_button = QPushButton("Shuffle", self.ui.projectPanel)
        self.shuffle_button.setObjectName("shuffleButton")

        self.bench_selected_button = QPushButton("Bench Selected", self.ui.projectPanel)
        self.bench_selected_button.setObjectName("benchSelectedButton")

        self.promote_selected_button = QPushButton("Promote Selected", self.ui.projectPanel)
        self.promote_selected_button.setObjectName("promoteSelectedButton")

        self.swap_selected_button = QPushButton("Swap Selected", self.ui.projectPanel)
        self.swap_selected_button.setObjectName("swapSelectedButton")
        self.swap_selected_button.setEnabled(False)

        self.workspace = WorkspaceView(self.ui.canvasPanel)
        self.title_list = QListWidget(self.ui.projectPanel)
        self.bench_list = QListWidget(self.ui.projectPanel)
        self.progress_label = QLabel("", self.ui.projectPanel)
        self.progress_bar = QProgressBar(self.ui.projectPanel)

        self.poster_preview_label = QLabel(self.ui.propertiesPanel)
        self.poster_controls_layout = QHBoxLayout()
        self.previous_poster_button = QPushButton("◀", self.ui.propertiesPanel)
        self.poster_counter_label = QLabel("0 / 0", self.ui.propertiesPanel)
        self.next_poster_button = QPushButton("▶", self.ui.propertiesPanel)

        self.airiness_label = QLabel("Airiness: 50", self.ui.propertiesPanel)
        self.airiness_slider = QSlider(Qt.Orientation.Horizontal, self.ui.propertiesPanel)

        self.canvas_preset_combo = QComboBox(self.ui.propertiesPanel)
        self.canvas_width_spin = QDoubleSpinBox(self.ui.propertiesPanel)
        self.canvas_height_spin = QDoubleSpinBox(self.ui.propertiesPanel)
        self.canvas_color_button = QPushButton("Canvas Colour...", self.ui.propertiesPanel)

        self.centerpiece_enabled_check = QCheckBox("Centrepiece text", self.ui.propertiesPanel)
        self.centerpiece_text_edit = QTextEdit(self.ui.propertiesPanel)
        self.centerpiece_font_button = QPushButton("Font...", self.ui.propertiesPanel)
        self.centerpiece_font_size_spin = QSpinBox(self.ui.propertiesPanel)
        self.centerpiece_color_button = QPushButton("Text Colour...", self.ui.propertiesPanel)
        self.centerpiece_darkening_label = QLabel("Poster darkening: 45", self.ui.propertiesPanel)
        self.centerpiece_darkening_slider = QSlider(Qt.Orientation.Horizontal, self.ui.propertiesPanel)

        self._install_menus()
        self._install_splitter()
        self._install_workspace()
        self._install_project_panel_widgets()
        self._install_properties_panel_widgets()

        self.ui.newMontageButton.hide()
        self.ui.openMontageButton.hide()
        self.ui.projectStatusLabel.hide()
        self.ui.propertiesStatusLabel.hide()

        self.create_from_imdb_button.clicked.connect(self.create_from_imdb_json)
        self.chronological_button.clicked.connect(self.sort_chronological)
        self.box_office_button.clicked.connect(self.sort_box_office)
        self.shuffle_button.clicked.connect(self.shuffle_layout)
        self.bench_selected_button.clicked.connect(self.bench_selected_titles)
        self.promote_selected_button.clicked.connect(self.promote_selected_titles)
        self.swap_selected_button.clicked.connect(self.swap_selected_titles)
        self.title_list.currentItemChanged.connect(self._title_selection_changed)
        self.title_list.itemSelectionChanged.connect(self._update_swap_button_state)
        self.bench_list.itemSelectionChanged.connect(self._update_swap_button_state)
        self.previous_poster_button.clicked.connect(self.previous_poster)
        self.next_poster_button.clicked.connect(self.next_poster)
        self.airiness_slider.valueChanged.connect(self._airiness_changed)
        self.canvas_color_button.clicked.connect(self.choose_canvas_color)
        self.canvas_preset_combo.currentTextChanged.connect(self._canvas_preset_changed)
        self.canvas_width_spin.valueChanged.connect(self._manual_canvas_size_changed)
        self.canvas_height_spin.valueChanged.connect(self._manual_canvas_size_changed)
        self.centerpiece_enabled_check.toggled.connect(self._centerpiece_controls_changed)
        self.centerpiece_text_edit.textChanged.connect(self._centerpiece_controls_changed)
        self.centerpiece_font_button.clicked.connect(self.choose_centerpiece_font)
        self.centerpiece_font_size_spin.valueChanged.connect(self._centerpiece_controls_changed)
        self.centerpiece_color_button.clicked.connect(self.choose_centerpiece_color)
        self.centerpiece_darkening_slider.valueChanged.connect(self._centerpiece_controls_changed)
        self.workspace.poster_selected.connect(self._workspace_poster_selected)
        self.workspace.poster_swap_requested.connect(self._workspace_poster_swap_requested)

        self.workspace.set_canvas_color(self.project.canvas_color)
        self._sync_canvas_controls_from_project()
        self._sync_centerpiece_controls_from_project()
        self._apply_centerpiece_to_workspace()
        self._refresh_project_panel()
        self._refresh_properties_panel()

    def _install_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        new_action = QAction("New Montage", self)
        open_action = QAction("Open Montage...", self)
        save_action = QAction("Save Montage", self)
        save_as_action = QAction("Save Montage As...", self)
        import_action = QAction("Create from IMDb JSON...", self)

        new_action.triggered.connect(self.new_montage)
        open_action.triggered.connect(self.open_montage)
        save_action.triggered.connect(self.save_montage)
        save_as_action.triggered.connect(self.save_montage_as)
        import_action.triggered.connect(self.create_from_imdb_json)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(import_action)

        edit_menu = self.menuBar().addMenu("Edit")

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)

        edit_menu.addAction(self.undo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(settings_action)

    def _install_splitter(self) -> None:
        self.ui.mainLayout.removeWidget(self.ui.projectPanel)
        self.ui.mainLayout.removeWidget(self.ui.canvasPanel)
        self.ui.mainLayout.removeWidget(self.ui.propertiesPanel)

        self.ui.projectPanel.setMinimumWidth(300)
        self.ui.projectPanel.setMaximumWidth(720)
        self.ui.projectPanel.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

        self.ui.canvasPanel.setMinimumWidth(420)
        self.ui.canvasPanel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.ui.propertiesPanel.setMinimumWidth(300)
        self.ui.propertiesPanel.setMaximumWidth(460)
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
        self.splitter.setSizes([380, 720, 340])

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

        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setWordWrap(True)
        self.progress_label.setFixedHeight(20)

        self.progress_bar.setObjectName("projectProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20)
        self._clear_progress()

        title_list_title = QLabel("Title List", self.ui.projectPanel)
        title_list_title.setObjectName("titleListTitleLabel")

        bench_list_title = QLabel("Bench", self.ui.projectPanel)
        bench_list_title.setObjectName("benchListTitleLabel")

        self.title_list.setObjectName("titleListWidget")
        self.title_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.title_list.setAlternatingRowColors(False)
        self.title_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.title_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.bench_list.setObjectName("benchListWidget")
        self.bench_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.bench_list.setAlternatingRowColors(False)
        self.bench_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.bench_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.chronological_button)
        layout_buttons.addWidget(self.box_office_button)
        layout_buttons.addWidget(self.shuffle_button)

        self.ui.projectLayout.insertWidget(3, self.create_from_imdb_button)
        self.ui.projectLayout.insertWidget(4, self.progress_label)
        self.ui.projectLayout.insertWidget(5, self.progress_bar)
        self.ui.projectLayout.insertLayout(6, layout_buttons)
        self.ui.projectLayout.insertWidget(7, title_list_title)
        self.ui.projectLayout.insertWidget(8, self.title_list, 2)
        self.ui.projectLayout.insertWidget(9, self.bench_selected_button)
        self.ui.projectLayout.insertWidget(10, bench_list_title)
        self.ui.projectLayout.insertWidget(11, self.bench_list, 1)
        self.ui.projectLayout.insertWidget(12, self.promote_selected_button)
        self.ui.projectLayout.insertWidget(13, self.swap_selected_button)

    def _install_properties_panel_widgets(self) -> None:
        self.poster_preview_label.setObjectName("posterPreviewLabel")
        self.poster_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_preview_label.setMinimumHeight(320)
        self.poster_preview_label.setMaximumHeight(360)
        self.poster_preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.poster_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.poster_controls_layout.addWidget(self.previous_poster_button)
        self.poster_controls_layout.addWidget(self.poster_counter_label, 1)
        self.poster_controls_layout.addWidget(self.next_poster_button)

        self.airiness_slider.setRange(0, 100)
        self.airiness_slider.setValue(self.project.airiness)

        for name in CANVAS_PRESETS:
            self.canvas_preset_combo.addItem(name)

        for spin in (self.canvas_width_spin, self.canvas_height_spin):
            spin.setRange(50.0, 3000.0)
            spin.setDecimals(1)
            spin.setSingleStep(5.0)
            spin.setSuffix(" mm")

        canvas_size_form = QFormLayout()
        canvas_size_form.setContentsMargins(0, 0, 0, 0)
        canvas_size_form.addRow("Canvas", self.canvas_preset_combo)
        canvas_size_form.addRow("Width", self.canvas_width_spin)
        canvas_size_form.addRow("Height", self.canvas_height_spin)

        self.ui.propertiesLayout.insertWidget(1, self.poster_preview_label)
        self.ui.propertiesLayout.insertLayout(2, self.poster_controls_layout)
        self.ui.propertiesLayout.insertSpacing(3, 12)
        self.ui.propertiesLayout.insertLayout(4, canvas_size_form)
        self.ui.propertiesLayout.insertWidget(5, self.airiness_label)
        self.ui.propertiesLayout.insertWidget(6, self.airiness_slider)
        self.ui.propertiesLayout.insertWidget(7, self.canvas_color_button)

        self.centerpiece_text_edit.setMinimumHeight(78)
        self.centerpiece_text_edit.setPlaceholderText("Charles Tait\nVFX Supervisor")
        self.centerpiece_font_size_spin.setRange(8, 180)
        self.centerpiece_font_size_spin.setValue(self.project.centerpiece_font_size)
        self.centerpiece_darkening_slider.setRange(0, 90)
        self.centerpiece_darkening_slider.setValue(self.project.centerpiece_darkening)

        centerpiece_form = QFormLayout()
        centerpiece_form.setContentsMargins(0, 0, 0, 0)
        centerpiece_form.addRow("Text", self.centerpiece_text_edit)
        centerpiece_form.addRow("Size", self.centerpiece_font_size_spin)

        self.ui.propertiesLayout.insertSpacing(8, 14)
        self.ui.propertiesLayout.insertWidget(9, self.centerpiece_enabled_check)
        self.ui.propertiesLayout.insertLayout(10, centerpiece_form)
        self.ui.propertiesLayout.insertWidget(11, self.centerpiece_font_button)
        self.ui.propertiesLayout.insertWidget(12, self.centerpiece_color_button)
        self.ui.propertiesLayout.insertWidget(13, self.centerpiece_darkening_label)
        self.ui.propertiesLayout.insertWidget(14, self.centerpiece_darkening_slider)

    def new_montage(self) -> None:
        self._push_undo()
        self.project = Project()
        self.poster_entries.clear()
        self.missing_poster_titles.clear()
        self.omitted_layout_titles.clear()
        self.current_layout = None
        self.workspace.set_page_size(self.project.page_width_mm, self.project.page_height_mm)
        self.workspace.set_canvas_color(self.project.canvas_color)
        self.airiness_slider.setValue(self.project.airiness)
        self._sync_canvas_controls_from_project()
        self._sync_centerpiece_controls_from_project()
        self._apply_centerpiece_to_workspace()
        self._refresh_project_panel()
        self._refresh_properties_panel()

    def open_montage(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Montage",
            "projects",
            "Poster Montage Files (*.pmd);;JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        self._load_project_file(Path(file_path))

    def save_montage(self) -> None:
        if self.project.path is None:
            self.save_montage_as()
            return

        self._save_project_file(self.project.path)

    def save_montage_as(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Montage As",
            "projects/untitled_montage.pmd",
            "Poster Montage Files (*.pmd);;JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        path = Path(file_path)
        if path.suffix.lower() == "":
            path = path.with_suffix(".pmd")

        self.project.path = path
        self._save_project_file(path)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def create_from_imdb_json(self) -> None:
        if self.import_imdb_json():
            self.load_posters()

    def import_imdb_json(self) -> bool:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import IMDb JSON",
            "projects",
            "JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return False

        self._push_undo()
        self._set_progress("Importing IMDb JSON...", 0, 100)
        QApplication.processEvents()

        self.project.titles = import_imdb_json(file_path)
        self.project.source = str(Path(file_path).name)
        self.project.dirty = True
        self.poster_entries.clear()
        self.missing_poster_titles.clear()
        self.omitted_layout_titles.clear()
        self.current_layout = None
        self.workspace.clear_posters()

        if self.project.name == "Untitled Montage":
            self.project.name = "IMDb Montage"

        self._refresh_project_panel()
        self._refresh_properties_panel()
        self._update_window_title()
        return True

    def sort_chronological(self) -> None:
        self._push_undo()
        active_titles = self.project.active_titles
        self._ensure_metadata_for_titles(active_titles, "Checking dates")

        active_titles = sorted(
            active_titles,
            key=lambda title: (title.year is None, -(title.year or 0), title.title.lower()),
        )
        self._replace_active_order(active_titles)
        self.statusBar().showMessage("Sorted newest first.")

    def sort_box_office(self) -> None:
        self._push_undo()
        active_titles = self.project.active_titles
        self._ensure_metadata_for_titles(active_titles, "Checking box office")

        active_titles = sorted(
            active_titles,
            key=lambda title: (title.revenue is None, -(title.revenue or 0), title.title.lower()),
        )
        self._replace_active_order(active_titles)
        self.statusBar().showMessage("Sorted by box office where available.")

    def shuffle_layout(self) -> None:
        self._push_undo()
        active_titles = self.project.active_titles[:]
        random.shuffle(active_titles)
        self._replace_active_order(active_titles)
        self.statusBar().showMessage("Shuffled layout.")

    def _replace_active_order(self, active_titles: list[Title]) -> None:
        self.project.titles = active_titles + self.project.benched_titles
        self.project.dirty = True
        self._refresh_project_panel()
        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()
        self._update_window_title()

    def bench_selected_titles(self) -> None:
        self._push_undo()
        titles = self._selected_active_titles()
        if not titles:
            return

        for title in titles:
            title.benched = True
            title.bench_reason = "manual"

        self.project.dirty = True
        self._refresh_project_panel()
        self._refresh_properties_panel()

        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()

    def promote_selected_titles(self) -> None:
        self._push_undo()
        selected_rows = sorted({self.bench_list.row(item) for item in self.bench_list.selectedItems()})
        benched_titles = self.project.benched_titles

        if not selected_rows:
            return

        for row in selected_rows:
            if 0 <= row < len(benched_titles):
                benched_titles[row].benched = False
                benched_titles[row].bench_reason = ""

        self.project.dirty = True
        self._refresh_project_panel()
        self._refresh_properties_panel()
        self._update_swap_button_state()

        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()

    def swap_selected_titles(self) -> None:
        self._push_undo()
        active_titles = self._selected_active_titles()
        bench_titles = self._selected_benched_titles()

        if len(active_titles) != 1 or len(bench_titles) != 1:
            return

        active_title = active_titles[0]
        bench_title = bench_titles[0]

        active_title.benched = True
        active_title.bench_reason = "manual"
        bench_title.benched = False
        bench_title.bench_reason = ""
        self.project.dirty = True

        self._refresh_project_panel()
        self._refresh_properties_panel()
        self._update_swap_button_state()

        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()

    def load_posters(self) -> None:
        active_titles = self.project.active_titles

        if not active_titles:
            self.statusBar().showMessage("Import titles first.")
            return

        self.poster_entries.clear()
        self.missing_poster_titles.clear()
        self.omitted_layout_titles.clear()
        self.current_layout = None

        for title in self.project.titles:
            title.missing_poster = False

        total = len(active_titles)

        self.create_from_imdb_button.setEnabled(False)
        self._set_progress("Loading posters...", 0, total)

        try:
            for index, title in enumerate(active_titles, start=1):
                self._set_progress(f"Loading posters {index} / {total}: {title.title}", index - 1, total)
                QApplication.processEvents()

                if not title.imdb_title_id:
                    title.missing_poster = True
                    self.missing_poster_titles.append(title.title)
                    continue

                self._ensure_title_metadata(title)

                poster_path = get_poster(
                    title.imdb_title_id,
                    index=title.selected_poster_index,
                    size="w500",
                )

                if poster_path is None:
                    title.missing_poster = True
                    self.missing_poster_titles.append(title.title)
                    continue

                title.poster_path = poster_path
                self.poster_entries.append((title.imdb_title_id, poster_path))

            if not self.poster_entries:
                self.statusBar().showMessage("No posters were found.")
                self.workspace.clear_posters()
                self._set_progress("No posters were found.", total, total)
                self._clear_progress()
                return

            self._rebuild_grid_from_current_posters()

            self._set_progress(f"Loaded {len(self.poster_entries)} / {total} posters.", total, total)
            self.statusBar().showMessage(f"Loaded {len(self.poster_entries)} / {total} posters.")
            self._refresh_project_panel()
            self._clear_progress()

        finally:
            self.create_from_imdb_button.setEnabled(True)

    def previous_poster(self) -> None:
        self._change_selected_poster(-1)

    def next_poster(self) -> None:
        self._change_selected_poster(1)

    def choose_canvas_color(self) -> None:
        dialog = QColorDialog(QColor(self.project.canvas_color), self)
        dialog.setOption(QColorDialog.ColorDialogOption.NoButtons, False)
        dialog.currentColorChanged.connect(self._canvas_color_preview_changed)
        dialog.colorSelected.connect(self._canvas_color_selected)

        if dialog.exec() == QDialog.DialogCode.Rejected:
            self.workspace.set_canvas_color(self.project.canvas_color)

    def _canvas_color_preview_changed(self, color: QColor) -> None:
        if color.isValid():
            self.workspace.set_canvas_color(color)

    def _canvas_color_selected(self, color: QColor) -> None:
        if not color.isValid():
            return

        self._push_undo()
        self.project.canvas_color = color.name()
        self.workspace.set_canvas_color(self.project.canvas_color)
        self.project.dirty = True
        self._update_window_title()

    def _airiness_changed(self, value: int) -> None:
        self._push_undo()
        self._promote_auto_benched_titles()
        self.project.airiness = value
        self.airiness_label.setText(f"Airiness: {value}")
        self.project.dirty = True

        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()
        self._refresh_project_panel()
        self._update_window_title()

    def _canvas_preset_changed(self, preset_name: str) -> None:
        if self._updating_canvas_controls:
            return

        if preset_name not in CANVAS_PRESETS:
            return

        width, height = CANVAS_PRESETS[preset_name]
        self.project.canvas_preset = preset_name
        if preset_name != "Custom":
            self.project.page_width_mm = width
            self.project.page_height_mm = height
            self._sync_canvas_controls_from_project()
            self._apply_canvas_size_change()

    def _manual_canvas_size_changed(self, value: float) -> None:
        if self._updating_canvas_controls:
            return

        self.project.canvas_preset = "Custom"
        self.project.page_width_mm = self.canvas_width_spin.value()
        self.project.page_height_mm = self.canvas_height_spin.value()
        self._sync_canvas_controls_from_project()
        self._apply_canvas_size_change()

    def _apply_canvas_size_change(self) -> None:
        self._push_undo()
        self._promote_auto_benched_titles()
        self.workspace.set_page_size(self.project.page_width_mm, self.project.page_height_mm)
        self.workspace.set_canvas_color(self.project.canvas_color)
        self.project.dirty = True
        if self.poster_entries:
            self._sync_poster_entries_from_active_titles()
            self._rebuild_grid_from_current_posters()
        self._refresh_project_panel()
        self._update_window_title()

    def _sync_canvas_controls_from_project(self) -> None:
        self._updating_canvas_controls = True
        try:
            preset = self.project.canvas_preset
            if preset not in CANVAS_PRESETS:
                preset = "Custom"
            self.canvas_preset_combo.setCurrentText(preset)
            self.canvas_width_spin.setValue(float(self.project.page_width_mm))
            self.canvas_height_spin.setValue(float(self.project.page_height_mm))
        finally:
            self._updating_canvas_controls = False
        self.undo_stack: list[Project] = []
        self._restoring_undo = False

    def _ensure_metadata_for_titles(self, titles: list[Title], label: str) -> None:
        total = len(titles)
        if total <= 0:
            return

        for index, title in enumerate(titles, start=1):
            self._set_progress(f"{label} {index} / {total}: {title.title}", index - 1, total)
            QApplication.processEvents()
            self._ensure_title_metadata(title)

        self._set_progress(f"{label} complete.", total, total)
        self._clear_progress()

    def _ensure_title_metadata(self, title: Title) -> None:
        if not title.imdb_title_id:
            return

        metadata = lookup_imdb_id(title.imdb_title_id)
        if metadata is None:
            return

        if metadata.year is not None:
            title.year = metadata.year
        if getattr(metadata, "revenue", None) is not None:
            title.revenue = metadata.revenue

    def _promote_auto_benched_titles(self) -> None:
        changed = False
        for title in self.project.titles:
            if title.benched and title.bench_reason == "layout":
                title.benched = False
                title.bench_reason = ""
                changed = True

        if changed:
            self.project.dirty = True

    def _change_selected_poster(self, delta: int) -> None:
        title = self._selected_active_title()

        if title is None or not title.imdb_title_id:
            return

        count = get_poster_candidate_count(title.imdb_title_id)

        if count <= 0:
            return

        new_index = title.selected_poster_index + delta
        new_index = max(0, min(new_index, count - 1))

        if new_index == title.selected_poster_index:
            return

        self._push_undo()
        title.selected_poster_index = new_index
        self.project.dirty = True

        poster_path = get_poster(
            title.imdb_title_id,
            index=title.selected_poster_index,
            size="w500",
        )

        if poster_path is None:
            return

        title.poster_path = poster_path
        self.workspace.update_poster(title.imdb_title_id, poster_path)
        self._replace_poster_entry(title.imdb_title_id, poster_path)
        self._refresh_properties_panel_for_title(title)
        self._update_window_title()

    def _replace_poster_entry(self, imdb_title_id: str, poster_path: Path) -> None:
        self.poster_entries = [
            (entry_id, poster_path if entry_id == imdb_title_id else entry_path)
            for entry_id, entry_path in self.poster_entries
        ]

    def _sync_poster_entries_from_active_titles(self) -> None:
        self.poster_entries = [
            (title.imdb_title_id, title.poster_path)
            for title in self.project.active_titles
            if title.imdb_title_id and title.poster_path and not title.missing_poster
        ]

    def _rebuild_grid_from_current_posters(self) -> None:
        if not self.poster_entries:
            self.current_layout = None
            self.workspace.clear_posters()
            return

        layout = calculate_grid_layout(
            len(self.poster_entries),
            self.project.page_width_mm,
            self.project.page_height_mm,
            airiness=self.project.airiness,
        )

        if layout.omitted_count > 0:
            omitted_entries = self.poster_entries[layout.used_count:]
            omitted_ids = {imdb_id for imdb_id, _ in omitted_entries}

            self.omitted_layout_titles = []
            for title in self.project.active_titles:
                if title.imdb_title_id in omitted_ids:
                    title.benched = True
                    title.bench_reason = "layout"
                    self.omitted_layout_titles.append(title.title)

            self.project.dirty = True
            self.poster_entries = self.poster_entries[: layout.used_count]

            layout = calculate_grid_layout(
                len(self.poster_entries),
                self.project.page_width_mm,
                self.project.page_height_mm,
                airiness=self.project.airiness,
            )
            self._refresh_project_panel()
        else:
            self.omitted_layout_titles = []

        self.current_layout = layout
        self.workspace.show_poster_grid(self.poster_entries, layout)
        self._refresh_properties_panel()

    def _refresh_project_panel(self) -> None:
        active_titles = self.project.active_titles
        benched_titles = self.project.benched_titles

        self._update_window_title()

        self.title_list.clear()

        if not active_titles:
            empty_item = QListWidgetItem("(empty)")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setSizeHint(QSize(0, 13))
            self.title_list.addItem(empty_item)
        else:
            for title in active_titles:
                item = QListWidgetItem(self._title_label(title))
                item.setToolTip(self._title_tooltip(title))
                item.setSizeHint(QSize(0, 13))

                if title.missing_poster:
                    item.setData(Qt.ItemDataRole.UserRole, "missing_poster")
                    item.setForeground(QBrush(QColor("#ffb0a8")))
                    item.setBackground(QBrush(QColor("#332020")))

                self.title_list.addItem(item)

        self.bench_list.clear()

        if not benched_titles:
            empty_item = QListWidgetItem("(empty)")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setSizeHint(QSize(0, 13))
            self.bench_list.addItem(empty_item)
        else:
            for title in benched_titles:
                item = QListWidgetItem(self._title_label(title))
                item.setToolTip(self._title_tooltip(title))
                item.setSizeHint(QSize(0, 13))

                #if title.missing_poster:
                    #item.setForeground(QBrush(QColor("#ffb0a8")))
                    #item.setBackground(QBrush(QColor("#332020")))

                #self.bench_list.addItem(item)

        self._update_swap_button_state()

    def _refresh_properties_panel(self) -> None:
        title = self._selected_active_title()

        if title is None:
            self.poster_preview_label.clear()
            self.poster_counter_label.setText("0 / 0")
            self.previous_poster_button.setEnabled(False)
            self.next_poster_button.setEnabled(False)
            self.workspace.select_poster(None)
            return

        self._refresh_properties_panel_for_title(title)

    def _refresh_properties_panel_for_title(self, title: Title) -> None:
        if not title.imdb_title_id:
            self.poster_preview_label.clear()
            self.poster_counter_label.setText("0 / 0")
            self.previous_poster_button.setEnabled(False)
            self.next_poster_button.setEnabled(False)
            self.workspace.select_poster(None)
            return

        count = get_poster_candidate_count(title.imdb_title_id)

        if count <= 0:
            self.poster_preview_label.clear()
            self.poster_counter_label.setText("0 / 0")
            self.previous_poster_button.setEnabled(False)
            self.next_poster_button.setEnabled(False)
            self.workspace.select_poster(title.imdb_title_id)
            return

        title.selected_poster_index = max(0, min(title.selected_poster_index, count - 1))

        self.poster_counter_label.setText(f"{title.selected_poster_index + 1} / {count}")
        self.previous_poster_button.setEnabled(title.selected_poster_index > 0)
        self.next_poster_button.setEnabled(title.selected_poster_index < count - 1)

        poster_path = get_poster(
            title.imdb_title_id,
            index=title.selected_poster_index,
            size="w500",
        )

        if poster_path is None:
            self.poster_preview_label.clear()
            return

        title.poster_path = poster_path
        self._set_poster_preview(poster_path)
        self.workspace.select_poster(title.imdb_title_id)

    def _set_poster_preview(self, poster_path: Path) -> None:
        pixmap = QPixmap(str(poster_path))

        if pixmap.isNull():
            self.poster_preview_label.clear()
            return

        scaled = pixmap.scaled(
            self.poster_preview_label.width(),
            self.poster_preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.poster_preview_label.setPixmap(scaled)

    def _title_selection_changed(self, current, previous) -> None:
        self.bench_list.clearSelection()
        self._refresh_properties_panel()
        title = self._selected_active_title()
        self.workspace.select_poster(title.imdb_title_id if title and title.imdb_title_id else None)

    def _workspace_poster_selected(self, imdb_title_id: str) -> None:
        active_titles = self.project.active_titles
        for row, title in enumerate(active_titles):
            if title.imdb_title_id == imdb_title_id:
                self.title_list.setCurrentRow(row)
                self.title_list.clearSelection()
                self.title_list.item(row).setSelected(True)
                self.bench_list.clearSelection()
                self._refresh_properties_panel_for_title(title)
                return

    def _workspace_poster_swap_requested(self, source_imdb_id: str, target_imdb_id: str) -> None:
        self._push_undo()
        source_index = self._title_index_by_imdb_id(source_imdb_id)
        target_index = self._title_index_by_imdb_id(target_imdb_id)

        if source_index is None or target_index is None:
            return

        self.project.titles[source_index], self.project.titles[target_index] = (
            self.project.titles[target_index],
            self.project.titles[source_index],
        )
        self.project.dirty = True
        self._refresh_project_panel()
        self._sync_poster_entries_from_active_titles()
        self._rebuild_grid_from_current_posters()
        self._workspace_poster_selected(source_imdb_id)
        self._update_window_title()

    def _title_index_by_imdb_id(self, imdb_title_id: str) -> int | None:
        for index, title in enumerate(self.project.titles):
            if title.imdb_title_id == imdb_title_id:
                return index
        return None

    def _selected_active_title(self) -> Title | None:
        row = self.title_list.currentRow()
        active_titles = self.project.active_titles

        if row < 0 or row >= len(active_titles):
            return None

        return active_titles[row]

    def _selected_active_titles(self) -> list[Title]:
        active_titles = self.project.active_titles
        rows = sorted({self.title_list.row(item) for item in self.title_list.selectedItems()})

        return [
            active_titles[row]
            for row in rows
            if 0 <= row < len(active_titles)
        ]

    def _selected_benched_titles(self) -> list[Title]:
        benched_titles = self.project.benched_titles
        rows = sorted({self.bench_list.row(item) for item in self.bench_list.selectedItems()})

        return [
            benched_titles[row]
            for row in rows
            if 0 <= row < len(benched_titles)
        ]

    def _update_swap_button_state(self) -> None:
        self.swap_selected_button.setEnabled(
            len(self._selected_active_titles()) == 1
            and len(self._selected_benched_titles()) == 1
        )

    def _title_label(self, title: Title) -> str:
        label = title.title
        if title.year is not None:
            label += f" ({title.year})"
        return label

    def _title_tooltip(self, title: Title) -> str:
        label = self._title_label(title)
        if title.missing_poster:
            label += "\nMissing poster on TMDb"
        return label

    def _set_progress(self, text: str, value: int, maximum: int) -> None:
        self.progress_label.setText(text)
        self.progress_bar.setMaximum(max(1, maximum))
        self.progress_bar.setValue(max(0, min(value, maximum)))
        self._set_progress_active(True)

    def _clear_progress(self) -> None:
        self.progress_label.setText("")
        self.progress_bar.setValue(0)
        self._set_progress_active(False)

    def _set_progress_active(self, active: bool) -> None:
        self.progress_label.setProperty("active", active)
        self.progress_bar.setProperty("active", active)

        for widget in (self.progress_label, self.progress_bar):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _push_undo(self) -> None:
        if self._restoring_undo:
            return
        self.undo_stack.append(deepcopy(self.project))
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.undo_action.setEnabled(True)

    def undo(self) -> None:
        if not self.undo_stack:
            return

        self._restoring_undo = True
        try:
            self.project = self.undo_stack.pop()
            self.undo_action.setEnabled(bool(self.undo_stack))
            self.poster_entries.clear()
            self.missing_poster_titles.clear()
            self.omitted_layout_titles.clear()
            self.current_layout = None
            self.workspace.set_page_size(self.project.page_width_mm, self.project.page_height_mm)
            self.workspace.set_canvas_color(self.project.canvas_color)
            self._sync_canvas_controls_from_project()
            self._sync_centerpiece_controls_from_project()
            self._apply_centerpiece_to_workspace()
            self._sync_poster_entries_from_active_titles()
            if self.poster_entries:
                self._rebuild_grid_from_current_posters()
            else:
                self.workspace.clear_posters()
            self._refresh_project_panel()
            self._refresh_properties_panel()
            self._update_window_title()
            self.statusBar().showMessage("Undo")
        finally:
            self._restoring_undo = False

    def choose_centerpiece_font(self) -> None:
        current = QFont(self.project.centerpiece_font_family, self.project.centerpiece_font_size)
        font, ok = QFontDialog.getFont(current, self, "Choose Centrepiece Font")
        if not ok:
            return
        self._push_undo()
        self.project.centerpiece_font_family = font.family()
        self.project.centerpiece_font_size = max(1, font.pointSize())
        self._sync_centerpiece_controls_from_project()
        self._centerpiece_project_changed()

    def choose_centerpiece_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.project.centerpiece_color), self, "Choose Text Colour")
        if not color.isValid():
            return
        self._push_undo()
        self.project.centerpiece_color = color.name()
        self._centerpiece_project_changed()

    def _centerpiece_controls_changed(self) -> None:
        if self._updating_canvas_controls:
            return
        self._push_undo()
        self.project.centerpiece_enabled = self.centerpiece_enabled_check.isChecked()
        self.project.centerpiece_text = self.centerpiece_text_edit.toPlainText()
        self.project.centerpiece_font_size = self.centerpiece_font_size_spin.value()
        self.project.centerpiece_darkening = self.centerpiece_darkening_slider.value()
        self._centerpiece_project_changed()

    def _centerpiece_project_changed(self) -> None:
        self.centerpiece_darkening_label.setText(f"Poster darkening: {self.project.centerpiece_darkening}")
        self.project.dirty = True
        self._apply_centerpiece_to_workspace()
        self._update_window_title()

    def _sync_centerpiece_controls_from_project(self) -> None:
        self._updating_canvas_controls = True
        try:
            self.centerpiece_enabled_check.setChecked(self.project.centerpiece_enabled)
            self.centerpiece_text_edit.setPlainText(self.project.centerpiece_text)
            self.centerpiece_font_size_spin.setValue(self.project.centerpiece_font_size)
            self.centerpiece_darkening_slider.setValue(self.project.centerpiece_darkening)
            self.centerpiece_darkening_label.setText(f"Poster darkening: {self.project.centerpiece_darkening}")
        finally:
            self._updating_canvas_controls = False

    def _apply_centerpiece_to_workspace(self) -> None:
        self.workspace.set_centerpiece(
            text=self.project.centerpiece_text,
            font_family=self.project.centerpiece_font_family,
            font_size=self.project.centerpiece_font_size,
            color=self.project.centerpiece_color,
            darkening=self.project.centerpiece_darkening,
            enabled=self.project.centerpiece_enabled,
        )

    def _update_window_title(self) -> None:
        name = self.project.name or "Untitled Montage"
        source = self.project.source
        dirty = " *" if self.project.dirty else ""

        if source and source != "None":
            self.setWindowTitle(f"Poster Montage Designer — {name} — {source}{dirty}")
        else:
            self.setWindowTitle(f"Poster Montage Designer — {name}{dirty}")

    def _save_project_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "name": self.project.name,
            "source": self.project.source,
            "canvas_color": self.project.canvas_color,
            "airiness": self.project.airiness,
            "page_width_mm": self.project.page_width_mm,
            "page_height_mm": self.project.page_height_mm,
            "canvas_preset": self.project.canvas_preset,
            "centerpiece_text": self.project.centerpiece_text,
            "centerpiece_font_family": self.project.centerpiece_font_family,
            "centerpiece_font_size": self.project.centerpiece_font_size,
            "centerpiece_color": self.project.centerpiece_color,
            "centerpiece_darkening": self.project.centerpiece_darkening,
            "centerpiece_enabled": self.project.centerpiece_enabled,
            "titles": [
                {
                    "title": title.title,
                    "year": title.year,
                    "imdb_title_id": title.imdb_title_id,
                    "url": title.url,
                    "selected_poster_index": title.selected_poster_index,
                    "benched": title.benched,
                    "bench_reason": title.bench_reason,
                    "missing_poster": title.missing_poster,
                    "revenue": title.revenue,
                }
                for title in self.project.titles
            ],
        }

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        self.project.path = path
        self.project.dirty = False
        self.statusBar().showMessage(f"Saved {path.name}")
        self._update_window_title()

    def _load_project_file(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)

        titles = []
        for raw in data.get("titles", []):
            titles.append(
                Title(
                    title=str(raw.get("title", "")).strip(),
                    year=raw.get("year"),
                    imdb_title_id=raw.get("imdb_title_id"),
                    url=raw.get("url"),
                    selected_poster_index=int(raw.get("selected_poster_index", 0)),
                    benched=bool(raw.get("benched", False)),
                    bench_reason=str(raw.get("bench_reason") or ("manual" if bool(raw.get("benched", False)) else "")),
                    missing_poster=bool(raw.get("missing_poster", False)),
                    revenue=raw.get("revenue"),
                )
            )

        self.project = Project(
            name=str(data.get("name") or "Untitled Montage"),
            path=path,
            source=str(data.get("source") or "None"),
            titles=titles,
            dirty=False,
            canvas_color=str(data.get("canvas_color") or "#000000"),
            airiness=int(data.get("airiness", 50)),
            page_width_mm=float(data.get("page_width_mm", DEFAULT_PAGE_WIDTH_MM)),
            page_height_mm=float(data.get("page_height_mm", DEFAULT_PAGE_HEIGHT_MM)),
            canvas_preset=str(data.get("canvas_preset") or "Custom"),
            centerpiece_text=str(data.get("centerpiece_text") or ""),
            centerpiece_font_family=str(data.get("centerpiece_font_family") or "Segoe UI"),
            centerpiece_font_size=int(data.get("centerpiece_font_size", 42)),
            centerpiece_color=str(data.get("centerpiece_color") or "#ffffff"),
            centerpiece_darkening=int(data.get("centerpiece_darkening", 45)),
            centerpiece_enabled=bool(data.get("centerpiece_enabled", False)),
        )

        self.poster_entries.clear()
        self.missing_poster_titles.clear()
        self.omitted_layout_titles.clear()
        self.current_layout = None
        self.workspace.clear_posters()
        self.workspace.set_page_size(self.project.page_width_mm, self.project.page_height_mm)
        self.workspace.set_canvas_color(self.project.canvas_color)
        self.airiness_slider.setValue(self.project.airiness)
        self._sync_canvas_controls_from_project()
        self._sync_centerpiece_controls_from_project()
        self._apply_centerpiece_to_workspace()

        self._refresh_project_panel()
        self._refresh_properties_panel()
        self.statusBar().showMessage(f"Opened {path.name}")
        self._update_window_title()
