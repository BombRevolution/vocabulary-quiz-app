import os
from datetime import date

import fitz

CN_FONT = "simhei.ttf"


def _font_path(name):
    return os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)


def export_unmastered_pdf(book_name, words, out_path):
    doc = fitz.open()
    page_width, page_height = 595.0, 842.0
    margin = 48.0
    content_width = page_width - margin * 2
    y = margin

    def new_page():
        p = doc.new_page(width=page_width, height=page_height)
        p.insert_text(
            (margin, margin - 18),
            f"不熟练词整理 - {book_name}",
            fontsize=14,
            fontname="china-s",
            fontfile=_font_path(CN_FONT),
            color=(0.16, 0.42, 0.69),
        )
        p.insert_text(
            (page_width - margin, margin - 18),
            str(date.today()),
            fontsize=10,
            fontname="china-s",
            fontfile=_font_path(CN_FONT),
            color=(0.44, 0.56, 0.59),
        )
        return p

    page = new_page()
    for w in words:
        word = w.get("word", "")
        pos = w.get("pos", "")
        meaning = w.get("meaning", "")
        title = word + (("  " + pos) if pos else "")
        title_rect = fitz.Rect(margin, y, page_width - margin, y + 40)
        page.insert_textbox(
            title_rect,
            title,
            fontsize=16,
            fontname="china-s",
            fontfile=_font_path(CN_FONT),
            color=(0.10, 0.13, 0.19),
        )
        y += 26
        if meaning:
            meaning_rect = fitz.Rect(margin, y, page_width - margin, y + 60)
            used = page.insert_textbox(
                meaning_rect,
                meaning,
                fontsize=12,
                fontname="china-s",
                fontfile=_font_path(CN_FONT),
                color=(0.30, 0.32, 0.36),
            )
            y += 30
        y += 8
        page.draw_line(
            fitz.Point(margin, y),
            fitz.Point(page_width - margin, y),
            color=(0.85, 0.89, 0.93),
            width=0.7,
        )
        y += 18
        if y > page_height - margin - 60:
            page = new_page()
            y = margin + 20

    doc.save(out_path)
    doc.close()