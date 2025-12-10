# test_keyboard_handler.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

import pytest
from pynput import keyboard

from keyboard_handler import KeyboardHandler


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

# === Extraction tests ===

def test_extract_from_memory_full(tmp_path: Path):
    """extract_logged_keys(source='memory') should return all recorded keystrokes."""
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Simulate typing "test"
    for ch in "test":
        handler.on_press(keyboard.KeyCode.from_char(ch))

    extracted = handler.extract_logged_keys(source="memory")
    assert extracted == ["t", "e", "s", "t"]


def test_extract_from_memory_with_limit(tmp_path: Path):
    """extract_logged_keys(source='memory', limit=N) should return only the last N tokens."""
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    for ch in "abcdef":
        handler.on_press(keyboard.KeyCode.from_char(ch))

    # Last 3 characters of "abcdef" are "d", "e", "f"
    extracted = handler.extract_logged_keys(source="memory", limit=3)
    assert extracted == ["d", "e", "f"]


def test_extract_from_file_single_session(tmp_path: Path):
    """
    After logging some keystrokes in one session,
    extract_logged_keys(source='file') should return those tokens
    from the last session in the log file.
    """
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Type 'h', 'i', then Enter
    handler.on_press(keyboard.KeyCode.from_char("h"))
    handler.on_press(keyboard.KeyCode.from_char("i"))
    handler.on_press(keyboard.Key.enter)

    tokens = handler.extract_logged_keys(source="file")

    # We expect our normalized tokens to appear in order
    # Exact list will be just ["h", "i", "<Enter>"] if your extraction
    # filters headers and blank lines correctly.
    assert "h" in tokens
    assert "i" in tokens
    assert "<Enter>" in tokens
    # sanity: order at the end
    assert tokens[-3:] == ["h", "i", "<Enter>"]


def test_extract_from_file_multiple_sessions_uses_last_session(tmp_path: Path):
    """
    If multiple sessions exist in the log file (multiple handlers created),
    extraction from 'file' should only return tokens from the last session.
    """
    log_path = tmp_path / "log.txt"

    # First session: "abc"
    handler1 = KeyboardHandler(mode="L", log_file=str(log_path))
    for ch in "abc":
        handler1.on_press(keyboard.KeyCode.from_char(ch))

    # Second session: "xyz"
    handler2 = KeyboardHandler(mode="L", log_file=str(log_path))
    for ch in "xyz":
        handler2.on_press(keyboard.KeyCode.from_char(ch))

    # Extract using the second handler (same file)
    tokens = handler2.extract_logged_keys(source="file")

    # We expect only the last session's tokens ("x", "y", "z")
    assert tokens[-3:] == ["x", "y", "z"]
    # And *not* the first session tokens if you're correctly splitting by session header
    assert "a" not in tokens
    assert "b" not in tokens
    assert "c" not in tokens


def test_extract_from_file_nonexistent_path_returns_empty(tmp_path: Path):
    """
    If the log_file path does not exist when extracting from 'file',
    extract_logged_keys should return an empty list.
    """
    log_path = tmp_path / "log.txt"
    handler = KeyboardHandler(mode="L", log_file=str(log_path))

    # Point the handler to a different, nonexistent file before extraction
    nonexistent_path = tmp_path / "does_not_exist.log"
    handler.log_file = str(nonexistent_path)

    tokens = handler.extract_logged_keys(source="file")
    assert tokens == []


