import os
import shutil
import sys
import ctypes
from pathlib import Path


APP_DIRECTORY = "SB Automation Suite"
DATA_DIRECTORY_ENV = "SB_AUTOMATION_DATA_DIR"
MUTABLE_DEFAULTS = (
    Path("config.json"),
    Path("games.json"),
    Path("entities/enemies.json"),
    Path("entities/items.json"),
)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def resource_root():
    if is_frozen():
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_path(*parts):
    return resource_root().joinpath(*parts)


def data_root():
    override = os.environ.get(DATA_DIRECTORY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if not is_frozen():
        return resource_path("data")

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base).expanduser().resolve() / APP_DIRECTORY / "data"
    return Path.home().resolve() / ".local" / "share" / APP_DIRECTORY / "data"


def data_path(*parts):
    return data_root().joinpath(*parts)


def debug_path(*parts):
    if is_frozen() or os.environ.get(DATA_DIRECTORY_ENV):
        root = data_root().parent / "debug"
    else:
        root = resource_path("debug")
    return root.joinpath(*parts)


def initialize_runtime_environment():
    _initialize_mutable_data()
    return configure_bundled_tesseract()


def configure_bundled_tesseract():
    tesseract_root = resource_path("tesseract")
    executable = tesseract_root / "tesseract.exe"
    tessdata = tesseract_root / "tessdata"
    if not executable.is_file() or not tessdata.is_dir():
        return None

    native_executable = _native_tool_path(executable)
    native_tessdata = _native_tool_path(tessdata)
    native_root = native_executable.parent
    os.environ["TESSDATA_PREFIX"] = str(native_tessdata)
    current_path = os.environ.get("PATH", "")
    path_entries = current_path.split(os.pathsep) if current_path else []
    if str(native_root) not in path_entries:
        os.environ["PATH"] = os.pathsep.join(
            [str(native_root), *path_entries]
        )
    return native_executable


def _native_tool_path(path):
    resolved = Path(path).resolve()
    if sys.platform != "win32":
        return resolved
    try:
        get_short_path = ctypes.windll.kernel32.GetShortPathNameW
        buffer = ctypes.create_unicode_buffer(32768)
        if get_short_path(str(resolved), buffer, len(buffer)):
            return Path(buffer.value)
    except (AttributeError, OSError, ValueError):
        pass
    return resolved


def _initialize_mutable_data():
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    if not is_frozen():
        return root

    defaults_root = resource_path("defaults")
    for relative_path in MUTABLE_DEFAULTS:
        destination = root / relative_path
        if destination.exists():
            continue
        source = defaults_root / relative_path
        if not source.is_file():
            raise FileNotFoundError(f"No existe dato inicial: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()
    return root
