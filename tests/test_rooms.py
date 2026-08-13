import json

import server.handler as handler
from server import models


class TestRoomMessageHandler:
    async def test_non_member_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "is_room_member", lambda room_id, user_id: False)

        await handler.handle_room_message(
            fake_ws, {"room_id": 1, "content": "hello"}, 1
        )

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "you are not a member of this room",
        }

    async def test_member_sends_and_broadcasts_to_others(
        self, fake_ws, monkeypatch
    ):
        sender = models.User(id=1, username="me", is_online=False)
        room = models.Room(id=1, room_name="dev", is_private=False, owner_id=1)
        saved = {}
        broadcast = {}
        monkeypatch.setattr(handler.db, "is_room_member", lambda room_id, user_id: True)
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: sender)
        monkeypatch.setattr(handler.db, "get_room_by_id", lambda room_id: room)
        monkeypatch.setattr(
            handler.db,
            "save_message",
            lambda sender_id, message, room_id: saved.update(
                sender_id=sender_id, message=message, room_id=room_id
            ),
        )
        monkeypatch.setattr(
            handler,
            "broadcast_to_room",
            lambda room_id, message, exclude_user_id: broadcast.update(
                room_id=room_id, message=message, exclude_user_id=exclude_user_id
            ),
        )

        await handler.handle_room_message(
            fake_ws, {"room_id": 1, "content": "hello"}, 1
        )

        assert saved == {"sender_id": 1, "message": "hello", "room_id": 1}
        assert broadcast["room_id"] == 1
        assert broadcast["exclude_user_id"] == 1

        message = broadcast["message"]
        assert message["type"] == "room_message"
        assert message["from"] == "me"
        assert message["room"] == "dev"
        assert message["content"] == "hello"
        assert "timestamp" in message


class TestJoinRoomHandler:
    async def test_join_public_room(self, fake_ws, monkeypatch):
        room = models.Room(id=1, room_name="dev", is_private=False, owner_id=1)
        added = []

        monkeypatch.setattr(handler.db, "get_room_by_name", lambda name: room)
        monkeypatch.setattr(
            handler.db, "add_room_member", lambda room_id, user_id: added.append((room_id, user_id))
        )

        await handler.handle_join_room(fake_ws, {"name": "dev"}, 5)

        assert added == [(1, 5)]
        message = fake_ws.sent[-1]
        assert message["type"] == "success"
        assert message["message"] == "joined room"
        assert message["room"]["id"] == 1

    async def test_private_room_requires_invite(self, fake_ws, monkeypatch):
        room = models.Room(id=1, room_name="secret", is_private=True, owner_id=1)
        monkeypatch.setattr(handler.db, "get_room_by_name", lambda name: room)
        monkeypatch.setattr(handler.db, "is_room_member", lambda room_id, user_id: False)

        await handler.handle_join_room(fake_ws, {"name": "secret"}, 5)

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "cannot join private room without invite",
        }

    async def test_private_room_member_can_join(self, fake_ws, monkeypatch):
        room = models.Room(id=1, room_name="secret", is_private=True, owner_id=1)
        monkeypatch.setattr(handler.db, "get_room_by_name", lambda name: room)
        monkeypatch.setattr(handler.db, "is_room_member", lambda room_id, user_id: True)
        monkeypatch.setattr(handler.db, "add_room_member", lambda room_id, user_id: None)

        await handler.handle_join_room(fake_ws, {"name": "secret"}, 5)

        message = fake_ws.sent[-1]
        assert message["type"] == "success"
        assert message["message"] == "joined room"
        assert message["room"]["is_private"] is True


class TestRouting:
    async def test_room_message_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, data, user_id):
            calls.append((websocket, data, user_id))

        monkeypatch.setattr(handler, "handle_room_message", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(
                fake_ws,
                json.dumps({"type": "room_message", "room_id": 1, "content": "hello"}),
            )
        finally:
            handler.connected_clients.pop(1, None)

        assert len(calls) == 1
        assert calls[0][1] == {"type": "room_message", "room_id": 1, "content": "hello"}
        assert calls[0][2] == 1

    async def test_room_message_routing_requires_login(self, fake_ws):
        await handler.handle_message(
            fake_ws, json.dumps({"type": "room_message", "room_id": 1, "content": "hi"})
        )

        assert fake_ws.sent[-1] == {"type": "error", "message": "not logged in"}
