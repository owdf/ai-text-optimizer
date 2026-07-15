"""
设置窗口 - 统一主题、触控友好、分区清晰
"""

import threading
import customtkinter as ctk
from typing import Optional, Callable, List, Tuple
from config import get_config
from ai_service import AIService
from language import t, get_lang_manager
from icons import get_icon_manager
from ui.theme import (
    Colors, Space, Radius, Type, Size,
    font, apply_window_chrome, make_card, make_section_header, make_hint,
    make_field_row, make_label, style_entry, style_option_menu, style_textbox,
    primary_button, success_button, secondary_button, status_color,
)


# UI 显示名 ↔ 存储值
_FORMAT_OPENAI = "OpenAI"
_FORMAT_ANTHROPIC = "Anthropic"
_FORMAT_STORE = {
    _FORMAT_OPENAI: AIService.API_FORMAT_OPENAI,
    _FORMAT_ANTHROPIC: AIService.API_FORMAT_ANTHROPIC,
}
_FORMAT_DISPLAY = {
    AIService.API_FORMAT_OPENAI: _FORMAT_OPENAI,
    AIService.API_FORMAT_ANTHROPIC: _FORMAT_ANTHROPIC,
    "openai_compatible": _FORMAT_OPENAI,
    "claude": _FORMAT_ANTHROPIC,
}

_WIN_W, _WIN_H = 640, 720


class SettingsWindow:
    """设置窗口"""

    def __init__(self, master=None, dispatcher=None):
        self.config = get_config()
        self.lang_mgr = get_lang_manager()
        self._master = master
        self._dispatcher = dispatcher
        self._window: Optional[ctk.CTkToplevel] = None
        self._is_visible = False
        self._on_close: Optional[Callable] = None
        self._on_save: Optional[Callable] = None
        self._icons = get_icon_manager()
        self._entries = {}
        self._preset_var = None
        self._preset_menu = None
        self._preset_ids: List[str] = []
        self._preset_names: List[str] = []
        self._provider_var = None
        self._format_seg = None
        self._model_entry = None
        self._lang_var = None
        self._prompt_text = None
        self._status_label = None
        self._test_btn = None
        self._save_btn = None
        self._testing = False

    def _create_window(self) -> None:
        if self._window is not None:
            return

        if self._master is not None:
            self._window = ctk.CTkToplevel(self._master)
        else:
            self._window = ctk.CTkToplevel()
        apply_window_chrome(self._window, t("settings_title"))
        self._window.geometry(f"{_WIN_W}x{_WIN_H}")
        self._window.resizable(True, True)
        self._window.minsize(560, 600)

        self._center_window()
        self._create_widgets()
        self._load_config()
        self._window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _center_window(self) -> None:
        if self._window is None:
            return
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        x = (sw - _WIN_W) // 2
        y = max(20, (sh - _WIN_H) // 2)
        self._window.geometry(f"{_WIN_W}x{_WIN_H}+{x}+{y}")

    def _create_widgets(self) -> None:
        if self._window is None:
            return

        # 根布局：可滚动内容 + 固定底栏
        root = ctk.CTkFrame(self._window, fg_color=Colors.BG, corner_radius=0)
        root.pack(fill="both", expand=True)

        # 顶栏
        top = ctk.CTkFrame(root, fg_color=Colors.SURFACE, height=52, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ai_icon = self._icons.create_icon("settings", size=22, color=Colors.PRIMARY)
        ctk.CTkLabel(
            top,
            image=ai_icon,
            text=f"  {t('settings_title')}",
            font=font(Type.TITLE, "bold"),
            text_color=Colors.TEXT,
            compound="left",
        ).pack(side="left", padx=Size.WINDOW_PAD)

        scroll = ctk.CTkScrollableFrame(
            root,
            fg_color=Colors.BG,
            scrollbar_button_color=Colors.SURFACE_MUTED,
            scrollbar_button_hover_color=Colors.SURFACE_HOVER,
        )
        scroll.pack(fill="both", expand=True, padx=Size.WINDOW_PAD, pady=(Space.MD, Space.SM))

        self._build_ai_section(scroll)
        self._build_hotkey_section(scroll)
        self._build_lang_section(scroll)
        self._build_prompt_section(scroll)

        # 固定底栏（主操作始终可见）
        footer = ctk.CTkFrame(
            root,
            fg_color=Colors.SURFACE,
            height=64,
            corner_radius=0,
            border_width=1,
            border_color=Colors.BORDER,
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="both", expand=True, padx=Size.WINDOW_PAD, pady=Space.MD)

        save_icon = self._icons.create_icon("save", size=16, color=Colors.TEXT_INVERSE)
        self._save_btn = primary_button(
            btn_row, t("save"), self._save_config, icon=save_icon, width=120
        )
        self._save_btn.pack(side="left", padx=(0, Space.SM))

        reset_icon = self._icons.create_icon("reset", size=16, color=Colors.TEXT)
        secondary_button(
            btn_row, t("reset"), self._reset_config, icon=reset_icon, width=100
        ).pack(side="left")

        self._status_label = ctk.CTkLabel(
            btn_row,
            text="",
            font=font(Type.LABEL),
            text_color=Colors.TEXT_SECONDARY,
            anchor="e",
        )
        self._status_label.pack(side="right", fill="x", expand=True, padx=(Space.MD, 0))

    # ----- sections -----

    def _build_ai_section(self, parent) -> None:
        card = make_card(parent, fill="x", pady=(0, Space.MD))
        icon = self._icons.create_icon("ai", size=18, color=Colors.ACCENT_AI)
        make_section_header(card, t("settings_ai"), Colors.ACCENT_AI, icon)

        # 预设
        self._create_preset_selector(card)
        make_hint(card, t("settings_preset_hint"))

        # API Key
        self._create_label_entry(card, t("settings_api_key"), "api_key", show="*")
        # Base URL
        self._create_label_entry(card, t("settings_base_url"), "base_url")

        # 模型（自定义）
        model_row = make_field_row(card)
        make_label(model_row, t("settings_model")).pack(side="left")
        self._model_entry = ctk.CTkEntry(
            model_row,
            placeholder_text=t("settings_model_hint"),
        )
        style_entry(self._model_entry)
        self._model_entry.pack(side="left", fill="x", expand=True, padx=(Space.SM, 0))

        # API 格式：分段控件
        fmt_row = make_field_row(card)
        make_label(fmt_row, t("settings_format")).pack(side="left")
        self._provider_var = ctk.StringVar(value=_FORMAT_OPENAI)
        self._format_seg = ctk.CTkSegmentedButton(
            fmt_row,
            values=[_FORMAT_OPENAI, _FORMAT_ANTHROPIC],
            variable=self._provider_var,
            height=Size.ENTRY_H,
            font=font(Type.BODY),
            selected_color=Colors.PRIMARY,
            selected_hover_color=Colors.PRIMARY_HOVER,
            unselected_color=Colors.SURFACE_MUTED,
            unselected_hover_color=Colors.SURFACE_HOVER,
            text_color=Colors.TEXT_INVERSE,
            text_color_disabled=Colors.TEXT_SECONDARY,
            fg_color=Colors.SURFACE_MUTED,
            corner_radius=Radius.MD,
        )
        self._format_seg.pack(side="left", padx=(Space.SM, 0), fill="x", expand=True)
        self._format_seg.set(_FORMAT_OPENAI)

        # 测试连接
        test_row = ctk.CTkFrame(card, fg_color="transparent")
        test_row.pack(fill="x", padx=Size.SECTION_PAD_X, pady=(Space.SM, Size.SECTION_PAD_Y))

        test_icon = self._icons.create_icon("test", size=16, color=Colors.TEXT_INVERSE)
        self._test_btn = success_button(
            test_row, t("settings_test"), self._test_connection, icon=test_icon, width=150
        )
        self._test_btn.pack(side="left")

    def _build_hotkey_section(self, parent) -> None:
        card = make_card(parent, fill="x", pady=(0, Space.MD))
        icon = self._icons.create_icon("settings", size=18, color=Colors.ACCENT_HOTKEY)
        make_section_header(card, t("settings_hotkey"), Colors.ACCENT_HOTKEY, icon)
        self._create_label_entry(card, t("hotkey_key"), "hotkey")
        make_hint(card, "Format: ctrl+shift+q · alt+a · f2")
        # bottom padding
        ctk.CTkFrame(card, fg_color="transparent", height=Space.SM).pack()

    def _build_lang_section(self, parent) -> None:
        card = make_card(parent, fill="x", pady=(0, Space.MD))
        make_section_header(card, t("settings_language"), Colors.ACCENT_LANG)

        row = make_field_row(card)
        make_label(row, t("settings_language")).pack(side="left")

        self._lang_var = ctk.StringVar(value=self.lang_mgr.get_lang())
        langs = self.lang_mgr.get_available_langs()
        lang_names = [self.lang_mgr.get_lang_name(l) for l in langs]
        menu = ctk.CTkOptionMenu(
            row,
            variable=self._lang_var,
            values=lang_names,
            command=self._on_lang_change,
        )
        style_option_menu(menu, width=220)
        menu.pack(side="left", padx=(Space.SM, 0))
        ctk.CTkFrame(card, fg_color="transparent", height=Size.SECTION_PAD_Y).pack()

    def _build_prompt_section(self, parent) -> None:
        card = make_card(parent, fill="x", pady=(0, Space.MD))
        icon = self._icons.create_icon("text", size=18, color=Colors.ACCENT_PROMPT)
        make_section_header(card, t("settings_prompt"), Colors.ACCENT_PROMPT, icon)
        make_hint(card, t("settings_prompt_desc"))

        self._prompt_text = ctk.CTkTextbox(card, height=96, wrap="word")
        style_textbox(self._prompt_text)
        self._prompt_text.pack(
            fill="x",
            padx=Size.SECTION_PAD_X,
            pady=(0, Size.SECTION_PAD_Y),
        )

    def _build_preset_lists(self) -> Tuple[List[str], List[str]]:
        services = AIService.get_preset_services()
        ids = ["custom"]
        names = [t("settings_custom")]
        for pid, meta in services.items():
            if pid == "custom":
                continue
            ids.append(pid)
            names.append(meta["name"])
        return ids, names

    def _create_preset_selector(self, parent):
        row = make_field_row(parent)
        make_label(row, t("settings_preset")).pack(side="left")

        self._preset_ids, self._preset_names = self._build_preset_lists()
        self._preset_var = ctk.StringVar(value=self._preset_names[0])
        self._preset_menu = ctk.CTkOptionMenu(
            row,
            variable=self._preset_var,
            values=self._preset_names,
            command=self._on_preset_change,
        )
        style_option_menu(self._preset_menu, width=280)
        self._preset_menu.pack(side="left", padx=(Space.SM, 0), fill="x", expand=True)

    def _create_label_entry(self, parent, label_text: str, key: str, show: str = None):
        row = make_field_row(parent)
        make_label(row, label_text).pack(side="left")
        entry = ctk.CTkEntry(row, show=show)
        style_entry(entry)
        entry.pack(side="left", fill="x", expand=True, padx=(Space.SM, 0))
        self._entries[key] = entry

    def _set_model_entry(self, model: str) -> None:
        if self._model_entry is None:
            return
        self._model_entry.delete(0, "end")
        if model:
            self._model_entry.insert(0, model)

    def _set_provider_display(self, provider: str) -> None:
        normalized = AIService.normalize_provider(provider)
        display = _FORMAT_DISPLAY.get(normalized, _FORMAT_OPENAI)
        if self._provider_var is not None:
            self._provider_var.set(display)
        if self._format_seg is not None:
            try:
                self._format_seg.set(display)
            except Exception:
                pass

    def _get_provider_store(self) -> str:
        display = self._provider_var.get() if self._provider_var else _FORMAT_OPENAI
        return _FORMAT_STORE.get(display, AIService.API_FORMAT_OPENAI)

    def _apply_preset(self, preset_id: str) -> None:
        if preset_id == "custom":
            return
        preset = AIService.get_preset_service(preset_id)
        if not preset:
            return

        base_url = preset.get("base_url") or ""
        if "base_url" in self._entries:
            self._entries["base_url"].delete(0, "end")
            self._entries["base_url"].insert(0, base_url)

        model = preset.get("model") or ""
        if not model and preset.get("models"):
            model = preset["models"][0]
        self._set_model_entry(model)

        if "provider" in preset:
            self._set_provider_display(preset["provider"])

    def _on_preset_change(self, choice: str):
        try:
            index = self._preset_names.index(choice)
            preset_id = self._preset_ids[index]
        except ValueError:
            return
        self._apply_preset(preset_id)

    def _match_preset_from_config(self) -> str:
        base_url = (self.config.get("ai_service.base_url", "") or "").rstrip("/")
        if not base_url:
            return "custom"
        for pid, meta in AIService.get_preset_services().items():
            if pid == "custom":
                continue
            preset_url = (meta.get("base_url") or "").rstrip("/")
            if preset_url and preset_url == base_url:
                return pid
        return "custom"

    def _set_preset_menu(self, preset_id: str) -> None:
        if not self._preset_ids or self._preset_var is None:
            return
        try:
            idx = self._preset_ids.index(preset_id)
            self._preset_var.set(self._preset_names[idx])
        except ValueError:
            self._preset_var.set(self._preset_names[0])

    def _on_lang_change(self, choice: str):
        langs = self.lang_mgr.get_available_langs()
        lang_names = [self.lang_mgr.get_lang_name(l) for l in langs]
        try:
            index = lang_names.index(choice)
            self.lang_mgr.set_lang(langs[index])
        except (ValueError, IndexError):
            pass

    def _load_config(self):
        if "api_key" in self._entries:
            self._entries["api_key"].delete(0, "end")
            self._entries["api_key"].insert(0, self.config.get("ai_service.api_key", ""))
        if "base_url" in self._entries:
            self._entries["base_url"].delete(0, "end")
            self._entries["base_url"].insert(0, self.config.get("ai_service.base_url", ""))

        self._set_model_entry(self.config.get("ai_service.model", "gpt-4o") or "")
        self._set_provider_display(
            self.config.get("ai_service.provider", AIService.API_FORMAT_OPENAI)
        )
        self._set_preset_menu(self._match_preset_from_config())

        if "hotkey" in self._entries:
            self._entries["hotkey"].delete(0, "end")
            self._entries["hotkey"].insert(0, self.config.get("hotkey.trigger", "ctrl+shift+q"))

        if self._prompt_text is not None:
            self._prompt_text.delete("1.0", "end")
            extra = self.config.get_prompt("extra") or self.config.get("prompts.extra", "") or ""
            if extra:
                self._prompt_text.insert("1.0", extra)

        if self._lang_var is not None:
            self._lang_var.set(self.lang_mgr.get_lang_name(self.lang_mgr.get_lang()))

    def _save_config(self):
        if "api_key" in self._entries:
            self.config.set("ai_service.api_key", self._entries["api_key"].get())
        if "base_url" in self._entries:
            self.config.set("ai_service.base_url", self._entries["base_url"].get().strip())

        model = self._model_entry.get().strip() if self._model_entry else ""
        self.config.set("ai_service.model", model)
        self.config.set("ai_service.provider", self._get_provider_store())

        if "hotkey" in self._entries:
            self.config.set("hotkey.trigger", self._entries["hotkey"].get())

        if self._prompt_text is not None:
            extra = self._prompt_text.get("1.0", "end").strip()
            self.config.set_prompt("extra", extra)

        langs = self.lang_mgr.get_available_langs()
        lang_names = [self.lang_mgr.get_lang_name(l) for l in langs]
        try:
            index = lang_names.index(self._lang_var.get())
            self.config.set("general.language", langs[index])
        except (ValueError, IndexError, AttributeError):
            pass

        saved = self.config.save()
        self._set_status(
            t("settings_saved") if saved else t("settings_save_failed"),
            "success" if saved else "error",
        )

        if self._on_save:
            self._on_save()

    def _reset_config(self):
        self.config.reset_to_default()
        self._load_config()
        self._set_status(t("reset"), "info")

    def _test_connection(self):
        if self._testing:
            return
        self._save_config()

        from ai_service import get_ai_service
        ai_service = get_ai_service()

        self._testing = True
        self._set_status(t("settings_testing"), "info")
        if self._test_btn is not None:
            self._test_btn.configure(state="disabled", text=f" {t('settings_testing')}")

        def test():
            result = ai_service.test_connection()

            def done():
                self._testing = False
                if self._window is None:
                    return
                if self._test_btn is not None:
                    self._test_btn.configure(state="normal", text=f" {t('settings_test')}")
                if result["success"]:
                    self._set_status(t("settings_connected"), "success")
                else:
                    msg = result.get("message", "")[:40]
                    self._set_status(f"{t('settings_connect_failed')}: {msg}", "error")

            if self._dispatcher is not None:
                self._dispatcher(done)
            elif self._window:
                self._window.after(0, done)

        threading.Thread(target=test, daemon=True).start()

    def _set_status(self, message: str, kind: str = "neutral"):
        if self._status_label:
            self._status_label.configure(text=message, text_color=status_color(kind))

    def _on_window_close(self):
        self.close()
        if self._on_close:
            self._on_close()

    def show(self):
        if self._window is None:
            self._create_window()
        self._window.deiconify()
        self._window.lift()
        self._window.focus_force()
        self._is_visible = True

    def close(self):
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
