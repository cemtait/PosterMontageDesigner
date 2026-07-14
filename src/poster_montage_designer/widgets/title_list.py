from __future__ import annotations

from PySide6.QtCore import QByteArray, QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QListWidget


TITLE_MIME_TYPE = "application/x-posterfolio-title"


class DraggableTitleList(QListWidget):
    """Title list that exchanges IMDb IDs with the canvas via Qt drag-and-drop."""

    canvas_title_dropped = Signal(str)

    def __init__(self, source_kind: str, parent=None) -> None:
        super().__init__(parent)
        self.source_kind = source_kind
        self.setDragEnabled(True)
        self.setAcceptDrops(source_kind == "bench")
        self.setDropIndicatorShown(source_kind == "bench")
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def startDrag(self, supported_actions) -> None:
        item = self.currentItem()
        if item is None:
            return

        imdb_title_id = item.data(Qt.ItemDataRole.UserRole)
        if not imdb_title_id:
            return

        mime_data = QMimeData()
        payload = f"{self.source_kind}|{imdb_title_id}".encode("utf-8")
        mime_data.setData(TITLE_MIME_TYPE, QByteArray(payload))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.viewport().grab(self.visualItemRect(item)))
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event) -> None:
        if self.source_kind == "bench" and event.mimeData().hasFormat(TITLE_MIME_TYPE):
            source_kind, _ = decode_title_mime(event.mimeData())
            if source_kind == "canvas":
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        source_kind, imdb_title_id = decode_title_mime(event.mimeData())
        if self.source_kind == "bench" and source_kind == "canvas" and imdb_title_id:
            self.canvas_title_dropped.emit(imdb_title_id)
            event.acceptProposedAction()
            return
        event.ignore()


def decode_title_mime(mime_data: QMimeData) -> tuple[str, str]:
    if not mime_data.hasFormat(TITLE_MIME_TYPE):
        return "", ""
    try:
        text = bytes(mime_data.data(TITLE_MIME_TYPE)).decode("utf-8")
        source_kind, imdb_title_id = text.split("|", 1)
        return source_kind, imdb_title_id
    except (UnicodeDecodeError, ValueError):
        return "", ""
