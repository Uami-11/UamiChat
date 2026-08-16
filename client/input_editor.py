import os
import sys
import threading

from . import ui


class InputBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.draft = ""
        self.active = False

    def snapshot(self):
        with self.lock:
            return self.active, self.draft


input_buffer = InputBuffer()


def _delete_last_word(draft):
    """Remove the trailing word along with any whitespace before it."""
    end = len(draft)

    while end and draft[end - 1].isspace():
        end -= 1

    while end and not draft[end - 1].isspace():
        end -= 1

    while end and draft[end - 1].isspace():
        end -= 1

    return draft[:end]


def apply_key(draft, key):
    """Apply a keyboard input to the current draft."""
    if key in ("\r", "\n"):
        return draft

    if key in ("\b", "\x7f"):
        return draft[:-1]

    if key in ("\x03", "\x04"):
        return draft

    if key == "\x15":
        return ""

    if key == "\x17":
        return _delete_last_word(draft)

    if key.startswith("\x1b"):
        return draft

    if key.isprintable():
        return draft + key

    return draft


def read_line():
    """
    Read one line from stdin while keeping track of the current draft.
    """

    if not sys.stdin.isatty():
        return input("")

    with input_buffer.lock:
        input_buffer.active = True
        input_buffer.draft = ""

    try:
        if os.name == "nt":
            return _read_windows()

        return _read_unix()

    finally:
        with input_buffer.lock:
            input_buffer.active = False
            input_buffer.draft = ""


def _read_windows():
    import msvcrt

    while True:
        key = msvcrt.getwch()

        if key == "\r":
            sys.stdout.write("\r\n")
            return input_buffer.draft

        if key == "\x03":
            raise KeyboardInterrupt

        if key == "\x04":
            raise EOFError

        # Windows arrow/function keys produce a prefix.
        if key in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue

        with input_buffer.lock:
            input_buffer.draft = apply_key(input_buffer.draft, key)
            draft = input_buffer.draft

        ui.render_input(draft)


def _read_unix():
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while True:
            key = sys.stdin.read(1)

            if key in ("\r", "\n"):
                sys.stdout.write("\r\n")
                return input_buffer.draft

            if key == "\x03":
                raise KeyboardInterrupt

            if key == "\x04":
                raise EOFError

            if key == "\x1b":
                _swallow_escape_sequence()
                continue

            with input_buffer.lock:
                input_buffer.draft = apply_key(input_buffer.draft, key)
                draft = input_buffer.draft

            ui.render_input(draft)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _swallow_escape_sequence():
    """
    Swallow terminal escape sequences such as arrow keys.
    """
    if os.name == "nt":
        return

    import select

    while select.select([sys.stdin], [], [], 0.01)[0]:
        sys.stdin.read(1)