"""
theme.py — Color palettes, font helper, and theme toggle for VOS GUI.

Supports DARK (default) and LIGHT themes.
Theme preference is persisted in config.json.
"""

import customtkinter as ctk

# ==================== DARK PALETTE (Deep Space/Pro Max) ====================
DARK = {
    # Surface Hierarchy (High depth, very dark base)
    "BG":              "#090D14",  # Pitch blue
    "BG_GRADIENT_END": "#0D1320",  
    "CARD_BG":         "#111825",  # Elevated surface with slight blue tint
    "CARD_HOVER":      "#151E2E",  
    
    # Borders & Glow (Returning thickness and energy)
    "BORDER":          "#1C273D",  
    "BORDER_GLOW":     "#3D63AD",  # Electric glow
    
    # Core Branding
    "ACCENT":          "#4F7DFF",  # Electric Blue (High Contrast)
    "ACCENT_HOVER":    "#3B6CFF",  
    
    # Type
    "TEXT":            "#F8FAFC",  # Pure crisp white
    "DIM_TEXT":        "#94A3B8",  # Slate
    
    # Semantic (Neon/Slightly desaturated for dark mode legibility)
    "SUCCESS":         "#4F7DFF",  # Done/Positive actions
    "GOOD":            "#10B981",  # Vitals OK - Neon Green
    "WARNING":         "#F59E0B",  
    "ERROR":           "#EF4444",  
}

# ==================== LIGHT PALETTE ====================
LIGHT = {
    "BG":              "#F8FAFC",
    "BG_GRADIENT_END": "#F1F5F9",
    "CARD_BG":         "#FFFFFF",
    "CARD_HOVER":      "#F1F5F9",
    "BORDER":          "#E2E8F0",
    "BORDER_GLOW":     "#CBD5E1",
    "ACCENT":          "#2563EB",
    "ACCENT_HOVER":    "#1D4ED8",
    "TEXT":            "#0F172A",
    "DIM_TEXT":        "#64748B",
    "SUCCESS":         "#2563EB",
    "GOOD":            "#10B981",
    "WARNING":         "#D97706",
    "ERROR":           "#DC2626",
}

# ==================== DESIGN TOKENS ====================
RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "full": 999,
}

SPACE = {
    "xs": 4,   # space-1
    "sm": 8,   # space-2
    "md": 12,  # space-3
    "lg": 16,  # space-4
    "xl": 24,  # space-6
    "2xl": 32, # space-8
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
