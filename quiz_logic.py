import re
import unicodedata


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