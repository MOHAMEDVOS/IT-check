import sys
from datetime import datetime

# ── Comtypes COM server subprocess guard ──────────────────────────────────────
_COM_SERVER_FLAGS = {'-Automation', '-Embedding', '/Automation', '/Embedding'}
if len(sys.argv) > 1 and sys.argv[1] in _COM_SERVER_FLAGS:
    import comtypes.server.localserver
    comtypes.server.localserver.main()
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

# ---- GLOBAL PATCH: Suppress ALL implicit cmd popups from subprocess calls ----
import platform
import subprocess
try:
    if platform.system() == "Windows":
        _original_popen = subprocess.Popen

        class PatchedPopen(_original_popen):
            def __init__(self, *args, **kwargs):
                if 'creationflags' not in kwargs:
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                elif not (kwargs['creationflags'] & subprocess.CREATE_NO_WINDOW):
                    kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
                super().__init__(*args, **kwargs)

        subprocess.Popen = PatchedPopen
except Exception:
    pass
# ------------------------------------------------------------------------------

import customtkinter as ctk
import tkinter as tk
import threading
import multiprocessing
import concurrent.futures
import os
import json
import argparse

import pystray
from PIL import Image, ImageTk

from logger import get_logger
from thresholds import (
    APP_VERSION, APP_NAME,
    SPEED_DOWNLOAD_MIN, SPEED_UPLOAD_MIN,
    PING_STABILITY_MIN, MIC_LEVEL_MIN, MIC_LEVEL_WARN,
    RAM_MIN_GB, CPU_PERF_SCORE_MIN,
    DISK_FREE_MIN_GB, DISK_FREE_WARN_GB,
    DASHBOARD_URL, API_KEY,
)
from gui.theme import colors, get_font, toggle_theme, get_theme, set_theme
from gui.cards import (
    SpecsCard, ChromeCard, PingCard, SpeedCard,
    MicCard, DiskCard
)
from gui.dialogs import NameDialog
from modules.auth import check_authorization

log = get_logger("app")

# ==================== CONFIG ====================
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# Auto-check: run full diagnostics every 1 hour while app is open
AUTO_CHECK_INTERVAL_MS = 1 * 60 * 60 * 1000  # 1 hour

ctk.set_appearance_mode("dark")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Failed to load config: {e}")
    return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log.error(f"Failed to save config: {e}")


class VOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Vital Operations Scanner")
        self.geometry("980x620")
        self.minsize(900, 540)
        self.configure(fg_color=colors["BG"])

        # Subtle gradient background (canvas behind content)
        self._gradient_canvas = None
        self._setup_gradient_bg()

        # Icon
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "assets", "IT.ico")
            self.iconbitmap(icon_path)
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vos.app.2.1")
        except Exception as e:
            log.debug(f"Icon load skipped: {e}")

        # Fonts
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
        if os.path.exists(font_dir):
            for f in os.listdir(font_dir):
                if f.endswith(".ttf"):
                    try:
                        ctk.FontManager.load_font(os.path.join(font_dir, f))
                    except Exception as e:
                        log.debug(f"Font load failed for {f}: {e}")

        # Load config
        cfg = load_config()
        self.emp_name = cfg.get("employee_name", "")
        self.anydesk_id = cfg.get("anydesk_id", "")
        self.team = cfg.get("team", "")
        self.res_id = cfg.get("res_id", "")
        self.dashboard_url = DASHBOARD_URL

        # Apply saved theme
        saved_theme = cfg.get("theme", "dark")
        set_theme(saved_theme)

        self._build_header()
        self._build_footer()
        self._build_cards()

        self.results = {}
        # FIX 4: Lock to protect self.results from concurrent thread writes
        self._results_lock = threading.Lock()
        self.running = False
        self.is_authorized = False
        self._is_silent_check = False
        # FIX 3: Removed dead _update_btn field (was set to None and never used)
        self._tray_icon = None

        # FIX 1: Connect _on_unmap so minimizing sends app to tray
        self.protocol("WM_DELETE_WINDOW", self._to_tray)
        self.bind("<Unmap>", self._on_unmap)

        # First automated check in 1 hour, then every 1 hour
        self.after(AUTO_CHECK_INTERVAL_MS, self._run_auto_check)

        # Handle startup mode (Background flag)
        if getattr(sys, '_started_in_background', False):
            self.withdraw()
            log.info("App started in background mode (withdrawn to tray)")
        else:
            self.after(200, self._check_startup_name)
            self.after(500, self._check_for_updates)

    # ─────────────────────── Gradient background ───────────────────────
    def _setup_gradient_bg(self):
        """Draw a very subtle vertical gradient on a canvas behind all content."""
        try:
            c1 = colors.get("BG", "#0A1118")
            c2 = colors.get("BG_GRADIENT_END", "#0D1520")
            self._bg_colors = (c1, c2)

            self._gradient_canvas = tk.Canvas(
                self, highlightthickness=0,
                bg=c1,
            )
            self._gradient_canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self._gradient_canvas.lower()

            def _hex_to_rgb(h):
                h = h.lstrip("#")
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

            def _rgb_to_hex(r, g, b):
                return f"#{r:02x}{g:02x}{b:02x}"

            # FIX (Warning): debounce gradient redraws so window resize doesn't lag
            self._gradient_after_id = None

            def _schedule_redraw(*args):
                if self._gradient_after_id is not None:
                    try:
                        self.after_cancel(self._gradient_after_id)
                    except Exception:
                        pass
                self._gradient_after_id = self.after(50, _redraw)

            def _redraw():
                self._gradient_after_id = None
                try:
                    w = self._gradient_canvas.winfo_width()
                    h = self._gradient_canvas.winfo_height()
                    if w < 2 or h < 2:
                        return
                    r1, g1, b1 = _hex_to_rgb(self._bg_colors[0])
                    r2, g2, b2 = _hex_to_rgb(self._bg_colors[1])
                    self._gradient_canvas.delete("gradient")
                    step = max(1, h // 80)
                    for i in range(0, h + step, step):
                        t = i / h if h else 0
                        r = int(r1 + (r2 - r1) * t)
                        g = int(g1 + (g2 - g1) * t)
                        b = int(b1 + (b2 - b1) * t)
                        color = _rgb_to_hex(r, g, b)
                        self._gradient_canvas.create_rectangle(
                            0, i, w, i + step + 1,
                            fill=color, outline=color,
                            tags="gradient",
                        )
                except Exception:
                    pass

            self._gradient_canvas.bind("<Configure>", _schedule_redraw)
            self.after(100, _redraw)
        except Exception as e:
            log.debug(f"Gradient bg skipped: {e}")

    # ─────────────────────── Auto-check (every 1 hour) ───────────────────────
    def _run_auto_check(self):
        """Run full system check in the background, then schedule the next one."""
        self.after(AUTO_CHECK_INTERVAL_MS, self._run_auto_check)
        if self.running:
            log.debug("Auto-check skipped: a check is already running")
            return
        log.info("Starting scheduled auto-check (every 1 hour)")
        self._run_silent_diagnostics()

    # ─────────────── Silent diagnostics (no UI, no window pop) ───────────────
    def _run_silent_diagnostics(self):
        """Run all diagnostics silently — zero UI updates, window stays hidden."""
        if self.running:
            return
        self.running = True
        self._is_silent_check = True
        log.info("Starting silent auto-check (no UI updates)")
        threading.Thread(target=self._run_silent_worker, daemon=True).start()

    def _run_silent_worker(self):
        """Background worker: runs every check, stores results, posts to dashboard."""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._silent_task_specs): "specs",
                    executor.submit(self._silent_task_chrome): "chrome",
                    executor.submit(self._silent_task_speed): "speed",
                    executor.submit(self._silent_task_mic): "mic",
                    executor.submit(self._silent_task_disk): "disk",
                }
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    try:
                        future.result()
                        log.info(f"Silent task '{name}' completed")
                    except Exception as e:
                        log.error(f"Silent task '{name}' failed: {e}", exc_info=True)

            self._silent_task_ping("8.8.8.8")
        except Exception as e:
            log.error(f"Silent auto-check failed: {e}", exc_info=True)
        finally:
            self.running = False
            self._is_silent_check = False
            self._post_results_to_dashboard()
            self._do_update_check(silent=True)
            log.info("Silent auto-check completed")

    def _silent_task_specs(self):
        try:
            from modules.specs import get_system_specs
            result = get_system_specs()
            with self._results_lock:
                self.results["specs"] = result
            log.info("Silent specs check done")
        except Exception as e:
            log.error(f"Silent specs check failed: {e}")

    def _silent_task_chrome(self):
        try:
            from modules.chrome import check_chrome
            result = check_chrome()
            with self._results_lock:
                self.results["chrome"] = result
            log.info("Silent chrome check done")
        except Exception as e:
            log.error(f"Silent chrome check failed: {e}")

    def _silent_task_speed(self):
        # VPN check
        try:
            from modules.vpn import check_vpn
            vpn_info = check_vpn()
            with self._results_lock:
                self.results["vpn"] = vpn_info
        except Exception as e:
            log.warning(f"Silent VPN check failed: {e}")
        # Speed test
        try:
            from modules.speed import run_speedtest
            res = run_speedtest()
            def _parse(val):
                try:
                    return float(str(val).split()[0])
                except Exception:
                    return 0.0
            res["_raw_down"] = _parse(res.get("download", "0"))
            res["_raw_up"] = _parse(res.get("upload", "0"))
            with self._results_lock:
                self.results["speed"] = res
            log.info(f"Silent speed check done: {res['_raw_down']:.1f}down / {res['_raw_up']:.1f}up")
        except Exception as e:
            log.error(f"Silent speed check failed: {e}")

    def _silent_task_mic(self):
        try:
            from modules.mic import check_mic_level
            res = check_mic_level()
            mic_data = {
                "level": res.get("level", 0),
                "device": res.get("device_name", "Unknown"),
                "type": res.get("device_type", "Unknown"),
            }
            with self._results_lock:
                self.results["mic"] = mic_data
            log.info("Silent mic check done")
        except Exception as e:
            log.error(f"Silent mic check failed: {e}")

    def _silent_task_disk(self):
        try:
            from modules.disk import check_disk_space
            result = check_disk_space()
            with self._results_lock:
                self.results["disk"] = result
            log.info("Silent disk check done")
        except Exception as e:
            log.error(f"Silent disk check failed: {e}")

    def _silent_task_ping(self, target):
        try:
            from modules.ping import run_ping
            res = run_ping(target)
            with self._results_lock:
                self.results["ping"] = res
            log.info(f"Silent ping check done: {getattr(res, 'stability_score', '?')}/100")
        except Exception as e:
            log.error(f"Silent ping check failed: {e}")

    # ─────────────────────── System tray ───────────────────────
    def _on_unmap(self, event):
        """When window is minimized, send to tray instead of taskbar."""
        if event.widget is self and self.state() == "iconic":
            self.after(10, self._to_tray)

    def _to_tray(self):
        """Hide window and show in system tray (notification area)."""
        log.info("Minimizing to tray...")
        try:
            if self._tray_icon is None:
                self._tray_icon = self._create_tray_icon()
                self._tray_icon.run_detached()
            self.withdraw()
        except Exception as e:
            log.error(f"Failed to minimize to tray: {e}")
            self.iconify()

    def _from_tray(self):
        """Show window again from tray."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def is_app_hidden(self):
        """Check if the app is currently minimized or hidden in tray."""
        return self.state() in ["iconic", "withdrawn"]

    def _quit_app(self):
        """Exit app and remove tray icon."""
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
            self._tray_icon = None
        self.quit()

    def _create_tray_icon(self):
        """Build system tray icon with Show / Exit menu."""
        try:
            from PIL import Image
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "assets", "IT.ico")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                if hasattr(img, "convert"):
                    img = img.convert("RGBA")
                w, h = img.size
                if w > 64 or h > 64:
                    resample = getattr(Image, "Resampling", Image)
                    img = img.resize((64, 64), resample.LANCZOS)
            else:
                raise FileNotFoundError(icon_path)
        except Exception as e:
            log.debug(f"Tray icon image load failed: {e}")
            from PIL import Image
            img = Image.new("RGBA", (32, 32), (0, 210, 255, 255))

        app = self

        def on_show(icon, item):
            app.after(0, app._from_tray)

        def on_exit(icon, item):
            app.after(0, app._quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Show VOS", on_show, default=True),
            pystray.MenuItem("Exit", on_exit),
        )
        icon = pystray.Icon("vos", img, f"{APP_NAME} - Vital Operations Scanner", menu)
        return icon

    # ─────────────────────── UI Build ───────────────────────
    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(8, 10))

        self.header.columnconfigure(0, weight=0)
        self.header.columnconfigure(1, weight=1)
        self.header.columnconfigure(2, weight=0)

        # Employee info badge
        self.emp_card = ctk.CTkFrame(
            self.header, fg_color=colors["CARD_BG"],
            corner_radius=8, border_width=1, border_color=colors["BORDER"],
        )
        inner = ctk.CTkFrame(self.emp_card, fg_color="transparent")
        inner.pack(padx=12, pady=6)

        name_row = ctk.CTkFrame(inner, fg_color="transparent")
        name_row.pack(fill="x", anchor="w")
        ctk.CTkLabel(
            name_row, text="Name :",
            font=get_font("Outfit", 10, "bold"), text_color=colors["DIM_TEXT"],
        ).pack(side="left", padx=(0, 4))
        self.emp_name_lbl = ctk.CTkLabel(
            name_row, text=self.emp_name or "—",
            font=get_font("Outfit", 11, "bold"), text_color=colors["TEXT"],
            wraplength=250, justify="left"
        )
        self.emp_name_lbl.pack(side="left")

        id_row = ctk.CTkFrame(inner, fg_color="transparent")
        id_row.pack(fill="x", anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            id_row, text="Anydesk ID :",
            font=get_font("Outfit", 10, "bold"), text_color=colors["DIM_TEXT"],
        ).pack(side="left", padx=(0, 4))
        self.emp_id_lbl = ctk.CTkLabel(
            id_row, text=self.anydesk_id or "—",
            font=get_font("Outfit", 11, "bold"), text_color=colors["ACCENT"],
        )
        self.emp_id_lbl.pack(side="left")

        team_row = ctk.CTkFrame(inner, fg_color="transparent")
        team_row.pack(fill="x", anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            team_row, text="Team :",
            font=get_font("Outfit", 10, "bold"), text_color=colors["DIM_TEXT"],
        ).pack(side="left", padx=(0, 4))
        self.emp_team_lbl = ctk.CTkLabel(
            team_row, text=self.team or "—",
            font=get_font("Outfit", 11, "bold"), text_color=colors["TEXT"],
        )
        self.emp_team_lbl.pack(side="left")

        res_id_row = ctk.CTkFrame(inner, fg_color="transparent")
        res_id_row.pack(fill="x", anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            res_id_row, text="RES-ID :",
            font=get_font("Outfit", 10, "bold"), text_color=colors["DIM_TEXT"],
        ).pack(side="left", padx=(0, 4))
        self.emp_res_id_lbl = ctk.CTkLabel(
            res_id_row, text=self.res_id or "—",
            font=get_font("Outfit", 11, "bold"), text_color="#f472b6",
        )
        self.emp_res_id_lbl.pack(side="left")

        if self.emp_name and self.anydesk_id:
            self.emp_card.grid(row=0, column=0, sticky="w", padx=(0, 20))

        # Center Area: BMO Animated GIF
        self.logo_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.logo_frame.grid(row=0, column=1)

        self._bmo_frames = []
        self._bmo_delay = 100
        self._bmo_animating = False
        self._bmo_after_id = None
        self._bmo_frame_index = 0
        try:
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            gif_path = os.path.join(base_path, "assets", "bmo.gif")
            if os.path.exists(gif_path):
                img = Image.open(gif_path)
                resample = getattr(Image, "Resampling", Image).LANCZOS
                try:
                    while True:
                        frame = img.copy()
                        if frame.mode == "P":
                            frame = frame.convert("RGBA")
                        elif frame.mode != "RGBA" and frame.mode != "RGB":
                            frame = frame.convert("RGB")
                        if frame.size != (140, 140):
                            frame = frame.resize((140, 140), resample)
                        self._bmo_frames.append(ImageTk.PhotoImage(frame))
                        img.seek(img.tell() + 1)
                except EOFError:
                    pass
                self._bmo_delay = img.info.get("duration", 100) or 100
                if self._bmo_delay < 20:
                    self._bmo_delay = 50
            if self._bmo_frames:
                self._bmo_label = tk.Label(self.logo_frame, image=self._bmo_frames[0], bg=colors["BG"])
                self._bmo_label.pack()
            else:
                self._bmo_label = None
                icon_path = os.path.join(base_path, "assets", "IT.ico")
                if os.path.exists(icon_path):
                    img = Image.open(icon_path)
                    logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
                    logo_lbl = ctk.CTkLabel(self.logo_frame, image=logo_img, text="")
                    logo_lbl.pack()
        except Exception as e:
            log.debug(f"BMO GIF load skipped: {e}")
            self._bmo_label = None

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, sticky="ne")
        self.run_btn = ctk.CTkButton(
            self.btn_frame, text="🔍  Check My System",
            font=get_font("Outfit", 14, "bold"),
            fg_color=colors["ACCENT"], text_color="#FFFFFF",
            text_color_disabled="#FFFFFF",
            hover_color=colors["ACCENT_HOVER"],
            corner_radius=8, height=45, command=self.start_diagnostics,
        )
        self.run_btn.pack(side="top", fill="x", pady=(0, 4))

        # FIX 2: Create button but do NOT pack it here.
        # _apply_auth_ui is the only place that shows/hides it.
        self.quick_drill_btn = ctk.CTkButton(
            self.btn_frame, text="Quick Drill !",
            font=get_font("Outfit", 10, "bold"),
            fg_color=colors["BORDER"], text_color=colors["TEXT"],
            hover_color=colors["WARNING"],
            corner_radius=6, height=28, command=self._clear_chrome_data,
            state="disabled",
        )
        # intentionally NOT calling .pack() here

    def _build_footer(self):
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", fill="x", pady=(0, 6))
        self.footer_lbl = ctk.CTkLabel(
            self.footer_frame,
            text="VOS  ·  Developed by Mohamed Abdo",
            font=get_font("Outfit", 9, "bold"), text_color="#FFFFFF",
        )
        self.footer_lbl.pack()

    def _build_cards(self):
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=colors["BORDER"],
            scrollbar_button_hover_color=colors["ACCENT"],
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        for c in range(3):
            self.scroll_frame.columnconfigure(c, weight=1, uniform="col")
        self.scroll_frame.rowconfigure(0, weight=0, uniform="row")
        self.scroll_frame.rowconfigure(1, weight=1, uniform="row")

        self.cards = {
            "specs":  SpecsCard(self.scroll_frame),
            "chrome": ChromeCard(self.scroll_frame),
            "ping":   PingCard(self.scroll_frame),
            "speed":  SpeedCard(self.scroll_frame),
            "mic":    MicCard(self.scroll_frame),
            "disk":   DiskCard(self.scroll_frame),
        }

        gap = 6
        self.cards["specs"].grid( row=0, column=0, sticky="nsew", padx=(0, gap), pady=(0, gap))
        self.cards["chrome"].grid(row=0, column=1, sticky="nsew", padx=gap,     pady=(0, gap))
        self.cards["disk"].grid(  row=0, column=2, sticky="nsew", padx=(gap, 0), pady=(0, gap))

    def _start_bmo_animation(self):
        if not self._bmo_frames or not self._bmo_label or self._bmo_animating or self._is_silent_check:
            return
        self._bmo_animating = True
        self._bmo_frame_index = 0
        self._tick_bmo_frame()

    def _tick_bmo_frame(self):
        if not self._bmo_animating or not self._bmo_frames or not self._bmo_label:
            return
        try:
            self._bmo_frame_index = (self._bmo_frame_index + 1) % len(self._bmo_frames)
            self._bmo_label.configure(image=self._bmo_frames[self._bmo_frame_index])
            self._bmo_after_id = self.after(self._bmo_delay, self._tick_bmo_frame)
        except Exception:
            self._bmo_animating = False

    def _stop_bmo_animation(self):
        self._bmo_animating = False
        if self._bmo_after_id is not None:
            try:
                self.after_cancel(self._bmo_after_id)
            except Exception:
                pass
            self._bmo_after_id = None
        if self._bmo_frames and self._bmo_label:
            try:
                self._bmo_label.configure(image=self._bmo_frames[0])
            except Exception:
                pass

    def _clear_chrome_data(self):
        from gui.dialogs import LogoutConfirmDialog

        def _on_confirm():
            self.quick_drill_btn.configure(
                state="disabled",
                text="⏳ Clearing... (Chrome will close)",
                text_color=colors["WARNING"]
            )
            threading.Thread(target=self._do_clear_chrome_data, daemon=True).start()

        LogoutConfirmDialog(self, on_confirm=_on_confirm)

    def _do_clear_chrome_data(self):
        try:
            from modules.chrome import clear_chrome_data
            success = clear_chrome_data()
            if success:
                def _update_success():
                    self.quick_drill_btn.configure(
                        state="normal",
                        text="✅ Cache, Cookies & Settings Cleared",
                        text_color=colors["SUCCESS"]
                    )
                    self.after(4000, lambda: self.quick_drill_btn.configure(
                        text="Quick Drill !", text_color=colors["TEXT"]
                    ))
                self.after(0, _update_success)
                log.info("Chrome data successfully cleared.")
            else:
                def _update_fail():
                    self.quick_drill_btn.configure(
                        state="normal",
                        text="❌ Failed to clear Chrome data",
                        text_color=colors["ERROR"]
                    )
                    self.after(4000, lambda: self.quick_drill_btn.configure(
                        text="Quick Drill !", text_color=colors["TEXT"]
                    ))
                self.after(0, _update_fail)
                log.warning("Chrome data clear returned false.")
        except Exception as e:
            log.error(f"Failed to clear Chrome data: {e}", exc_info=True)
            self.after(0, lambda: self.quick_drill_btn.configure(
                state="normal", text="Quick Drill !", text_color=colors["TEXT"]
            ))

    # ─────────────────────── Auto-Update Check ───────────────────────
    def _check_for_updates(self, silent=False):
        threading.Thread(target=self._do_update_check, args=(silent,), daemon=True).start()

    def _do_update_check(self, silent=False):
        try:
            from modules.updater import check_for_update, apply_update
            result = check_for_update()
            if result and result.get("update_available"):
                new_ver = result.get("latest_version", "?")
                dl_url = result.get("download_url", "")

                if str(new_ver) == str(APP_VERSION):
                    log.debug(f"Update check: Skipping false positive (both are {new_ver})")
                    return

                log.info(f"Update check: Current={APP_VERSION}, Latest={new_ver} -> UPDATE AVAILABLE")

                def _show_update_ui():
                    self.footer_lbl.configure(
                        text=f"🔔 Update available: v{new_ver}",
                        text_color=colors["WARNING"],
                    )
                    if dl_url and not silent and not self.is_app_hidden():
                        update_btn = ctk.CTkButton(
                            self.btn_frame,
                            text="🔔  Update Now",
                            font=get_font("Outfit", 11, "bold"),
                            fg_color=colors["WARNING"],
                            text_color=colors["BG"],
                            hover_color=colors["SUCCESS"],
                            corner_radius=8,
                            height=32,
                        )
                        update_btn.pack(fill="x", pady=(0, 4))

                        def _on_update_click():
                            update_btn.configure(state="disabled", text="⏳ Downloading...")
                            self.footer_lbl.configure(text="Downloading update, please wait...", text_color=colors["SUCCESS"])
                            threading.Thread(target=apply_update, args=(dl_url,), daemon=True).start()

                        update_btn.configure(command=_on_update_click)

                self.after(0, _show_update_ui)
                log.info(f"Update available: v{new_ver}")
        except Exception as e:
            log.debug(f"Update check skipped: {e}")

    # ─────────────────────── Startup ───────────────────────
    def _check_startup_name(self):
        if not self.emp_name or not self.anydesk_id:
            NameDialog(
                self,
                current_name=self.emp_name,
                current_anydesk=self.anydesk_id,
                current_dashboard_url=self.dashboard_url,
                current_team=self.team,
                current_res_id=self.res_id,
                on_close=self._on_info_saved,
            )
        else:
            self._trigger_auth_check()

    def _trigger_auth_check(self):
        threading.Thread(target=self._do_auth_check, daemon=True).start()

    def _do_auth_check(self):
        if not self.res_id or not self.emp_name:
            self.after(0, self._apply_auth_ui, False)
            return
        is_auth = check_authorization(self.res_id, self.emp_name)
        log.info(f"Authorization check completed. Result: {is_auth}")
        self.after(0, self._apply_auth_ui, is_auth)

    def _apply_auth_ui(self, is_authorized):
        self.is_authorized = is_authorized
        gap = 6
        if is_authorized:
            log.info("User IS authorized. Un-hiding cards...")
            self.cards["speed"].grid(row=1, column=0, sticky="nsew", padx=(0, gap), pady=(0, gap))
            self.cards["mic"].grid(  row=1, column=1, sticky="nsew", padx=gap,      pady=(0, gap))
            self.cards["ping"].grid( row=1, column=2, sticky="nsew", padx=(gap, 0), pady=(0, gap))
            # FIX 2: single canonical pack location for quick_drill_btn
            self.quick_drill_btn.pack(side="top", fill="x", pady=(4, 0))
        else:
            log.info("User is NOT authorized. Keeping restricted UI hidden.")
            self.cards["ping"].grid_forget()
            self.cards["speed"].grid_forget()
            self.cards["mic"].grid_forget()
            self.quick_drill_btn.pack_forget()

    def _on_info_saved(self):
        cfg = load_config()
        self.emp_name = cfg.get("employee_name", "")
        self.anydesk_id = cfg.get("anydesk_id", "")
        self.team = cfg.get("team", "")
        self.res_id = cfg.get("res_id", "")

        self.emp_name_lbl.configure(text=self.emp_name or "—")
        self.emp_id_lbl.configure(text=self.anydesk_id or "—")
        self.emp_team_lbl.configure(text=self.team or "—")
        self.emp_res_id_lbl.configure(text=self.res_id or "—")

        if self.emp_name and self.anydesk_id:
            self.emp_card.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self._trigger_auth_check()

    # ─────────────────────── Diagnostics ───────────────────────
    def start_diagnostics(self, silent=False):
        if self.running:
            return
        self.running = True
        self._is_silent_check = silent

        if not silent:
            self._start_bmo_animation()
            self.run_btn.configure(state="disabled", text="⏳  Checking...")

        log.info(f"Starting diagnostics {'(silent)' if silent else ''}")

        with self._results_lock:
            self.results = {}
            self.results["speed"] = {"_raw_down": 0.0, "_raw_up": 0.0}
            self.results["mic"] = {"level": 0, "device": "Unknown"}

        target = self.cards["ping"].target.get() or "8.8.8.8"

        for c in self.cards.values():
            c.update_status("Checking...", colors["DIM_TEXT"])
            if hasattr(c, 'prog'):
                c.prog.set(0)
                c.prog.configure(progress_color=colors["SUCCESS"])
            if hasattr(c, 'lvl_val'):
                c.lvl_val.configure(text="—/100")
            if hasattr(c, 'verdict'):
                c.verdict.configure(text="")
            if hasattr(c, 'down_num'):
                c.down_num.configure(text="—", text_color=colors["TEXT"])
                c.up_num.configure(text="—", text_color=colors["TEXT"])
                c.type_val.configure(text="—")
                c._err_lbl.configure(text="")
            if hasattr(c, 'reset_vpn_status'):
                c.reset_vpn_status()
            if hasattr(c, 'type_val') and not hasattr(c, 'down_num'):
                c.type_val.configure(text="—")
                if hasattr(c, 'hide_fix_btn'):
                    c.hide_fix_btn()
            if hasattr(c, 'content_text'):
                c.content_text.configure(state="normal")
                c.content_text.delete("0.0", "end")
                c.content_text.insert("0.0", "Awaiting diagnostics...")
                c.content_text.configure(state="disabled")

        self._mic_thread = threading.Thread(target=self._task_mic, daemon=True)
        self._mic_thread.start()
        threading.Thread(target=self._run_all, args=(target,), daemon=True).start()

    def _run_all(self, target):
        log.info("Running all diagnostic tasks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._task_specs): "specs",
                executor.submit(self._task_chrome): "chrome",
                executor.submit(self._task_speed): "speed",
                executor.submit(self._task_disk): "disk",
            }

            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                    log.info(f"Task '{name}' completed successfully")
                except Exception as e:
                    log.error(f"Task '{name}' failed: {e}", exc_info=True)
                    self.after(0, lambda n=name: self.cards[n].update_status(
                        "Something went wrong", colors["ERROR"]
                    ))

        log.info("Running ping task sequentially")
        try:
            self._task_ping(target)
            log.info("Task 'ping' completed successfully")
        except Exception as e:
            log.error(f"Task 'ping' failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["ping"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

        if hasattr(self, '_mic_thread') and self._mic_thread.is_alive():
            log.debug("Waiting for mic thread...")
            self._mic_thread.join(timeout=10)

        log.info(f"All tasks done. Results: {list(self.results.keys())}")
        self.after(0, self._finish_diagnostics)

    def _finish_diagnostics(self):
        was_silent = self._is_silent_check
        self.running = False
        self._is_silent_check = False

        self._stop_bmo_animation()

        if not was_silent:
            self.run_btn.configure(state="normal", text="🔍  Check My System")
            if self.is_authorized:
                self.quick_drill_btn.configure(state="normal")
            else:
                self.quick_drill_btn.configure(state="disabled")

        self.update_observations()
        threading.Thread(target=self._post_results_to_dashboard, daemon=True).start()

    # ─────────────────────── Dashboard Integration ───────────────────────
    def _post_results_to_dashboard(self):
        """POST results to team dashboard (silent, non-blocking)."""
        try:
            import requests as req_lib

            cfg = load_config()
            dashboard_url = DASHBOARD_URL
            api_key = API_KEY
            agent_name = cfg.get("employee_name", "Unknown")
            anydesk_id = cfg.get("anydesk_id", "—")
            team = cfg.get("team", "—")
            res_id = cfg.get("res_id", "—")

            # FIX 4: Take a snapshot of results under lock before reading
            with self._results_lock:
                results_snapshot = dict(self.results)

            specs = results_snapshot.get("specs", {})
            cpu_model = specs.get("cpu_model", "—").split("@")[0].strip()
            ram_str = specs.get("total_ram", "—").split()[0].split(".")[0] if specs.get("total_ram") else "—"
            gpu_name = specs.get("gpu_name", "—")
            cpu_score = specs.get("cpu_score", 0)
            cpu_label = specs.get("cpu_label", "—")
            pc_specs = f"{cpu_model} / {ram_str}GB RAM" if cpu_model != "—" else "—"

            chrome_res = results_snapshot.get("chrome", None)
            chrome_str = "—"
            chrome_status = "—"
            if chrome_res and hasattr(chrome_res, "status"):
                chrome_status = chrome_res.status
                if chrome_status == "UP_TO_DATE":
                    chrome_str = "Up to date"
                elif chrome_status == "OUTDATED":
                    chrome_str = "Needs Update"
                else:
                    chrome_str = "—"

            ping_res = results_snapshot.get("ping", None)
            conn_str = "—"
            ping_details = {}
            if ping_res and hasattr(ping_res, "stability_score"):
                conn_str = f"{ping_res.stability_score}/100 ({ping_res.verdict})"
                ping_details = {
                    "score": ping_res.stability_score,
                    "verdict": ping_res.verdict,
                    "avg_ms": getattr(ping_res, "avg_rtt", 0),
                    "jitter_ms": getattr(ping_res, "jitter", 0),
                    "loss_pct": getattr(ping_res, "packet_loss_pct", 0),
                    "spikes": getattr(ping_res, "spike_count", 0),
                    "target": getattr(ping_res, "host", "—"),
                    "distribution": getattr(ping_res, "latency_distribution", ""),
                }

            speed_res = results_snapshot.get("speed", {})
            raw_down = speed_res.get("_raw_down", 0)
            raw_up = speed_res.get("_raw_up", 0)
            conn_type = speed_res.get("connection_type", "—")
            speed_str = f"{raw_down:.1f}down / {raw_up:.1f}up Mbps" if (raw_down or raw_up) else "—"

            mic_res = results_snapshot.get("mic", {})
            mic_lvl = mic_res.get("level", 0)
            mic_device = f"{mic_res.get('device', '—')} — {mic_res.get('type', '—')}"
            mic_str = f"{mic_lvl}/100" if mic_lvl else "—"

            disk_res = results_snapshot.get("disk", {})
            disk_free = disk_res.get("free_gb", 0)
            disk_total = disk_res.get("total_gb", 0)
            disk_pct = disk_res.get("used_pct", 0)
            disk_str = f"{disk_free:.1f}GB free" if disk_free else "—"

            payload = {
                "agent_name":           agent_name,
                "anydesk_id":           anydesk_id,
                "team":                 team,
                "res_id":               res_id,
                "pc_specs":             pc_specs,
                "gpu":                  gpu_name,
                "cpu_score":            cpu_score,
                "cpu_label":            cpu_label,
                "chrome_version":       chrome_str,
                "chrome_status":        chrome_status,
                "connection_type":      conn_type,
                "connection_stability": conn_str,
                "ping_details":         json.dumps(ping_details) if ping_details else "{}",
                "download_mbps":        round(raw_down, 1),
                "upload_mbps":          round(raw_up, 1),
                "internet_speed":       speed_str,
                "mic_level":            mic_str,
                "mic_device":           mic_device,
                "disk_space":           disk_str,
                "disk_free_gb":         round(disk_free, 1) if disk_free else 0,
                "disk_used_pct":        round(disk_pct, 1) if disk_pct else 0,
                "vpn_active":           results_snapshot.get("vpn", {}).get("active", False),
                "vpn_name":             results_snapshot.get("vpn", {}).get("vpn_name", ""),
                "last_checked":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notes":                results_snapshot.get("mic", {}).get("notes", ""),
            }

            headers = {}
            if api_key:
                headers["X-API-Key"] = api_key

            resp = req_lib.post(f"{dashboard_url}/api/results", json=payload,
                                headers=headers, timeout=5)
            resp.raise_for_status()
            log.info(f"Results posted to dashboard at {dashboard_url}")
        except Exception as e:
            log.debug(f"Dashboard POST failed (silent): {e}")

    # ─────────────────────── Task Implementations ───────────────────────
    def _task_specs(self):
        self.after(0, lambda: self.cards["specs"].update_status("Checking...", colors["WARNING"]))
        try:
            from modules.specs import get_system_specs
            res = get_system_specs()
            with self._results_lock:
                self.results["specs"] = res

            model = res['cpu_model'].split('@')[0].strip()
            ram_val = res['total_ram'].split()[0].split('.')[0]
            gpu_name = res.get('gpu_name', '—')

            def _update():
                self.cards["specs"].cpu_val.configure(text=f"Processor : {model}")
                self.cards["specs"].mem_val.configure(text=f"RAM : {ram_val}GB")
                self.cards["specs"].update_status("Done ✓", colors["SUCCESS"])

            self.after(0, _update)
            log.info(f"Specs: {model}, {ram_val}GB RAM, GPU: {gpu_name}")
        except Exception as e:
            log.error(f"Specs check failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["specs"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    def _task_chrome(self):
        self.after(0, lambda: self.cards["chrome"].update_status("Checking browser...", colors["WARNING"]))
        try:
            from modules.chrome import check_chrome
            res = check_chrome()
            with self._results_lock:
                self.results["chrome"] = res

            if res.error or res.status == "NOT_INSTALLED":
                msg = res.error if res.error else res.note
                def _update_err():
                    self.cards["chrome"].note_lbl.configure(text=f"● {msg}", text_color=colors["ERROR"])
                    self.cards["chrome"].update_status("Something went wrong", colors["ERROR"])
                self.after(0, _update_err)
                return

            def _update_ok():
                if res.status == "UP_TO_DATE":
                    status_txt = "Chrome is up to date"
                    status_color = colors["SUCCESS"]
                elif res.status == "OUTDATED":
                    status_txt = "Chrome needs to be updated"
                    status_color = colors["ERROR"]
                else:
                    status_txt = res.note or "Chrome status could not be determined"
                    status_color = colors["WARNING"]

                self.cards["chrome"].status_val.configure(
                    text=status_txt,
                    text_color=status_color,
                )
                if res.note and res.note != status_txt:
                    self.cards["chrome"].note_lbl.configure(
                        text=res.note,
                        text_color=colors["DIM_TEXT"],
                    )
                else:
                    self.cards["chrome"].note_lbl.configure(text="")
                self.cards["chrome"].update_status("Done ✓", colors["SUCCESS"])

            self.after(0, _update_ok)
            log.info(f"Chrome: {res.status} (v{res.installed_milestone})")
        except Exception as e:
            log.error(f"Chrome check failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["chrome"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    def _task_ping(self, target):
        self.after(0, lambda: self.cards["ping"].update_status("Testing connection...", colors["WARNING"]))
        try:
            from modules.ping import run_ping
            res = run_ping(
                target,
                callback=lambda msg: self.after(
                    0, lambda m=msg: self.cards["ping"].update_status(m, colors["WARNING"])
                ),
            )
            with self._results_lock:
                self.results["ping"] = res

            if res.error:
                def _update_err():
                    self.cards["ping"].verdict.configure(text="FAILED", text_color=colors["ERROR"])
                    self.cards["ping"].update_content(res.error)
                    self.cards["ping"].update_status("Something went wrong", colors["ERROR"])
                self.after(0, _update_err)
                return

            if res.verdict.upper() in ["EXCELLENT", "GOOD", "FAIR"]:
                text = "Good Connection – Your network is stable. No issues detected."
            elif res.verdict.upper() == "MARGINAL":
                text = "Unstable Connection – Your network is fluctuating and may affect calls."
            else:
                text = "Poor Connection – Your connection is unstable and may cause call drops or delays."

            def _update_ok():
                self.cards["ping"].update_content(text.strip())
                self.cards["ping"].verdict.configure(
                    text=res.verdict.upper(), text_color=res.verdict_color
                )
                self.cards["ping"].update_status("Done ✓", colors["SUCCESS"])

            self.after(0, _update_ok)
            log.info(f"Ping: {res.stability_score}/100 ({res.verdict})")
        except Exception as e:
            log.error(f"Ping check failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["ping"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    def _task_speed(self):
        self.after(0, lambda: self.cards["speed"].update_status("Measuring speed...", colors["WARNING"]))

        try:
            from modules.vpn import check_vpn
            vpn_info = check_vpn()
            with self._results_lock:
                self.results["vpn"] = vpn_info

            def _update_vpn():
                self.cards["speed"].update_vpn_status(
                    active=vpn_info["active"],
                    vpn_name=vpn_info.get("vpn_name", ""),
                )
            self.after(0, _update_vpn)
            if vpn_info["active"]:
                log.warning(f"VPN detected: {vpn_info['vpn_name']}")
        except Exception as e:
            log.warning(f"VPN check failed: {e}")

        try:
            from modules.speed import run_speedtest
            res = run_speedtest()

            def _parse_mbps(val):
                try:
                    return float(str(val).split()[0])
                except Exception:
                    return 0.0

            raw_down = _parse_mbps(res.get("download", "0"))
            raw_up = _parse_mbps(res.get("upload", "0"))
            res["_raw_down"] = raw_down
            res["_raw_up"] = raw_up
            with self._results_lock:
                self.results["speed"] = res

            def _update():
                self.cards["speed"].update_speed(
                    down_mbps=raw_down,
                    up_mbps=raw_up,
                    server=res.get("server", ""),
                    latency=str(res.get("latency", "")),
                    jitter=str(res.get("jitter", "")),
                    conn_type=res.get("connection_type", ""),
                )
                self.cards["speed"].update_status("Done ✓", colors["SUCCESS"])

            self.after(0, _update)
            log.info(f"Speed: {raw_down:.1f}down / {raw_up:.1f}up Mbps")
        except Exception as e:
            log.error(f"Speed test failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["speed"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    def _task_mic(self):
        try:
            from modules.mic import check_mic_level
            res = check_mic_level()
            lvl = res.get("level", 0)
            dev_name = res.get("device_name", "Unknown")
            dev_type = res.get("device_type", "Unknown")
            err = res.get("error")
            with self._results_lock:
                self.results["mic"] = {"level": lvl, "device": dev_name, "type": dev_type}

            def _update():
                txt = dev_name[:60] + "..." if len(dev_name) > 60 else dev_name
                self.cards["mic"].dev_val.configure(text=txt)
                self.cards["mic"].type_val.configure(text=dev_type)
                self.cards["mic"].lvl_val.configure(text=f"{lvl}/100")
                self.cards["mic"].prog.set(lvl / 100.0)
                color = (
                    colors.get("GOOD", colors["SUCCESS"]) if lvl >= MIC_LEVEL_MIN
                    else colors["WARNING"] if lvl > MIC_LEVEL_WARN
                    else colors["ERROR"]
                )
                self.cards["mic"].prog.configure(progress_color=color)
                self.cards["mic"].update_status(
                    "Done ✓" if not err else "Check mic",
                    colors["SUCCESS"] if not err else colors["WARNING"],
                )

            self.after(0, _update)
            log.info(f"Mic: {lvl}/100 ({dev_name} - {dev_type})")
        except Exception as e:
            log.error(f"Mic check failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["mic"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    def _auto_fix_mic(self):
        try:
            with self._results_lock:
                old_lvl = self.results.get("mic", {}).get("level", "0")
            from modules.mic import set_mic_level
            success = set_mic_level(1.0)
            if success:
                def _re_run_and_upload():
                    self._task_mic()
                    with self._results_lock:
                        if "mic" in self.results:
                            self.results["mic"]["notes"] = f"Fix mic triggered (From {old_lvl} to 100)"
                    self.after(600, self.update_observations)
                    self.after(1000, lambda: threading.Thread(target=self._post_results_to_dashboard, daemon=True).start())
                threading.Thread(target=_re_run_and_upload, daemon=True).start()
        except Exception as e:
            log.error(f"Failed to auto-fix mic: {e}")

    def _task_disk(self):
        self.after(0, lambda: self.cards["disk"].update_status("Checking disk...", colors["WARNING"]))
        try:
            from modules.disk import check_disk_space
            res = check_disk_space()
            with self._results_lock:
                self.results["disk"] = res

            free_gb = res.get("free_gb", 0)
            total_gb = res.get("total_gb", 1)
            drive = res.get("drive", "C:")
            used_pct = res.get("used_pct", 0)

            def _update():
                self.cards["disk"].drive_val.configure(text=drive)
                color = (
                    colors.get("GOOD", colors["SUCCESS"]) if free_gb >= DISK_FREE_MIN_GB
                    else colors["WARNING"] if free_gb >= DISK_FREE_WARN_GB
                    else colors["ERROR"]
                )
                self.cards["disk"].free_val.configure(
                    text=f"{free_gb:.1f} GB free / {total_gb:.0f} GB",
                    text_color=color,
                )
                self.cards["disk"].prog.set(used_pct / 100.0)
                self.cards["disk"].prog.configure(progress_color=color)
                self.cards["disk"].update_status("Done ✓", colors["SUCCESS"])

            self.after(0, _update)
            log.info(f"Disk: {free_gb:.1f}GB free on {drive}")
        except Exception as e:
            log.error(f"Disk check failed: {e}", exc_info=True)
            self.after(0, lambda: self.cards["disk"].update_status(
                "Something went wrong", colors["ERROR"]
            ))

    # ─────────────────────── Observations ───────────────────────
    def update_observations(self):
        # Take a safe snapshot first
        with self._results_lock:
            results_snapshot = dict(self.results)

        if "specs" in results_snapshot:
            w = []
            res = results_snapshot["specs"]
            try:
                ram_str = str(res.get("total_ram", "8.0")).split()[0]
                ram_gb = float(ram_str)
                is_weak = res.get("perf_score", 100) < CPU_PERF_SCORE_MIN
                if ram_gb < RAM_MIN_GB or is_weak:
                    w.append({
                        "title": "Your Computer May Struggle",
                        "desc": "Your PC's hardware is below the minimum needed for smooth work.\nMinimum: Intel Core i5 (6th Gen or newer) and 8 GB RAM.",
                        "steps": [],
                    })
            except Exception as e:
                log.warning(f"Observations: specs check failed: {e}")
            self.cards["specs"].set_feedback(w)

        if "ping" in results_snapshot:
            w = []
            res = results_snapshot["ping"]
            score = getattr(res, 'stability_score', 100)
            if score < PING_STABILITY_MIN:
                w.append({
                    "title": "Unstable Internet Connection",
                    "desc": "Your connection is dropping or fluctuating too much for reliable calls.",
                    "steps": [
                        "Clear your browser's cache and cookies",
                        "Close all open browser tabs",
                        "Shut your PC down completely",
                        "Turn off your router for 10 minutes",
                        "Turn the router back on",
                        "Start your PC and log back in",
                    ],
                })
            self.cards["ping"].set_feedback(w)

        if "mic" in results_snapshot:
            w = []
            res = results_snapshot["mic"]
            try:
                lvl = float(res.get("level", 100))
                if lvl < MIC_LEVEL_MIN:
                    self.cards["mic"].show_fix_btn(self._auto_fix_mic)
                else:
                    self.cards["mic"].hide_fix_btn()
            except Exception as e:
                log.warning(f"Observations: mic check failed: {e}")
            self.cards["mic"].set_feedback(w)

        if "speed" in results_snapshot:
            w = []
            res = results_snapshot["speed"]
            try:
                down = float(res.get("_raw_down", res.get("download", 0)))
                up = float(res.get("_raw_up", res.get("upload", 0)))
                if down < SPEED_DOWNLOAD_MIN or up < SPEED_UPLOAD_MIN:
                    w.append({
                        "title": "Internet Speed Is Too Slow",
                        "desc": (
                            f"Measured: {down:.1f} Mbps down / {up:.1f} Mbps up.\n"
                            f"Minimum needed: {SPEED_DOWNLOAD_MIN} Mbps down and {SPEED_UPLOAD_MIN} Mbps up."
                        ),
                        "steps": [
                            "Clear your browser's cache and cookies",
                            "Close all open browser tabs",
                            "Shut your PC down completely",
                            "Turn off your router for 10 minutes",
                            "Turn the router back on",
                            "Start your PC and log back in",
                        ],
                    })
            except Exception as e:
                log.warning(f"Observations: speed check failed: {e}")

            vpn = results_snapshot.get("vpn", {})
            if vpn.get("active"):
                w.append({
                    "title": "VPN Connection Detected",
                    "desc": (
                        f"Active VPN: {vpn.get('vpn_name', 'Unknown')}\n"
                        "VPN connections can cause slow speeds, high latency, "
                        "and dropped VoIP calls. Disable it for best performance."
                    ),
                    "steps": [],
                })
            self.cards["speed"].set_feedback(w)

        if "chrome" in results_snapshot:
            w = []
            res = results_snapshot["chrome"]
            status = getattr(res, 'status', "")
            if status == "OUTDATED":
                w.append({
                    "title": "Chrome Needs an Update",
                    "desc": "Important: Log out of Readymode before restarting Chrome.",
                    "steps": [
                        "Open Chrome menu (⋮) in the top right",
                        "Go to Help → About Google Chrome",
                        "Click Update if shown",
                        "Wait for the update to finish, then click Relaunch",
                    ],
                })
            self.cards["chrome"].set_feedback(w)

        if "disk" in results_snapshot:
            w = []
            res = results_snapshot["disk"]
            try:
                free_gb = float(res.get("free_gb", 100))
                if free_gb < DISK_FREE_MIN_GB:
                    w.append({
                        "title": "Low Disk Space",
                        "desc": f"Your system drive has only {free_gb:.1f} GB free. Minimum recommended: {DISK_FREE_MIN_GB} GB.",
                        "steps": [
                            "Open Settings → System → Storage",
                            "Click 'Temporary files' and delete them",
                            "Empty the Recycle Bin",
                            "Uninstall unused programs",
                        ],
                    })
            except Exception as e:
                log.warning(f"Observations: disk check failed: {e}")
            self.cards["disk"].set_feedback(w)


# FIX (Warning): store at module level so Python's garbage collector
# never releases the mutex while the app is running
_MUTEX = None


def enforce_single_instance(restore=True):
    try:
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        hMutex = kernel32.CreateMutexW(None, False, "Global\\VOS_App_SingleInstance_Mutex")
        if not hMutex:
            return None

        ERROR_ALREADY_EXISTS = 183
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            if not restore:
                sys.exit(0)
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            from thresholds import APP_NAME
            window_title = f"{APP_NAME} - Vital Operations Scanner"
            hwnd = user32.FindWindowW(None, window_title)
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            sys.exit(0)

        return hMutex
    except Exception:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", action="store_true", help="Start or run in background without restoring window")
    args, unknown = parser.parse_known_args()

    sys._started_in_background = args.background

    multiprocessing.freeze_support()
    # FIX (Warning): store at module level so GC doesn't release it early
    _MUTEX = enforce_single_instance(restore=not args.background)
    app = VOSApp()
    app.mainloop()