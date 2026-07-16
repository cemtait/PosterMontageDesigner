from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QDrag, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QApplication

from poster_montage_designer.layouts.grid import GridLayout
from poster_montage_designer.widgets.title_list import TITLE_MIME_TYPE, decode_title_mime


MM_PER_INCH = 25.4


class PosterPageItem(QGraphicsItem):
    def __init__(self, width_mm: float, height_mm: float) -> None:
        super().__init__()
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.canvas_color = QColor("#000000")

    def set_canvas_color(self, color: QColor | str) -> None:
        self.canvas_color = QColor(color)
        self.update()

    def boundingRect(self) -> QRectF:
        shadow_pad = 32
        return QRectF(-shadow_pad, -shadow_pad, self.width_mm + shadow_pad * 2, self.height_mm + shadow_pad * 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        page = QRectF(0, 0, self.width_mm, self.height_mm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for i in range(18, 0, -1):
            offset = 2.0 + i * 0.65
            alpha = int(20 * (i / 18.0) ** 2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(page.translated(offset, offset), 1.0, 1.0)
        painter.setBrush(self.canvas_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(page)


class CroppedPosterItem(QGraphicsItem):
    def __init__(self, imdb_title_id: str, pixmap: QPixmap, target_rect: QRectF) -> None:
        super().__init__()
        self.imdb_title_id = imdb_title_id
        self.pixmap = pixmap
        self.width_mm = target_rect.width()
        self.height_mm = target_rect.height()
        self.selected = False
        self.drop_target = False
        self.drag_placeholder = False
        self.setPos(target_rect.topLeft())
        self.setZValue(10)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self.pixmap = pixmap
        self.update()

    def set_selected_visual(self, selected: bool) -> None:
        self.selected = selected
        self.update()

    def set_drop_target(self, active: bool) -> None:
        self.drop_target = active
        self.update()

    def set_drag_placeholder(self, active: bool) -> None:
        self.drag_placeholder = active
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width_mm, self.height_mm)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        target = QRectF(0, 0, self.width_mm, self.height_mm)

        if self.drag_placeholder:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(QColor(118, 118, 118, 185), 1.2))
            painter.setBrush(QColor(72, 72, 72, 150))
            painter.drawRect(target.adjusted(0.6, 0.6, -0.6, -0.6))
            return

        if self.pixmap.isNull():
            return
        pixmap_aspect = self.pixmap.width() / self.pixmap.height()
        target_aspect = self.width_mm / self.height_mm
        if pixmap_aspect > target_aspect:
            source_height = self.pixmap.height()
            source_width = source_height * target_aspect
            source_x = (self.pixmap.width() - source_width) / 2.0
            source_y = 0.0
        else:
            source_width = self.pixmap.width()
            source_height = source_width / target_aspect
            source_x = 0.0
            source_y = (self.pixmap.height() - source_height) / 2.0
        source = QRectF(source_x, source_y, source_width, source_height)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(target, self.pixmap, source)
        if self.drop_target:
            painter.setPen(QPen(QColor("#ffd36a"), 3.0))
            painter.setBrush(QColor(255, 211, 106, 35))
            painter.drawRect(target.adjusted(1.0, 1.0, -1.0, -1.0))
        elif self.selected:
            painter.setPen(QPen(QColor("#8dc8ff"), 1.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(target.adjusted(0.6, 0.6, -0.6, -0.6))


class WorkspaceView(QGraphicsView):
    poster_selected = Signal(str)
    poster_swap_requested = Signal(str, str)
    bench_poster_replace_requested = Signal(str, str)

    MIN_ZOOM = 0.05
    MAX_ZOOM = 20.0
    ZOOM_STEP = 1.15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._page_width_mm = 27.0 * MM_PER_INCH
        self._page_height_mm = 40.0 * MM_PER_INCH
        self._page_item = PosterPageItem(self._page_width_mm, self._page_height_mm)
        self._poster_items: list[CroppedPosterItem] = []
        self._poster_item_by_imdb_id: dict[str, CroppedPosterItem] = {}
        self._selected_imdb_id: str | None = None
        self._pressed_item: CroppedPosterItem | None = None
        self._press_view_pos = QPoint()
        self._drop_target_item: CroppedPosterItem | None = None
        self._zoom = 1.0
        self._is_panning = False
        self._last_pan_pos = QPoint()
        self._scene.setBackgroundBrush(QColor("#202020"))
        self._scene.addItem(self._page_item)
        self.setObjectName("workspaceView")
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setAcceptDrops(True)
        self._rebuild_scene_rect()
        QTimer.singleShot(0, self.fit_page)

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_canvas_color(self, color: QColor | str) -> None:
        self._page_item.set_canvas_color(color)
        self._scene.update(self._page_item.sceneBoundingRect())
        self.viewport().update()

    def set_page_size(self, width_mm: float, height_mm: float) -> None:
        current_color = self._page_item.canvas_color
        self._page_width_mm = width_mm
        self._page_height_mm = height_mm
        self.clear_posters()
        self._scene.removeItem(self._page_item)
        self._page_item = PosterPageItem(width_mm, height_mm)
        self._page_item.set_canvas_color(current_color)
        self._scene.addItem(self._page_item)
        self._rebuild_scene_rect()
        self.fit_page()

    def clear_posters(self) -> None:
        self._clear_drop_target()
        for item in self._poster_items:
            self._scene.removeItem(item)
        self._poster_items.clear()
        self._poster_item_by_imdb_id.clear()
        self._selected_imdb_id = None
        self._pressed_item = None

    def show_poster_grid(self, poster_entries: list[tuple[str, Path]], layout: GridLayout) -> None:
        selected_id = self._selected_imdb_id
        self.clear_posters()
        for (imdb_title_id, poster_path), cell in zip(poster_entries[: layout.used_count], layout.cells, strict=False):
            pixmap = QPixmap(str(poster_path))
            if pixmap.isNull():
                continue
            item = CroppedPosterItem(imdb_title_id, pixmap, QRectF(cell.x_mm, cell.y_mm, cell.width_mm, cell.height_mm))
            self._scene.addItem(item)
            self._poster_items.append(item)
            self._poster_item_by_imdb_id[imdb_title_id] = item
        if selected_id:
            self.select_poster(selected_id)

    def update_poster(self, imdb_title_id: str, poster_path: Path) -> None:
        item = self._poster_item_by_imdb_id.get(imdb_title_id)
        if item is None:
            return
        pixmap = QPixmap(str(poster_path))
        if not pixmap.isNull():
            item.set_pixmap(pixmap)

    def select_poster(self, imdb_title_id: str | None) -> None:
        self._selected_imdb_id = imdb_title_id
        for item in self._poster_items:
            item.set_selected_visual(item.imdb_title_id == imdb_title_id)

    def fit_page(self) -> None:
        if self.viewport().width() <= 1 or self.viewport().height() <= 1:
            return
        page = QRectF(0, 0, self._page_width_mm, self._page_height_mm)
        padded = page.adjusted(-90, -90, 90, 90)
        self.resetTransform()
        self.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()
        self.centerOn(page.center())

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() == 0:
            return
        factor = self.ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / self.ZOOM_STEP
        new_zoom = self._zoom * factor
        if new_zoom < self.MIN_ZOOM:
            factor = self.MIN_ZOOM / self._zoom
            new_zoom = self.MIN_ZOOM
        elif new_zoom > self.MAX_ZOOM:
            factor = self.MAX_ZOOM / self._zoom
            new_zoom = self.MAX_ZOOM
        old_scene_pos = self.mapToScene(event.position().toPoint())
        self.scale(factor, factor)
        self._zoom = new_zoom
        new_scene_pos = self.mapToScene(event.position().toPoint())
        delta = new_scene_pos - old_scene_pos
        self.translate(delta.x(), delta.y())
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            item = self._poster_item_at(event.pos())
            if item is not None:
                self._pressed_item = item
                self._press_view_pos = event.pos()
                self.select_poster(item.imdb_title_id)
                self.poster_selected.emit(item.imdb_title_id)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self._pressed_item and (event.pos() - self._press_view_pos).manhattanLength() >= QApplication.startDragDistance():
            self._start_poster_drag(self._pressed_item)
            self._pressed_item = None
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed_item = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(TITLE_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        source_kind, source_id = decode_title_mime(event.mimeData())
        target = self._poster_item_at(event.position().toPoint())
        valid = target is not None and target.imdb_title_id != source_id and source_kind in {"canvas", "bench"}
        self._set_drop_target(target if valid else None)
        if valid:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._clear_drop_target()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        source_kind, source_id = decode_title_mime(event.mimeData())
        target = self._poster_item_at(event.position().toPoint())
        self._clear_drop_target()
        if target is None or not source_id or target.imdb_title_id == source_id:
            event.ignore()
            return
        if source_kind == "canvas":
            self.poster_swap_requested.emit(source_id, target.imdb_title_id)
        elif source_kind == "bench":
            self.bench_poster_replace_requested.emit(source_id, target.imdb_title_id)
        else:
            event.ignore()
            return
        event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.fit_page()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_F:
            self.fit_page()
            event.accept()
            return
        super().keyPressEvent(event)

    def _start_poster_drag(self, item: CroppedPosterItem) -> None:
        from PySide6.QtCore import QByteArray, QMimeData

        mime_data = QMimeData()
        mime_data.setData(TITLE_MIME_TYPE, QByteArray(f"canvas|{item.imdb_title_id}".encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime_data)

        # Render the same crop at the exact size currently displayed in the view.
        # This makes the poster feel as though it has been lifted from its cell,
        # rather than expanding to an arbitrary thumbnail size.
        scene_rect = item.mapRectToScene(item.boundingRect())
        view_rect = self.mapFromScene(scene_rect).boundingRect()
        drag_width = max(1, view_rect.width())
        drag_height = max(1, view_rect.height())
        drag_pixmap = QPixmap(drag_width, drag_height)
        drag_pixmap.fill(Qt.GlobalColor.transparent)

        target = QRectF(0, 0, drag_width, drag_height)
        pixmap_aspect = item.pixmap.width() / item.pixmap.height()
        target_aspect = drag_width / drag_height
        if pixmap_aspect > target_aspect:
            source_height = item.pixmap.height()
            source_width = source_height * target_aspect
            source_x = (item.pixmap.width() - source_width) / 2.0
            source_y = 0.0
        else:
            source_width = item.pixmap.width()
            source_height = source_width / target_aspect
            source_x = 0.0
            source_y = (item.pixmap.height() - source_height) / 2.0

        painter = QPainter(drag_pixmap)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setOpacity(0.90)
        painter.drawPixmap(
            target,
            item.pixmap,
            QRectF(source_x, source_y, source_width, source_height),
        )
        painter.end()

        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(QPoint(drag_pixmap.width() // 2, drag_pixmap.height() // 2))
        item.set_drag_placeholder(True)
        try:
            drag.exec(Qt.DropAction.MoveAction)
        finally:
            item.set_drag_placeholder(False)
            self._clear_drop_target()

    def _set_drop_target(self, item: CroppedPosterItem | None) -> None:
        if item is self._drop_target_item:
            return
        self._clear_drop_target()
        self._drop_target_item = item
        if item is not None:
            item.set_drop_target(True)

    def _clear_drop_target(self) -> None:
        if self._drop_target_item is not None:
            self._drop_target_item.set_drop_target(False)
            self._drop_target_item = None

    def _poster_item_at(self, view_pos: QPoint) -> CroppedPosterItem | None:
        item = self.itemAt(view_pos)
        while item is not None:
            if isinstance(item, CroppedPosterItem):
                return item
            item = item.parentItem()
        return None

    def _rebuild_scene_rect(self) -> None:
        margin = 220
        self._page_item.setPos(0, 0)
        self._scene.setSceneRect(QRectF(-margin, -margin, self._page_width_mm + margin * 2, self._page_height_mm + margin * 2))
