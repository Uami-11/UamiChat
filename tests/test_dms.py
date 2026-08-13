import asyncio
import json
import uuid
from datetime import datetime

import pytest

import server.handler as handler
from server import db, models


def unique_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def room_data():
    owner = db.create_user(unique_name("owner"), "hash")
    invitee = db.create_user(unique_name("invitee"), "hash")
    stranger = db.create_user(unique_name("stranger"), "hash")
    room = db.create_room(unique_name("room"), False, owner.id)
    db.add_room_member(room.id, owner.id)

    created_users = [u for u in (owner, invitee, stranger) if u]
    yield owner, invitee, stranger, room

    conn = db.get_connection()
    cur = conn.cursor()
    user_ids = [u.id for u in created_users]
    cur.execute(
        "DELETE FROM messages WHERE sender_id = ANY(%s) OR recipient_id = ANY(%s) OR room_id = %s",
        (user_ids, user_ids, room.id),
    )
    cur.execute("DELETE FROM room_members WHERE room_id = %s", (room.id,))
    cur.execute(
        "DELETE FROM friendships WHERE user_id = ANY(%s) OR friend_id = ANY(%s)",
        (user_ids, user_ids),
    )
    cur.execute("DELETE FROM rooms WHERE id = %s", (room.id,))
    cur.execute("DELETE FROM users WHERE id = ANY(%s)", (user_ids,))
    conn.commit()
    conn.close()


class TestIsRoomOwnerDB:
    def test_owner_is_room_owner(self, room_data):
        owner, invitee, stranger, room = room_data
        assert db.is_room_owner(room.id, owner.id) is True

    def test_non_owner_is_not_room_owner(self, room_data):
        owner, invitee, stranger, room = room_data
        assert db.is_room_owner(room.id, stranger.id) is False


class TestInviteToRoomDB:
    def test_owner_can_invite(self, room_data):
        owner, invitee, stranger, room = room_data
        assert db.invite_to_room(room.id, owner.id, invitee.id) is True
        assert db.is_room_member(room.id, invitee.id) is True

    def test_non_owner_cannot_invite(self, room_data):
        owner, invitee, stranger, room = room_data
        assert db.invite_to_room(room.id, stranger.id, invitee.id) is False
        assert db.is_room_member(room.id, invitee.id) is False

    def test_cannot_invite_existing_member(self, room_data):
        owner, invitee, stranger, room = room_data
        db.add_room_member(room.id, invitee.id)
        assert db.invite_to_room(room.id, owner.id, invitee.id) is False


class TestMessagesDB:
    def test_save_and_mark_message_read(self, room_data):
        owner, invitee, stranger, room = room_data

        db.save_message(sender_id=owner.id, message="hi", recipient_id=invitee.id)
        unread = db.get_unread_dms(invitee.id)
        assert len(unread) == 1
        assert unread[0]["message"] == "hi"
        assert unread[0]["created_at"] is not None

        db.mark_message_read(invitee.id, owner.id)
        assert db.get_unread_dms(invitee.id) == []


class TestDirectMessageHandler:
    async def test_unknown_recipient_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_direct_message(
            fake_ws, {"to": "ghost", "content": "hi"}, 1
        )

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_blocked_sender_errors(self, fake_ws, monkeypatch):
        recipient = models.User(id=2, username="bob", is_online=False)
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: recipient)
        monkeypatch.setattr(handler.db, "is_blocked", lambda sender_id, recipient_id: True)

        await handler.handle_direct_message(
            fake_ws, {"to": "bob", "content": "hi"}, 1
        )

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "cannot send message to this user",
        }

    async def test_success_sends_and_notifies_online_recipient(
        self, fake_ws, fake_ws_factory, monkeypatch
    ):
        sender = models.User(id=1, username="me", is_online=False)
        recipient = models.User(id=2, username="bob", is_online=False)
        saved = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: recipient)
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: sender)
        monkeypatch.setattr(handler.db, "is_blocked", lambda sender_id, recipient_id: False)
        monkeypatch.setattr(
            handler.db,
            "save_message",
            lambda sender_id, message, recipient_id: saved.update(
                sender_id=sender_id, message=message, recipient_id=recipient_id
            ),
        )

        recipient_ws = fake_ws_factory()
        handler.connected_clients[recipient.id] = recipient_ws
        try:
            await handler.handle_direct_message(
                fake_ws, {"to": "bob", "content": "hi"}, 1
            )
            await asyncio.sleep(0)
        finally:
            handler.connected_clients.pop(recipient.id, None)

        assert saved == {"sender_id": 1, "message": "hi", "recipient_id": 2}
        assert fake_ws.sent[-1] == {"type": "success", "message": "message sent"}

        sent = recipient_ws.sent[-1]
        assert sent["type"] == "direct_message"
        assert sent["from"] == "me"
        assert sent["content"] == "hi"
        assert "timestamp" in sent


class TestInboxHandler:
    async def test_returns_unread_messages_with_usernames(self, fake_ws, monkeypatch):
        sender = models.User(id=2, username="bob", is_online=False)
        monkeypatch.setattr(
            handler.db,
            "get_unread_dms",
            lambda user_id: [{"sender_id": 2, "message": "hi", "created_at": datetime(2026, 8, 13, 7, 30, 0)}],
        )
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: sender)

        await handler.handle_inbox(fake_ws, 1)

        assert fake_ws.sent[-1] == {
            "type": "inbox_result",
            "messages": [{"from": "bob", "content": "hi", "timestamp": "2026-08-13T07:30:00"}],
        }


class TestMarkReadHandler:
    async def test_unknown_sender_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_mark_read(fake_ws, {"from": "ghost"}, 1)

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_marks_messages_read(self, fake_ws, monkeypatch):
        sender = models.User(id=2, username="bob", is_online=False)
        marked = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: sender)
        monkeypatch.setattr(
            handler.db,
            "mark_message_read",
            lambda user_id, sender_id: marked.update(
                user_id=user_id, sender_id=sender_id
            ),
        )

        await handler.handle_mark_read(fake_ws, {"from": "bob"}, 1)

        assert marked == {"user_id": 1, "sender_id": 2}
        assert fake_ws.sent[-1] == {
            "type": "success",
            "message": "messages marked as read",
        }


class TestInviteHandler:
    async def test_unknown_invitee_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_invite(fake_ws, {"room_id": 1, "username": "ghost"}, 1)

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_failed_invite_errors(self, fake_ws, monkeypatch):
        invitee = models.User(id=2, username="bob", is_online=False)
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: invitee)
        monkeypatch.setattr(
            handler.db,
            "invite_to_room",
            lambda room_id, inviter_id, invitee_id: False,
        )

        await handler.handle_invite(fake_ws, {"room_id": 1, "username": "bob"}, 1)

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "could not invite user to room",
        }

    async def test_success_notifies_online_invitee(
        self, fake_ws, fake_ws_factory, monkeypatch
    ):
        inviter = models.User(id=1, username="me", is_online=False)
        invitee = models.User(id=2, username="bob", is_online=False)
        room = models.Room(id=1, room_name="secret", is_private=True, owner_id=1)
        invited = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: invitee)
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: inviter)
        monkeypatch.setattr(handler.db, "get_room_by_id", lambda room_id: room)
        monkeypatch.setattr(
            handler.db,
            "invite_to_room",
            lambda room_id, inviter_id, invitee_id: invited.update(
                room_id=room_id, inviter_id=inviter_id, invitee_id=invitee_id
            )
            or True,
        )

        invitee_ws = fake_ws_factory()
        handler.connected_clients[invitee.id] = invitee_ws
        try:
            await handler.handle_invite(fake_ws, {"room_id": 1, "username": "bob"}, 1)
            await asyncio.sleep(0)
        finally:
            handler.connected_clients.pop(invitee.id, None)

        assert invited == {"room_id": 1, "inviter_id": 1, "invitee_id": 2}
        assert fake_ws.sent[-1] == {
            "type": "success",
            "message": "user invited to room",
        }
        assert invitee_ws.sent[-1] == {
            "type": "invite_received",
            "room": "secret",
            "from": "me",
        }


class TestRouting:
    async def test_direct_message_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, data, user_id):
            calls.append((websocket, data, user_id))

        monkeypatch.setattr(handler, "handle_direct_message", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(
                fake_ws,
                json.dumps({"type": "direct_message", "to": "bob", "content": "hi"}),
            )
        finally:
            handler.connected_clients.pop(1, None)

        assert len(calls) == 1
        assert calls[0][1] == {"type": "direct_message", "to": "bob", "content": "hi"}
        assert calls[0][2] == 1

    async def test_inbox_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, user_id):
            calls.append((websocket, user_id))

        monkeypatch.setattr(handler, "handle_inbox", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(fake_ws, json.dumps({"type": "inbox"}))
        finally:
            handler.connected_clients.pop(1, None)

        assert calls == [(fake_ws, 1)]

    async def test_mark_read_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, data, user_id):
            calls.append((websocket, data, user_id))

        monkeypatch.setattr(handler, "handle_mark_read", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(
                fake_ws, json.dumps({"type": "mark_read", "from": "bob"})
            )
        finally:
            handler.connected_clients.pop(1, None)

        assert len(calls) == 1
        assert calls[0][1] == {"type": "mark_read", "from": "bob"}
        assert calls[0][2] == 1

    async def test_invite_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, data, user_id):
            calls.append((websocket, data, user_id))

        monkeypatch.setattr(handler, "handle_invite", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(
                fake_ws, json.dumps({"type": "invite", "room_id": 1, "username": "bob"})
            )
        finally:
            handler.connected_clients.pop(1, None)

        assert len(calls) == 1
        assert calls[0][1] == {"type": "invite", "room_id": 1, "username": "bob"}
        assert calls[0][2] == 1

    async def test_dm_routing_requires_login(self, fake_ws):
        await handler.handle_message(
            fake_ws, json.dumps({"type": "direct_message", "to": "bob", "content": "hi"})
        )

        assert fake_ws.sent[-1] == {"type": "error", "message": "not logged in"}
