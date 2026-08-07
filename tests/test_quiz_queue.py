import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quiz_logic import build_queue

T = "2026-08-07"


def item(i, status, nrd=None, prio=0, fqd=None):
    return {"id": i, "status": status, "next_review_date": nrd, "priority": prio, "first_quiz_date": fqd}


def test_review_words_first():
    items = [
        item(1, "new", None, 0, None),
        item(2, "poor", "2026-08-07", 10, T),
        item(3, "good", "2026-08-06", 3, T),
    ]
    q = build_queue(items, T, 50)
    assert q[0] == 2
    assert 3 in q


def test_due_review_only():
    items = [
        item(2, "poor", "2026-08-07", 10, T),
        item(3, "good", "2026-08-10", 3, T),
    ]
    q = build_queue(items, T, 50)
    assert q == [2]


def test_new_words_limited_by_daily():
    items = [item(i, "new", None, 0, None) for i in range(1, 11)]
    q = build_queue(items, T, 4)
    assert len(q) == 4


def test_new_words_exclude_today_done():
    items = [
        item(1, "new", None, 0, None),
        item(2, "new", None, 0, T),
    ]
    q = build_queue(items, T, 5)
    assert 2 not in q
    assert 1 in q


def test_priority_order_desc():
    items = [
        item(1, "poor", "2026-08-07", 5, T),
        item(2, "poor", "2026-08-07", 20, T),
        item(3, "poor", "2026-08-07", 2, T),
    ]
    q = build_queue(items, T, 0)
    assert q == [2, 1, 3]


def test_empty():
    assert build_queue([], T, 50) == []
