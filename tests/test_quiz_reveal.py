import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quiz_logic import reveal_mask

def test_reveal_30_percent_rounds_up():
    assert reveal_mask("apple", 30) == "ap___"

def test_reveal_50_percent():
    assert reveal_mask("book", 50) == "bo__"

def test_reveal_100_percent():
    assert reveal_mask("apple", 100) == "apple"

def test_reveal_0_percent():
    assert reveal_mask("apple", 0) == "_____"

def test_reveal_empty_word():
    assert reveal_mask("", 30) == ""

def test_reveal_percent_clamped():
    assert reveal_mask("apple", 200) == "apple"
    assert reveal_mask("apple", -10) == "_____"