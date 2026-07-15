"""Clipboard privacy regressions in the hotkey capture path."""

import threading
from unittest.mock import patch

from main import AITextOptimizer


def test_no_selection_never_falls_back_to_existing_clipboard():
    class Selector:
        @staticmethod
        def get_selection():
            return None

    app = AITextOptimizer.__new__(AITextOptimizer)
    app.text_selector = Selector()
    app._processing_lock = threading.Lock()
    app._processing = True
    finished = threading.Event()
    seen = []
    app._post_to_ui = lambda callback, *args: callback(*args)
    app._process_text = lambda text: seen.append(text)
    app._show_no_text = lambda: (seen.append("NO_TEXT"), finished.set())

    with patch("main.pyperclip.paste", side_effect=AssertionError("stale read")) as paste:
        app._start_text_capture()
        assert finished.wait(1)
        paste.assert_not_called()

    assert seen == ["NO_TEXT"]
    assert app._processing is False


def test_successful_capture_restores_snapshot():
    from clipboard import ClipboardManager

    class ConfigStub:
        @staticmethod
        def get(key, default=None):
            return default

    class User32Stub:
        def __init__(self):
            self.values = iter((10, 11))

        def GetClipboardSequenceNumber(self):
            return next(self.values)

    class SnapshotStub:
        def __init__(self):
            self.captured = False
            self.restored = False
            self.closed = False

        def capture(self):
            self.captured = True

        def restore(self):
            self.restored = True

        def close(self):
            self.closed = True

    manager = ClipboardManager.__new__(ClipboardManager)
    manager._lock = threading.Lock()
    manager.config = ConfigStub()
    manager.user32 = User32Stub()
    manager._press_ctrl_c = lambda: None
    manager._get_clipboard = lambda: "new selection"
    snapshot = SnapshotStub()

    with patch("clipboard._ClipboardSnapshot", return_value=snapshot):
        assert manager.get_selected_text() == "new selection"

    assert snapshot.captured
    assert snapshot.restored
    assert snapshot.closed
