import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importer
from ui_theme import COLOR_BG, COLOR_TEXT, COLOR_MUTED, COLOR_PRIMARY, font


class ImportDialog(tk.Toplevel):
    def __init__(self, root, conn, on_close=None):
        super().__init__(root)
        self.conn = conn
        self.on_close = on_close
        self.title("导入词库")
        self.geometry("920x700")
        self.minsize(760, 560)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.path = None
        self.sheets = []
        self.has_header = True

        rows = tk.Frame(self, bg=COLOR_BG)
        rows.pack(fill="both", expand=True, padx=20, pady=16)
        rows.columnconfigure(1, weight=1)

        tk.Label(rows, text="导入词库", font=font(18, bold=True), bg=COLOR_BG,
                 fg=COLOR_PRIMARY).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        ttk.Button(rows, text="选择文件", style="Secondary.TButton",
                   command=self.pick_file).grid(row=1, column=0, sticky="w", pady=6)
        self.file_label = tk.Label(rows, text="未选择文件", font=font(10), bg=COLOR_BG,
                                   fg=COLOR_MUTED, anchor="w")
        self.file_label.grid(row=1, column=1, sticky="ew", pady=6, padx=(12, 0))

        tk.Label(rows, text="工作表", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=6)
        self.sheet_var = tk.StringVar()
        self.sheet_box = ttk.Combobox(rows, textvariable=self.sheet_var, state="readonly", width=30)
        self.sheet_box.grid(row=2, column=1, sticky="w", pady=6, padx=(12, 0))
        self.sheet_box.bind("<<ComboboxSelected>>", lambda e: self.preview())

        tk.Label(rows, text="英文单词列", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=6)
        self.word_var = tk.StringVar()
        self.word_box = ttk.Combobox(rows, textvariable=self.word_var, state="readonly", width=30)
        self.word_box.grid(row=3, column=1, sticky="w", pady=6, padx=(12, 0))

        tk.Label(rows, text="中文释义列", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=6)
        self.meaning_var = tk.StringVar()
        self.meaning_box = ttk.Combobox(rows, textvariable=self.meaning_var, state="readonly", width=30)
        self.meaning_box.grid(row=4, column=1, sticky="w", pady=6, padx=(12, 0))

        tk.Label(rows, text="词库名称", font=font(12), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=5, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(rows, width=32)
        self.name_entry.grid(row=5, column=1, sticky="w", pady=6, padx=(12, 0))

        self.header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rows, text="首行是表头（列名）", variable=self.header_var,
                        command=self._toggle_header, style="TCheckbutton").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=6)
        self.header_hint = tk.Label(rows, text="提示：若文件第一行就是单词数据，请取消勾选", font=font(10),
                                    bg=COLOR_BG, fg=COLOR_MUTED)
        self.header_hint.grid(row=6, column=1, sticky="w", pady=6, padx=(12, 0))

        preview_frame = tk.Frame(rows, bg=COLOR_BG)
        preview_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        rows.rowconfigure(7, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        tk.Label(preview_frame, text="数据预览", font=font(12, bold=True), bg=COLOR_BG,
                 fg=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        self.preview_tree = ttk.Treeview(preview_frame, height=10, show="headings")
        self.preview_tree.grid(row=1, column=0, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        sb = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.preview_tree.configure(yscrollcommand=sb.set)

        ttk.Button(rows, text="确认导入", style="Primary.TButton",
                   command=self.do_import).grid(row=8, column=0, columnspan=3, pady=12, ipadx=24)

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
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件：{e}")
            return
        self.sheet_box["values"] = self.sheets
        self.sheet_var.set(self.sheets[0])
        self.preview()

    def preview(self):
        head, rows = importer.read_sheet(self.path, self.sheet_var.get(), 8, has_header=self.has_header)
        cols = [f"{i}: {h}" for i, h in enumerate(head)]
        self.word_box["values"] = cols
        self.meaning_box["values"] = cols
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
        try:
            wc = int(self.word_var.get().split(":")[0])
            mc = int(self.meaning_var.get().split(":")[0])
        except (ValueError, IndexError):
            messagebox.showwarning("提示", "请选择英文单词列和中文释义列")
            return
        try:
            n = importer.import_book(self.conn, name, self.path, self.sheet_var.get(), wc, mc,
                                     has_header=self.has_header)
            messagebox.showinfo("导入成功", f"已导入 {n} 个单词")
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror("导入失败", f"导入出错：{e}")