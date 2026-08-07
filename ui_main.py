import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import database
from ui_theme import (COLOR_BG, COLOR_CARD, COLOR_LIGHT_BLUE, COLOR_PRIMARY, COLOR_MUTED,
                      COLOR_TEXT, COLOR_WRONG, font, maximize)


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
        tk.Label(left, text="词库", font=font(17, bold=True), bg=COLOR_BG, fg=COLOR_PRIMARY).pack(anchor="w")
        self.book_list = tk.Listbox(left, width=28, height=16, font=font(14),
                                    bg=COLOR_CARD, fg=COLOR_TEXT, selectbackground=COLOR_LIGHT_BLUE,
                                    selectforeground=COLOR_PRIMARY, highlightthickness=1,
                                    highlightbackground=COLOR_LIGHT_BLUE, relief="flat", bd=0)
        self.book_list.pack(fill="both", expand=True, pady=8)
        self.book_list.bind("<<ListboxSelect>>", lambda e: self.refresh())

        btn_col = tk.Frame(left, bg=COLOR_BG)
        btn_col.pack(fill="x")
        ttk.Button(btn_col, text="导入词库", style="Secondary.TButton",
                   command=self.open_import).pack(fill="x", pady=(0, 6))
        ttk.Button(btn_col, text="重置进度", style="Danger.TButton",
                   command=self.reset_progress).pack(fill="x", pady=(0, 6))
        ttk.Button(btn_col, text="删除词库", style="Danger.TButton",
                   command=self.delete_book).pack(fill="x", pady=(0, 6))
        ttk.Button(btn_col, text="设置", style="Secondary.TButton",
                   command=self.open_settings).pack(fill="x")

        right = tk.Frame(main, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True)
        right.columnconfigure(0, weight=1)

        self.title = tk.Label(right, text="", font=font(17, bold=True), bg=COLOR_BG, fg=COLOR_TEXT)
        self.title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        card = tk.Frame(right, bg=COLOR_CARD, highlightthickness=1, highlightbackground=COLOR_LIGHT_BLUE)
        card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        stat_grid = tk.Frame(card, bg=COLOR_CARD)
        stat_grid.pack(fill="x", padx=16, pady=16)
        self._stat_cells = {}
        names = [("new_done_today", "今日新词"), ("due", "待复习"), ("wrong_total", "错题总数"),
                 ("mastered", "已掌握"), ("word_total", "词库词数")]
        for i, (key, label) in enumerate(names):
            cell = tk.Frame(stat_grid, bg=COLOR_LIGHT_BLUE, highlightthickness=1,
                            highlightbackground=COLOR_LIGHT_BLUE)
            cell.grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            stat_grid.columnconfigure(i, weight=1)
            tk.Label(cell, text="—", font=font(24, bold=True), bg=COLOR_LIGHT_BLUE,
                     fg=COLOR_PRIMARY).pack(pady=(10, 2))
            tk.Label(cell, text=label, font=font(11), bg=COLOR_LIGHT_BLUE,
                     fg=COLOR_MUTED).pack(pady=(0, 10))
            self._stat_cells[key] = cell.winfo_children()[0]

        start_btn = ttk.Button(right, text="开始学习", style="Primary.TButton", command=self.start_quiz)
        start_btn.grid(row=2, column=0, ipadx=40, ipady=12, pady=(0, 12))

        lists = tk.Frame(right, bg=COLOR_BG)
        lists.grid(row=3, column=0, sticky="nsew")
        right.rowconfigure(3, weight=1)
        lists.rowconfigure(0, weight=1)
        lists.columnconfigure(0, weight=1)
        lists.columnconfigure(1, weight=1)

        self._build_list_card(lists, 0, "近期错题", self._load_wrong_words, "wrong")
        self._build_list_card(lists, 1, "今日待复习", self._load_due_words, "due")

    def _build_list_card(self, parent, col, tag, loader, tree_attr):
        card = tk.Frame(parent, bg=COLOR_CARD, highlightthickness=1, highlightbackground=COLOR_LIGHT_BLUE)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 6 if col == 0 else 0))
        tk.Label(card, text=tag, font=font(14, bold=True), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", padx=12, pady=(10, 4))
        body = tk.Frame(card, bg=COLOR_CARD)
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        tree = ttk.Treeview(body, height=8, show="headings", columns=("word", "meaning"))
        tree.heading("word", text="单词")
        tree.heading("meaning", text="释义")
        tree.column("word", width=120, anchor="w")
        tree.column("meaning", width=220, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        empty = tk.Label(body, text="暂无数据", font=font(11), bg=COLOR_CARD, fg=COLOR_MUTED)
        empty.grid(row=0, column=0)
        setattr(self, tree_attr + "_empty", empty)
        setattr(self, tree_attr + "_tree", tree)
        setattr(self, tree_attr + "_card", card)

    def _load_wrong_words(self, book_id, limit=8):
        rows = self.conn.execute(
            "SELECT w.word, w.meaning FROM words w JOIN word_state ws ON ws.word_id=w.id AND ws.book_id=w.book_id "
            "WHERE w.book_id=? AND ws.wrong_count>0 ORDER BY ws.wrong_count DESC, ws.last_result_date DESC LIMIT ?",
            (book_id, limit)).fetchall()
        return [(r["word"], r["meaning"]) for r in rows]

    def _load_due_words(self, book_id, limit=8):
        rows = self.conn.execute(
            "SELECT w.word, w.meaning FROM words w JOIN word_state ws ON ws.word_id=w.id AND ws.book_id=w.book_id "
            "WHERE w.book_id=? AND ws.status IN ('poor','blur','good') "
            "AND ws.next_review_date IS NOT NULL AND ws.next_review_date<=date('now','localtime') "
            "ORDER BY ws.priority DESC LIMIT ?",
            (book_id, limit)).fetchall()
        return [(r["word"], r["meaning"]) for r in rows]

    def _fill_list_tree(self, tree, empty_label, data):
        tree.delete(*tree.get_children())
        if not data:
            tree.grid_forget()
            empty_label.grid(row=0, column=0)
            return
        empty_label.grid_forget()
        tree.grid(row=0, column=0, sticky="nsew")
        for word, meaning in data:
            tree.insert("", "end", values=(word, meaning))

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
            self.title.config(text="暂无词库，请先导入词库")
            for w in self._stat_cells.values():
                w.config(text="—")
            self._fill_list_tree(self.wrong_tree, self.wrong_empty, [])
            self._fill_list_tree(self.due_tree, self.due_empty, [])
            return
        self.title.config(text=f"当前词库：{book['name']}")
        counts = self._state_counts(book["id"])
        values = {"new_done_today": f"{counts['new_done_today']} / {self.config['daily_new_words']}",
                  "due": str(counts["due"]), "wrong_total": str(counts["wrong_total"]),
                  "mastered": str(counts["mastered"]), "word_total": str(book["word_count"])}
        for key, val in values.items():
            self._stat_cells[key].config(text=val)
        self._fill_list_tree(self.wrong_tree, self.wrong_empty, self._load_wrong_words(book["id"]))
        self._fill_list_tree(self.due_tree, self.due_empty, self._load_due_words(book["id"]))

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
            messagebox.showinfo("提示", "请先导入词库")
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

    def delete_book(self):
        book = self.current_book()
        if not book:
            return
        ok = messagebox.askyesno("删除词库",
            f"确定要删除「{book['name']}」词库吗？\n\n"
            "该词库的所有单词和学习进度将被永久删除。\n此操作不可恢复！")
        if not ok:
            return
        database.delete_book(self.conn, book["id"])
        messagebox.showinfo("已删除", f"「{book['name']}」词库已删除。")
        self.refresh()

    def open_import(self):
        from ui_import import ImportDialog
        ImportDialog(self.root, self.conn, on_close=self.refresh)

    def open_settings(self):
        from ui_settings import SettingsDialog
        SettingsDialog(self.root, self.config, self.db_path)