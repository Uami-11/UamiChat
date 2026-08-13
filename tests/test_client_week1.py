import client.commands as commands
import client.ui as ui


class TestParseInput:
    def test_plain_text_becomes_room_message(self):
        assert commands.parse_input("hello everyone") == {
            "type": "room_message",
            "content": "hello everyone",
        }

    def test_empty_input_is_error(self):
        result = commands.parse_input("")
        assert result["type"] == "error"

    def test_whitespace_input_is_error(self):
        result = commands.parse_input("   ")
        assert result["type"] == "error"

    def test_dm(self):
        assert commands.parse_input("/dm nirwan hello") == {
            "type": "direct_message",
            "to": "nirwan",
            "content": "hello",
        }

    def test_dm_preserves_multiple_words_in_message(self):
        result = commands.parse_input("/dm nirwan hello there world")
        assert result == {
            "type": "direct_message",
            "to": "nirwan",
            "content": "hello there world",
        }

    def test_dm_missing_username_is_error(self):
        result = commands.parse_input("/dm")
        assert result["type"] == "error"

    def test_dm_missing_message_is_error(self):
        result = commands.parse_input("/dm nirwan")
        assert result["type"] == "error"

    def test_rooms(self):
        assert commands.parse_input("/rooms") == {"type": "list_rooms"}

    def test_join(self):
        assert commands.parse_input("/join dev") == {"type": "join_room", "name": "dev"}

    def test_join_missing_name_is_error(self):
        result = commands.parse_input("/join")
        assert result["type"] == "error"

    def test_create(self):
        assert commands.parse_input("/create dev") == {
            "type": "create_room",
            "name": "dev",
        }

    def test_create_missing_name_is_error(self):
        result = commands.parse_input("/create")
        assert result["type"] == "error"

    def test_help(self):
        assert commands.parse_input("/help") == {"type": "help"}

    def test_quit(self):
        assert commands.parse_input("/quit") == {"type": "quit"}

    def test_unknown_command_is_error(self):
        result = commands.parse_input("/bogus")
        assert result["type"] == "error"

    def test_commands_are_case_insensitive(self):
        assert commands.parse_input("/ROOMS") == {"type": "list_rooms"}
        assert commands.parse_input("/Quit") == {"type": "quit"}


class TestGetCommandList:
    def test_returns_list_of_strings(self):
        command_list = commands.get_command_list()
        assert isinstance(command_list, list)
        assert all(isinstance(c, str) for c in command_list)

    def test_covers_core_commands(self):
        text = "\n".join(commands.get_command_list())
        for command in ["/dm", "/rooms", "/join", "/create", "/help", "/quit"]:
            assert command in text


class TestUI:
    def test_welcome(self, console):
        ui.print_welcome()
        out = console.export_text()
        assert "Welcome to UamiChat" in out
        assert "/help" in out

    def test_message_shows_username_content_and_timestamp(self, console):
        ui.print_message("nirwan", "hello", "12:00")
        out = console.export_text()
        assert "nirwan" in out
        assert "hello" in out
        assert "12:00" in out

    def test_system(self, console):
        ui.print_system("user joined the room")
        assert "user joined the room" in console.export_text()

    def test_error(self, console):
        ui.print_error("something went wrong")
        assert "something went wrong" in console.export_text()

    def test_help_lists_commands(self, console):
        ui.print_help(commands.get_command_list())
        out = console.export_text()
        assert "/rooms" in out
        assert "/quit" in out

    def test_room_list_renders_rows(self, console):
        rooms = [
            {"name": "dev", "members": 3, "created": "today"},
            {"name": "general", "members": 5, "created": "yesterday"},
        ]
        ui.print_room_list(rooms)
        out = console.export_text()
        assert "dev" in out
        assert "general" in out

    def test_clear_screen_does_not_raise(self, console):
        ui.clear_screen()
