"""
全局热键监听模块 - 使用虚拟键码检测

优化版本：
- 缓存热键配置（避免每次按键都读配置文件）
- 配置变更时自动刷新缓存
- 动态计算触发键虚拟键码，支持任意按键
"""

import threading
from typing import Callable, Optional
from pynput import keyboard
from pynput.keyboard import Key, Listener, KeyCode
from config import get_config


def _get_key_vk(key_name: str) -> int:
    """根据按键名获取 Windows 虚拟键码（纯查表，不依赖 Win32 API）

    ASCII 标准虚拟键码，所有键盘布局通用：
    - a-z: 0x41-0x5A (VK_A - VK_Z)
    - 0-9: 0x30-0x39 (VK_0 - VK_9)
    """
    key = key_name.lower().strip()
    if len(key) != 1:
        # 功能键和特殊键
        _SPECIAL = {
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
            'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
            'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
            'space': 0x20, 'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
            'backspace': 0x08, 'delete': 0x2E, 'esc': 0x1B, 'escape': 0x1B,
            'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
            'home': 0x24, 'end': 0x23, 'page_up': 0x21, 'page_down': 0x22,
            'insert': 0x2D, 'caps_lock': 0x14,
        }
        return _SPECIAL.get(key, 0)

    c = ord(key)
    if ord('a') <= c <= ord('z'):
        return c - ord('a') + 0x41
    if ord('0') <= c <= ord('9'):
        return c - ord('0') + 0x30
    # 符号键
    _SYMBOL = {
        '-': 0xBD, '=': 0xBB, '[': 0xDB, ']': 0xDD,
        '\\': 0xDC, ';': 0xBA, "'": 0xDE, ',': 0xBC,
        '.': 0xBE, '/': 0xBF, '`': 0xC0,
    }
    return _SYMBOL.get(key, 0)


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
        self._trigger = False
        self._running = False
        self._triggered = False

        # [优化] 缓存热键配置，避免每次按键读文件
        self._cached_hotkey: Optional[str] = None
        self._cached_parts: dict = {}
        self._trigger_vk: int = 0x51  # 默认 Q 键
        self._trigger_char: str = 'q'
        self._refresh_hotkey_cache()

    def _refresh_hotkey_cache(self) -> None:
        """刷新热键配置缓存"""
        hotkey = self.config.get_hotkey().lower().strip()
        if hotkey != self._cached_hotkey:
            self._cached_hotkey = hotkey

            # 解析修饰键
            need_ctrl = 'ctrl' in hotkey
            need_shift = 'shift' in hotkey
            need_alt = 'alt' in hotkey

            # 提取触发键（非修饰键的部分）
            parts = [p.strip() for p in hotkey.split('+')]
            mod_keys = {'ctrl', 'shift', 'alt'}
            trigger_key = next((p for p in parts if p not in mod_keys), 'q')

            self._cached_parts = {
                'need_ctrl': need_ctrl,
                'need_shift': need_shift,
                'need_alt': need_alt,
            }
            self._trigger_vk = _get_key_vk(trigger_key)
            self._trigger_char = trigger_key

            print(f"[热键] 缓存已刷新: {hotkey}, vk=0x{self._trigger_vk:02X}")

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
        # 检测触发键（使用虚拟键码）
        elif hasattr(key, 'vk') and key.vk == self._trigger_vk:
            self._trigger = True
        # 备用检测：字符
        elif hasattr(key, 'char') and key.char and key.char.lower() == self._trigger_char:
            self._trigger = True

        # [优化] 使用缓存的热键配置，不再每次读文件
        parts = self._cached_parts
        match = (
            (not parts['need_ctrl'] or self._ctrl) and
            (not parts['need_shift'] or self._shift) and
            (not parts['need_alt'] or self._alt) and
            self._trigger
        )

        if match and not self._triggered:
            self._triggered = True
            print("[热键] 组合键触发！")
            # 重置状态
            self._ctrl = False
            self._shift = False
            self._alt = False
            self._trigger = False
            # 在新线程执行回调
            threading.Thread(target=self._safe_callback, daemon=True).start()

    def _on_release(self, key):
        """按键释放"""
        if key in (Key.ctrl_l, Key.ctrl_r):
            self._ctrl = False
            self._triggered = False
        elif key in (Key.shift_l, Key.shift_r):
            self._shift = False
            self._triggered = False
        elif key in (Key.alt_l, Key.alt_r):
            self._alt = False
            self._triggered = False
        elif hasattr(key, 'vk') and key.vk == self._trigger_vk:
            self._trigger = False
            self._triggered = False
        elif hasattr(key, 'char') and key.char and key.char.lower() == self._trigger_char:
            self._trigger = False
            self._triggered = False

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
        """更新热键并刷新缓存（保存后无条件重启监听器）"""
        self.config.set_hotkey(new_hotkey)
        self.config.save()
        # 强制刷新缓存
        self._cached_hotkey = None
        self._refresh_hotkey_cache()
        # 重置所有按键状态
        self._ctrl = False
        self._shift = False
        self._alt = False
        self._trigger = False
        self._triggered = False
        # 无条件重启监听器
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
