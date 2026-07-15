"""Hotkey matching and lifecycle regressions."""

from hotkey import HotkeyListener


def _listener_state(**overrides):
    listener = HotkeyListener.__new__(HotkeyListener)
    listener._cached_parts = {
        "need_ctrl": True,
        "need_shift": False,
        "need_alt": False,
    }
    listener._ctrl = True
    listener._shift = False
    listener._alt = False
    listener._trigger = True
    for key, value in overrides.items():
        setattr(listener, key, value)
    return listener


def test_hotkey_rejects_extra_modifier():
    assert _listener_state()._matches_hotkey()
    assert not _listener_state(_shift=True)._matches_hotkey()
    assert not _listener_state(_alt=True)._matches_hotkey()


def test_update_does_not_restart_stopped_listener():
    class ConfigStub:
        hotkey = "ctrl+q"

        def set_hotkey(self, value):
            self.hotkey = value

        def get_hotkey(self):
            return self.hotkey

        def save(self):
            return True

    listener = HotkeyListener.__new__(HotkeyListener)
    listener.config = ConfigStub()
    listener._running = False
    listener._cached_hotkey = "ctrl+q"
    listener._cached_parts = {}
    listener._listener = None
    calls = []
    listener.stop = lambda: calls.append("stop")
    listener.start = lambda: calls.append("start")

    listener.update_hotkey("alt+a")

    assert calls == []
    assert listener.config.hotkey == "alt+a"
