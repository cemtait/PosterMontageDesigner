from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView


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

        # Soft blocky shadow for now. We can replace this with a nicer blur later.
        for i, alpha in enumerate((35, 24, 15, 8)):
            offset = 5 + i * 3
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRect(page.translated(offset, offset))

        painter.setBrush(QColor("#eeeeee"))
        painter.setPen(QPen(QColor("#111111"), 0.8))
        painter.drawRect(page)

        painter.setPen(QPen(QColor("#c8c8c8"), 0.5))
        painter.drawRect(page.adjusted(8, 8, -8, -8))


class WorkspaceView(QGraphicsView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._page_width_mm = 27.0 * MM_PER_INCH
        self._page_height_mm = 40.0 * MM_PER_INCH
        self._page_item = PosterPageItem(self._page_width_mm, self._page_height_mm)

        self._zoom = 1.0
        self._pan = QPointF(0, 0)

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

        self._rebuild_scene_rect()

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def pan(self) -> QPointF:
        return self._pan

    def set_page_size(self, width_mm: float, height_mm: float) -> None:
        self._page_width_mm = width_mm
        self._page_height_mm = height_mm

        self._scene.removeItem(self._page_item)
        self._page_item = PosterPageItem(width_mm, height_mm)
        self._scene.addItem(self._page_item)

        self._rebuild_scene_rect()
        self._fit_page()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_page()

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

    def _fit_page(self) -> None:
        if self.viewport().width() <= 1 or self.viewport().height() <= 1:
            return

        target = QRectF(0, 0, self._page_width_mm, self._page_height_mm)
        padded = target.adjusted(-90, -90, 90, 90)

        self.resetTransform()
        self.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)
        self.centerOn(target.center())