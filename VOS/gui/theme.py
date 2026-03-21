"""
theme.py — Color palettes, font helper, and theme toggle for VOS GUI.

Supports DARK (default) and LIGHT themes.
Theme preference is persisted in config.json.
"""

import customtkinter as ctk

# ==================== DARK PALETTE (Linear-style) ====================
# Clean, low-saturation neutrals with a refined blue accent.
DARK = {
    "BG":              "#0B0F14",
    "BG_GRADIENT_END": "#0D1320",
    "CARD_BG":         "#0F1623",
    "CARD_HOVER":      "#121C2D",
    # Stronger separation + visible glow ring on dark BG
    "BORDER":          "#182235",
    "BORDER_GLOW":     "#3E5FA8",
    "ACCENT":          "#4F7DFF",
    "ACCENT_HOVER":    "#3B6CFF",
    "TEXT":            "#E7ECF3",
    "DIM_TEXT":        "#A3AEC2",
    "SUCCESS":         "#4F7DFF",  # general success/DONE labels (blue)
    "GOOD":            "#22D3EE",  # vitals OK (cyan)
    "WARNING":         "#F2B24C",
    "ERROR":           "#F26D6D",
}

# ==================== LIGHT PALETTE (Linear-style) ====================
LIGHT = {
    "BG":              "#F7F8FA",
    "BG_GRADIENT_END": "#EEF1F5",
    "CARD_BG":         "#FFFFFF",
    "CARD_HOVER":      "#F3F5F9",
    "BORDER":          "#E1E6EF",
    "BORDER_GLOW":     "#A6B1C5",
    "ACCENT":          "#2563EB",
    "ACCENT_HOVER":    "#1D4ED8",
    "TEXT":            "#0B1220",
    "DIM_TEXT":        "#556277",
    "SUCCESS":         "#2563EB",  # general success/DONE labels (blue)
    "GOOD":            "#06B6D4",  # vitals OK (cyan)
    "WARNING":         "#D97706",
    "ERROR":           "#DC2626",
}

# ── Active palette (starts as dark) ─────────────────────────────────────
_current_theme = "dark"
colors = dict(DARK)  # mutable copy


def get_theme() -> str:
    """Return the current theme name: 'dark' or 'light'."""
    return _current_theme


def set_theme(theme: str):
    """Switch palette to 'dark' or 'light'. Does NOT redraw widgets."""
    global _current_theme
    _current_theme = theme.lower()
    source = DARK if _current_theme == "dark" else LIGHT
    colors.update(source)
    ctk.set_appearance_mode("dark" if _current_theme == "dark" else "light")


def toggle_theme() -> str:
    """Toggle between dark and light. Returns the new theme name."""
    new = "light" if _current_theme == "dark" else "dark"
    set_theme(new)
    return new


def get_font(family: str, size: int, weight: str = "normal") -> ctk.CTkFont:
    """Create a CTkFont with the given parameters."""
    return ctk.CTkFont(family=family, size=size, weight=weight)
