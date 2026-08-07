import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk
from datetime import date, timedelta
import pytest
import database
import ui_quiz
import ui_theme

ui_quiz.messagebox.showinfo = lambda *a, **k: None
ui_quiz.messagebox.askyesno = lambda *a, **k: None


@pytest.fixture()
def quiz_app():
    db_path = "vocab_test_ui_pytest.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = database.get_conn(db_path)
    database.init_db(conn)
    bid = database.add_book(conn, "TEST", "imported")
    database.insert_words(conn, bid, [
        ("apple", "n. 苹果", "n"),
        ("banana", "n. 香蕉", "n"),
        ("cat", "n. 猫", "n"),
    ])
    cfg = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
           "hint_mode": "reveal", "hint_percent": 30,
           "key_skip": "<Control-d>", "key_hint": "<Control-space>"}
    root = tk.Tk()
    ui_theme.apply_theme(root)
    root.withdraw()
    book = database.list_books(conn)[0]
    qa = ui_quiz.QuizApp(root, conn, book, cfg)
    yield qa
    try:
        qa.win.destroy()
    except Exception:
        pass
    root.destroy()
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_submit_ignored_while_disabled(quiz_app):
    qa = quiz_app
    first = qa.queue[qa.idx]["word"]
    total_before = qa.stats["wrong"]
    qa.entry.insert(0, "zzz" + first)
    qa.submit()
    assert qa.stats["wrong"] == total_before + 1
    assert str(qa.entry.cget("state")) == "disabled"
    second_word = qa.queue[qa.idx]["word"]
    wrong_before = qa.stats["wrong"]
    correct_before = qa.stats["correct"]
    qa.entry.insert(0, second_word)
    qa.submit()
    assert qa.stats["wrong"] == wrong_before
    assert qa.stats["correct"] == correct_before


def test_skip_marks_mastered(quiz_app):
    qa = quiz_app
    item = qa.queue[qa.idx]
    correct_before = qa.stats["correct"]
    blur_before = qa.stats["blur"]
    wrong_before = qa.stats["wrong"]
    skipped_before = qa.stats.get("skipped", 0)
    qa.skip()
    row = qa.conn.execute(
        "SELECT status, next_review_date FROM word_state WHERE book_id=? AND word_id=?",
        (qa.book["id"], item["id"])).fetchone()
    assert row[0] == "mastered"
    expected = (date.fromisoformat(qa.today) + timedelta(days=30)).isoformat()
    assert row[1] == expected
    assert qa.stats["correct"] == correct_before
    assert qa.stats["blur"] == blur_before
    assert qa.stats["wrong"] == wrong_before
    assert qa.stats.get("skipped", 0) == skipped_before + 1


def test_hint_used_correct_counts_as_blur(quiz_app):
    qa = quiz_app
    item = qa.queue[qa.idx]
    qa.hint_used.add(item["id"])
    qa.entry.insert(0, item["word"])
    qa.submit()
    assert qa.stats["blur"] == 1
    row = qa.conn.execute(
        "SELECT status FROM word_state WHERE book_id=? AND word_id=?",
        (qa.book["id"], item["id"])).fetchone()
    assert row[0] == "blur"


def test_skip_hotkey_bound(quiz_app):
    qa = quiz_app
    bindings = qa.entry.bind() or ()
    assert "<Control-Key-d>" in bindings
    assert "<Control-Key-space>" in bindings