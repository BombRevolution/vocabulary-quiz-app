import json
import os
import tkinter as tk
from tkinter import ttk


class SettingsDialog(tk.Toplevel):
    def __init__(self, root, config, db_path):
        super().__init__(root)
        self.config = config
        self.db_path = db_path
        self.title("设置")
        self.geometry("360x220")
        self.grab_set()
        rows = ttk.Frame(self, padding=16)
        rows.pack(fill="both", expand=True)
        ttk.Label(rows, text="每日新词数").grid(row=0, column=0, sticky="w", pady=6)
        self.daily_var = tk.IntVar(value=int(config.get("daily_new_words", 50)))
        ttk.Spinbox(rows, from_=1, to=500, textvariable=self.daily_var, width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(rows, text="忽略大小写").grid(row=1, column=0, sticky="w", pady=6)
        self.case_var = tk.BooleanVar(value=config.get("ignore_case", True))
        ttk.Checkbutton(rows, variable=self.case_var).grid(row=1, column=1, sticky="w")
        ttk.Label(rows, text="忽略标点").grid(row=2, column=0, sticky="w", pady=6)
        self.punct_var = tk.BooleanVar(value=config.get("ignore_punct", False))
        ttk.Checkbutton(rows, variable=self.punct_var).grid(row=2, column=1, sticky="w")
        ttk.Button(rows, text="保存", command=self.save).grid(row=3, column=0, columnspan=2, pady=12)

    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()