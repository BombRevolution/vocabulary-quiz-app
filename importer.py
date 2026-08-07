import re
import pandas as pd
import database

HEADER_WORDS = {"word", "words", "english", "单词", "英文", "词汇", "meaning", "meaning(s)",
                "释义", "中文", "对应", "序号", "id", "no", "no.", "index", "position"}


def detect_excel(path):
    if path.lower().endswith(".csv"):
        return ["sheet1"]
    xl = pd.ExcelFile(path)
    return xl.sheet_names


def _read(path, sheet, has_header):
    header = 0 if has_header else None
    if path.lower().endswith(".csv"):
        return pd.read_csv(path, header=header)
    return pd.read_excel(path, sheet_name=sheet, header=header)


def read_sheet(path, sheet, head_n=10, has_header=True):
    df = _read(path, sheet, has_header)
    headers = [str(c) for c in df.columns]
    rows = df.head(head_n).fillna("").astype(str).values.tolist()
    return headers, rows


def _score_word(s):
    return 1 if re.match(r"^[A-Za-z][A-Za-z\s\-'．.]*$", s) else 0


def _score_meaning(s):
    return 1 if re.search(r"[\u4e00-\u9fff]", s) else 0


def auto_detect(path):
    if path.lower().endswith(".csv"):
        sheet = "sheet1"
        df = pd.read_csv(path, header=None)
    else:
        sheet = pd.ExcelFile(path).sheet_names[0]
        df = pd.read_excel(path, sheet_name=sheet, header=None)
    df = df.fillna("")
    head_rows = df.head(10).astype(str)

    n_cols = len(df.columns)
    first_is_header = False
    if n_cols > 0:
        first_cells = [str(head_rows.iloc[0, c]).strip().lower() for c in range(n_cols)]
        if any(c in HEADER_WORDS or c.strip().rstrip(".") in HEADER_WORDS for c in first_cells):
            first_is_header = True

    data_offset = 1 if first_is_header else 0
    word_scores = [0] * n_cols
    meaning_scores = [0] * n_cols
    for _, row in head_rows.iterrows():
        for c in range(n_cols):
            s = str(row.iloc[c]).strip()
            word_scores[c] += _score_word(s)
            meaning_scores[c] += _score_meaning(s)
    if data_offset > 0:
        for c in range(n_cols):
            s = str(head_rows.iloc[0, c]).strip()
            if s:
                word_scores[c] -= _score_word(s)
                meaning_scores[c] -= _score_meaning(s)

    word_col = max(range(n_cols), key=lambda i: word_scores[i]) if word_scores else 0
    meaning_col = max(range(n_cols), key=lambda i: meaning_scores[i]) if meaning_scores else 0
    if word_col == meaning_col and n_cols > 1:
        meaning_col = 0 if meaning_scores[0] >= meaning_scores[1] else 1 if n_cols > 1 else word_col

    return {"sheet": sheet, "word_col": word_col, "meaning_col": meaning_col,
            "has_header": first_is_header}


def clean_meaning(raw):
    m = str(raw).strip()
    m = re.sub(r"[.。]+\s*$", "", m)
    pos_match = re.search(r"([a-z]+)(?:\[[^\]]*\])?\s*[.．]", m)
    pos = pos_match.group(1) if pos_match else ""
    return m, pos


def load_words(path, sheet, word_col, meaning_col, has_header=True):
    df = _read(path, sheet, has_header)
    out = []
    for _, row in df.iterrows():
        w = row.iloc[word_col]
        m = row.iloc[meaning_col]
        if w is None or str(w).strip() == "":
            continue
        out.append((str(w).strip(), str(m) if m is not None else ""))
    return out


def import_book(conn, name, path, sheet, word_col, meaning_col, has_header=True):
    rows = load_words(path, sheet, word_col, meaning_col, has_header)
    cleaned = []
    for w, m in rows:
        cm, pos = clean_meaning(m)
        cleaned.append((w, cm, pos))
    bid = database.add_book(conn, name, "imported")
    return database.insert_words(conn, bid, cleaned)