"""
浮动窗口模块 - 支持多语言 + 统一主题
"""

import customtkinter as ctk
from typing import Optional, Callable
from config import get_config
from language import t
from icons import get_icon_manager
from ui.theme import (
    Colors, Space, Radius, Type, Size,
    font, mono_font, apply_window_chrome, ghost_icon_button,
    primary_button, secondary_button, status_color,
)


class FloatingWindow:
    """浮动结果窗口"""

    TYPE_ICONS = {
        "error": "error",
        "code": "code",
        "log": "log",
        "config": "config",
        "plain": "text",
    }

    APP_ICONS = {
        "editor": "code",
        "browser": "source",
        "terminal": "log",
        "messaging": "text",
        "ai": "ai",
        "other": "source",
    }

    def __init__(self, master=None):
        self.config = get_config()
        self._master = master
        self._window: Optional[ctk.CTkToplevel] = None
        self._is_visible = False
        self._on_close: Optional[Callable] = None
        self._on_copy: Optional[Callable[[str], None]] = None
        self._icons = get_icon_manager()

        self._app_label = None
        self._type_label = None
        self._original_text = None
        self._result_text = None
        self._copy_btn = None
        self._copy_orig_btn = None
        self._close_btn = None
        self._status_label = None
        self._orig_header_label = None
        self._result_header_label = None

    def set_master(self, master) -> None:
        """绑定主 Tk 根窗口，避免 withdraw 后 Toplevel 不显示"""
        self._master = master

    def _create_window(self) -> None:
        if self._window is not None:
            return

        # 必须挂到主 root，否则 root.withdraw() 后弹窗可能不可见
        if self._master is not None:
            self._window = ctk.CTkToplevel(self._master)
        else:
            self._window = ctk.CTkToplevel()
        apply_window_chrome(self._window, t("window_title"))
        self._window.geometry("600x520")
        self._window.resizable(True, True)
        self._window.minsize(480, 420)

        self._center_window()
        self._create_widgets()
        self._window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        # 先隐藏，等 show() 再显示，避免启动时闪出空窗
        self._window.withdraw()

    def _center_window(self) -> None:
        if self._window is None:
            return
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        x = (sw - 600) // 2
        y = (sh - 520) // 2
        self._window.geometry(f"600x520+{x}+{y}")

    def _create_widgets(self) -> None:
        if self._window is None:
            return

        main = ctk.CTkFrame(self._window, fg_color=Colors.BG, corner_radius=0)
        main.pack(fill="both", expand=True)

        # 标题栏
        header = ctk.CTkFrame(main, fg_color=Colors.SURFACE, height=48, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ai_icon = self._icons.create_icon("ai", size=22, color=Colors.ACCENT_AI)
        ctk.CTkLabel(header, image=ai_icon, text="").pack(side="left", padx=(Size.WINDOW_PAD, Space.SM))

        ctk.CTkLabel(
            header,
            text=t("window_title"),
            font=font(Type.SECTION, "bold"),
            text_color=Colors.ACCENT_AI,
        ).pack(side="left")

        close_icon = self._icons.create_icon("close", size=18, color=Colors.DANGER)
        ghost_icon_button(header, close_icon, self._on_window_close).pack(
            side="right", padx=Space.SM, pady=Space.SM
        )

        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)

        # 上下文信息栏（徽章式）
        ctx_frame = ctk.CTkFrame(main, fg_color=Colors.SURFACE_MUTED, height=36, corner_radius=0)
        ctx_frame.pack(fill="x")
        ctx_frame.pack_propagate(False)

        source_icon = self._icons.create_icon("source", size=16, color=Colors.TEXT_SECONDARY)
        self._app_label = ctk.CTkLabel(
            ctx_frame,
            image=source_icon,
            text=" —",
            font=font(Type.HINT),
            text_color=Colors.TEXT_SECONDARY,
            compound="left",
        )
        self._app_label.pack(side="left", padx=Size.WINDOW_PAD)

        ctk.CTkLabel(ctx_frame, text="·", text_color=Colors.BORDER, width=12).pack(side="left")

        text_icon = self._icons.create_icon("text", size=16, color=Colors.TEXT_SECONDARY)
        self._type_label = ctk.CTkLabel(
            ctx_frame,
            image=text_icon,
            text=f" {t('analyzing')}",
            font=font(Type.HINT),
            text_color=Colors.TEXT_SECONDARY,
            compound="left",
        )
        self._type_label.pack(side="left", padx=Space.SM)

        # 内容区域
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=Space.MD, pady=Space.MD)

        # 原文
        orig_frame = ctk.CTkFrame(
            content, fg_color=Colors.SURFACE, corner_radius=Radius.MD,
            border_width=1, border_color=Colors.BORDER,
        )
        orig_frame.pack(fill="x", pady=(0, Space.MD))

        orig_header = ctk.CTkFrame(orig_frame, fg_color="transparent")
        orig_header.pack(fill="x", padx=Space.MD, pady=(Space.MD, Space.SM))

        copy_icon = self._icons.create_icon("copy", size=16, color=Colors.PRIMARY)
        self._orig_header_label = ctk.CTkLabel(
            orig_header,
            image=copy_icon,
            text=f" {t('original')}",
            font=font(Type.LABEL, "bold"),
            text_color=Colors.PRIMARY,
            compound="left",
        )
        self._orig_header_label.pack(side="left")

        self._original_text = ctk.CTkTextbox(
            orig_frame,
            height=88,
            font=mono_font(Type.HINT),
            wrap="word",
            state="disabled",
            fg_color=Colors.INPUT_BG,
            text_color=Colors.TEXT,
            corner_radius=Radius.SM,
            border_width=0,
        )
        self._original_text.pack(fill="x", padx=Space.MD, pady=(0, Space.MD))

        # AI 结果
        result_frame = ctk.CTkFrame(
            content, fg_color=Colors.SURFACE, corner_radius=Radius.MD,
            border_width=1, border_color=Colors.BORDER,
        )
        result_frame.pack(fill="both", expand=True)

        result_header = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_header.pack(fill="x", padx=Space.MD, pady=(Space.MD, Space.SM))

        ai_small_icon = self._icons.create_icon("ai", size=16, color=Colors.ACCENT_PROMPT)
        self._result_header_label = ctk.CTkLabel(
            result_header,
            image=ai_small_icon,
            text=f" {t('ai_result')}",
            font=font(Type.LABEL, "bold"),
            text_color=Colors.ACCENT_PROMPT,
            compound="left",
        )
        self._result_header_label.pack(side="left")

        self._result_text = ctk.CTkTextbox(
            result_frame,
            font=mono_font(Type.BODY),
            wrap="word",
            state="disabled",
            fg_color=Colors.INPUT_BG,
            text_color=Colors.TEXT,
            corner_radius=Radius.SM,
            border_width=0,
        )
        self._result_text.pack(fill="both", expand=True, padx=Space.MD, pady=(0, Space.MD))

        # 底部操作栏
        footer = ctk.CTkFrame(
            main, fg_color=Colors.SURFACE, height=56, corner_radius=0,
            border_width=1, border_color=Colors.BORDER,
        )
        footer.pack(fill="x")
        footer.pack_propagate(False)

        copy_result_icon = self._icons.create_icon("copy", size=16, color=Colors.TEXT_INVERSE)
        self._copy_btn = primary_button(
            footer, t("copy_result"), self._on_copy_click, icon=copy_result_icon, width=128
        )
        self._copy_btn.configure(height=Size.BTN_H_SM)
        self._copy_btn.pack(side="left", padx=(Size.WINDOW_PAD, Space.SM), pady=Space.SM)

        copy_orig_icon = self._icons.create_icon("copy", size=16, color=Colors.TEXT)
        self._copy_orig_btn = secondary_button(
            footer, t("copy_original"), self._on_copy_original_click, icon=copy_orig_icon, width=130
        )
        self._copy_orig_btn.configure(height=Size.BTN_H_SM)
        self._copy_orig_btn.pack(side="left", padx=Space.SM, pady=Space.SM)

        self._status_label = ctk.CTkLabel(
            footer, text="", font=font(Type.CAPTION), text_color=Colors.SUCCESS
        )
        self._status_label.pack(side="left", padx=Space.MD)

        close_btn_icon = self._icons.create_icon("close", size=14, color=Colors.TEXT)
        self._close_btn = secondary_button(
            footer, t("close"), self._on_window_close, icon=close_btn_icon, width=90
        )
        self._close_btn.configure(height=Size.BTN_H_SM)
        self._close_btn.pack(side="right", padx=Size.WINDOW_PAD, pady=Space.SM)

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        if self._window:
            x = self._window.winfo_x() + (event.x - self._drag_x)
            y = self._window.winfo_y() + (event.y - self._drag_y)
            self._window.geometry(f"+{x}+{y}")

    def show(self, original_text: str, result_text: str, context_info: dict = None) -> None:
        if self._window is None:
            self._create_window()

        if context_info:
            self._update_context(context_info)

        self._set_text(self._original_text, original_text)
        self._set_text(self._result_text, result_text)

        # 强制置顶显示（Windows 上 withdraw 根窗口后需多次激活）
        self._window.deiconify()
        self._window.lift()
        try:
            self._window.attributes("-topmost", True)
        except Exception:
            pass
        self._window.focus_force()
        self._window.update_idletasks()
        # 短暂保持置顶后再放开，避免一直压住其它窗口
        self._window.after(300, self._release_topmost)
        self._is_visible = True
        self._set_status("")

    def _release_topmost(self) -> None:
        if self._window is not None and self._is_visible:
            try:
                self._window.attributes("-topmost", False)
                self._window.lift()
            except Exception:
                pass

    def _update_context(self, info: dict) -> None:
        app = info.get("app_name", "Unknown")
        cat = info.get("app_category", "other")
        ctype = info.get("content_type", "plain")
        lang = info.get("language", "")

        app_icon_name = self.APP_ICONS.get(cat, "source")
        app_icon = self._icons.create_icon(app_icon_name, size=16, color=Colors.TEXT_SECONDARY)
        self._app_label.configure(image=app_icon, text=f" {app}")

        type_icon_name = self.TYPE_ICONS.get(ctype, "text")
        type_icon = self._icons.create_icon(type_icon_name, size=16, color=Colors.TEXT_SECONDARY)
        type_names = {
            "error": t("cat_debug"),
            "code": t("cat_code"),
            "log": t("cat_log"),
            "config": t("cat_config"),
            "plain": t("cat_general")
        }
        type_text = type_names.get(ctype, "Unknown")
        if lang and lang != "unknown":
            type_text += f" ({lang})"
        self._type_label.configure(image=type_icon, text=f" {type_text}")

    def hide(self) -> None:
        if self._window:
            self._window.withdraw()
            self._is_visible = False

    def close(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None
            self._is_visible = False

    def _set_text(self, textbox, text):
        if textbox is None:
            return
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

    def _get_text(self, textbox) -> str:
        if textbox is None:
            return ""
        return textbox.get("1.0", "end-1c")

    def _set_status(self, msg, kind: str = "success"):
        if self._status_label:
            self._status_label.configure(text=msg, text_color=status_color(kind))

    def _on_copy_click(self):
        text = self._get_text(self._result_text)
        if text and self._on_copy:
            self._on_copy(text)
            self._set_status(t("copied"), "success")
            if self._window:
                self._window.after(2000, lambda: self._set_status(""))

    def _on_copy_original_click(self):
        text = self._get_text(self._original_text)
        if text and self._on_copy:
            self._on_copy(text)
            self._set_status(t("original_copied"), "success")
            if self._window:
                self._window.after(2000, lambda: self._set_status(""))

    def _on_window_close(self):
        self.hide()
        if self._on_close:
            self._on_close()

    def set_on_close(self, callback):
        self._on_close = callback

    def set_on_copy(self, callback):
        self._on_copy = callback

    def is_visible(self):
        return self._is_visible

    def update_result(self, text):
        if self._window:
            self._set_text(self._result_text, text)
            # 结果更新时也确保窗口可见
            if not self._is_visible:
                self._window.deiconify()
                self._is_visible = True
            self._window.lift()


_floating_window = None

def get_floating_window(master=None):
    global _floating_window
    if _floating_window is None:
        _floating_window = FloatingWindow(master=master)
    elif master is not None:
        _floating_window.set_master(master)
    return _floating_window
