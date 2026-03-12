"""
cards.py — All diagnostic card widgets for the VOS GUI.

Extracted from main.py for maintainability.
Each card is a BaseCard subclass that displays one diagnostic result.
"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
from gui.theme import colors, get_font
from thresholds import MIC_LEVEL_MIN, MIC_LEVEL_WARN


class BaseCard(ctk.CTkFrame):
    """Base card with consistent padding, header, status badge, hover, and checking pulse."""

    def __init__(self, master, title, icon, **kwargs):
        # "Glow" card:
        # - outer frame is transparent and holds the glow bitmap
        # - inner frame is the actual glass surface
        super().__init__(master, fg_color="transparent", corner_radius=12, **kwargs)
        self._pulse_job = None
        self._is_checking = False
        self._hovered = False
        self._pulse_on = False
        self._glow_after = None
        self._glow_size = (0, 0)
        self._glow_img_subtle = None
        self._glow_img_strong = None
        self.inner = ctk.CTkFrame(
            self,
            fg_color=colors["CARD_BG"],
            corner_radius=10,
            border_width=2,
            border_color=colors["BORDER"],
        )
        self.inner.pack(fill="both", expand=True, padx=0, pady=0)

        # Hover: subtle border glow (bound after children exist)
        # Header
        self.header_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(6, 2))

        title_fr = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_fr.pack(side="left")

        icon_lbl = ctk.CTkLabel(
            title_fr,
            text=icon,
            font=get_font("Outfit", 13),
            text_color=colors["ACCENT"],
        )
        icon_lbl.pack(side="left", padx=(0, 6))

        self.title_label = ctk.CTkLabel(
            title_fr,
            text=title,
            font=get_font("Outfit", 12, "bold"),
            text_color=colors["TEXT"],
        )
        self.title_label.pack(side="left")

        # Status badge (compact)
        self.status_badge = ctk.CTkFrame(
            self.header_frame, fg_color=colors["BORDER"], corner_radius=3
        )
        self.status_badge.pack(side="right")
        self.status_label = ctk.CTkLabel(
            self.status_badge,
            text="NOT CHECKED",
            font=get_font("Outfit", 9, "bold"),
            text_color=colors["DIM_TEXT"],
            padx=5,
            pady=1,
        )
        self.status_label.pack()

        # Separator
        sep = ctk.CTkFrame(self.inner, fg_color=colors["BORDER"], height=1)
        sep.pack(fill="x", padx=10)

        # Horizontal container for content + feedback
        self.main_container = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=4)

        # Left side: Actual Card Content
        self.content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

        # Right side: Feedback Frame (Hidden initially)
        self.feedback_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=colors["BG"],
            corner_radius=8,
            border_width=1,
            border_color=colors["BORDER"],
        )

        # Hover: bind on self + propagate to children so hover works over full card
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
        self.inner.bind("<Enter>", self._on_hover_enter)
        self.inner.bind("<Leave>", self._on_hover_leave)
        self._bind_hover_to_children(self.inner)

        # Default visual state
        self._apply_visual_state()

    def _bind_hover_to_children(self, widget):
        for w in widget.winfo_children():
            # Skip binding to widgets that should handle their own events if any
            w.bind("<Enter>", self._on_hover_enter)
            w.bind("<Leave>", self._on_hover_leave)
            self._bind_hover_to_children(w)

    def _apply_visual_state(self):
        """Update the internal card border color based on hover/checking state."""
        surface = colors["CARD_HOVER"] if self._hovered else colors["CARD_BG"]
        
        # Accent pulse/hover
        if self._hovered or (self._is_checking and self._pulse_on):
            border = colors["ACCENT"]
        else:
            border = colors["BORDER"]
            
        try:
            self.inner.configure(fg_color=surface, border_color=border)
        except Exception:
            pass

    def _on_hover_enter(self, event=None):
        if self._is_checking:
            return
        self._hovered = True
        self._apply_visual_state()

    def _on_hover_leave(self, event=None):
        def _check():
            if self._is_checking:
                return
            try:
                x, y = self.winfo_pointerxy()
                containing = self.winfo_containing(x, y)
                current = containing
                while current:
                    if current == self:
                        return
                    try:
                        current = current.master
                    except Exception:
                        break
            except Exception:
                pass
            self._hovered = False
            self._apply_visual_state()
        self.after(50, _check)

    def _start_pulse(self):
        if self._pulse_job or self._is_checking:
            return
        self._is_checking = True
        self._pulse_on = True
        self._pulse_tick()

    def _pulse_tick(self):
        if not self._is_checking:
            return
        # Pulse between subtle/strong glow (without changing hover state)
        self._pulse_on = not self._pulse_on
        self._apply_visual_state()
        self._pulse_job = self.after(450, self._pulse_tick)

    def _stop_pulse(self):
        self._is_checking = False
        self._pulse_on = False
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        self._apply_visual_state()

    def update_status(self, text, color=None):
        if color is None:
            color = colors["DIM_TEXT"]
        self.status_label.configure(text=text.upper(), text_color=color)
        # Shimmer/pulse on border while checking
        if "checking" in text.lower() or "..." in text:
            self._start_pulse()
        else:
            self._stop_pulse()

    def set_feedback(self, warnings: list):
        """
        Receives a list of warning dicts: [{'title': '...', 'desc': '...', 'steps': [...]}]
        If empty, hides the feedback box. Otherwise, builds and shows it.
        """
        # Clear existing feedback widgets
        for widget in self.feedback_frame.winfo_children():
            widget.destroy()

        if not warnings:
            self.feedback_frame.pack_forget()
            return

        # Show the frame
        self.feedback_frame.pack(side="right", fill="y", padx=(10, 0), expand=False)

        # Simple scrollable container for the warnings
        scroll = ctk.CTkScrollableFrame(
            self.feedback_frame,
            fg_color="transparent",
            width=200,
            corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=3, pady=3)

        for w in warnings:
            header = ctk.CTkFrame(scroll, fg_color="transparent")
            header.pack(fill="x", padx=6, pady=(4, 2))
            
            ctk.CTkLabel(
                header,
                text="⚠",
                font=get_font("Outfit", 12),
                text_color=colors["WARNING"],
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                header,
                text=w["title"],
                font=get_font("Outfit", 11, "bold"),
                text_color=colors["TEXT"],
                wraplength=160,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                scroll,
                text=w["desc"],
                font=get_font("Outfit", 10),
                text_color=colors["DIM_TEXT"],
                wraplength=180,
                justify="left",
            ).pack(fill="x", padx=8, pady=(0, 4))

            if w.get("steps"):
                steps_fr = ctk.CTkFrame(scroll, fg_color="transparent")
                steps_fr.pack(fill="x", padx=8, pady=(0, 6))
                for i, step in enumerate(w["steps"], 1):
                    ctk.CTkLabel(
                        steps_fr,
                        text=f"{i}. {step}",
                        font=get_font("Outfit", 10),
                        text_color=colors["DIM_TEXT"],
                        wraplength=170,
                        justify="left",
                    ).pack(anchor="w", pady=0)

            if w.get("action"):
                action_dict = w["action"]
                btn = ctk.CTkButton(
                    scroll,
                    text=action_dict["label"],
                    font=get_font("Outfit", 11, "bold"),
                    fg_color=colors["ACCENT"],
                    text_color="#FFFFFF",
                    hover_color=colors["ACCENT_HOVER"],
                    corner_radius=5,
                    height=26,
                    width=120,
                    command=action_dict["command"]
                )
                btn.pack(pady=(4, 6), padx=8, anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
class SpecsCard(BaseCard):
    def __init__(self, master):
        super().__init__(master, "Your Computer", "💻")

        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        self.cpu_val = ctk.CTkLabel(
            self.content,
            text="Processor : —",
            font=get_font("Outfit", 11, "bold"),
            text_color=colors["ACCENT"],
            wraplength=220,
            justify="left",
            anchor="w",
        )
        self.cpu_val.grid(row=0, column=0, sticky="w", pady=(4, 2))

        self.mem_val = ctk.CTkLabel(
            self.content,
            text="RAM : —",
            font=get_font("Outfit", 11, "bold"),
            text_color=colors["ACCENT"],
        )
        self.mem_val.grid(row=0, column=1, sticky="w", pady=(4, 2))


# ─────────────────────────────────────────────────────────────────────────────
class ChromeCard(BaseCard):
    def __init__(self, master):
        super().__init__(master, "Chrome Browser", "🌐")

        self.content.grid_columnconfigure(0, weight=1)

        # Simple status line only – no version numbers
        self.status_val = ctk.CTkLabel(
            self.content,
            text="Waiting to check Chrome status…",
            font=get_font("Outfit", 11, "bold"),
            text_color=colors["DIM_TEXT"],
        )
        self.status_val.grid(row=0, column=0, sticky="w", pady=(2, 2))

        self.note_lbl = ctk.CTkLabel(
            self.content,
            text="",
            font=get_font("Outfit", 10),
            text_color=colors["DIM_TEXT"],
        )
        self.note_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.note_lbl.configure(wraplength=260, justify="left")


# ─────────────────────────────────────────────────────────────────────────────
class PingCard(BaseCard):
    def __init__(self, master):
        super().__init__(master, "Connection Stability", "📡")

        # Target input next to header
        target_fr = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        target_fr.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(
            target_fr,
            text="Target:",
            font=get_font("JetBrainsMono NFP", 10),
            text_color=colors["DIM_TEXT"],
        ).pack(side="left", padx=(0, 4))
        self.target = ctk.CTkEntry(
            target_fr,
            placeholder_text="e.g. google.com",
            width=100,
            height=24,
            fg_color=colors["BORDER"],
            border_width=0,
            text_color=colors["TEXT"],
            font=get_font("JetBrainsMono NFP", 10),
        )
        self.target.pack(side="left")
        self.target.insert(0, "8.8.8.8")

        self.verdict = ctk.CTkLabel(
            target_fr,
            text="",
            font=get_font("Outfit", 12, "bold"),
            text_color=colors.get("GOOD", colors["SUCCESS"]),
        )
        self.verdict.pack(side="left", padx=(8, 0))

        # Results textbox
        self.content_text = ctk.CTkTextbox(
            self.content,
            fg_color="transparent",
            text_color=colors["TEXT"],
            activate_scrollbars=True,
            font=get_font("JetBrainsMono NFP", 10),
            height=48,
        )
        self.content_text.pack(fill="both", expand=True)
        self.content_text.insert("0.0", "Awaiting diagnostics...")
        self.content_text.configure(state="disabled")

    def update_content(self, text):
        self.content_text.configure(state="normal")
        self.content_text.delete("0.0", "end")
        self.content_text.insert("0.0", text)
        self.content_text.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
class SpeedCard(BaseCard):
    def __init__(self, master):
        super().__init__(master, "Internet Speed", "📶")

        self.content.pack_configure(pady=(2, 2))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0)

        # Type (hidden from UI, still detected for dashboard)
        self._type_lbl = ctk.CTkLabel(
            self.content,
            text="Type",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        )
        # Not placed on grid — hidden from users
        self.type_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("Outfit", 11),
            text_color=colors["TEXT"],
        )
        # Not placed on grid — hidden from users

        # Download
        ctk.CTkLabel(
            self.content,
            text="Download",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=0, column=0, sticky="w", pady=0)
        self.down_num = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("Outfit", 12, "bold"),
            text_color=colors["TEXT"],
        )
        self.down_num.grid(row=0, column=1, sticky="e", padx=(8, 0), pady=0)

        # Upload
        ctk.CTkLabel(
            self.content,
            text="Upload",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=1, column=0, sticky="w", pady=0)
        self.up_num = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("Outfit", 12, "bold"),
            text_color=colors["TEXT"],
        )
        self.up_num.grid(row=1, column=1, sticky="e", padx=(8, 0), pady=0)

        # Error label (hidden)
        self._err_lbl = ctk.CTkLabel(
            self.content,
            text="",
            font=get_font("Outfit", 10),
            text_color=colors["ERROR"],
        )
        self._err_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=0)

        # ── VPN Status Section ──
        self._vpn_sep = ctk.CTkFrame(self.content, fg_color=colors["BORDER"], height=1)
        self._vpn_sep.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 2))

        ctk.CTkLabel(
            self.content,
            text="VPN Status",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=4, column=0, sticky="w", pady=0)
        self.vpn_status_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("Outfit", 11, "bold"),
            text_color=colors["DIM_TEXT"],
        )
        self.vpn_status_val.grid(row=4, column=1, sticky="e", padx=(8, 0), pady=0)

        # VPN name (shown only when active)
        self.vpn_name_val = ctk.CTkLabel(
            self.content,
            text="",
            font=get_font("Outfit", 10),
            text_color=colors["WARNING"],
        )
        self.vpn_name_val.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.vpn_name_val.grid_remove()

    def update_vpn_status(self, active, vpn_name=""):
        """Update VPN status display on the card."""
        if active:
            self.vpn_status_val.configure(
                text="🔴 VPN Active", text_color=colors["ERROR"]
            )
            self.vpn_name_val.configure(text=f"⚠ {vpn_name}")
            self.vpn_name_val.grid()
        else:
            self.vpn_status_val.configure(
                text="🟢 No VPN Detected", text_color=colors["SUCCESS"]
            )
            self.vpn_name_val.grid_remove()

    def reset_vpn_status(self):
        """Reset VPN status to default state."""
        self.vpn_status_val.configure(text="—", text_color=colors["DIM_TEXT"])
        self.vpn_name_val.grid_remove()

    def update_speed(self, down_mbps, up_mbps, server="", latency="", jitter="", conn_type=""):
        from thresholds import SPEED_DOWNLOAD_MIN, SPEED_DOWNLOAD_WARN, SPEED_UPLOAD_MIN, SPEED_UPLOAD_WARN

        self.type_val.configure(text=conn_type if conn_type else "—")

        down_color = (
            colors.get("GOOD", colors["SUCCESS"]) if down_mbps >= SPEED_DOWNLOAD_MIN
            else colors["WARNING"] if down_mbps >= SPEED_DOWNLOAD_WARN
            else colors["ERROR"]
        )
        self.down_num.configure(text=f"{down_mbps:.1f} Mbps", text_color=down_color)

        up_color = (
            colors.get("GOOD", colors["SUCCESS"]) if up_mbps >= SPEED_UPLOAD_MIN
            else colors["WARNING"] if up_mbps >= SPEED_UPLOAD_WARN
            else colors["ERROR"]
        )
        self.up_num.configure(text=f"{up_mbps:.1f} Mbps", text_color=up_color)

        self._err_lbl.configure(text="")

    def update_content(self, text):
        self._err_lbl.configure(text=text)


# ─────────────────────────────────────────────────────────────────────────────
class MicCard(BaseCard):
    def __init__(self, master):
        super().__init__(master, "Microphone", "🎙")

        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.content,
            text="Device",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=0, column=0, sticky="nw", pady=(0, 2))
        self.dev_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("JetBrainsMono NFP", 11),
            text_color=colors["TEXT"],
            wraplength=240,
            justify="left",
            anchor="w",
        )
        self.dev_val.grid(row=0, column=1, sticky="nw", padx=(10, 0), pady=(0, 2))

        ctk.CTkLabel(
            self.content,
            text="Type",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=1, column=0, sticky="nw", pady=(0, 2))
        self.type_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("JetBrainsMono NFP", 11),
            text_color=colors["TEXT"],
            wraplength=240,
            justify="left",
            anchor="w",
        )
        self.type_val.grid(row=1, column=1, sticky="nw", padx=(10, 0), pady=(0, 2))

        ctk.CTkLabel(
            self.content,
            text="Signal Strength",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=2, column=0, sticky="nw", pady=(0, 2))
        self.lvl_val = ctk.CTkLabel(
            self.content,
            text="—/100",
            font=get_font("JetBrainsMono NFP", 12, "bold"),
            text_color=colors["ACCENT"],
        )
        self.lvl_val.grid(row=2, column=1, sticky="nw", padx=(10, 0), pady=(0, 2))

        self.prog = ctk.CTkProgressBar(
            self.content,
            height=6,
            fg_color=colors["BORDER"],
            progress_color=colors["SUCCESS"],
            corner_radius=8,
        )
        self.prog.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self.prog.set(0)

        # Standalone auto-fix button (Hidden by default)
        self.fix_btn = ctk.CTkButton(
            self.content,
            text="Fix Volume",
            font=get_font("Outfit", 11, "bold"),
            fg_color=colors["ACCENT"],
            text_color="#FFFFFF",
            hover_color=colors["ACCENT_HOVER"],
            corner_radius=5,
            height=26,
            width=100,
        )
        self.fix_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.fix_btn.grid_remove()  # Hide initially

    def show_fix_btn(self, command):
        self.fix_btn.configure(command=command)
        self.fix_btn.grid()

    def hide_fix_btn(self):
        self.fix_btn.grid_remove()


# ─────────────────────────────────────────────────────────────────────────────
class DiskCard(BaseCard):
    """Shows free disk space on the system drive."""

    def __init__(self, master):
        super().__init__(master, "Disk Space", "💾")

        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            self.content,
            text="System Drive",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 1))
        self.drive_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("JetBrainsMono NFP", 12, "bold"),
            text_color=colors["ACCENT"],
        )
        self.drive_val.grid(row=0, column=1, sticky="e", padx=(8, 0), pady=(0, 1))

        ctk.CTkLabel(
            self.content,
            text="Free Space",
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
        ).grid(row=1, column=0, sticky="w", pady=(0, 1))
        self.free_val = ctk.CTkLabel(
            self.content,
            text="—",
            font=get_font("JetBrainsMono NFP", 12, "bold"),
            text_color=colors["ACCENT"],
        )
        self.free_val.grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(0, 1))

        self.prog = ctk.CTkProgressBar(
            self.content,
            height=6,
            fg_color=colors["BORDER"],
            progress_color=colors["SUCCESS"],
            corner_radius=8,
        )
        self.prog.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self.prog.set(0)



