"""
剪贴板操作模块 - 改进版

优化版本：
- 修复所有裸except子句为具体异常类型
- 添加更详细的错误日志
- 使用结构化日志模块
"""

import time
import threading
from typing import Optional
import ctypes
import pyperclip
from config import get_config
from logger import get_logger

logger = get_logger("clipboard")


class _ClipboardSnapshot:
    """Keep the current OLE clipboard object alive and restore it later."""

    def __init__(self):
        self._ole32 = ctypes.windll.ole32
        self._data_object = ctypes.c_void_p()
        self._ole_initialized = False
        self._text_available = False
        self._text = ""

    def capture(self) -> None:
        self._ole32.OleInitialize.argtypes = [ctypes.c_void_p]
        self._ole32.OleInitialize.restype = ctypes.c_long
        self._ole32.OleGetClipboard.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        self._ole32.OleGetClipboard.restype = ctypes.c_long

        hr = self._ole32.OleInitialize(None)
        if hr >= 0:
            self._ole_initialized = True
            if self._ole32.OleGetClipboard(ctypes.byref(self._data_object)) < 0:
                self._data_object = ctypes.c_void_p()

        # Text fallback for environments where OLE capture is unavailable.
        try:
            value = pyperclip.paste()
            if isinstance(value, str):
                self._text_available = True
                self._text = value
        except (pyperclip.PyperclipException, OSError, RuntimeError):
            pass

    def restore(self) -> None:
        restored = False
        if self._data_object.value:
            self._ole32.OleSetClipboard.argtypes = [ctypes.c_void_p]
            self._ole32.OleSetClipboard.restype = ctypes.c_long
            self._ole32.OleFlushClipboard.restype = ctypes.c_long
            if self._ole32.OleSetClipboard(self._data_object) >= 0:
                restored = self._ole32.OleFlushClipboard() >= 0

        if not restored and self._text_available:
            try:
                pyperclip.copy(self._text)
            except (pyperclip.PyperclipException, OSError, RuntimeError):
                pass

    def close(self) -> None:
        if self._data_object.value:
            try:
                vtable = ctypes.cast(
                    self._data_object,
                    ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
                ).contents
                release = ctypes.WINFUNCTYPE(
                    ctypes.c_ulong, ctypes.c_void_p
                )(vtable[2])
                release(self._data_object)
            except (ValueError, OSError, TypeError):
                pass
            self._data_object = ctypes.c_void_p()

        if self._ole_initialized:
            self._ole32.OleUninitialize()
            self._ole_initialized = False


class ClipboardManager:
    """剪贴板管理器"""

    def __init__(self):
        self._lock = threading.Lock()
        self.config = get_config()
        self.user32 = ctypes.windll.user32
        self.user32.GetClipboardSequenceNumber.restype = ctypes.c_ulong

    def get_selected_text(self) -> Optional[str]:
        """
        获取选中文本

        Windows限制：鼠标选中的文本不会自动进入剪贴板
        必须通过Ctrl+C或右键复制才能获取

        程序会模拟Ctrl+C，并只接受本次操作产生的新剪贴板内容；
        完成后恢复原剪贴板。
        """
        with self._lock:
            snapshot = _ClipboardSnapshot()
            changed = False
            try:
                snapshot.capture()
                before = self.user32.GetClipboardSequenceNumber()
                self._press_ctrl_c()

                interval = self._bounded_config_float(
                    "clipboard.check_interval", 0.05, 0.01, 0.25
                )
                timeout = self._bounded_config_float(
                    "clipboard.copy_timeout", 1.0, 0.1, 3.0
                )
                deadline = time.monotonic() + timeout

                while time.monotonic() < deadline:
                    if self.user32.GetClipboardSequenceNumber() != before:
                        changed = True
                        selected = self._get_clipboard()
                        return selected if selected and selected.strip() else None
                    time.sleep(interval)
                return None
            finally:
                if changed:
                    snapshot.restore()
                snapshot.close()

    def _bounded_config_float(
        self, key: str, default: float, minimum: float, maximum: float
    ) -> float:
        try:
            value = float(self.config.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(minimum, min(value, maximum))

    def get_clipboard_text(self) -> Optional[str]:
        """直接获取剪贴板内容"""
        try:
            content = pyperclip.paste()
            return content if content and content.strip() else None
        # [优化] 替换裸except为具体异常类型
        except (pyperclip.PyperclipException, OSError, RuntimeError) as e:
            logger.warning(f"get_clipboard_text error: {type(e).__name__}: {e}")
            return None

    def _press_ctrl_c(self):
        """模拟 Ctrl+C"""
        VK_CONTROL = 0x11
        VK_C = 0x43
        KEYUP = 0x0002

        ctrl_down = False
        c_down = False
        try:
            self.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            ctrl_down = True
            time.sleep(0.02)

            self.user32.keybd_event(VK_C, 0, 0, 0)
            c_down = True
            time.sleep(0.02)
        finally:
            if c_down:
                self.user32.keybd_event(VK_C, 0, KEYUP, 0)
                time.sleep(0.02)
            if ctrl_down:
                self.user32.keybd_event(VK_CONTROL, 0, KEYUP, 0)

    def _get_clipboard(self) -> str:
        try:
            content = pyperclip.paste()
            return content if content else ""
        # [优化] 替换裸except为具体异常类型
        except (pyperclip.PyperclipException, OSError, RuntimeError):
            return ""

    def set_content(self, text: str) -> bool:
        try:
            pyperclip.copy(text)
            return True
        # [优化] 替换裸except为具体异常类型
        except (pyperclip.PyperclipException, OSError, RuntimeError) as e:
            logger.warning(f"set_content error: {type(e).__name__}: {e}")
            return False


class TextSelector:
    """文本选择器"""

    def __init__(self):
        self._clipboard = ClipboardManager()
        self._last_selected = None

    def get_selection(self) -> Optional[str]:
        """获取选中文本"""
        text = self._clipboard.get_selected_text()
        self._last_selected = text if text else None
        return text

    def get_last_selected(self) -> Optional[str]:
        return self._last_selected

    def copy_to_clipboard(self, text: str) -> bool:
        return self._clipboard.set_content(text)


_text_selector = None

def get_text_selector() -> TextSelector:
    global _text_selector
    if _text_selector is None:
        _text_selector = TextSelector()
    return _text_selector
