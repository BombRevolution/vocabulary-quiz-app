import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import database


class MainApp:
    def __init__(self, root, conn, db_path, config):
        self.root = root
        self.conn = conn
        self.db_path = db_path
        self.config = config
        root.title("单词拼写测试")
        root.geometry("760x520")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 16))
        ttk.Label(left, text="词库").pack(anchor="w")
        self.book_list = tk.Listbox(left, width=26, height=18)
        self.book_list.pack(fill="y")
        self.book_list.bind("<<ListboxSelect>>", lambda e: self.refresh())
        btn_row = ttk.Frame(left)
        btn_row.pack(fill="x", pady=6)
        ttk.Button(btn_row, text="导入词库", command=self.open_import).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="设置", command=self.open_settings).pack(side="left")

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)
        self.title = ttk.Label(right, text="", font=("", 16, "bold"))
        self.title.pack(anchor="w")
        self.stats = ttk.Label(right, text="", justify="left", font=("", 12))
        self.stats.pack(anchor="w", pady=12)
        ttk.Button(right, text="开始学习", command=self.start_quiz).pack(anchor="w", ipadx=24, ipady=8)

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
            self.stats.config(text="请先导入词库")
            return
        self.title.config(text=f"当前词库：{book['name']}")
        counts = self._state_counts(book["id"])
        txt = (f"今日新词：{counts['new_done_today']} / {self.config['daily_new_words']}\n"
               f"待复习：{counts['due']}\n"
               f"错题总数：{counts['wrong_total']}\n"
               f"已掌握：{counts['mastered']}\n"
               f"共 {book['word_count']} 词")
        self.stats.config(text=txt)

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

    def open_import(self):
        from ui_import import ImportDialog
        ImportDialog(self.root, self.conn, on_close=self.refresh)

    def open_settings(self):
        from ui_settings import SettingsDialog
        SettingsDialog(self.root, self.config, self.db_path)