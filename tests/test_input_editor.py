import client.input_editor as input_editor
import client.ui as ui
from client.input_editor import apply_key


class TestApplyKey:
    def test_appends_printable_characters(self):
        assert apply_key("hel", "l") == "hell"

    def test_backspace_removes_last_character(self):
        assert apply_key("hello", "\b") == "hell"

    def test_delete_removes_last_character(self):
        assert apply_key("hello", "\x7f") == "hell"

    def test_enter_does_not_change_draft(self):
        assert apply_key("hello", "\r") == "hello"
        assert apply_key("hello", "\n") == "hello"

    def test_ctrl_c_does_not_change_draft(self):
        assert apply_key("hello", "\x03") == "hello"

    def test_ctrl_d_does_not_change_draft(self):
        assert apply_key("hello", "\x04") == "hello"

    def test_ctrl_u_clears_the_line(self):
        assert apply_key("hello world", "\x15") == ""

    def test_ctrl_w_deletes_last_word(self):
        assert apply_key("hello world", "\x17") == "hello"

    def test_ctrl_w_deletes_word_and_trailing_space(self):
        assert apply_key("hello world ", "\x17") == "hello"

    def test_ctrl_w_on_single_word_clears(self):
        assert apply_key("hello", "\x17") == ""

    def test_ctrl_w_on_command(self):
        assert apply_key("/dm hi", "\x17") == "/dm"

    def test_ctrl_w_on_empty_draft(self):
        assert apply_key("", "\x17") == ""

    def test_escape_sequence_does_not_change_draft(self):
        assert apply_key("hello", "\x1b[A") == "hello"

    def test_non_printable_characters_are_dropped(self):
        assert apply_key("hello", "\t") == "hello"


class TestDeleteLastWord:
    def test_deletes_word_and_preceding_space(self):
        assert input_editor._delete_last_word("hello world") == "hello"

    def test_handles_trailing_whitespace(self):
        assert input_editor._delete_last_word("hello world ") == "hello"

    def test_single_word(self):
        assert input_editor._delete_last_word("hello") == ""

    def test_only_whitespace(self):
        assert input_editor._delete_last_word("  ") == ""

    def test_empty(self):
        assert input_editor._delete_last_word("") == ""


class TestInputLineText:
    def test_renders_prompt_and_draft(self):
        assert ui.input_line_text("abc") == "\r\x1b[2K> abc"

    def test_renders_empty_draft(self):
        assert ui.input_line_text("") == "\r\x1b[2K> "
