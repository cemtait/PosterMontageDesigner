from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow

from poster_montage_designer.layouts.grid import GridLayout
from poster_montage_designer.models import Project
from poster_montage_designer.services.render import render_project_image


ProgressCallback = Callable[[str, int, int], None]


class ExportController:
    """Coordinates export UI and render service calls.

    MainWindow still owns the visible progress widgets/status bar, but export
    filename choice and render orchestration now live here. This is the first
    step toward export-all-pages and richer export settings.
    """

    def __init__(self, parent: QMainWindow) -> None:
        self.parent = parent

    def export_current_page(
        self,
        *,
        project: Project,
        layout: GridLayout | None,
        visible_imdb_ids: list[str],
        progress_callback: ProgressCallback,
        clear_progress: Callable[[], None],
    ) -> None:
        if layout is None or not visible_imdb_ids:
            self.parent.statusBar().showMessage("Load posters before exporting.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Export Image",
            f"exports/{project.current_page.name}.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tif);;All Files (*.*)",
        )
        if not file_path:
            return

        output_path = Path(file_path)
        if output_path.suffix.lower() == "":
            output_path = output_path.with_suffix(".png")

        def progress(message: str, value: int, maximum: int) -> None:
            progress_callback(message, value, maximum)
            QApplication.processEvents()

        try:
            render_project_image(
                project=project,
                layout=layout,
                visible_imdb_ids=visible_imdb_ids,
                output_path=output_path,
                width_px=4961,
                progress_callback=progress,
            )

            progress_callback("Export complete.", 1, 1)
            QApplication.processEvents()
            self.parent.statusBar().showMessage(f"Exported {output_path.name}")

        finally:
            clear_progress()
