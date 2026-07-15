"""
热键设置窗口 - 按下热键方式 + 统一主题
"""

import customtkinter as ctk
from typing import Optional, Callable
from config import get_config
from language import t
from icons import get_icon_manager
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from ui.theme import (
    Colors, Space, Radius, Type, Size,
    font, apply_window_chrome, make_card, secondary_button, status_color,
)


class HotkeyWindow:
    """热键设置窗口 - 按下热键方式"""

    def __init__(self, master=None, dispatcher=None):
        self.config = get_config()
        self._master = master
        self._dispatcher = dispatcher
        self._window: Optional[ctk.CTkToplevel] = None
        self._is_visible = False
        self._on_close: Optional[Callable] = None
        self._on_save: Optional[Callable] = None
        self._icons = get_icon_manager()

        # 监听状态
        self._listening = False
        self._listener = None
        self._pressed_keys = set()
        self._save_after_id = None  # 取消/替换延迟保存定时器

        # UI组件
        self._status_label = None
        self._preview_label = None
        self._listen_btn = None
        self._current_label = None

    def _dispatch_ui(self, callback, *args):
        if self._dispatcher is not None:
            self._dispatcher(callback, *args)
        elif self._window is not None:
            self._window.after(0, callback, *args)

    def _create_window(self) -> None:
        if self._window is not None:
            return

        if self._master is not None:
            self._window = ctk.CTkToplevel(self._master)
        else:
            self._window = ctk.CTkToplevel()
        apply_window_chrome(self._window, t("hotkey_title"))
        self._window.geometry("480x460")
        self._window.resizable(False, False)

        self._center_window()
        self._create_widgets()
        self._window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _center_window(self) -> None:
        if self._window is None:
            return
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        x = (sw - 480) // 2
        y = (sh - 460) // 2
        self._window.geometry(f"480x460+{x}+{y}")

    def _create_widgets(self) -> None:
        if self._window is None:
            return

        main = ctk.CTkFrame(self._window, fg_color=Colors.BG, corner_radius=0)
        main.pack(fill="both", expand=True, padx=Size.WINDOW_PAD, pady=Size.WINDOW_PAD)

        # 标题
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, Space.LG))

        settings_icon = self._icons.create_icon("settings", size=22, color=Colors.ACCENT_AI)
        ctk.CTkLabel(
            header,
            image=settings_icon,
            text=f"  {t('hotkey_title')}",
            font=font(Type.TITLE, "bold"),
            text_color=Colors.TEXT,
            compound="left",
        ).pack(side="left")

        # 当前热键卡片
        current_frame = make_card(main, fill="x", pady=(0, Space.LG))
        ctk.CTkLabel(
            current_frame,
            text=t("hotkey_current"),
            font=font(Type.LABEL),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(padx=Size.SECTION_PAD_X, pady=(Size.SECTION_PAD_Y, Space.XS), anchor="w")

        current_hotkey = self.config.get_hotkey().upper().replace("+", " + ")
        self._current_label = ctk.CTkLabel(
            current_frame,
            text=current_hotkey,
            font=font(22, "bold"),
            text_color=Colors.PRIMARY,
        )
        self._current_label.pack(padx=Size.SECTION_PAD_X, pady=(0, Size.SECTION_PAD_Y), anchor="w")

        # 监听区域
        listen_frame = make_card(main, fill="x", pady=(0, Space.LG))

        ctk.CTkLabel(
            listen_frame,
            text=t("hotkey_press"),
            font=font(Type.BODY, "bold"),
            text_color=Colors.TEXT,
        ).pack(pady=(Size.SECTION_PAD_Y, Space.SM))

        ctk.CTkLabel(
            listen_frame,
            text=t("hotkey_example"),
            font=font(Type.HINT),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(0, Space.MD))

        # 预览区
        preview_box = ctk.CTkFrame(
            listen_frame, fg_color=Colors.INPUT_BG, corner_radius=Radius.MD, height=56
        )
        preview_box.pack(fill="x", padx=Size.SECTION_PAD_X, pady=(0, Space.MD))
        preview_box.pack_propagate(False)

        self._preview_label = ctk.CTkLabel(
            preview_box,
            text=t("hotkey_waiting"),
            font=font(20, "bold"),
            text_color=Colors.WARNING,
        )
        self._preview_label.pack(expand=True)

        self._status_label = ctk.CTkLabel(
            listen_frame,
            text="",
            font=font(Type.HINT),
            text_color=Colors.TEXT_SECONDARY,
        )
        self._status_label.pack(pady=(0, Space.SM))

        # 主操作按钮 ≥44px
        self._listen_btn = ctk.CTkButton(
            listen_frame,
            text=t("hotkey_start_listen"),
            font=font(Type.BODY, "bold"),
            height=44,
            width=220,
            fg_color=Colors.DANGER,
            hover_color=Colors.DANGER_HOVER,
            text_color=Colors.TEXT_INVERSE,
            command=self._toggle_listen,
            corner_radius=Radius.MD,
        )
        self._listen_btn.pack(pady=(Space.SM, Size.SECTION_PAD_Y))

        # 底栏：快捷预设 + 关闭
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")

        preset_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        preset_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            preset_frame,
            text=t("hotkey_preset") + ":",
            font=font(Type.HINT),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, Space.SM))

        for label, value in (
            ("Ctrl+Q", "ctrl+q"),
            ("Ctrl+Shift+Q", "ctrl+shift+q"),
            ("Alt+A", "alt+a"),
        ):
            ctk.CTkButton(
                preset_frame,
                text=label,
                font=font(Type.CAPTION),
                height=32,
                width=max(72, len(label) * 9),
                fg_color=Colors.SURFACE_MUTED,
                hover_color=Colors.SURFACE_HOVER,
                text_color=Colors.TEXT,
                command=lambda v=value: self._set_preset(v),
                corner_radius=Radius.SM,
            ).pack(side="left", padx=2)

        secondary_button(
            btn_frame, t("close"), self._on_window_close, width=88
        ).pack(side="right")

    def _toggle_listen(self):
        """切换监听状态"""
        if self._listening:
            self._stop_listen()
        else:
            self._start_listen()

    def _start_listen(self):
        """开始监听"""
        self._listening = True
        self._pressed_keys = set()

        self._listen_btn.configure(
            text=t("hotkey_stop_listen"),
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_HOVER,
            text_color=Colors.TEXT_INVERSE,
        )
        self._preview_label.configure(text=t("hotkey_waiting"), text_color=Colors.WARNING)
        self._status_label.configure(text=t("hotkey_press_esc"), text_color=Colors.TEXT_SECONDARY)

        # 启动键盘监听
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._listener.start()

    def _stop_listen(self):
        """停止监听"""
        self._listening = False

        if self._window is not None and self._save_after_id is not None:
            try:
                self._window.after_cancel(self._save_after_id)
            except Exception:
                pass
            self._save_after_id = None

        if self._listener:
            self._listener.stop()
            self._listener = None

        if self._listen_btn is not None:
            self._listen_btn.configure(
                text=t("hotkey_start_listen"),
                fg_color=Colors.DANGER,
                hover_color=Colors.DANGER_HOVER,
                text_color=Colors.TEXT_INVERSE,
            )
        if self._status_label is not None:
            self._status_label.configure(text="")

    def _on_key_press(self, key):
        """按键按下"""
        if not self._listening:
            return

        # ESC取消
        if key == Key.esc:
            self._dispatch_ui(self._cancel_listen_from_key)
            return

        self._pressed_keys.add(key)

        # 构建热键字符串
        parts = []

        # 检查修饰键
        ctrl = Key.ctrl_l in self._pressed_keys or Key.ctrl_r in self._pressed_keys
        shift = Key.shift_l in self._pressed_keys or Key.shift_r in self._pressed_keys
        alt = Key.alt_l in self._pressed_keys or Key.alt_r in self._pressed_keys

        if ctrl:
            parts.append("Ctrl")
        if shift:
            parts.append("Shift")
        if alt:
            parts.append("Alt")

        # 检查普通键
        normal_key = None
        for k in self._pressed_keys:
            if k not in (Key.ctrl_l, Key.ctrl_r, Key.shift_l, Key.shift_r, Key.alt_l, Key.alt_r):
                if hasattr(k, 'char') and k.char:
                    normal_key = k.char.upper()
                elif hasattr(k, 'name'):
                    normal_key = k.name.upper()
                break

        if normal_key:
            parts.append(normal_key)

        # 更新预览
        if parts:
            hotkey_str = " + ".join(parts)
            self._dispatch_ui(self._show_preview, hotkey_str)

            # 如果有普通键且有修饰键，保存
            if normal_key and (ctrl or shift or alt):
                # 构建保存格式
                save_parts = []
                if ctrl:
                    save_parts.append("ctrl")
                if shift:
                    save_parts.append("shift")
                if alt:
                    save_parts.append("alt")
                save_parts.append(normal_key.lower())

                hotkey_save = "+".join(save_parts)

                # 只保留最近一次延迟保存，避免多次 after 互相覆盖
                self._dispatch_ui(self._schedule_hotkey_save, hotkey_save)

    def _cancel_listen_from_key(self):
        if self._window is None:
            return
        self._stop_listen()
        if self._preview_label is not None:
            self._preview_label.configure(
                text=t("hotkey_cancelled"), text_color=Colors.DANGER
            )

    def _show_preview(self, hotkey_str: str):
        if self._window is not None and self._preview_label is not None:
            self._preview_label.configure(
                text=hotkey_str, text_color=Colors.SUCCESS
            )

    def _schedule_hotkey_save(self, hotkey: str):
        if self._window is None:
            return
        if self._save_after_id is not None:
            try:
                self._window.after_cancel(self._save_after_id)
            except Exception:
                pass
        self._save_after_id = self._window.after(
            500, lambda h=hotkey: self._save_hotkey(h)
        )

    def _on_key_release(self, key):
        """按键释放"""
        if not self._listening:
            return

        self._pressed_keys.discard(key)

    def _save_hotkey(self, hotkey: str):
        """保存热键"""
        self._save_after_id = None
        if self._window is None:
            return

        self._stop_listen()

        # 保存到配置
        self.config.set("hotkey.trigger", hotkey)
        self.config.save()

        # 更新显示
        display = hotkey.upper().replace("+", " + ")
        if self._preview_label is not None:
            self._preview_label.configure(text=display, text_color=Colors.SUCCESS)
        if self._current_label is not None:
            self._current_label.configure(text=display)
        if self._status_label is not None:
            self._status_label.configure(text=t("hotkey_saved"), text_color=status_color("success"))

        # 回调
        if self._on_save:
            self._on_save(hotkey)

    def _set_preset(self, hotkey: str):
        """设置预设热键"""
        self._stop_listen()

        display = hotkey.upper().replace("+", " + ")
        self._preview_label.configure(text=display, text_color=Colors.SUCCESS)
        if self._current_label is not None:
            self._current_label.configure(text=display)

        # 保存
        self.config.set("hotkey.trigger", hotkey)
        self.config.save()

        self._status_label.configure(text=t("hotkey_saved"), text_color=status_color("success"))

        if self._on_save:
            self._on_save(hotkey)

    def _on_window_close(self):
        """关闭窗口"""
        self._stop_listen()
        self.close()
        if self._on_close:
            self._on_close()

    def show(self):
        """显示窗口"""
        if self._window is None:
            self._create_window()
        self._window.deiconify()
        self._window.lift()
        self._window.focus_force()
        self._is_visible = True

    def close(self):
        """关闭窗口"""
        self._stop_listen()
        if self._window:
            self._window.destroy()
            self._window = None
            self._is_visible = False

    def set_on_close(self, callback):
        self._on_close = callback

    def set_on_save(self, callback):
        self._on_save = callback

    def is_visible(self):
        return self._is_visible


_hotkey_window = None

def get_hotkey_window(master=None, dispatcher=None):
    global _hotkey_window
    if _hotkey_window is None:
        _hotkey_window = HotkeyWindow(master=master, dispatcher=dispatcher)
    elif master is not None:
        _hotkey_window._master = master
    if dispatcher is not None:
        _hotkey_window._dispatcher = dispatcher
    return _hotkey_window
