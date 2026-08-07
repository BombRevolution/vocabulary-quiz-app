import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import database
import pdf_export
from ui_theme import (COLOR_BG, COLOR_CARD, COLOR_PRIMARY, COLOR_LIGHT_BLUE, COLOR_TEXT,
                      COLOR_MUTED, font, center_window, fit_and_center)


class WrongWordsDialog(tk.Toplevel):
    def __init__(self, root, conn, book):
        super().__init__(root)
        self.conn = conn
        self.book = book
        self.title(f"不熟练词整理 - {book['name']}")
        self.geometry("900x680")
        self.minsize(760, 560)
        self.resizable(True, True)
        self.configure(bg=COLOR_BG)
        self.grab_set()

        main = tk.Frame(self, bg=COLOR_BG, padx=20, pady=16)
        main.pack(fill="both", expand=True)

        self.words = database.list_unmastered_words(conn, book["id"])
        tk.Label(main, text=f"不熟练词整理 - {book['name']}", font=font(17, bold=True),
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(anchor="w")
        tk.Label(main, text=f"共 {len(self.words)} 个不熟练词（含不会/模糊）",
                 font=font(12), bg=COLOR_BG, fg=COLOR_MUTED).pack(anchor="w", pady=(4, 12))

        card = tk.Frame(main, bg=COLOR_CARD, highlightthickness=1, highlightbackground=COLOR_LIGHT_BLUE)
        card.pack(fill="both", expand=True)
        body = tk.Frame(card, bg=COLOR_CARD)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        columns = ("word", "pos", "meaning")
        self.tree = ttk.Treeview(body, show="headings", columns=columns)
        self.tree.heading("word", text="单词")
        self.tree.heading("pos", text="词性")
        self.tree.heading("meaning", text="中文释义")
        self.tree.column("word", width=180, anchor="w")
        self.tree.column("pos", width=80, anchor="center")
        self.tree.column("meaning", width=420, anchor="w")
        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        for w in self.words:
            self.tree.insert("", "end", values=(w["word"], w["pos"], w["meaning"]))

        if not self.words:
            tk.Label(main, text="当前词库没有不熟练词，太棒了！",
                     font=font(13), bg=COLOR_BG, fg=COLOR_MUTED).pack(pady=20)

        btn_row = tk.Frame(main, bg=COLOR_BG)
        btn_row.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_row, text="导出 PDF", style="Primary.TButton",
                   command=self.export_pdf).pack(side="right")
        ttk.Button(btn_row, text="关闭", style="Secondary.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))

        fit_and_center(self, 900, 680)

    def export_pdf(self):
        if not self.words:
            messagebox.showinfo("提示", "当前词库没有不熟练词，无需导出")
            return
        path = filedialog.asksaveasfilename(
            title="导出不熟练词 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf")],
            initialfile=f"不熟练词整理-{self.book['name']}.pdf")
        if not path:
            return
        try:
            pdf_export.export_unmastered_pdf(self.book["name"], self.words, path)
        except Exception as e:
            messagebox.showerror("导出失败", f"导出 PDF 出错：{e}")
            return
        messagebox.showinfo("导出成功", f"已导出 {len(self.words)} 个不熟练词到：\n{path}")