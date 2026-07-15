"""Runtime paths shared by source and packaged builds."""

import os
import sys
from pathlib import Path


APP_DIR_NAME = "AITextOptimizer"


def is_frozen() -> bool:
    """Return whether the process is running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def get_user_data_dir() -> Path:
    """Return a stable per-user data directory."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def resolve_data_file(filename: str, source_dir: Path) -> Path:
    """Resolve a writable data file without using PyInstaller's temp folder.

    Source runs retain the historical CWD/script-directory behavior. Frozen
    builds use a portable file beside the executable when one already exists,
    otherwise they use the per-user data directory.
    """
    if is_frozen():
        portable = Path(sys.executable).resolve().parent / filename
        if portable.exists():
            return portable
        return get_user_data_dir() / filename

    cwd_path = Path.cwd() / filename
    if cwd_path.exists():
        return cwd_path
    return Path(source_dir) / filename


def resolve_log_dir(source_dir: Path) -> Path:
    """Return a persistent log directory for the current runtime."""
    if is_frozen():
        return get_user_data_dir() / "logs"
    return Path(source_dir) / "logs"
