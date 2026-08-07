import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from ui_theme import (COLOR_BG, COLOR_TEXT, COLOR_PRIMARY, COLOR_LIGHT_BLUE,
                      font, center_window, CheckBox, fit_and_center)

HINT_MODE_LABELS = {
    "reveal": "揭示前N%字母",
    "full": "显示完整拼写照抄",
    "count": "显示字母个数",
}
HINT_MODE_LABELS_REV = {v: k for k, v in HINT_MODE_LABELS.items()}

MODIFIER_KEYSYMS = {"Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R",
                    "Caps_Lock", "Num_Lock"}


def build_event_sequence(state, keysym):
    mods = []
    if state & 0x4:
        mods.append("Control")
    if state & 0x1:
        mods.append("Shift")
    if state & 0x8:
        mods.append("Alt")
    if not mods:
        return ""
    return "<" + "-".join(mods + [keysym]) + ">"


class SettingsDialog(tk.Toplevel):
    def __init__(self, root, config, db_path):
        super().__init__(root)
        self.config = config
        self.db_path = db_path
        self.title("设置")
        self.resizable(True, True)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.option_add("*TCombobox*Listbox.font", font(12))
        st = ttk.Style(self)
        st.configure("S.TEntry", padding=2)
        st.configure("S.TCombobox", padding=2)
        rows = tk.Frame(self, bg=COLOR_BG, padx=32, pady=18)
        rows.pack(fill="both", expand=True)
        tk.Label(rows, text="设置", font=font(16, bold=True), bg=COLOR_BG,
                 fg=COLOR_PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        tk.Label(rows, text="每日新词数", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        self.daily_var = tk.IntVar(value=int(config.get("daily_new_words", 50)))
        sp = self._big_spinbox(rows, self.daily_var, 1, 500)
        sp.grid(row=1, column=1, sticky="w")
        tk.Label(rows, text="忽略大小写", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        self.case_var = tk.BooleanVar(value=config.get("ignore_case", True))
        CheckBox(rows, variable=self.case_var).grid(row=2, column=1, sticky="w")
        tk.Label(rows, text="忽略标点", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=4)
        self.punct_var = tk.BooleanVar(value=config.get("ignore_punct", False))
        CheckBox(rows, variable=self.punct_var).grid(row=3, column=1, sticky="w")
        tk.Label(rows, text="提示方案", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=4)
        initial_mode = config.get("hint_mode", "reveal")
        self.hint_mode_var = tk.StringVar(value=HINT_MODE_LABELS[initial_mode])
        hint_mode_box = ttk.Combobox(rows, textvariable=self.hint_mode_var, state="readonly", width=12,
                                     style="S.TCombobox", font=font(12), values=list(HINT_MODE_LABELS.values()))
        hint_mode_box.grid(row=4, column=1, sticky="w")
        tk.Label(rows, text="揭示比例", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=5, column=0, sticky="w", pady=4)
        self.hint_percent_var = tk.IntVar(value=int(config.get("hint_percent", 30)))
        percent_box = ttk.Combobox(rows, textvariable=self.hint_percent_var, state="readonly", width=6,
                                   style="S.TCombobox", font=font(12), values=[20, 30, 40, 50])
        percent_box.grid(row=5, column=1, sticky="w")
        tk.Label(rows, text="跳过快捷键", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=6, column=0, sticky="w", pady=4)
        self.skip_key_entry = ttk.Entry(rows, width=14, style="S.TEntry", font=font(12))
        self.skip_key_entry.insert(0, config.get("key_skip", "<Control-d>"))
        self.skip_key_entry.grid(row=6, column=1, sticky="w")
        self.skip_key_entry.bind("<KeyPress>", lambda e: self._capture_key(e, self.skip_key_entry))
        tk.Label(rows, text="提示快捷键", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=7, column=0, sticky="w", pady=4)
        self.hint_key_entry = ttk.Entry(rows, width=14, style="S.TEntry", font=font(12))
        self.hint_key_entry.insert(0, config.get("key_hint", "<Control-space>"))
        self.hint_key_entry.grid(row=7, column=1, sticky="w")
        self.hint_key_entry.bind("<KeyPress>", lambda e: self._capture_key(e, self.hint_key_entry))
        ttk.Button(rows, text="保存", style="Primary.TButton", command=self.save).grid(row=8, column=0, columnspan=2, pady=(14, 0))
        self.update_idletasks()
        fit_and_center(self, self.winfo_reqwidth() + 24, self.winfo_reqheight() + 16)

    def _big_spinbox(self, parent, var, lo, hi):
        frame = tk.Frame(parent, bg=COLOR_BG)
        ttk.Entry(frame, textvariable=var, style="S.TEntry", font=font(12), width=4, justify="center").grid(
            row=0, column=0, rowspan=2, sticky="ns")

        def bump(delta):
            try:
                v = int(var.get())
            except (ValueError, tk.TclError):
                v = lo
            var.set(max(lo, min(hi, v + delta)))

        btn_kw = dict(font=font(10), bg=COLOR_LIGHT_BLUE, fg=COLOR_PRIMARY, relief="flat",
                      bd=0, width=2, cursor="hand2",
                      activebackground="#d6e6ff", activeforeground=COLOR_PRIMARY)
        tk.Button(frame, text="▲", command=lambda: bump(1), **btn_kw).grid(
            row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 2))
        tk.Button(frame, text="▼", command=lambda: bump(-1), **btn_kw).grid(
            row=1, column=1, sticky="nsew", padx=(6, 0), pady=(2, 0))
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        return frame

    def _capture_key(self, event, entry):
        if event.keysym == "Escape" or event.keysym in MODIFIER_KEYSYMS:
            return "break"
        seq = build_event_sequence(event.state, event.keysym)
        if seq:
            entry.delete(0, "end")
            entry.insert(0, seq)
        return "break"

    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        self.config["hint_mode"] = HINT_MODE_LABELS_REV[self.hint_mode_var.get()]
        self.config["hint_percent"] = self.hint_percent_var.get()
        skip_key = self.skip_key_entry.get().strip() or "<Control-d>"
        hint_key = self.hint_key_entry.get().strip() or "<Control-space>"
        if skip_key == hint_key:
            messagebox.showwarning("快捷键冲突", "跳过与提示快捷键不能相同，请重新设置")
            return
        self.config["key_skip"] = skip_key
        self.config["key_hint"] = hint_key
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()