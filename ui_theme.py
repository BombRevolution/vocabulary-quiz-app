import ctypes
import tkinter as tk
from tkinter import ttk

FONT_FAMILY = "Microsoft YaHei UI"

COLOR_PRIMARY = "#2b6cb0"
COLOR_PRIMARY_DARK = "#1e4e79"
COLOR_LIGHT_BLUE = "#ebf4ff"
COLOR_BG = "#f5f7fa"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#1a202c"
COLOR_MUTED = "#718096"
COLOR_BORDER = "#d9e2ec"

COLOR_CORRECT = "#2e7d32"
COLOR_BLUR = "#e65100"
COLOR_WRONG = "#c62828"

SCALE = 1.4


def font(size, bold=False):
    name = (FONT_FAMILY, int(size * SCALE))
    if bold:
        name = (FONT_FAMILY, int(size * SCALE), "bold")
    return name


def scale_size(w, h):
    return int(w * SCALE), int(h * SCALE)


def screen_size(root=None):
    if root is not None:
        try:
            return root.winfo_screenwidth(), root.winfo_screenheight()
        except Exception:
            pass
    return 1440, 960


def compute_scale(root=None):
    global SCALE
    sw, sh = screen_size(root)
    s = min(1.4, sw / 820.0, sh / 560.0)
    SCALE = max(s, 1.0)
    return SCALE


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def apply_theme(root):
    enable_dpi_awareness()
    compute_scale(root)
    try:
        import ctypes as _c
        factor = _c.windll.shcore.GetScaleFactorForDevice(0) / 96.0
        root.tk.call("tk", "scaling", factor)
    except Exception:
        pass

    fb = font(12)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=fb, background=COLOR_BG, foreground=COLOR_TEXT)

    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_CARD)
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
    style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT)

    style.configure("Title.TLabel", font=font(20, bold=True), foreground=COLOR_PRIMARY, background=COLOR_BG)
    style.configure("Heading.TLabel", font=font(16, bold=True), foreground=COLOR_TEXT, background=COLOR_BG)
    style.configure("Muted.TLabel", font=font(10), foreground=COLOR_MUTED, background=COLOR_BG)
    style.configure("CardTitle.TLabel", font=font(16, bold=True), foreground=COLOR_PRIMARY, background=COLOR_CARD)
    style.configure("StatValue.TLabel", font=font(20, bold=True), foreground=COLOR_PRIMARY,
                    background=COLOR_CARD, anchor="center")
    style.configure("StatName.TLabel", font=font(10), foreground=COLOR_MUTED, background=COLOR_CARD,
                    anchor="center")

    style.configure("Primary.TButton", font=fb, background=COLOR_PRIMARY, foreground="#ffffff",
                    borderwidth=0, focusthickness=0, padding=scale_size(18, 8))
    style.map("Primary.TButton",
              background=[("active", COLOR_PRIMARY_DARK), ("pressed", COLOR_PRIMARY_DARK)],
              foreground=[("disabled", "#cbd5e0")])
    style.configure("Secondary.TButton", font=fb, background=COLOR_LIGHT_BLUE,
                    foreground=COLOR_PRIMARY, borderwidth=0, focusthickness=0, padding=scale_size(12, 6))
    style.map("Secondary.TButton",
              background=[("active", "#d6e6ff"), ("pressed", "#d6e6ff")],
              foreground=[("disabled", "#a0aec0")])
    style.configure("Danger.TButton", font=fb, background="#fef2f2", foreground=COLOR_WRONG,
                    borderwidth=0, focusthickness=0, padding=scale_size(12, 6))
    style.map("Danger.TButton",
              background=[("active", "#fee2e2"), ("pressed", "#fee2e2")])

    style.configure("TEntry", font=fb, fieldbackground=COLOR_CARD, bordercolor=COLOR_BORDER,
                    lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER, padding=scale_size(6, 6))
    style.map("TEntry", bordercolor=[("focus", COLOR_PRIMARY)], lightcolor=[("focus", COLOR_PRIMARY)],
              darkcolor=[("focus", COLOR_PRIMARY)])

    style.configure("TProgressbar", troughcolor=COLOR_LIGHT_BLUE, background=COLOR_PRIMARY,
                    borderwidth=0, thickness=int(14 * SCALE))

    style.configure("Treeview", font=fb, background=COLOR_CARD, fieldbackground=COLOR_CARD,
                    foreground=COLOR_TEXT, rowheight=int(26 * SCALE))
    style.map("Treeview", background=[("selected", COLOR_LIGHT_BLUE)],
              foreground=[("selected", COLOR_PRIMARY)])
    style.configure("Treeview.Heading", font=font(10, bold=True), background=COLOR_LIGHT_BLUE,
                    foreground=COLOR_PRIMARY, padding=scale_size(4, 4))

    style.configure("TCheckbutton", font=fb, background=COLOR_BG, foreground=COLOR_TEXT)
    style.configure("TSpinbox", font=fb, fieldbackground=COLOR_CARD, arrowcolor=COLOR_PRIMARY,
                    padding=int(4 * SCALE))
    style.configure("TCombobox", font=fb, fieldbackground=COLOR_CARD, arrowcolor=COLOR_PRIMARY,
                    padding=int(4 * SCALE))