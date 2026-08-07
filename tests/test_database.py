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