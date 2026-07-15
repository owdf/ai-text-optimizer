"""
统一 UI 设计令牌 — AI Text Optimizer
深色生产力工具风格：高对比、清晰分区、触控友好
"""

from typing import Optional, Tuple
import customtkinter as ctk


# ---------------------------------------------------------------------------
# Color system (dark productivity + Catppuccin accents)
# ---------------------------------------------------------------------------
class Colors:
    # Surfaces
    BG = "#0f1117"              # window / deepest bg
    SURFACE = "#181825"         # cards
    SURFACE_ELEVATED = "#1e1e2e"
    SURFACE_MUTED = "#313244"
    SURFACE_HOVER = "#45475a"

    # Borders / dividers
    BORDER = "#313244"
    BORDER_FOCUS = "#89b4fa"

    # Text
    TEXT = "#f1f5f9"            # primary body (high contrast)
    TEXT_SECONDARY = "#a6adc8"  # muted labels / hints
    TEXT_INVERSE = "#0f1117"

    # Accents by role
    PRIMARY = "#89b4fa"         # brand / links
    PRIMARY_HOVER = "#74c7ec"
    PRIMARY_SOFT = "#1e3a5f"

    ACCENT_AI = "#cba6f7"       # AI sections
    ACCENT_HOTKEY = "#89b4fa"
    ACCENT_LANG = "#f9e2af"
    ACCENT_PROMPT = "#a6e3a1"

    # Semantic
    SUCCESS = "#22c55e"
    SUCCESS_HOVER = "#16a34a"
    SUCCESS_SOFT = "#14532d"
    DANGER = "#f38ba8"
    DANGER_HOVER = "#eba0ac"
    WARNING = "#f9e2af"
    INFO = "#89b4fa"

    # Controls
    INPUT_BG = "#11111b"
    INPUT_BORDER = "#45475a"
    BTN_SECONDARY = "#45475a"
    BTN_SECONDARY_HOVER = "#585b70"
    BTN_GHOST_HOVER = "#313244"


# ---------------------------------------------------------------------------
# Spacing / radius / type scale
# ---------------------------------------------------------------------------
class Space:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24


class Radius:
    SM = 6
    MD = 10
    LG = 14
    XL = 16


class Type:
    TITLE = 18
    SECTION = 15
    BODY = 13
    LABEL = 12
    HINT = 11
    CAPTION = 10


class Size:
    """Touch-friendly targets (min ~40px for primary actions)."""
    BTN_H = 40
    BTN_H_SM = 36
    ENTRY_H = 38
    ICON_BTN = 40
    LABEL_W = 100
    SECTION_PAD_X = 16
    SECTION_PAD_Y = 14
    WINDOW_PAD = 16


def font(size: int = Type.BODY, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)


def mono_font(size: int = Type.BODY) -> ctk.CTkFont:
    return ctk.CTkFont(size=size, family="Consolas")


def apply_window_chrome(window: ctk.CTkToplevel, title: str) -> None:
    """Common toplevel chrome."""
    window.title(title)
    window.configure(fg_color=Colors.BG)
    try:
        window.attributes("-topmost", True)
    except Exception:
        pass


def make_card(parent, **pack_kwargs) -> ctk.CTkFrame:
    """Elevated content card."""
    card = ctk.CTkFrame(
        parent,
        fg_color=Colors.SURFACE,
        corner_radius=Radius.LG,
        border_width=1,
        border_color=Colors.BORDER,
    )
    if pack_kwargs:
        card.pack(**pack_kwargs)
    return card


def make_section_header(
    parent,
    text: str,
    accent: str = Colors.PRIMARY,
    icon_image=None,
) -> ctk.CTkFrame:
    """Section title row with accent bar + optional icon."""
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=Size.SECTION_PAD_X, pady=(Size.SECTION_PAD_Y, Space.SM))

    # Accent bar
    bar = ctk.CTkFrame(header, width=3, height=18, fg_color=accent, corner_radius=2)
    bar.pack(side="left", padx=(0, Space.SM))
    bar.pack_propagate(False)

    if icon_image is not None:
        ctk.CTkLabel(header, image=icon_image, text="").pack(side="left", padx=(0, Space.SM))

    ctk.CTkLabel(
        header,
        text=text,
        font=font(Type.SECTION, "bold"),
        text_color=accent,
        anchor="w",
    ).pack(side="left")
    return header


def make_hint(parent, text: str, wraplength: int = 520) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(
        parent,
        text=text,
        font=font(Type.HINT),
        text_color=Colors.TEXT_SECONDARY,
        wraplength=wraplength,
        anchor="w",
        justify="left",
    )
    lbl.pack(fill="x", padx=Size.SECTION_PAD_X, pady=(0, Space.SM))
    return lbl


def make_field_row(parent) -> ctk.CTkFrame:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=Size.SECTION_PAD_X, pady=Space.SM)
    return row


def make_label(parent, text: str, width: int = Size.LABEL_W) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        width=width,
        anchor="w",
        font=font(Type.LABEL),
        text_color=Colors.TEXT_SECONDARY,
    )


def style_entry(entry: ctk.CTkEntry, height: int = Size.ENTRY_H) -> None:
    entry.configure(
        height=height,
        corner_radius=Radius.MD,
        border_width=1,
        border_color=Colors.INPUT_BORDER,
        fg_color=Colors.INPUT_BG,
        text_color=Colors.TEXT,
        placeholder_text_color=Colors.TEXT_SECONDARY,
        font=font(Type.BODY),
    )


def style_option_menu(menu: ctk.CTkOptionMenu, width: int = 220) -> None:
    menu.configure(
        width=width,
        height=Size.ENTRY_H,
        corner_radius=Radius.MD,
        fg_color=Colors.SURFACE_MUTED,
        button_color=Colors.SURFACE_HOVER,
        button_hover_color=Colors.BTN_SECONDARY_HOVER,
        text_color=Colors.TEXT,
        font=font(Type.BODY),
        dropdown_fg_color=Colors.SURFACE_ELEVATED,
        dropdown_hover_color=Colors.SURFACE_MUTED,
        dropdown_text_color=Colors.TEXT,
    )


def primary_button(parent, text: str, command, icon=None, width: int = 120, **kwargs) -> ctk.CTkButton:
    btn = ctk.CTkButton(
        parent,
        text=text if icon is None else f" {text}",
        image=icon,
        compound="left" if icon is not None else "left",
        command=command,
        height=Size.BTN_H,
        width=width,
        corner_radius=Radius.MD,
        fg_color=Colors.PRIMARY,
        hover_color=Colors.PRIMARY_HOVER,
        text_color=Colors.TEXT_INVERSE,
        font=font(Type.BODY, "bold"),
        **kwargs,
    )
    return btn


def success_button(parent, text: str, command, icon=None, width: int = 140, **kwargs) -> ctk.CTkButton:
    btn = ctk.CTkButton(
        parent,
        text=text if icon is None else f" {text}",
        image=icon,
        compound="left" if icon is not None else "left",
        command=command,
        height=Size.BTN_H,
        width=width,
        corner_radius=Radius.MD,
        fg_color=Colors.SUCCESS,
        hover_color=Colors.SUCCESS_HOVER,
        text_color=Colors.TEXT_INVERSE,
        font=font(Type.BODY, "bold"),
        **kwargs,
    )
    return btn


def secondary_button(parent, text: str, command, icon=None, width: int = 100, **kwargs) -> ctk.CTkButton:
    btn = ctk.CTkButton(
        parent,
        text=text if icon is None else f" {text}",
        image=icon,
        compound="left" if icon is not None else "left",
        command=command,
        height=Size.BTN_H,
        width=width,
        corner_radius=Radius.MD,
        fg_color=Colors.BTN_SECONDARY,
        hover_color=Colors.BTN_SECONDARY_HOVER,
        text_color=Colors.TEXT,
        font=font(Type.BODY),
        **kwargs,
    )
    return btn


def ghost_icon_button(parent, icon, command, size: int = Size.ICON_BTN) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        image=icon,
        text="",
        width=size,
        height=size,
        fg_color="transparent",
        hover_color=Colors.BTN_GHOST_HOVER,
        command=command,
        corner_radius=Radius.SM,
    )


def style_textbox(tb: ctk.CTkTextbox) -> None:
    tb.configure(
        corner_radius=Radius.MD,
        border_width=1,
        border_color=Colors.INPUT_BORDER,
        fg_color=Colors.INPUT_BG,
        text_color=Colors.TEXT,
        font=font(Type.BODY),
        scrollbar_button_color=Colors.SURFACE_MUTED,
        scrollbar_button_hover_color=Colors.SURFACE_HOVER,
    )


def status_color(kind: str) -> str:
    return {
        "success": Colors.SUCCESS,
        "error": Colors.DANGER,
        "warning": Colors.WARNING,
        "info": Colors.TEXT_SECONDARY,
        "neutral": Colors.TEXT_SECONDARY,
    }.get(kind, Colors.TEXT_SECONDARY)
