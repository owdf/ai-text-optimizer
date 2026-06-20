"""
全局热键监听模块 - 使用虚拟键码检测

优化版本：
- 缓存热键配置（避免每次按键都读配置文件）
- 配置变更时自动刷新缓存
"""

import threading
from typing import Callable, Optional
from pynput import keyboard
from pynput.keyboard import Key, Listener, KeyCode
from config import get_config


# Q键的虚拟键码
VK_Q = 0x51


class HotkeyListener:
    """全局热键监听器（带配置缓存）"""

    def __init__(self, callback: Callable[[], None]):
        """初始化"""
        self.callback = callback
        self.config = get_config()
        self._listener: Optional[Listener] = None
        self._ctrl = False
        self._shift = False
        self._alt = False
        self._q = False
        self._running = False
        self._triggered = False

        # [优化] 缓存热键配置，避免每次按键读文件
        self._cached_hotkey: Optional[str] = None
        self._cached_parts: dict = {}
        self._refresh_hotkey_cache()

    def _refresh_hotkey_cache(self) -> None:
        """刷新热键配置缓存"""
        hotkey = self.config.get_hotkey().lower().strip()
        if hotkey != self._cached_hotkey:
            self._cached_hotkey = hotkey
            self._cached_parts = {
                'need_ctrl': 'ctrl' in hotkey,
                'need_shift': 'shift' in hotkey,
                'need_alt': 'alt' in hotkey,
                'need_q': 'q' in hotkey,
            }

    def _on_press(self, key):
        """按键按下"""
        # 检测Ctrl
        if key in (Key.ctrl_l, Key.ctrl_r):
            self._ctrl = True
        # 检测Shift
        elif key in (Key.shift_l, Key.shift_r):
            self._shift = True
        # 检测Alt
        elif key in (Key.alt_l, Key.alt_r):
            self._alt = True
        # 检测Q键（使用虚拟键码）
        elif hasattr(key, 'vk') and key.vk == VK_Q:
            self._q = True
        # 备用检测：字符q
        elif hasattr(key, 'char') and key.char and key.char.lower() == 'q':
            self._q = True

        # [优化] 使用缓存的热键配置，不再每次读文件
        parts = self._cached_parts
        match = (
            (not parts['need_ctrl'] or self._ctrl) and
            (not parts['need_shift'] or self._shift) and
            (not parts['need_alt'] or self._alt) and
            (not parts['need_q'] or self._q)
        )

        if match and not self._triggered:
            self._triggered = True
            print("[热键] 组合键触发！")
            # 重置状态
            self._ctrl = False
            self._shift = False
            self._alt = False
            self._q = False
            # 在新线程执行回调
            threading.Thread(target=self._safe_callback, daemon=True).start()

    def _on_release(self, key):
        """按键释放"""
        if key in (Key.ctrl_l, Key.ctrl_r):
            self._ctrl = False
            self._triggered = False
        elif key in (Key.shift_l, Key.shift_r):
            self._shift = False
        elif key in (Key.alt_l, Key.alt_r):
            self._alt = False
        elif hasattr(key, 'vk') and key.vk == VK_Q:
            self._q = False
        elif hasattr(key, 'char') and key.char and key.char.lower() == 'q':
            self._q = False

    def _safe_callback(self):
        """安全执行回调"""
        try:
            self.callback()
        except Exception as e:
            print(f"[热键] 回调错误: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """启动监听"""
        if self._running:
            return
        self._running = True
        self._listener = Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
        print(f"[热键] 监听已启动，热键: {self.config.get_hotkey()}")

    def stop(self):
        """停止监听"""
        if not self._running:
            return
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        print("[热键] 监听已停止")

    def update_hotkey(self, new_hotkey: str):
        """更新热键并刷新缓存"""
        self.config.set_hotkey(new_hotkey)
        self.config.save()
        # [优化] 刷新缓存
        self._refresh_hotkey_cache()
        if self._running:
            self.stop()
            self.start()

    def is_running(self):
        """是否运行中"""
        return self._running


# 全局实例
_hotkey_listener = None

def get_hotkey_listener(callback=None):
    """获取热键监听器"""
    global _hotkey_listener
    if _hotkey_listener is None:
        if callback is None:
            raise ValueError("需要提供回调函数")
        _hotkey_listener = HotkeyListener(callback)
    return _hotkey_listener

def stop_hotkey_listener():
    """停止热键监听"""
    global _hotkey_listener
    if _hotkey_listener:
        _hotkey_listener.stop()
        _hotkey_listener = None
