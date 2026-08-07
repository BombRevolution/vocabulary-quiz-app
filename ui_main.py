import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import database
from ui_theme import (COLOR_BG, COLOR_CARD, COLOR_LIGHT_BLUE, COLOR_PRIMARY, COLOR_MUTED,
                      COLOR_TEXT, font, maximize)


class MainApp:
    def __init__(self, root, conn, db_path, config):
        self.root = root
        self.conn = conn
        self.db_path = db_path
        self.config = config
        root.title("单词拼写测试")
        root.geometry("1100x760")
        root.minsize(900, 640)
        root.configure(bg=COLOR_BG)
        self._build_ui()
        self.refresh()
        maximize(root)

    def _build_ui(self):
        main = tk.Frame(self.root, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=16)

        left = tk.Frame(main, bg=COLOR_BG)
        left.pack(side="left", fill="y", padx=(0, 20))
        tk.Label(left, text="词库", font=font(16, bold=True), bg=COLOR_BG, fg=COLOR_PRIMARY).pack(anchor="w")
        self.book_list = tk.Listbox(left, width=28, height=16, font=font(12),
                                    bg=COLOR_CARD, fg=COLOR_TEXT, selectbackground=COLOR_LIGHT_BLUE,
                                    selectforeground=COLOR_PRIMARY, highlightthickness=1,
                                    highlightbackground=COLOR_LIGHT_BLUE, relief="flat", bd=0)
        self.book_list.pack(fill="y", pady=8)
        self.book_list.bind("<<ListboxSelect>>", lambda e: self.refresh())

        btn_col = tk.Frame(left, bg=COLOR_BG)
        btn_col.pack(fill="x")
        ttk.Button(btn_col, text="导入词库", style="Secondary.TButton",
                   command=self.open_import).pack(fill="x", pady=(0, 6))
        ttk.Button(btn_col, text="重置进度", style="Danger.TButton",
                   command=self.reset_progress).pack(fill="x", pady=(0, 6))
        ttk.Button(btn_col, text="设置", style="Secondary.TButton",
                   command=self.open_settings).pack(fill="x")

        right = tk.Frame(main, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True)

        self.title = tk.Label(right, text="", font=font(16, bold=True), bg=COLOR_BG, fg=COLOR_TEXT)
        self.title.pack(anchor="w", pady=(0, 12))

        card = tk.Frame(right, bg=COLOR_CARD, highlightthickness=1, highlightbackground=COLOR_LIGHT_BLUE)
        card.pack(fill="both", expand=False, pady=(0, 16))

        stat_grid = tk.Frame(card, bg=COLOR_CARD)
        stat_grid.pack(fill="x", padx=16, pady=16)
        self._stat_cells = {}
        names = [("new_done_today", "今日新词"), ("due", "待复习"), ("wrong_total", "错题总数"),
                 ("mastered", "已掌握"), ("word_total", "词库词数")]
        for i, (key, label) in enumerate(names):
            cell = tk.Frame(stat_grid, bg=COLOR_CARD)
            cell.grid(row=0, column=i, padx=12, sticky="nsew")
            stat_grid.columnconfigure(i, weight=1)
            tk.Label(cell, text="—", font=font(20, bold=True), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack()
            tk.Label(cell, text=label, font=font(10), bg=COLOR_CARD, fg=COLOR_MUTED).pack()
            self._stat_cells[key] = cell.winfo_children()[0]

        start_btn = ttk.Button(right, text="开始学习", style="Primary.TButton", command=self.start_quiz)
        start_btn.pack(anchor="w", ipadx=28, ipady=10)

    def current_book(self):
        sel = self.book_list.curselection()
        if not sel:
            return None
        return self.books[sel[0]]

    def refresh(self):
        self.books = database.list_books(self.conn)
        self.book_list.delete(0, "end")
        for b in self.books:
            self.book_list.insert("end", f"{b['name']}（{b['word_count']}词）")
        if self.books:
            self.book_list.selection_set(0)
        self.update_stats()

    def update_stats(self):
        book = self.current_book()
        if not book:
            self.title.config(text="暂无词库")
            for w in self._stat_cells.values():
                w.config(text="—")
            return
        self.title.config(text=f"当前词库：{book['name']}")
        counts = self._state_counts(book["id"])
        values = {"new_done_today": f"{counts['new_done_today']} / {self.config['daily_new_words']}",
                  "due": str(counts["due"]), "wrong_total": str(counts["wrong_total"]),
                  "mastered": str(counts["mastered"]), "word_total": str(book["word_count"])}
        for key, val in values.items():
            self._stat_cells[key].config(text=val)

    def _state_counts(self, book_id):
        due_rows = self.conn.execute(
            "SELECT COUNT(*) c FROM word_state ws JOIN words w ON w.id=ws.word_id "
            "WHERE ws.book_id=? AND ws.status IN ('poor','blur','good') "
            "AND ws.next_review_date IS NOT NULL AND ws.next_review_date<=date('now','localtime')",
            (book_id,)).fetchone()
        wrong = self.conn.execute(
            "SELECT COALESCE(SUM(ws.wrong_count),0) FROM word_state ws WHERE ws.book_id=?",
            (book_id,)).fetchone()[0]
        mast = self.conn.execute(
            "SELECT COUNT(*) FROM word_state WHERE book_id=? AND status='mastered'",
            (book_id,)).fetchone()[0]
        new_done = self.conn.execute(
            "SELECT COUNT(*) FROM word_state WHERE book_id=? AND first_quiz_date=date('now','localtime')",
            (book_id,)).fetchone()[0]
        return {"due": due_rows["c"], "wrong_total": wrong, "mastered": mast, "new_done_today": new_done}

    def start_quiz(self):
        book = self.current_book()
        if not book:
            return
        from ui_quiz import QuizApp
        QuizApp(self.root, self.conn, book, self.config, on_close=self.refresh)

    def reset_progress(self):
        book = self.current_book()
        if not book:
            return
        ok = messagebox.askyesno("重置进度",
            f"确定要重置「{book['name']}」的全部学习进度吗？\n\n"
            "所有单词将回到未学习状态，错题记录和掌握情况将清空。\n此操作不可撤销。")
        if not ok:
            return
        database.reset_book_progress(self.conn, book["id"])
        messagebox.showinfo("已重置", f"「{book['name']}」的学习进度已重置。")
        self.refresh()

    def open_import(self):
        from ui_import import ImportDialog
        ImportDialog(self.root, self.conn, on_close=self.refresh)

    def open_settings(self):
        from ui_settings import SettingsDialog
        SettingsDialog(self.root, self.config, self.db_path)