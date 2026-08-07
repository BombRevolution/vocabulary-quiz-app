import os, tempfile
import pytest
import sys, os.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database


@pytest.fixture()
def conn():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = database.get_conn(path)
    database.init_db(c)
    yield c
    c.close()
    os.remove(path)


def test_init_creates_tables(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"books", "words", "word_state", "daily_log", "settings"} <= names


def test_settings_roundtrip(conn):
    database.set_setting(conn, "daily_new_words", "50")
    assert database.get_setting(conn, "daily_new_words") == "50"
    assert database.get_setting(conn, "missing", "7") == "7"


def test_add_book_and_list(conn):
    bid = database.add_book(conn, "测试词库", "imported")
    books = database.list_books(conn)
    assert books[0]["name"] == "测试词库"
    assert books[0]["source"] == "imported"
    assert books[0]["word_count"] == 0


def test_insert_words_dedup(conn):
    bid = database.add_book(conn, "测试词库", "imported")
    n = database.insert_words(conn, bid, [("apple", "n. 苹果", "n"), ("apple", "n. 苹果", "n"), ("banana", "n. 香蕉", "n")])
    assert n == 2
    cnt = conn.execute("SELECT COUNT(*) FROM words WHERE book_id=?", (bid,)).fetchone()[0]
    assert cnt == 2
    wc = conn.execute("SELECT word_count FROM books WHERE id=?", (bid,)).fetchone()[0]
    assert wc == 2


def test_insert_words_creates_states(conn):
    bid = database.add_book(conn, "测试词库", "imported")
    database.insert_words(conn, bid, [("apple", "n. 苹果", "n")])
    row = conn.execute("SELECT status FROM word_state WHERE book_id=? AND word_id=(SELECT id FROM words WHERE word='apple')", (bid,)).fetchone()
    assert row[0] == "new"


def test_reset_book_progress(conn):
    bid = database.add_book(conn, "测试词库", "imported")
    database.insert_words(conn, bid, [("apple", "n. 苹果", "n"), ("banana", "n. 香蕉", "n")])
    conn.execute("UPDATE word_state SET status='poor', wrong_count=3, review_count=5, priority=8, "
                 "last_result_date='2026-08-07', next_review_date='2026-08-08', first_quiz_date='2026-08-07' "
                 "WHERE book_id=?", (bid,))
    conn.commit()
    database.reset_book_progress(conn, bid)
    rows = conn.execute("SELECT status, wrong_count, review_count, priority, last_result_date, "
                        "next_review_date, first_quiz_date FROM word_state WHERE book_id=?", (bid,)).fetchall()
    assert len(rows) == 2
    for r in rows:
        assert r["status"] == "new"
        assert r["wrong_count"] == 0
        assert r["review_count"] == 0
        assert r["priority"] == 0
        assert r["last_result_date"] is None
        assert r["next_review_date"] is None
        assert r["first_quiz_date"] is None


def test_delete_book_removes_all(conn):
    bid = database.add_book(conn, "待删除词库", "imported")
    database.insert_words(conn, bid, [("apple", "n. 苹果", "n"), ("banana", "n. 香蕉", "n")])
    conn.execute("INSERT INTO daily_log(book_id, date, new_done, correct, wrong, completed) "
                 "VALUES(?, '2026-08-07', 2, 1, 1, 0)", (bid,))
    conn.commit()
    database.delete_book(conn, bid)
    assert conn.execute("SELECT COUNT(*) FROM books WHERE id=?", (bid,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM words WHERE book_id=?", (bid,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM word_state WHERE book_id=?", (bid,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM daily_log WHERE book_id=?", (bid,)).fetchone()[0] == 0


def test_delete_book_keeps_others(conn):
    bid1 = database.add_book(conn, "词库一", "imported")
    bid2 = database.add_book(conn, "词库二", "imported")
    database.insert_words(conn, bid1, [("apple", "n. 苹果", "n")])
    database.insert_words(conn, bid2, [("banana", "n. 香蕉", "n")])
    database.delete_book(conn, bid1)
    books = database.list_books(conn)
    assert len(books) == 1
    assert books[0]["id"] == bid2
    assert conn.execute("SELECT COUNT(*) FROM words WHERE book_id=?", (bid2,)).fetchone()[0] == 1