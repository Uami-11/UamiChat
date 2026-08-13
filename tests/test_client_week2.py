import websockets
import websockets.exceptions

import client.commands as commands
import client.ui as ui
from client import main


class TestWeek2Commands:
    def test_invite(self):
        assert commands.parse_input("/invite bob") == {
            "type": "invite",
            "username": "bob",
        }

    def test_invite_missing_username_is_error(self):
        result = commands.parse_input("/invite")
        assert result["type"] == "error"

    def test_inbox(self):
        assert commands.parse_input("/inbox") == {"type": "inbox"}

    def test_online(self):
        assert commands.parse_input("/online") == {"type": "online_friends"}

    def test_addfriend(self):
        assert commands.parse_input("/addfriend bob") == {
            "type": "add_friend",
            "username": "bob",
        }

    def test_addfriend_missing_username_is_error(self):
        result = commands.parse_input("/addfriend")
        assert result["type"] == "error"

    def test_block(self):
        assert commands.parse_input("/block bob") == {
            "type": "block",
            "username": "bob",
        }

    def test_block_missing_username_is_error(self):
        result = commands.parse_input("/block")
        assert result["type"] == "error"

    def test_markread(self):
        assert commands.parse_input("/markread bob") == {
            "type": "mark_read",
            "from": "bob",
        }

    def test_markread_missing_username_is_error(self):
        result = commands.parse_input("/markread")
        assert result["type"] == "error"

    def test_command_list_covers_week2_commands(self):
        text = "\n".join(commands.get_command_list())
        for command in ["/invite", "/inbox", "/online", "/addfriend", "/block", "/markread"]:
            assert command in text


class TestWeek2UI:
    def test_inbox_renders_messages(self, console):
        ui.print_inbox(
            [{"from": "bob", "content": "hi", "timestamp": "12:00"}]
        )
        out = console.export_text()
        assert "bob" in out
        assert "hi" in out

    def test_online_friends_renders_usernames(self, console):
        ui.print_online_friends([{"id": 2, "username": "bob", "is_online": True}])
        assert "bob" in console.export_text()

    def test_online_friends_empty(self, console):
        ui.print_online_friends([])
        assert "No online friends" in console.export_text()


class TestWithRoomContext:
    def test_room_message_gets_room_id(self):
        result = main.with_room_context(
            {"type": "room_message", "content": "hi"},
            {"id": 3, "name": "dev"},
        )
        assert result == {"type": "room_message", "content": "hi", "room_id": 3}

    def test_room_message_without_room_errors(self):
        result = main.with_room_context({"type": "room_message", "content": "hi"}, None)
        assert result["type"] == "error"

    def test_invite_gets_room_id(self):
        result = main.with_room_context(
            {"type": "invite", "username": "bob"},
            {"id": 3, "name": "dev"},
        )
        assert result == {"type": "invite", "username": "bob", "room_id": 3}

    def test_invite_without_room_errors(self):
        result = main.with_room_context({"type": "invite", "username": "bob"}, None)
        assert result["type"] == "error"

    def test_other_messages_unaffected(self):
        result = main.with_room_context({"type": "list_rooms"}, None)
        assert result == {"type": "list_rooms"}


class TestListen:
    async def test_routes_message_types(self, monkeypatch, console):
        messages = [
            {"type": "inbox_result", "messages": [{"from": "bob", "content": "hi"}]},
            {"type": "error", "message": "boom"},
        ]

        async def fake_receive(websocket):
            if messages:
                return messages.pop(0)
            raise websockets.exceptions.ConnectionClosed(None, None)

        monkeypatch.setattr(main.connection, "receive", fake_receive)

        await main.listen(None)

        out = console.export_text()
        assert "bob" in out
        assert "boom" in out

    async def test_sets_current_room_on_join(self, monkeypatch, console):
        messages = [
            {
                "type": "success",
                "message": "joined room",
                "room": {"id": 5, "name": "dev"},
            }
        ]

        async def fake_receive(websocket):
            if messages:
                return messages.pop(0)
            raise websockets.exceptions.ConnectionClosed(None, None)

        monkeypatch.setattr(main.connection, "receive", fake_receive)

        original = main.current_room
        main.current_room = None
        try:
            await main.listen(None)
            assert main.current_room == {"id": 5, "name": "dev"}
        finally:
            main.current_room = original
