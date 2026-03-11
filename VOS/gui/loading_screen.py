"""
loading_screen.py — Modern AI-style splash/loading screen for VOS startup.

Shows the IT mascot logo with floating animation, cycles loading messages,
and animates ellipsis dots. On completion, destroys the splash and launches VOSApp.
"""

import math
import os
import sys

import customtkinter as ctk
import tkinter as tk
from PIL import Image

from gui.theme import colors, get_font


# Messages to cycle through, base text without dots
LOADING_MESSAGES = [
    "Initializing",
    "Loading modules",
    "Processing data",
]

# Duration of splash (ms) before transitioning to main app
SPLASH_DURATION_MS = 2800

# Animation intervals (ms)
FLOAT_INTERVAL_MS = 50
DOTS_INTERVAL_MS = 300


def get_base_path():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LoadingScreen(ctk.CTk):
    """Modern loading splash with floating logo and animated loading text."""

    def __init__(self, on_complete):
        super().__init__()
        self._on_complete = on_complete
        self._float_offset = 0.0
        self._msg_index = 0
        self._dots_count = 0
        self._logo_frame = None
        self._logo_label = None
        self._text_label = None
        self._after_ids = []
        self._finished = False

        self.title("VOS")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(fg_color=colors["BG"])

        # Remove window decorations for a cleaner look (optional; keep for now so user can see it)
        self.overrideredirect(False)
        self.attributes("-topmost", True)

        # Ensure dark mode for splash
        ctk.set_appearance_mode("dark")

        # Load fonts if available
        font_dir = os.path.join(get_base_path(), "assets", "fonts")
        if os.path.exists(font_dir):
            for f in os.listdir(font_dir):
                if f.endswith(".ttf"):
                    try:
                        ctk.FontManager.load_font(os.path.join(font_dir, f))
                    except Exception:
                        pass

        self._build_ui()
        self._center_on_screen()
        self._start_animations()
        aid = self.after(SPLASH_DURATION_MS, self._finish)
        if aid:
            self._after_ids.append(aid)

    def _build_ui(self):
        """Build the splash UI: gradient background, logo, loading text."""
        # Gradient background canvas
        self._canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg=colors["BG"],
        )
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._draw_gradient()

        # Logo container (place for animated positioning)
        self._logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._logo_frame.place(relx=0.5, rely=0.38, anchor="center")

        try:
            icon_path = os.path.join(get_base_path(), "assets", "IT.ico")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                self._logo_image = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(200, 200)
                )
                self._logo_label = ctk.CTkLabel(
                    self._logo_frame, text="", image=self._logo_image, fg_color="transparent"
                )
                self._logo_label.pack()
            else:
                self._logo_label = ctk.CTkLabel(
                    self._logo_frame, text="VOS", font=get_font("Outfit", 48), text_color=colors["ACCENT"]
                )
                self._logo_label.pack()
        except Exception:
            self._logo_label = ctk.CTkLabel(
                self._logo_frame, text="VOS", font=get_font("Outfit", 48), text_color=colors["ACCENT"]
            )
            self._logo_label.pack()

        # Loading text (below logo)
        self._text_label = ctk.CTkLabel(
            self,
            text=LOADING_MESSAGES[0] + ".",
            font=get_font("Outfit", 16),
            text_color=colors["DIM_TEXT"],
            fg_color="transparent",
        )
        self._text_label.place(relx=0.5, rely=0.72, anchor="center")

    def _draw_gradient(self):
        """Draw a subtle vertical gradient on the canvas."""
        w = 440
        h = 420
        self._canvas.config(width=w, height=h)

        c1 = colors["BG"]
        c2 = colors["BG_GRADIENT_END"]
        try:
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        except Exception:
            r1, g1, b1 = 11, 15, 20
            r2, g2, b2 = 13, 19, 32

        for i in range(h):
            t = i / max(h - 1, 1)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b2 + (b1 - b2) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self._canvas.create_line(0, i, w, i, fill=color)

    def _center_on_screen(self):
        """Center the splash window on screen."""
        self.update_idletasks()
        w, h = 440, 420
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _start_animations(self):
        """Start the float and text animations."""
        aid1 = self.after(0, self._tick_float)
        aid2 = self.after(0, self._tick_loading_text)
        if aid1:
            self._after_ids.append(aid1)
        if aid2:
            self._after_ids.append(aid2)

    def _tick_float(self):
        """Update floating/bouncing logo position."""
        if self._finished:
            return
        if self._logo_frame and self.winfo_exists():
            try:
                self._float_offset += 0.12
                dy = 10 * math.sin(self._float_offset)
                rely = 0.38 + (dy / 420)
                self._logo_frame.place(relx=0.5, rely=rely, anchor="center")
            except Exception:
                pass
            aid = self.after(FLOAT_INTERVAL_MS, self._tick_float)
            if aid:
                self._after_ids.append(aid)

    def _tick_loading_text(self):
        """Cycle messages and animate dots: 'Initializing.' -> '..' -> '...' -> next message."""
        if self._finished:
            return
        if self._text_label and self.winfo_exists():
            self._dots_count += 1
            # Every 3 dot cycles, advance to next message
            if self._dots_count % 3 == 0:
                self._msg_index = (self._msg_index + 1) % len(LOADING_MESSAGES)
            base = LOADING_MESSAGES[self._msg_index]
            dots = "." * ((self._dots_count % 3) + 1)
            self._text_label.configure(text=base + dots)
            aid = self.after(DOTS_INTERVAL_MS, self._tick_loading_text)
            if aid:
                self._after_ids.append(aid)

    def _finish(self):
        """Close the splash and invoke the completion callback to launch the main app."""
        if self._finished:
            return
        self._finished = True
        try:
            for aid in self._after_ids:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
            self._after_ids.clear()
            callback = self._on_complete
            self.destroy()
            if callback:
                callback()
        except Exception:
            pass
