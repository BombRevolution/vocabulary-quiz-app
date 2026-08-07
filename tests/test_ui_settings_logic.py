import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import build_event_sequence, MODIFIER_KEYSYMS


def test_build_single_modifier():
    assert build_event_sequence(0x4, "d") == "<Control-d>"


def test_build_multi_modifier():
    assert build_event_sequence(0x5, "s") == "<Control-Shift-s>"


def test_build_space():
    assert build_event_sequence(0x4, "space") == "<Control-space>"


def test_build_alt():
    assert build_event_sequence(0x8, "h") == "<Alt-h>"


def test_no_modifier_rejected():
    assert build_event_sequence(0, "a") == ""


def test_modifier_keysyms_excluded():
    for ks in MODIFIER_KEYSYMS:
        assert ks in ("Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R",
                      "Caps_Lock", "Num_Lock")