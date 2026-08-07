import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importer
from ui_theme import (COLOR_BG, COLOR_TEXT, COLOR_MUTED, COLOR_PRIMARY, COLOR_LIGHT_BLUE,
                      font, center_window, CheckBox)


class ImportDialog(tk.Toplevel):
    def __init__(self, root, conn, on_close=None):
        super().__init__(root)
        self.conn = conn
        self.on_close = on_close
        self.title("导入词库")
        self.geometry("900x660")
        self.minsize(760, 540)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.path = None
        self.sheets = []
        self.detected = None
        self.has_header = True

        rows = tk.Frame(self, bg=COLOR_BG)
        rows.pack(fill="both", expand=True, padx=24, pady=18)
        rows.columnconfigure(1, weight=1)

        tk.Label(rows, text="导入词库", font=font(18, bold=True), bg=COLOR_BG,
                 fg=COLOR_PRIMARY).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        ttk.Button(rows, text="选择文件", style="Secondary.TButton",
                   command=self.pick_file).grid(row=1, column=0, sticky="w", pady=6)
        self.file_label = tk.Label(rows, text="支持 .xls / .xlsx / .csv", font=font(11), bg=COLOR_BG,
                                   fg=COLOR_MUTED, anchor="w")
        self.file_label.grid(row=1, column=1, sticky="ew", pady=6, padx=(12, 0))

        tk.Label(rows, text="词库名称", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(rows, width=34)
        self.name_entry.grid(row=2, column=1, sticky="w", pady=6, padx=(12, 0))

        self.header_var = tk.BooleanVar(value=True)
        header_row = tk.Frame(rows, bg=COLOR_BG)
        header_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=6)
        CheckBox(header_row, variable=self.header_var, command=self._toggle_header).pack(side="left")
        tk.Label(header_row, text="首行是表头（列名）", font=font(14), bg=COLOR_BG,
                 fg=COLOR_TEXT).pack(side="left", padx=(8, 0))

        preview_frame = tk.Frame(rows, bg=COLOR_BG)
        preview_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        rows.rowconfigure(4, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        tk.Label(preview_frame, text="数据预览", font=font(14, bold=True), bg=COLOR_BG,
                 fg=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        self.preview_tree = ttk.Treeview(preview_frame, height=10, show="headings")
        self.preview_tree.grid(row=1, column=0, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        sb = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.preview_tree.configure(yscrollcommand=sb.set)

        ttk.Button(rows, text="确认导入", style="Primary.TButton",
                   command=self.do_import).grid(row=5, column=0, columnspan=3, pady=12, ipadx=24)

        center_window(self)

    def _toggle_header(self):
        self.has_header = self.header_var.get()
        if self.path:
            self.preview()

    def pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("词库文件", "*.xls *.xlsx *.csv")])
        if not path:
            return
        self.path = path
        self.file_label.config(text=path)
        try:
            self.sheets = importer.detect_excel(path)
            self.detected = importer.auto_detect(path)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件：{e}")
            return
        default_name = os.path.splitext(os.path.basename(path))[0]
        if not self.name_entry.get().strip():
            self.name_entry.insert(0, default_name)
        self.has_header = self.detected["has_header"]
        self.header_var.set(self.has_header)
        self.preview()

    def preview(self):
        head, rows = importer.read_sheet(self.path, self.detected["sheet"], 8, has_header=self.has_header)
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = [str(i) for i in range(len(head))]
        for i, h in enumerate(head):
            self.preview_tree.heading(str(i), text=h)
        for r in rows:
            self.preview_tree.insert("", "end", values=r)

    def do_import(self):
        if not self.path:
            messagebox.showwarning("提示", "请先选择文件")
            return
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入词库名称")
            return
        if not self.detected:
            messagebox.showwarning("提示", "请先选择文件")
            return
        try:
            n = importer.import_book(self.conn, name, self.path, self.detected["sheet"],
                                     self.detected["word_col"], self.detected["meaning_col"],
                                     has_header=self.has_header)
            messagebox.showinfo("导入成功", f"已导入 {n} 个单词")
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror("导入失败", f"导入出错：{e}")
