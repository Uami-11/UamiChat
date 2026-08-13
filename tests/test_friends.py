import asyncio
import json
import uuid

import pytest

import server.handler as handler
from server import db, models


def unique_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def users():
    alice = db.create_user(unique_name("alice"), "hash")
    bob = db.create_user(unique_name("bob"), "hash")
    created = [u for u in (alice, bob) if u]
    yield created

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM friendships WHERE user_id = ANY(%s) OR friend_id = ANY(%s)",
        ([u.id for u in created], [u.id for u in created]),
    )
    cur.execute("DELETE FROM users WHERE id = ANY(%s)", ([u.id for u in created],))
    conn.commit()
    conn.close()


class TestFriendRequestsDB:
    def test_send_friend_request_stores_pending(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)

        assert db.get_friends(alice.id) == []

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM friendships WHERE user_id=%s AND friend_id=%s",
            (alice.id, bob.id),
        )
        assert cur.fetchone()[0] == "pending"
        conn.close()

    def test_send_friend_request_twice_does_not_error(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)
        db.send_friend_request(alice.id, bob.id)

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM friendships WHERE user_id=%s AND friend_id=%s",
            (alice.id, bob.id),
        )
        assert cur.fetchone()[0] == 1
        conn.close()

    def test_accept_friend_request_makes_them_friends(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)
        db.accept_friend_request(bob.id, alice.id)

        assert any(f.id == alice.id for f in db.get_friends(bob.id))
        assert any(f.id == bob.id for f in db.get_friends(alice.id))

    def test_decline_friend_request_removes_pending(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)
        db.decline_friend_request(bob.id, alice.id)

        assert db.get_friends(alice.id) == []
        assert db.get_friends(bob.id) == []

    def test_get_friends_works_both_directions(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)
        db.accept_friend_request(bob.id, alice.id)

        friends_alice = db.get_friends(alice.id)
        friends_bob = db.get_friends(bob.id)

        assert len(friends_alice) == 1 and friends_alice[0].id == bob.id
        assert len(friends_bob) == 1 and friends_bob[0].id == alice.id

    def test_get_online_friends_filters_by_online_status(self, users):
        alice, bob = users
        db.set_user_online(alice.id, True)
        db.send_friend_request(alice.id, bob.id)
        db.accept_friend_request(bob.id, alice.id)

        online = db.get_online_friends(bob.id)
        assert [f.id for f in online] == [alice.id]

        db.set_user_online(alice.id, False)
        assert db.get_online_friends(bob.id) == []

    def test_block_user_inserts_when_no_friendship_exists(self, users):
        alice, bob = users
        db.block_user(alice.id, bob.id)

        assert db.is_blocked(bob.id, alice.id) is True

    def test_block_user_updates_existing_friendship(self, users):
        alice, bob = users
        db.send_friend_request(alice.id, bob.id)
        db.accept_friend_request(bob.id, alice.id)

        db.block_user(alice.id, bob.id)

        assert db.is_blocked(bob.id, alice.id) is True
        assert db.get_friends(alice.id) == []

    def test_is_blocked_checks_both_directions(self, users):
        alice, bob = users
        db.block_user(bob.id, alice.id)

        assert db.is_blocked(alice.id, bob.id) is True
        assert db.is_blocked(bob.id, alice.id) is True


class TestAddFriendHandler:
    async def test_unknown_user_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_add_friend(fake_ws, {"username": "ghost"}, 1)

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_adding_self_errors(self, fake_ws, monkeypatch):
        me = models.User(id=1, username="me", is_online=False)
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: me)

        await handler.handle_add_friend(fake_ws, {"username": "me"}, 1)

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "cannot add yourself as a friend",
        }

    async def test_success_sends_request_and_notifies_target(
        self, fake_ws, fake_ws_factory, monkeypatch
    ):
        me = models.User(id=1, username="me", is_online=False)
        target = models.User(id=2, username="bob", is_online=False)
        sent = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: target)
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: me)
        monkeypatch.setattr(
            handler.db,
            "send_friend_request",
            lambda user_id, friend_id: sent.update(user_id=user_id, friend_id=friend_id),
        )

        target_ws = fake_ws_factory()
        handler.connected_clients[target.id] = target_ws
        try:
            await handler.handle_add_friend(fake_ws, {"username": "bob"}, 1)
            await asyncio.sleep(0)
        finally:
            handler.connected_clients.pop(target.id, None)

        assert sent == {"user_id": 1, "friend_id": 2}
        assert fake_ws.sent[-1] == {"type": "success", "message": "friend request sent"}
        assert target_ws.sent[-1] == {
            "type": "success",
            "message": "me sent you a friend request",
        }


class TestAcceptFriendHandler:
    async def test_unknown_user_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_accept_friend(fake_ws, {"username": "ghost"}, 1)

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_accepting_self_errors(self, fake_ws, monkeypatch):
        me = models.User(id=1, username="me", is_online=False)
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: me)

        await handler.handle_accept_friend(fake_ws, {"username": "me"}, 1)

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "cannot add yourself as a friend",
        }

    async def test_accept_notifies_both_users(
        self, fake_ws, fake_ws_factory, monkeypatch
    ):
        me = models.User(id=1, username="me", is_online=False)
        other = models.User(id=2, username="bob", is_online=False)
        accepted = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: other)
        monkeypatch.setattr(handler.db, "get_user_by_id", lambda user_id: me)
        monkeypatch.setattr(
            handler.db,
            "accept_friend_request",
            lambda user_id, friend_id: accepted.update(
                user_id=user_id, friend_id=friend_id
            ),
        )

        other_ws = fake_ws_factory()
        handler.connected_clients[other.id] = other_ws
        try:
            await handler.handle_accept_friend(fake_ws, {"username": "bob"}, 1)
            await asyncio.sleep(0)
        finally:
            handler.connected_clients.pop(other.id, None)

        assert accepted == {"user_id": 1, "friend_id": 2}
        assert fake_ws.sent[-1] == {
            "type": "success",
            "message": "friend request accepted",
        }
        assert other_ws.sent[-1] == {
            "type": "success",
            "message": "me accepted your friend request",
        }


class TestOnlineFriendsHandler:
    async def test_returns_online_friends(self, fake_ws, monkeypatch):
        online = [models.User(id=2, username="bob", is_online=True)]
        monkeypatch.setattr(handler.db, "get_online_friends", lambda user_id: online)

        await handler.handle_online_friends(fake_ws, 1)

        assert fake_ws.sent[-1] == {
            "type": "online_friends_result",
            "users": [{"id": 2, "username": "bob", "is_online": True}],
        }


class TestBlockHandler:
    async def test_unknown_user_errors(self, fake_ws, monkeypatch):
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: None)

        await handler.handle_block(fake_ws, {"username": "ghost"}, 1)

        assert fake_ws.sent[-1] == {"type": "error", "message": "user not found"}

    async def test_blocking_self_errors(self, fake_ws, monkeypatch):
        me = models.User(id=1, username="me", is_online=False)
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: me)

        await handler.handle_block(fake_ws, {"username": "me"}, 1)

        assert fake_ws.sent[-1] == {
            "type": "error",
            "message": "cannot block yourself",
        }

    async def test_block_success(self, fake_ws, monkeypatch):
        target = models.User(id=2, username="bob", is_online=False)
        blocked = {}
        monkeypatch.setattr(handler.db, "get_user_by_username", lambda username: target)
        monkeypatch.setattr(
            handler.db,
            "block_user",
            lambda user_id, target_id: blocked.update(
                user_id=user_id, target_id=target_id
            ),
        )

        await handler.handle_block(fake_ws, {"username": "bob"}, 1)

        assert blocked == {"user_id": 1, "target_id": 2}
        assert fake_ws.sent[-1] == {"type": "success", "message": "user blocked"}


class TestRouting:
    async def test_add_friend_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, data, user_id):
            calls.append((websocket, data, user_id))

        monkeypatch.setattr(handler, "handle_add_friend", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(
                fake_ws, json.dumps({"type": "add_friend", "username": "bob"})
            )
        finally:
            handler.connected_clients.pop(1, None)

        assert len(calls) == 1
        assert calls[0][1] == {"type": "add_friend", "username": "bob"}
        assert calls[0][2] == 1

    async def test_online_friends_routes_with_user_id(self, fake_ws, monkeypatch):
        calls = []

        async def stub(websocket, user_id):
            calls.append((websocket, user_id))

        monkeypatch.setattr(handler, "handle_online_friends", stub)
        handler.connected_clients[1] = fake_ws
        try:
            await handler.handle_message(fake_ws, json.dumps({"type": "online_friends"}))
        finally:
            handler.connected_clients.pop(1, None)

        assert calls == [(fake_ws, 1)]

    async def test_friend_routing_requires_login(self, fake_ws):
        await handler.handle_message(
            fake_ws, json.dumps({"type": "add_friend", "username": "bob"})
        )

        assert fake_ws.sent[-1] == {"type": "error", "message": "not logged in"}
