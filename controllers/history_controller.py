from __future__ import annotations

from copy import deepcopy

from poster_montage_designer.models import Project


class HistoryController:
    """Small undo/redo controller that owns project snapshots.

    This keeps history bookkeeping out of MainWindow while preserving the
    existing deepcopy-based behaviour. Later we can replace the internals with
    command objects without changing the window code again.
    """

    def __init__(self) -> None:
        self._undo_stack: list[Project] = []
        self._redo_stack: list[Project] = []
        self._restoring = False

    @property
    def is_restoring(self) -> bool:
        return self._restoring

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    def push(self, project: Project) -> None:
        if self._restoring:
            return

        self._undo_stack.append(deepcopy(project))
        self._redo_stack.clear()

    def undo(self, current_project: Project) -> Project | None:
        if not self._undo_stack:
            return None

        self._restoring = True
        try:
            self._redo_stack.append(deepcopy(current_project))
            return self._undo_stack.pop()
        finally:
            self._restoring = False

    def redo(self, current_project: Project) -> Project | None:
        if not self._redo_stack:
            return None

        self._restoring = True
        try:
            self._undo_stack.append(deepcopy(current_project))
            return self._redo_stack.pop()
        finally:
            self._restoring = False
