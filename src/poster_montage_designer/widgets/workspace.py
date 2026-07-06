from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView

from poster_montage_designer.layouts.grid import GridLayout


MM_PER_INCH = 25.4


class PosterPageItem(QGraphicsItem):
    def __init__(self, width_mm: float, height_mm: float) -> None:
        super().__init__()
        self.width_mm = width_mm
        self.height_mm = height_mm

    def boundingRect(self) -> QRectF:
        shadow_pad = 18
        return QRectF(
            -shadow_pad,
            -shadow_pad,
            self.width_mm + shadow_pad * 2,
            self.height_mm + shadow_pad * 2,
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        page = QRectF(0, 0, self.width_mm, self.height_mm)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for i, alpha in enumerate((35, 24, 15, 8)):
            offset = 5 + i * 3
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRect(page.translated(offset, offset))

        painter.setBrush(QColor("#eeeeee"))
        painter.setPen(QPen(QColor("#111111"), 0.8))
        painter.drawRect(page)


class CroppedPosterItem(QGraphicsItem):
    def __init__(self, pixmap: QPixmap, target_rect: QRectF) -> None:
        super().__init__()

        self.pixmap = pixmap
        self.width_mm = target_rect.width()
        self.height_mm = target_rect.height()

        self.setPos(target_rect.topLeft())
        self.setZValue(10)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width_mm, self.height_mm)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self.pixmap.isNull():
            return

        target = QRectF(0, 0, self.width_mm, self.height_mm)

        pixmap_aspect = self.pixmap.width() / self.pixmap.height()
        target_aspect = self.width_mm / self.height_mm

        if pixmap_aspect > target_aspect:
            # Image is wider than the cell: crop left/right.
            source_height = self.pixmap.height()
            source_width = source_height * target_aspect
            source_x = (self.pixmap.width() - source_width) / 2.0
            source_y = 0.0
        else:
            # Image is taller than the cell: crop top/bottom.
            source_width = self.pixmap.width()
            source_height = source_width / target_aspect
            source_x = 0.0
            source_y = (self.pixmap.height() - source_height) / 2.0

        source = QRectF(source_x, source_y, source_width, source_height)

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(target, self.pixmap, source)


class WorkspaceView(QGraphicsView):
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

        self._rebuild_scene_rect()
        QTimer.singleShot(0, self.fit_page)

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_page_size(self, width_mm: float, height_mm: float) -> None:
        self._page_width_mm = width_mm
        self._page_height_mm = height_mm

        self.clear_posters()

        self._scene.removeItem(self._page_item)
        self._page_item = PosterPageItem(width_mm, height_mm)
        self._scene.addItem(self._page_item)

        self._rebuild_scene_rect()
        self.fit_page()

    def clear_posters(self) -> None:
        for item in self._poster_items:
            self._scene.removeItem(item)
        self._poster_items.clear()

    def show_poster_grid(self, poster_paths: list[Path], layout: GridLayout) -> None:
        self.clear_posters()

        used_paths = poster_paths[: layout.used_count]

        for poster_path, cell in zip(used_paths, layout.cells, strict=False):
            pixmap = QPixmap(str(poster_path))
            if pixmap.isNull():
                continue

            target_rect = QRectF(
                cell.x_mm,
                cell.y_mm,
                cell.width_mm,
                cell.height_mm,
            )

            item = CroppedPosterItem(pixmap, target_rect)
            self._scene.addItem(item)
            self._poster_items.append(item)

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

        zoom_in = event.angleDelta().y() > 0
        factor = self.ZOOM_STEP if zoom_in else 1.0 / self.ZOOM_STEP
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

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.fit_page()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_F:
            self.fit_page()
            event.accept()
            return

        super().keyPressEvent(event)

    def _rebuild_scene_rect(self) -> None:
        margin = 220
        self._page_item.setPos(0, 0)

        self._scene.setSceneRect(
            QRectF(
                -margin,
                -margin,
                self._page_width_mm + margin * 2,
                self._page_height_mm + margin * 2,
            )
        )