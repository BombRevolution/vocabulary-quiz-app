import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quiz_logic import next_review_date, apply_result

T = "2026-08-07"


def test_review_intervals():
    assert next_review_date("poor", T) == "2026-08-08"
    assert next_review_date("blur", T) == "2026-08-10"
    assert next_review_date("good", T) == "2026-08-14"
    assert next_review_date("mastered", T) == "2026-09-06"


def test_correct_promotes_new_to_good():
    s = apply_result({"status": "new", "wrong_count": 0, "review_count": 0, "priority": 0, "first_quiz_date": None}, "correct", T)
    assert s["status"] == "good"
    assert s["first_quiz_date"] == T


def test_correct_promotes_poor_to_blur():
    s = apply_result({"status": "poor", "wrong_count": 1, "review_count": 0, "priority": 5, "first_quiz_date": T}, "correct", T)
    assert s["status"] == "blur"


def test_correct_promotes_blur_to_good():
    s = apply_result({"status": "blur", "wrong_count": 1, "review_count": 0, "priority": 5, "first_quiz_date": T}, "correct", T)
    assert s["status"] == "good"


def test_correct_masters_good():
    s = apply_result({"status": "good", "wrong_count": 0, "review_count": 5, "priority": 0, "first_quiz_date": T}, "correct", T)
    assert s["status"] == "mastered"
    assert s["next_review_date"] == "2026-09-06"


def test_blur_demotes_any():
    s = apply_result({"status": "mastered", "wrong_count": 0, "review_count": 9, "priority": 0, "first_quiz_date": T}, "blur", T)
    assert s["status"] == "blur"


def test_wrong_demotes_to_poor():
    s = apply_result({"status": "mastered", "wrong_count": 0, "review_count": 9, "priority": 0, "first_quiz_date": T}, "wrong", T)
    assert s["status"] == "poor"
    assert s["wrong_count"] == 1
    assert s["priority"] >= 5
    assert s["next_review_date"] == "2026-08-08"


def test_review_count_increments():
    s = apply_result({"status": "new", "wrong_count": 0, "review_count": 0, "priority": 0, "first_quiz_date": None}, "correct", T)
    assert s["review_count"] == 1
