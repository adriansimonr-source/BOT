import os
import shutil
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules


ROOT = Path(SPEC).resolve().parent
TESSERACT_EXECUTABLE = shutil.which("tesseract")
TESSERACT_ROOT = Path(
    os.environ.get("TESSERACT_HOME")
    or (Path(TESSERACT_EXECUTABLE).parent if TESSERACT_EXECUTABLE else "")
).resolve()

if not (TESSERACT_ROOT / "tesseract.exe").is_file():
    raise SystemExit(
        "Tesseract no encontrado. Define TESSERACT_HOME antes de construir."
    )

datas = [
    (str(ROOT / "data/templates.json"), "data"),
    (str(ROOT / "data/templates/anchors"), "data/templates/anchors"),
    (str(ROOT / "data/logo/Logo_cami.png"), "data/logo"),
    (str(ROOT / "data/config.json"), "defaults"),
    (str(ROOT / "data/games.json"), "defaults"),
    (str(ROOT / "data/entities/enemies.json"), "defaults/entities"),
    (str(ROOT / "data/entities/items.json"), "defaults/entities"),
    (str(TESSERACT_ROOT / "tesseract.exe"), "tesseract"),
    (str(TESSERACT_ROOT / "tessdata"), "tesseract/tessdata"),
]

license_file = TESSERACT_ROOT / "doc/LICENSE"
if license_file.is_file():
    datas.append((str(license_file), "tesseract/doc"))

for library in TESSERACT_ROOT.glob("*.dll"):
    datas.append((str(library), "tesseract"))

hiddenimports = collect_submodules("winrt")
binaries = collect_dynamic_libs("winrt")

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SB_Automation_Suite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "data/logo/Logo_cami.png"),
    contents_directory="_internal",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SB_Automation_Suite",
)
