import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import quiz_logic
from ui_theme import (COLOR_BG, COLOR_CARD, COLOR_CORRECT, COLOR_BLUR, COLOR_WRONG,
                      COLOR_PRIMARY, COLOR_MUTED, COLOR_TEXT, COLOR_LIGHT_BLUE,
                      font, maximize)


class QuizApp:
    def __init__(self, root, conn, book, config, on_close=None):
        self.conn = conn
        self.book = book
        self.config = config
        self.on_close = on_close
        self.today = date.today().isoformat()
        self.daily_new = int(config.get("daily_new_words", 50))
        self.retry_pool = []
        self.retry_done = set()

        self.win = tk.Toplevel(root)
        self.win.title(f"拼写测试 - {book['name']}")
        self.win.geometry("900x680")
        self.win.minsize(760, 560)
        self.win.configure(bg=COLOR_BG)
        self.win.grab_set()

        self.items = self._load_queue()
        if not self.items:
            messagebox.showinfo("提示", "今日词汇已全部完成，明天再来！")
            self.win.destroy()
            return
        self.queue = list(self.items)
        self.total = len(self.queue)
        self.idx = 0
        self.stats = {"correct": 0, "blur": 0, "wrong": 0}

        self._build_ui()
        self._show_next()
        maximize(self.win)

    def _load_queue(self):
        rows = self.conn.execute(
            "SELECT w.id, w.word, w.meaning, w.pos, ws.status, ws.next_review_date, "
            "ws.priority, ws.first_quiz_date, ws.wrong_count, ws.review_count "
            "FROM words w JOIN word_state ws ON ws.word_id=w.id AND ws.book_id=w.book_id "
            "WHERE w.book_id=? ORDER BY w.id",
            (self.book["id"],)).fetchall()
        items = []
        for r in rows:
            items.append({
                "id": r["id"], "word": r["word"], "meaning": r["meaning"], "pos": r["pos"],
                "status": r["status"], "next_review_date": r["next_review_date"],
                "priority": r["priority"], "first_quiz_date": r["first_quiz_date"],
                "wrong_count": r["wrong_count"], "review_count": r["review_count"],
            })
        ids = quiz_logic.build_queue(items, self.today, self.daily_new)
        by_id = {i["id"]: i for i in items}
        return [by_id[i] for i in ids]

    def _build_ui(self):
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(2, weight=1)

        top = tk.Frame(self.win, bg=COLOR_BG)
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        self.prog = ttk.Progressbar(top, maximum=self.total)
        self.prog.pack(fill="x")
        self.prog_label = tk.Label(top, text="", font=font(10), bg=COLOR_BG, fg=COLOR_MUTED)
        self.prog_label.pack(pady=(4, 0))

        center = tk.Frame(self.win, bg=COLOR_BG)
        center.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
        self.win.rowconfigure(1, weight=1)

        card = tk.Frame(center, bg=COLOR_CARD, highlightthickness=1, highlightbackground=COLOR_LIGHT_BLUE)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="请根据释义拼写英文单词", font=font(10), bg=COLOR_CARD,
                 fg=COLOR_MUTED).pack(pady=(20, 4))
        self.meaning_label = tk.Label(card, text="", font=font(18, bold=True), bg=COLOR_CARD, fg=COLOR_TEXT,
                                      wraplength=760, justify="center")
        self.meaning_label.pack(pady=(8, 20))

        self.entry = ttk.Entry(card, font=font(18, bold=True), justify="center")
        self.entry.pack(ipady=10, padx=40)
        self.entry.bind("<Return>", lambda e: self.submit())

        self.feedback = tk.Label(card, text="", font=font(18, bold=True), bg=COLOR_CARD)
        self.feedback.pack(pady=(20, 4))
        self.hint = tk.Label(card, text="", font=font(10), bg=COLOR_CARD, fg=COLOR_MUTED)
        self.hint.pack(pady=(0, 12))

        bottom = tk.Frame(self.win, bg=COLOR_BG)
        bottom.grid(row=2, column=0, sticky="ew", padx=20, pady=12)
        bottom.columnconfigure(0, weight=1)
        self.remain = tk.Label(bottom, text="", font=font(10), bg=COLOR_BG, fg=COLOR_MUTED)
        self.remain.grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="退出并保存", style="Secondary.TButton",
                   command=self.finish).grid(row=0, column=1, sticky="e")

    def _state(self, item):
        return self.conn.execute(
            "SELECT status, wrong_count, review_count, priority, first_quiz_date "
            "FROM word_state WHERE book_id=? AND word_id=?",
            (self.book["id"], item["id"])).fetchone()

    def _save(self, item, result):
        st = self._state(item)
        state = dict(st) if st else {"status": "new", "wrong_count": 0, "review_count": 0,
                                     "priority": 0, "first_quiz_date": None}
        new = quiz_logic.apply_result(state, result, self.today)
        self.conn.execute(
            "UPDATE word_state SET status=?, wrong_count=?, review_count=?, priority=?, "
            "first_quiz_date=?, last_result_date=?, next_review_date=? WHERE book_id=? AND word_id=?",
            (new["status"], new["wrong_count"], new["review_count"], new["priority"],
             new.get("first_quiz_date"), new.get("last_result_date"), new.get("next_review_date"),
             self.book["id"], item["id"]))
        self.conn.commit()

    def _show_next(self):
        item = self.queue[self.idx]
        self.prog["value"] = self.idx
        self.prog.configure(maximum=self.total)
        self.prog_label.config(text=f"第 {self.idx + 1} / {self.total} 题")
        self.remain.config(text=f"剩余 {self.total - self.idx} 题")
        self.meaning_label.config(text=item["meaning"])
        self.feedback.config(text="", fg=COLOR_TEXT)
        self.hint.config(text="")
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.focus_set()

    def submit(self):
        user = self.entry.get()
        if not user.strip():
            return
        item = self.queue[self.idx]
        result = quiz_logic.judge(user, item["word"], self.config.get("ignore_case", True),
                                  self.config.get("ignore_punct", False))
        self.stats[result] += 1
        self._save(item, result)
        if result == "correct":
            self.feedback.config(text=f"✓ 正确：{item['word']}", fg=COLOR_CORRECT)
        elif result == "blur":
            self.feedback.config(text=f"很接近！正确拼写是 {item['word']}", fg=COLOR_BLUR)
        else:
            self.feedback.config(text=f"✗ 错误，正确拼写是 {item['word']}", fg=COLOR_WRONG)
        if result != "correct" and item["id"] not in self.retry_done:
            self.retry_pool.append(item)
            self.hint.config(text="本词将稍后重练")
        self.entry.config(state="disabled")
        self.idx += 1
        delay = 600 if result == "correct" else 1200
        self.win.after(delay, self._advance)

    def _advance(self):
        if self.retry_pool and self.idx >= len(self.queue):
            self.retry_done.update(i["id"] for i in self.retry_pool)
            self.queue.extend(self.retry_pool)
            self.retry_pool = []
            self.total = len(self.queue)
        if self.idx >= self.total:
            self.finish()
            return
        self._show_next()

    def finish(self):
        messagebox.showinfo("本次小结",
            f"正确 {self.stats['correct']} 题，模糊 {self.stats['blur']} 题，错误 {self.stats['wrong']} 题")
        self.win.destroy()
        if self.on_close:
            self.on_close()