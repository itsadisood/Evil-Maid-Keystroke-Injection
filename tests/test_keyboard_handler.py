# test_keyboard_handler.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

import pytest
from pynput import keyboard

from keyboard_handler import KeyboardHandler, typing_active  # adjust name if needed


def test_simple_text_logging(tmp_path: Path):
    """Typing plain characters should log them directly with no modifiers."""
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Simulate typing "abc"
    for ch in "abc":
        handler.on_press(keyboard.KeyCode.from_char(ch))

    assert handler.keystrokes_recorded == ["a", "b", "c"]

    # Ensure they were written to file (one per line + header)
    contents = log_path.read_text()
    # Basic sanity checks
    assert "a" in contents
    assert "b" in contents
    assert "c" in contents


def test_modifier_and_char_combo(tmp_path: Path):
    """
    Press Ctrl, then 'a'.

    With the current implementation:
    - pressing Ctrl logs "<Ctrl>"
    - pressing 'a' while Ctrl is held logs "Ctrl+a"
    """
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Press Ctrl
    handler.on_press(keyboard.Key.ctrl)
    # Press 'a'
    handler.on_press(keyboard.KeyCode.from_char("a"))
    # Release Ctrl
    handler.on_release(keyboard.Key.ctrl)

    assert handler.keystrokes_recorded == ["<Ctrl>", "Ctrl+a"]

    # After release, there should be no modifiers held
    assert handler.pressed_modifiers == set()

    contents = log_path.read_text()
    assert "<Ctrl>" in contents
    assert "Ctrl+a" in contents


def test_backspace_logging(tmp_path: Path):
    """
    Backspace is treated as a special key:
    - no modifiers held -> logs '<Backspace>'
    """
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Type 'h', 'i', then Backspace
    handler.on_press(keyboard.KeyCode.from_char("h"))
    handler.on_press(keyboard.KeyCode.from_char("i"))
    handler.on_press(keyboard.Key.backspace)

    assert handler.keystrokes_recorded == ["h", "i", "<Backspace>"]

    contents = log_path.read_text()
    assert "<Backspace>" in contents


def test_injection_mode_disables_logging(tmp_path: Path):
    """When mode='I', on_press should not log anything."""
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="I", log_file=str(log_path))

    handler.on_press(keyboard.KeyCode.from_char("x"))
    handler.on_press(keyboard.Key.backspace)
    handler.on_press(keyboard.Key.ctrl)

    # Nothing should be recorded
    assert handler.keystrokes_recorded == []

    # File should still contain only the session header
    contents = log_path.read_text()
    # Header is written in __init__, so file is not empty
    assert "Session started:" in contents
    # But no key tokens (rough sanity check)
    assert "<Backspace>" not in contents
    assert "x\n" not in contents


def test_typing_active_flag_disables_logging(tmp_path: Path, monkeypatch):
    """
    If global typing_active is True, on_press should skip logging.
    We'll monkeypatch the module-level flag.
    """
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Set typing_active to True in the imported module
    import keyboard_handler as kh  # adjust if your module is named differently

    monkeypatch.setattr(kh, "typing_active", True)

    handler.on_press(keyboard.KeyCode.from_char("z"))
    handler.on_press(keyboard.Key.backspace)

    # Nothing should be recorded because typing_active is True
    assert handler.keystrokes_recorded == []

    contents = log_path.read_text()
    # Header only
    assert "Session started:" in contents
    assert "z\n" not in contents
    assert "<Backspace>" not in contents
