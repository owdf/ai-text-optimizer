"""Persistent path behavior for source and PyInstaller builds."""

import sys
from pathlib import Path

from app_paths import resolve_data_file, resolve_log_dir


def test_frozen_build_uses_local_appdata(monkeypatch, tmp_path):
    local_appdata = tmp_path / "LocalAppData"
    exe_dir = tmp_path / "bin"
    exe_dir.mkdir()

    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "AITextOptimizer.exe"))

    assert resolve_data_file("config.json", tmp_path) == (
        local_appdata / "AITextOptimizer" / "config.json"
    )
    assert resolve_log_dir(tmp_path) == local_appdata / "AITextOptimizer" / "logs"


def test_frozen_build_honors_existing_portable_file(monkeypatch, tmp_path):
    exe_dir = tmp_path / "bin"
    exe_dir.mkdir()
    portable = exe_dir / "config.json"
    portable.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "AITextOptimizer.exe"))

    assert resolve_data_file("config.json", tmp_path) == portable
