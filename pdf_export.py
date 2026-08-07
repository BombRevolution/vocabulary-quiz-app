from datetime import date
import os

import fitz


def _font_path(name):
    return os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)


PAGE_W, PAGE_H = 595.0, 842.0
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 36.0, 46.0, 36.0
GUTTER = 12.0
COLS = 3
CONTENT_W = PAGE_W - 2 * MARGIN_X
COL_W = (CONTENT_W - (COLS - 1) * GUTTER) / COLS

WORD_SIZE = 12.0
MEAN_SIZE = 11.0
WORD_H = 15.0
MEAN_LH = 13.5
ROW_GAP = 6.0


def _wrap(text, font, fontsize, max_width):
    lines = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if font.text_length(cur + ch, fontsize=fontsize) > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur or not lines:
        lines.append(cur)
    return lines


def export_unmastered_pdf(book_name, words, out_path):
    doc = fitz.open()
    zh_path = _font_path("simhei.ttf")
    zh_font = fitz.Font(fontfile=zh_path)

    def new_page():
        p = doc.new_page(width=PAGE_W, height=PAGE_H)
        p.insert_text(
            (MARGIN_X, 28),
            f"不熟练词整理 - {book_name}",
            fontsize=12,
            fontname="zh",
            fontfile=zh_path,
            color=(0.16, 0.42, 0.69),
        )
        date_str = str(date.today())
        date_w = fitz.get_text_length(date_str, fontname="helv", fontsize=9)
        p.insert_text(
            (PAGE_W - MARGIN_X - date_w, 28),
            date_str,
            fontsize=9,
            fontname="helv",
            color=(0.44, 0.56, 0.59),
        )
        return p

    entries = []
    for w in words:
        word = w.get("word") or ""
        pos = w.get("pos") or ""
        meaning = w.get("meaning") or ""
        title = word + (("  " + pos) if pos else "")
        mean_lines = _wrap(meaning, zh_font, MEAN_SIZE, COL_W) if meaning else []
        height = WORD_H + len(mean_lines) * MEAN_LH
        entries.append((title, mean_lines, height))

    page = new_page()
    y = MARGIN_TOP
    i = 0
    n = len(entries)
    while i < n:
        row = entries[i:i + COLS]
        row_h = max(e[2] for e in row)
        if y + row_h > PAGE_H - MARGIN_BOTTOM:
            page = new_page()
            y = MARGIN_TOP
        for c, (title, mean_lines, _h) in enumerate(row):
            x = MARGIN_X + c * (COL_W + GUTTER)
            page.insert_text(
                (x, y + WORD_SIZE),
                title,
                fontsize=WORD_SIZE,
                fontname="helv",
                color=(0.10, 0.13, 0.19),
            )
            my = y + WORD_H + MEAN_SIZE
            for line in mean_lines:
                page.insert_text(
                    (x, my),
                    line,
                    fontsize=MEAN_SIZE,
                    fontname="zh",
                    fontfile=zh_path,
                    color=(0.30, 0.32, 0.36),
                )
                my += MEAN_LH
        y += row_h + ROW_GAP
        i += COLS

    doc.save(out_path)
    doc.close()