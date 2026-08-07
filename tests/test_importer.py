import os, sys, tempfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database, importer

CSV_CONTENT = "word,meaning\napple,n. 苹果。\nbanana,n. 香蕉\norange,a. 橙色的\n"


@pytest.fixture()
def csv_path():
    fd, p = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
        f.write(CSV_CONTENT)
    return p


@pytest.fixture()
def conn():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = database.get_conn(path)
    database.init_db(c)
    yield c
    c.close()
    os.remove(path)


def test_clean_meaning_removes_period_and_extracts_pos():
    m, pos = importer.clean_meaning("v. 分，划分。")
    assert m == "v. 分，划分"
    assert pos == "v"


def test_clean_meaning_handles_bracket_pos():
    m, pos = importer.clean_meaning("n[化].硫化物。")
    assert pos == "n"
    assert "硫化物" in m


def test_read_sheet_csv(csv_path):
    tables = importer.detect_excel(csv_path)
    head = importer.read_sheet(csv_path, tables[0], 3)
    headers, rows = head
    assert headers[0] == "word"
    assert len(rows) == 3


def test_import_book_csv(conn, csv_path):
    n = importer.import_book(conn, "我的词库", csv_path, importer.detect_excel(csv_path)[0], 0, 1)
    assert n == 3
    books = database.list_books(conn)
    assert books[-1]["name"] == "我的词库"
    assert books[-1]["word_count"] == 3