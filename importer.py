import re
import pandas as pd
import database


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