import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitz
import pdf_export


def test_export_creates_pdf_with_words():
    words = [
        {"word": "expectation", "pos": "n", "meaning": "期望，预期"},
        {"word": "diligent", "pos": "adj", "meaning": "勤奋的"},
    ]
    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        pdf_export.export_unmastered_pdf("测试词库", words, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
        doc = fitz.open(out)
        assert len(doc) >= 1
        text = "".join(page.get_text() for page in doc)
        assert "expectation" in text
        assert "diligent" in text
        assert "期望" in text
        assert "测试词库" in text
        doc.close()
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_export_empty_words():
    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        pdf_export.export_unmastered_pdf("空词库", [], out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
        doc = fitz.open(out)
        assert len(doc) >= 1
        doc.close()
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_export_missing_fields():
    words = [{"word": "word_only"}, {"word": "", "pos": None}]
    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        pdf_export.export_unmastered_pdf("词库", words, out)
        assert os.path.exists(out)
        doc = fitz.open(out)
        text = "".join(page.get_text() for page in doc)
        assert "word_only" in text
        doc.close()
    finally:
        if os.path.exists(out):
            os.remove(out)