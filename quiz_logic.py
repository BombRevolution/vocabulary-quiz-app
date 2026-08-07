import re
import math
import unicodedata
import random
from datetime import date, timedelta

REVIEW_INTERVALS = {"poor": 1, "blur": 3, "good": 7, "mastered": 30}


def next_review_date(status, today):
    d = date.fromisoformat(today) + timedelta(days=REVIEW_INTERVALS[status])
    return d.isoformat()


def apply_result(state, result, today):
    s = dict(state)
    s["review_count"] = s.get("review_count", 0) + 1
    if s.get("first_quiz_date") is None and result != "correct":
        s["first_quiz_date"] = today
    if result == "correct":
        if s["status"] == "new":
            s["status"] = "good"
        elif s["status"] == "poor":
            s["status"] = "blur"
        elif s["status"] == "blur":
            s["status"] = "good"
        elif s["status"] == "good":
            s["status"] = "mastered"
        s["priority"] = max(0, s.get("priority", 0) - 1)
        if s.get("first_quiz_date") is None:
            s["first_quiz_date"] = today
    elif result == "blur":
        s["status"] = "blur"
        s["priority"] = s.get("priority", 0) + 2
    else:
        old = s["status"]
        s["status"] = "poor"
        s["wrong_count"] = s.get("wrong_count", 0) + 1
        s["priority"] = s.get("priority", 0) + 5
        if old == "new":
            s["first_quiz_date"] = today
    s["last_result_date"] = today
    s["next_review_date"] = next_review_date(s["status"], today)
    return s


def build_queue(items, today, daily_new):
    due = [i for i in items
           if i["status"] in ("poor", "blur", "good")
           and i.get("next_review_date") and i["next_review_date"] <= today]
    due.sort(key=lambda i: i["priority"], reverse=True)
    fresh = [i for i in items if i["status"] == "new" and i.get("first_quiz_date") != today]
    random.shuffle(fresh)
    fresh = fresh[:daily_new]
    queue, r, f = [], 0, 0
    while r < len(due) or f < len(fresh):
        if r < len(due):
            queue.append(due[r]["id"])
            r += 1
        if f < len(fresh):
            queue.append(fresh[f]["id"])
            f += 1
    return queue


def normalize(text, ignore_case, ignore_punct):
    s = unicodedata.normalize("NFKC", str(text)).strip()
    if ignore_punct:
        s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]", "", s)
    if ignore_case:
        s = s.lower()
    return s


def edit_distance(a, b):
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i]
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[n]


def judge(user_input, correct, ignore_case, ignore_punct):
    u = normalize(user_input, ignore_case, ignore_punct)
    c = normalize(correct, ignore_case, ignore_punct)
    if u == c:
        return "correct"
    if edit_distance(u, c) == 1:
        return "blur"
    return "wrong"


def reveal_mask(word, percent):
    p = max(0, min(100, percent))
    n = math.ceil(len(word) * p / 100)
    return word[:n] + "_" * (len(word) - n)