"""
dialogs.py — Modal dialogs for VOS GUI.

Contains:
  - NameDialog: First-launch setup for employee name and AnyDesk ID.
"""

import customtkinter as ctk
from gui.theme import colors, get_font


def _load_config():
    """Import and delegate to the root config loader."""
    import os, sys, json
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(app_dir, "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_config(data):
    import os, sys, json
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(app_dir, "config.json")
    try:
        with open(cfg_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


class NameDialog(ctk.CTkToplevel):
    """First-launch setup dialog: name and AnyDesk ID."""

    def __init__(self, master, current_name="", current_anydesk="",
                 current_dashboard_url="", current_team="", current_res_id="", on_close=None):
        super().__init__(master)

        self.title("Welcome — Let's get you set up")
        dlg_w, dlg_h = 480, 540
        self.geometry(f"{dlg_w}x{dlg_h}")
        self.configure(fg_color=colors["BG"])
        self.resizable(False, False)

        self.on_close_cb = on_close

        # Center within the app window and keep the dialog fully inside
        # the main frame (no drifting off to screen corners).
        self.update_idletasks()
        master.update_idletasks()
        mw, mh = master.winfo_width(), master.winfo_height()
        mx, my = master.winfo_x(), master.winfo_y()

        # If main window is smaller than the dialog, clamp to its top-left.
        max_x = mx + max(0, mw - dlg_w)
        max_y = my + max(0, mh - dlg_h)
        x = mx + max(0, (mw - dlg_w) // 2)
        y = my + max(0, (mh - dlg_h) // 2)
        x = min(max_x, max(mx, x))
        y = min(max_y, max(my, y))
        self.geometry(f"+{x}+{y}")

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        main_fr = ctk.CTkFrame(self, fg_color="transparent")
        main_fr.pack(pady=28, padx=40, fill="both", expand=True)

        ctk.CTkLabel(
            main_fr,
            text="👋  Just a quick setup",
            font=get_font("Outfit", 18, "bold"),
            text_color=colors["TEXT"],
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            main_fr,
            text="Please enter your details to continue.",
            font=get_font("Outfit", 12),
            text_color=colors["DIM_TEXT"],
        ).pack(anchor="w", pady=(0, 20))

        # Name field
        ctk.CTkLabel(
            main_fr,
            text="Your Full Name (first · middle · last)",
            font=get_font("Outfit", 12),
            text_color=colors["DIM_TEXT"],
        ).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(
            main_fr,
            placeholder_text="e.g. Mohamed Ibrahim Abdo",
            width=400,
            height=40,
            fg_color=colors["CARD_BG"],
            border_color=colors["BORDER"],
            border_width=1,
            text_color=colors["TEXT"],
            font=get_font("Outfit", 13),
        )
        self.name_entry.pack(pady=(4, 12))
        self.name_entry.insert(0, current_name)

        # AnyDesk field
        ctk.CTkLabel(
            main_fr,
            text="Your AnyDesk ID",
            font=get_font("Outfit", 12),
            text_color=colors["DIM_TEXT"],
        ).pack(anchor="w")
        self.anydesk_entry = ctk.CTkEntry(
            main_fr,
            placeholder_text="e.g. 1 585 322 949",
            width=400,
            height=40,
            fg_color=colors["CARD_BG"],
            border_color=colors["BORDER"],
            border_width=1,
            text_color=colors["TEXT"],
            font=get_font("Outfit", 13),
        )
        self.anydesk_entry.pack(pady=(4, 12))
        self.anydesk_entry.insert(0, current_anydesk)

        # Team field
        ctk.CTkLabel(
            main_fr,
            text="Team Name",
            font=get_font("Outfit", 12),
            text_color=colors["DIM_TEXT"],
        ).pack(anchor="w")
        self.team_entry = ctk.CTkEntry(
            main_fr,
            placeholder_text="e.g. Sales Team A",
            width=400,
            height=40,
            fg_color=colors["CARD_BG"],
            border_color=colors["BORDER"],
            border_width=1,
            text_color=colors["TEXT"],
            font=get_font("Outfit", 13),
        )
        self.team_entry.pack(pady=(4, 12))
        self.team_entry.insert(0, current_team)

        # RES-ID field (fixed "RES-" prefix)
        ctk.CTkLabel(
            main_fr,
            text="RES-ID",
            font=get_font("Outfit", 12),
            text_color=colors["DIM_TEXT"],
        ).pack(anchor="w")
        
        res_fr = ctk.CTkFrame(
            main_fr,
            fg_color=colors["CARD_BG"],
            border_color=colors["BORDER"],
            border_width=1,
            height=40
        )
        res_fr.pack(fill="x", pady=(4, 12))
        
        ctk.CTkLabel(
            res_fr,
            text="RES-",
            font=get_font("Outfit", 13, "bold"),
            text_color=colors["TEXT"],
        ).pack(side="left", padx=(12, 0))
        
        self.res_id_entry = ctk.CTkEntry(
            res_fr,
            placeholder_text="1304",
            height=38,
            fg_color="transparent",
            border_width=0,
            text_color=colors["TEXT"],
            font=get_font("Outfit", 13),
        )
        self.res_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Strip "RES-" if it already exists in the config so we don't double it
        display_res = current_res_id
        if display_res.upper().startswith("RES-"):
            display_res = display_res[4:]
        self.res_id_entry.insert(0, display_res)

        self.err_lbl = ctk.CTkLabel(
            main_fr,
            text="",
            font=get_font("Outfit", 10),
            text_color=colors["ERROR"],
        )
        self.err_lbl.pack(pady=4)

        self.save_btn = ctk.CTkButton(
            main_fr,
            text="Let's Go  →",
            font=get_font("Outfit", 13, "bold"),
            fg_color=colors["BORDER"],
            hover_color=colors["ACCENT_HOVER"],
            text_color=colors["TEXT"],
            command=self._save,
            height=44,
            corner_radius=12,
        )
        self.save_btn.pack(fill="x", pady=(4, 0))

        self.name_entry.bind("<KeyRelease>", self._validate)
        self.anydesk_entry.bind("<KeyRelease>", self._validate)
        self.res_id_entry.bind("<KeyRelease>", self._validate)
        self._validate()

    def _validate(self, event=None):
        name = self.name_entry.get().strip()
        anydesk = self.anydesk_entry.get().strip()

        # Enforce numeric only on RES-ID
        res_val = self.res_id_entry.get()
        res_clean = "".join(filter(str.isdigit, res_val))
        if res_val != res_clean:
            self.res_id_entry.delete(0, "end")
            self.res_id_entry.insert(0, res_clean)

        name_parts = [p for p in name.split() if p.strip()]
        is_name_valid = len(name_parts) >= 3

        clean_anydesk = anydesk.replace(" ", "")
        is_anydesk_valid = clean_anydesk.isdigit() and len(clean_anydesk) >= 9

        self.name_entry.configure(
            border_color=(
                colors["SUCCESS"] if is_name_valid
                else colors["ERROR"] if name
                else colors["BORDER"]
            )
        )
        self.anydesk_entry.configure(
            border_color=(
                colors["SUCCESS"] if is_anydesk_valid
                else colors["ERROR"] if anydesk
                else colors["BORDER"]
            )
        )

        if not is_name_valid and name:
            self.err_lbl.configure(text="Please enter your full three-part name")
        elif not is_anydesk_valid and anydesk:
            self.err_lbl.configure(text="AnyDesk ID must be at least 9 digits")
        else:
            self.err_lbl.configure(text="")

        if is_name_valid and is_anydesk_valid:
            # Accent button should always have high-contrast text in both themes
            self.save_btn.configure(fg_color=colors["ACCENT"], text_color="#FFFFFF")
            return True
        else:
            self.save_btn.configure(fg_color=colors["BORDER"], text_color=colors["TEXT"])
            return False

    def _save(self):
        if self._validate():
            name = self.name_entry.get().strip()
            anydesk = self.anydesk_entry.get().strip()

            cfg = _load_config()
            cfg["employee_name"] = name
            cfg["anydesk_id"] = anydesk
            cfg["team"] = self.team_entry.get().strip()
            
            res_val = self.res_id_entry.get().strip()
            cfg["res_id"] = f"RES-{res_val}" if res_val else ""
            # Always set theme default if missing
            if not cfg.get("theme"):
                cfg["theme"] = "dark"
            _save_config(cfg)

            if self.on_close_cb:
                self.on_close_cb()
            self.destroy()

    def _on_closing(self):
        """
        If user closes the setup window from X without filling details,
        exit the entire app instead of trapping them in the dialog.
        """
        try:
            master = self.master
        except Exception:
            master = None
        self.destroy()
        if master is not None and master.winfo_exists():
            master.destroy()


class LogoutConfirmDialog(ctk.CTkToplevel):
    """Confirmation Dialog for clearing Chrome data."""

    def __init__(self, master, on_confirm=None):
        super().__init__(master)

        self.title("Quick Drill")
        self.configure(fg_color=colors["BG"])
        self.resizable(False, False)
        self.on_confirm_cb = on_confirm

        # ── Size & center ────────────────────────────────────────────
        dlg_w, dlg_h = 460, 320
        self.geometry(f"{dlg_w}x{dlg_h}")
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (dlg_w // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (dlg_h // 2)
        self.geometry(f"+{x}+{y}")

        self.transient(master)
        self.grab_set()

        # ── Dark title-bar (Windows DWM) ─────────────────────────────
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            dwm = ctypes.windll.dwmapi
            bg = colors.get("BG", "#0B0F14").lstrip("#")
            r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            bgr = ctypes.c_int(r | (g << 8) | (b << 16))
            dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(bgr), ctypes.sizeof(bgr))
            dark = ctypes.c_int(1)
            dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        except Exception:
            pass

        # ── Outer card ───────────────────────────────────────────────
        card = ctk.CTkFrame(
            self, fg_color=colors["CARD_BG"],
            corner_radius=12, border_width=1, border_color=colors["BORDER"],
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Amber accent stripe at top
        stripe = ctk.CTkFrame(card, fg_color="#D97706", height=4, corner_radius=0)
        stripe.pack(fill="x", padx=20, pady=(16, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=(18, 20))

        # ── Warning badge ────────────────────────────────────────────
        badge_fr = ctk.CTkFrame(inner, fg_color="#2D1B00", corner_radius=6)
        badge_fr.pack(fill="x", pady=(0, 14))
        badge_inner = ctk.CTkFrame(badge_fr, fg_color="transparent")
        badge_inner.pack(padx=12, pady=8)
        ctk.CTkLabel(
            badge_inner, text="⚠",
            font=get_font("Outfit", 16),
            text_color="#F59E0B",
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            badge_inner,
            text="Heads up — this will close Chrome",
            font=get_font("Outfit", 12, "bold"),
            text_color="#FBBF24",
        ).pack(side="left")

        # ── Message ──────────────────────────────────────────────────
        msg = (
            "Please log out of the Readymode Dialer first.\n\n"
            "This will clear your browser cache, cookies & site settings, "
            "then flush your DNS cache. Re-open Chrome when done."
        )
        ctk.CTkLabel(
            inner, text=msg,
            font=get_font("Outfit", 11),
            text_color=colors["DIM_TEXT"],
            justify="left", wraplength=370, anchor="w",
        ).pack(fill="x", pady=(0, 16))

        # ── Checkbox ─────────────────────────────────────────────────
        self.confirm_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            inner,
            text="I have logged out of the Readymode Dialer",
            variable=self.confirm_var,
            command=self._toggle_button,
            font=get_font("Outfit", 11, "bold"),
            text_color=colors["TEXT"],
            fg_color="#D97706",
            hover_color="#B45309",
            border_color=colors["BORDER"],
            checkmark_color="#FFFFFF",
            corner_radius=4,
        )
        self.checkbox.pack(anchor="w", pady=(0, 20))

        # ── Buttons ──────────────────────────────────────────────────
        btn_fr = ctk.CTkFrame(inner, fg_color="transparent")
        btn_fr.pack(fill="x")

        self.cancel_btn = ctk.CTkButton(
            btn_fr, text="Cancel",
            font=get_font("Outfit", 12, "bold"),
            fg_color="transparent",
            border_width=1, border_color=colors["BORDER"],
            hover_color=colors["CARD_HOVER"],
            text_color=colors["DIM_TEXT"],
            command=self.destroy,
            height=38, width=110, corner_radius=8,
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            btn_fr, text="Run Quick Drill",
            font=get_font("Outfit", 12, "bold"),
            fg_color="#D97706",
            hover_color="#B45309",
            border_width=1, border_color="#F59E0B",
            text_color="#FFFFFF",
            text_color_disabled="#888888",
            command=self._confirm,
            height=38, corner_radius=8,
            state="disabled",
        )
        self.clear_btn.pack(side="left", fill="x", expand=True)

    def _toggle_button(self):
        if self.confirm_var.get():
            self.clear_btn.configure(state="normal")
        else:
            self.clear_btn.configure(state="disabled")

    def _confirm(self):
        if self.on_confirm_cb:
            self.on_confirm_cb()
        self.destroy()
