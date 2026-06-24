"""
全局热键监听模块 - 支持任意按键组合

优化版本：
- 缓存热键配置（避免每次按键都读配置文件）
- 配置变更时自动刷新缓存
- 支持任意可打印按键和功能键（F1-F12等）
"""

import threading
import traceback
from typing import Callable, Optional, Set
from pynput import keyboard
from pynput.keyboard import Key, Listener, KeyCode
from config import get_config
from logger import get_logger

logger = get_logger("hotkey")


# 修饰键集合
_MODIFIER_KEYS: Set[str] = {'ctrl', 'shift', 'alt'}


def _get_key_char(key) -> Optional[str]:
    """从pynput的key对象中提取可匹配的字符/名称"""
    if hasattr(key, 'char') and key.char and key.char.strip():
        return key.char.lower()
    if hasattr(key, 'name') and key.name:
        name = key.name.lower()
        # 过滤掉修饰键等特殊键名
        if name in ('ctrl', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r',
                     'alt', 'alt_l', 'alt_r', 'alt_gr', 'cmd', 'cmd_l', 'cmd_r'):
            return None
        return name
    return None


class HotkeyListener:
    """全局热键监听器（带配置缓存，支持任意按键）"""

    def __init__(self, callback: Callable[[], None]):
        """初始化"""
        self.callback = callback
        self.config = get_config()
        self._listener: Optional[Listener] = None
        self._ctrl = False
        self._shift = False
        self._alt = False
        self._trigger_key_active = False
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
            parts = [p.strip() for p in hotkey.split('+')]
            self._cached_parts = {
                'need_ctrl': 'ctrl' in parts,
                'need_shift': 'shift' in parts,
                'need_alt': 'alt' in parts,
            }
            # 提取触发键（非修饰键部分）
            trigger_key = next((p for p in parts if p not in _MODIFIER_KEYS), 'q')
            self._cached_parts['trigger_key'] = trigger_key

    def _is_trigger_key(self, key) -> bool:
        """检测按下的键是否匹配配置的触发键"""
        trigger = self._cached_parts.get('trigger_key', 'q')
        key_char = _get_key_char(key)
        return key_char == trigger if key_char else False

    def _on_press(self, key):
        """按键按下"""
        # 检测修饰键
        if key in (Key.ctrl_l, Key.ctrl_r):
            self._ctrl = True
        elif key in (Key.shift_l, Key.shift_r):
            self._shift = True
        elif key in (Key.alt_l, Key.alt_r):
            self._alt = True
        # 检测触发键
        elif self._is_trigger_key(key):
            self._trigger_key_active = True

        # [优化] 使用缓存的热键配置，不再每次读文件
        parts = self._cached_parts
        match = (
            (not parts['need_ctrl'] or self._ctrl) and
            (not parts['need_shift'] or self._shift) and
            (not parts['need_alt'] or self._alt) and
            self._trigger_key_active
        )

        if match and not self._triggered:
            self._triggered = True
            logger.info(f"{self._cached_hotkey} 触发！")
            # 重置状态
            self._ctrl = False
            self._shift = False
            self._alt = False
            self._trigger_key_active = False
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
        elif self._is_trigger_key(key):
            self._trigger_key_active = False

    def _safe_callback(self):
        """安全执行回调"""
        try:
            self.callback()
        except Exception as e:
            logger.error(f"回调错误: {e}\n{traceback.format_exc()}")

    def start(self):
        """启动监听"""
        if self._running:
            return
        self._running = True
        self._listener = Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
        logger.info(f"监听已启动，热键: {self.config.get_hotkey()}")

    def stop(self):
        """停止监听"""
        if not self._running:
            return
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("监听已停止")

    def update_hotkey(self, new_hotkey: str):
        """更新热键并刷新缓存"""
        self.config.set_hotkey(new_hotkey)
        self.config.save()
        # [优化] 刷新缓存
        self._refresh_hotkey_cache()
        # 重置所有状态
        self._ctrl = False
        self._shift = False
        self._alt = False
        self._trigger_key_active = False
        self._triggered = False
        if self._running:
            self.stop()
            self.start()

    def is_running(self):
        """是否运行中"""
        return self._running


# 全局实例
_hotkey_listener: Optional[HotkeyListener] = None


def get_hotkey_listener(callback: Callable = None) -> HotkeyListener:
    """获取热键监听器"""
    global _hotkey_listener
    if _hotkey_listener is None:
        if callback is None:
            raise ValueError("需要提供回调函数")
        _hotkey_listener = HotkeyListener(callback)
    return _hotkey_listener


def stop_hotkey_listener() -> None:
    """停止热键监听"""
    global _hotkey_listener
    if _hotkey_listener:
        _hotkey_listener.stop()
        _hotkey_listener = None
