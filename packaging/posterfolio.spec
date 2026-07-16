# Run from project root: pyinstaller packaging/posterfolio.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH).parent.parent
package_root = project_root / "src" / "poster_montage_designer"

a = Analysis(
    [str(package_root / "app.py")],
    pathex=[str(project_root / "src")],
    datas=[(str(package_root / "assets"), "poster_montage_designer/assets")],
    hiddenimports=["PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineCore"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="Posterfolio",
    console=False,
    icon=str(package_root / "assets" / "icons" / "posterfolio.ico"),
)
