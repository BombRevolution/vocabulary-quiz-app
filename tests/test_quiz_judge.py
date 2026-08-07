import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quiz_logic import normalize, edit_distance, judge


def test_normalize_case():
    assert normalize("Apple", True, False) == "apple"
    assert normalize("Apple", False, False) == "Apple"


def test_normalize_punct():
    assert normalize("A.M.", True, True) == "am"
    assert normalize("A.M.", True, False) == "a.m."


def test_normalize_keeps_hyphen():
    assert normalize("well-known", True, False) == "well-known"


def test_edit_distance_equal():
    assert edit_distance("apple", "apple") == 0


def test_edit_distance_one_off():
    assert edit_distance("appple", "apple") == 1
    assert edit_distance("aplle", "apple") == 1
    assert edit_distance("appl", "apple") == 1


def test_judge_correct_ignores_case():
    assert judge("APPLE", "apple", True, False) == "correct"


def test_judge_punct_strict_default():
    assert judge("AM", "A.M.", True, False) == "wrong"


def test_judge_punct_ignored():
    assert judge("AM", "A.M.", True, True) == "correct"


def test_judge_blur_one_letter():
    assert judge("appple", "apple", True, False) == "blur"


def test_judge_wrong():
    assert judge("banana", "apple", True, False) == "wrong"