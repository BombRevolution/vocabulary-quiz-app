import json
import os
import tkinter as tk
from tkinter import ttk
from ui_theme import COLOR_BG, COLOR_TEXT, COLOR_PRIMARY, font, scale_size


class SettingsDialog(tk.Toplevel):
    def __init__(self, root, config, db_path):
        super().__init__(root)
        self.config = config
        self.db_path = db_path
        self.title("设置")
        w, h = scale_size(380, 260)
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        rows = tk.Frame(self, bg=COLOR_BG, padx=scale_size(24, 0)[0], pady=scale_size(0, 20)[1])
        rows.pack(fill="both", expand=True)
        p8 = scale_size(0, 8)[1]
        p16 = scale_size(0, 16)[1]
        tk.Label(rows, text="设置", font=font(16, bold=True), bg=COLOR_BG,
                 fg=COLOR_PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, p16))
        tk.Label(rows, text="每日新词数", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=p8)
        self.daily_var = tk.IntVar(value=int(config.get("daily_new_words", 50)))
        sp = ttk.Spinbox(rows, from_=1, to=500, textvariable=self.daily_var, width=12)
        sp.grid(row=1, column=1, sticky="w")
        tk.Label(rows, text="忽略大小写", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=p8)
        self.case_var = tk.BooleanVar(value=config.get("ignore_case", True))
        ttk.Checkbutton(rows, variable=self.case_var, style="TCheckbutton").grid(row=2, column=1, sticky="w")
        tk.Label(rows, text="忽略标点", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=p8)
        self.punct_var = tk.BooleanVar(value=config.get("ignore_punct", False))
        ttk.Checkbutton(rows, variable=self.punct_var, style="TCheckbutton").grid(row=3, column=1, sticky="w")
        ttk.Button(rows, text="保存", style="Primary.TButton", command=self.save).grid(row=4, column=0, columnspan=2, pady=(p16, 0))

    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()