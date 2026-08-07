import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    word_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    word TEXT NOT NULL,
    meaning TEXT NOT NULL,
    pos TEXT DEFAULT '',
    UNIQUE(book_id, word)
);
CREATE TABLE IF NOT EXISTS word_state (
    book_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    status TEXT DEFAULT 'new',
    wrong_count INTEGER DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    last_result_date TEXT,
    next_review_date TEXT,
    first_quiz_date TEXT,
    priority INTEGER DEFAULT 0,
    PRIMARY KEY(book_id, word_id)
);
CREATE TABLE IF NOT EXISTS daily_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    new_done INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    wrong INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def get_setting(conn, key, default=""):
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(conn, key, value):
    conn.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                 "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    conn.commit()


def add_book(conn, name, source):
    cur = conn.execute("INSERT INTO books(name, source) VALUES(?,?)", (name, source))
    conn.commit()
    return cur.lastrowid


def list_books(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM books ORDER BY id").fetchall()]


def insert_words(conn, book_id, words):
    inserted = 0
    for word, meaning, pos in words:
        if not word or not str(word).strip():
            continue
        w = str(word).strip()
        cur = conn.execute("INSERT OR IGNORE INTO words(book_id, word, meaning, pos) VALUES(?,?,?,?)",
                           (book_id, w, str(meaning).strip(), pos))
        if cur.rowcount == 0:
            continue
        wid = cur.lastrowid
        conn.execute("INSERT OR IGNORE INTO word_state(book_id, word_id) VALUES(?,?)", (book_id, wid))
        inserted += 1
    conn.execute("UPDATE books SET word_count = word_count + ? WHERE id=?", (inserted, book_id))
    conn.commit()
    return inserted


def reset_book_progress(conn, book_id):
    conn.execute(
        "UPDATE word_state SET status='new', wrong_count=0, review_count=0, priority=0, "
        "last_result_date=NULL, next_review_date=NULL, first_quiz_date=NULL WHERE book_id=?",
        (book_id,))
    conn.commit()


def delete_book(conn, book_id):
    try:
        conn.execute("DELETE FROM daily_log WHERE book_id=?", (book_id,))
        conn.execute("DELETE FROM word_state WHERE book_id=?", (book_id,))
        conn.execute("DELETE FROM words WHERE book_id=?", (book_id,))
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
