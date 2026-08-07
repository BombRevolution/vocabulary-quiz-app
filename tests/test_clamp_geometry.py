import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_theme import clamp_geometry

SCREENS = [
    (1920, 1080),   # 1080p 16:9
    (2560, 1440),   # 2K 16:9
    (2560, 1080),   # 2.5K 超宽
    (1920, 1200),   # 16:10
    (2560, 1600),   # 2K 16:10
    (1366, 768),    # 小屏
    (1280, 720),    # 小屏 16:9
]


def test_dialog_fits_every_screen():
    for sw, sh in SCREENS:
        for w, h in [(540, 720), (1040, 760), (900, 680)]:
            cw, ch, cx, cy = clamp_geometry(w, h, sw, sh)
            assert cw <= sw - 48
            assert ch <= sh - 48
            assert cx >= 0 and cy >= 0
            assert cw >= 320 and ch >= 240


def test_large_dialog_clamped_on_small_screen():
    cw, ch, cx, cy = clamp_geometry(1040, 760, 1280, 720)
    assert cw <= 1280 - 48
    assert ch <= 720 - 48
    assert cx >= 0 and cy >= 0


def test_small_dialog_unchanged_on_big_screen():
    cw, ch, cx, cy = clamp_geometry(540, 720, 2560, 1440)
    assert cw == 540
    assert ch == 720
    assert cx == (2560 - 540) // 2
    assert cy == (1440 - 720) // 2