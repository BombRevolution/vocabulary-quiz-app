import json
import os
import tkinter as tk
from tkinter import ttk
from ui_theme import COLOR_BG, COLOR_TEXT, COLOR_PRIMARY, font, center_window


class SettingsDialog(tk.Toplevel):
    def __init__(self, root, config, db_path):
        super().__init__(root)
        self.config = config
        self.db_path = db_path
        self.title("设置")
        self.geometry("560x420")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        rows = tk.Frame(self, bg=COLOR_BG, padx=32, pady=28)
        rows.pack(fill="both", expand=True)
        tk.Label(rows, text="设置", font=font(18, bold=True), bg=COLOR_BG,
                 fg=COLOR_PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        tk.Label(rows, text="每日新词数", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=10)
        self.daily_var = tk.IntVar(value=int(config.get("daily_new_words", 50)))
        sp = ttk.Spinbox(rows, from_=1, to=500, textvariable=self.daily_var, width=14)
        sp.grid(row=1, column=1, sticky="w")
        tk.Label(rows, text="忽略大小写", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=10)
        self.case_var = tk.BooleanVar(value=config.get("ignore_case", True))
        ttk.Checkbutton(rows, variable=self.case_var, style="TCheckbutton").grid(row=2, column=1, sticky="w")
        tk.Label(rows, text="忽略标点", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=10)
        self.punct_var = tk.BooleanVar(value=config.get("ignore_punct", False))
        ttk.Checkbutton(rows, variable=self.punct_var, style="TCheckbutton").grid(row=3, column=1, sticky="w")
        ttk.Button(rows, text="保存", style="Primary.TButton", command=self.save).grid(row=4, column=0, columnspan=2, pady=(20, 0))
        center_window(self)

    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()