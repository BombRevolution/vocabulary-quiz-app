import ctypes
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

FONT_FAMILY = "Microsoft YaHei UI"
FONT_SCALE = 1.3

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


def font(size, bold=False):
    size = int(round(size * FONT_SCALE))
    name = (FONT_FAMILY, size)
    if bold:
        name = (FONT_FAMILY, size, "bold")
    return name


def maximize(root):
    try:
        root.state("zoomed")
    except tk.TclError:
        try:
            root.attributes("-zoomed", True)
        except tk.TclError:
            pass


def center_window(win):
    try:
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass


class CheckBox(tk.Canvas):
    """自绘勾选框，方块大小按 DPI 随字体缩放，选中显示蓝色对勾。"""

    def __init__(self, parent, variable, command=None, size=None, bg=None, **kw):
        self._var = variable
        self._cmd = command
        if size is None:
            try:
                px_per_pt = parent.winfo_fpixels("1p")
                size = int(round(14 * px_per_pt * 1.5))
            except Exception:
                size = 24
        self._size = max(size, 20)
        b = bg if bg is not None else COLOR_BG
        super().__init__(parent, width=self._size, height=self._size, bg=b, highlightthickness=0,
                         bd=0, takefocus=1, **kw)
        self.bind("<Button-1>", self._toggle)
        self.bind("<space>", lambda e: self._toggle(e))
        self.bind("<Return>", lambda e: self._toggle(e))
        self._draw()

    def _toggle(self, event=None):
        self._var.set(not self._var.get())
        self._draw()
        if self._cmd:
            self._cmd()

    def _draw(self):
        self.delete("all")
        s = self._size
        pad = max(3, int(s * 0.14))
        x0, y0 = pad, pad
        x1, y1 = s - pad, s - pad
        if self._var.get():
            self.create_rectangle(x0, y0, x1, y1, outline=COLOR_PRIMARY, width=2,
                                  fill=COLOR_LIGHT_BLUE, tags="box")
            self.create_line(x0 + s * 0.18, y0 + s * 0.36, x0 + s * 0.36, y0 + s * 0.55,
                             x1 - s * 0.08, y0 + s * 0.14,
                             fill=COLOR_PRIMARY, width=max(3, int(s * 0.13)),
                             capstyle="round", joinstyle="round", tags="check")
        else:
            self.create_rectangle(x0, y0, x1, y1, outline=COLOR_MUTED, width=2,
                                  fill=COLOR_CARD, tags="box")


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
    try:
        import ctypes as _c
        factor = _c.windll.shcore.GetScaleFactorForDevice(0) / 96.0
        root.tk.call("tk", "scaling", factor)
    except Exception:
        pass

    fb = font(14)
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

    style.configure("Title.TLabel", font=font(22, bold=True), foreground=COLOR_PRIMARY, background=COLOR_BG)
    style.configure("Heading.TLabel", font=font(17, bold=True), foreground=COLOR_TEXT, background=COLOR_BG)
    style.configure("Muted.TLabel", font=font(11), foreground=COLOR_MUTED, background=COLOR_BG)
    style.configure("CardTitle.TLabel", font=font(17, bold=True), foreground=COLOR_PRIMARY, background=COLOR_CARD)
    style.configure("StatValue.TLabel", font=font(22, bold=True), foreground=COLOR_PRIMARY,
                    background=COLOR_CARD, anchor="center")
    style.configure("StatName.TLabel", font=font(11), foreground=COLOR_MUTED, background=COLOR_CARD,
                    anchor="center")

    style.configure("Primary.TButton", font=fb, background=COLOR_PRIMARY, foreground="#ffffff",
                    borderwidth=0, focusthickness=0, padding=(28, 14))
    style.map("Primary.TButton",
              background=[("active", COLOR_PRIMARY_DARK), ("pressed", COLOR_PRIMARY_DARK)],
              foreground=[("disabled", "#cbd5e0")])
    style.configure("Secondary.TButton", font=fb, background=COLOR_LIGHT_BLUE,
                    foreground=COLOR_PRIMARY, borderwidth=0, focusthickness=0, padding=(24, 12))
    style.map("Secondary.TButton",
              background=[("active", "#d6e6ff"), ("pressed", "#d6e6ff")],
              foreground=[("disabled", "#a0aec0")])
    style.configure("Danger.TButton", font=fb, background="#fef2f2", foreground=COLOR_WRONG,
                    borderwidth=0, focusthickness=0, padding=(24, 12))
    style.map("Danger.TButton",
              background=[("active", "#fee2e2"), ("pressed", "#fee2e2")])

    style.configure("TEntry", font=fb, fieldbackground=COLOR_CARD, bordercolor=COLOR_BORDER,
                    lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER, padding=8)
    style.map("TEntry", bordercolor=[("focus", COLOR_PRIMARY)], lightcolor=[("focus", COLOR_PRIMARY)],
              darkcolor=[("focus", COLOR_PRIMARY)])

    style.configure("TProgressbar", troughcolor=COLOR_LIGHT_BLUE, background=COLOR_PRIMARY,
                    borderwidth=0, thickness=16)

    tv_font = font(13)
    tv_rowheight = tkfont.Font(family=tv_font[0], size=tv_font[1]).metrics("linespace") + 10
    style.configure("Treeview", font=tv_font, background=COLOR_CARD, fieldbackground=COLOR_CARD,
                    foreground=COLOR_TEXT, rowheight=tv_rowheight)
    style.map("Treeview", background=[("selected", COLOR_LIGHT_BLUE)],
              foreground=[("selected", COLOR_PRIMARY)])
    style.configure("Treeview.Heading", font=font(11, bold=True), background=COLOR_LIGHT_BLUE,
                    foreground=COLOR_PRIMARY, padding=(4, 4))

    style.configure("TCheckbutton", font=fb, background=COLOR_BG, foreground=COLOR_TEXT)
    style.configure("TSpinbox", font=fb, fieldbackground=COLOR_CARD, arrowcolor=COLOR_PRIMARY,
                    padding=6)
    style.configure("TCombobox", font=fb, fieldbackground=COLOR_CARD, arrowcolor=COLOR_PRIMARY,
                    padding=6)