from pathlib import Path

from PySide6.QtUiTools import QUiLoader


class MainWindow:
    def __init__(self) -> None:
        ui_path = Path(__file__).parent.parent / "ui" / "main_window.ui"

        loader = QUiLoader()
        self.window = loader.load(str(ui_path))

        if self.window is None:
            raise RuntimeError(f"Could not load UI file: {ui_path}")

        self.window.resize(1000, 700)

    def show(self) -> None:
        self.window.show()