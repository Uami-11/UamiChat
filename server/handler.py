import json

from . import auth
from . import db

connected_clients = {}


def register_client(user_id, websocket):
    connected_clients[user_id] = websocket


def unregister_client(user_id):
    connected_clients.pop(user_id, None)
    db.set_user_online(user_id, False)


def send_to_client(user_id, message: dict):
    websocket = connected_clients.get(user_id)
    if websocket:
        import asyncio
        asyncio.ensure_future(websocket.send(json.dumps(message)))


def broadcast_to_room(room_id, message: dict, exclude_user_id=None):
    from . import db as database

    cur = database.get_connection().cursor()
    cur.execute(
        "SELECT user_id FROM room_members WHERE room_id=%s",
        (room_id,),
    )

    members = cur.fetchall()
    cur.connection.close()

    for (user_id,) in members:
        if user_id != exclude_user_id:
            send_to_client(user_id, message)


async def handle_message(websocket, raw_message: str):
    data = json.loads(raw_message)
    msg_type = data.get("type")

    if msg_type == "register":
        await handle_register(websocket, data)

    elif msg_type == "login":
        await handle_login(websocket, data)

    elif msg_type == "ping":
        await handle_ping(websocket, data)

    # Week 1 - Rooms
    elif msg_type == "create_room":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_create_room(websocket, data, user_id)

    elif msg_type == "join_room":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_join_room(websocket, data, user_id)

    elif msg_type == "list_rooms":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_list_rooms(websocket, user_id)

    elif msg_type == "add_friend":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_add_friend(websocket, data, user_id)

    elif msg_type == "accept_friend":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_accept_friend(websocket, data, user_id)

    elif msg_type == "online_friends":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_online_friends(websocket, user_id)

    elif msg_type == "block":
        user_id = None

        for uid, client in connected_clients.items():
            if client == websocket:
                user_id = uid
                break

        if user_id is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "not logged in",
            }))
            return

        await handle_block(websocket, data, user_id)

    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"unknown message type: {msg_type}",
        }))


async def handle_register(websocket, data: dict):
    result = auth.register_user(
        data["username"],
        data["password"],
    )

    if result["success"]:
        await websocket.send(json.dumps({
            "type": "success",
            "message": "registered",
            "username": result["user"].username,
        }))
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": result["message"],
        }))


async def handle_login(websocket, data: dict):
    result = auth.login_user(
        data["username"],
        data["password"],
    )

    if result["success"]:
        register_client(
            result["user"].id,
            websocket,
        )

        db.set_user_online(
            result["user"].id,
            True,
        )

        await websocket.send(json.dumps({
            "type": "success",
            "message": "logged in",
            "username": result["user"].username,
        }))
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": result["message"],
        }))


async def handle_ping(websocket, data: dict):
    await websocket.send(
        json.dumps({
            "type": "pong"
        })
    )


# ============================================================
# PARU MAHARJAN - WEEK 1 ROOMS
# ============================================================


async def handle_create_room(websocket, data, user_id):
    name = data.get("name")
    is_private = data.get("is_private", False)

    room = db.create_room(
        name,
        is_private,
        user_id,
    )

    if room is None:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "room name already exists",
        }))
        return

    # Automatically add the creator as a member
    db.add_room_member(
        room.id,
        user_id,
    )

    await websocket.send(json.dumps({
        "type": "success",
        "message": "room created",
        "room": {
            "id": room.id,
            "name": room.room_name,
            "is_private": room.is_private,
            "owner_id": room.owner_id,
        },
    }))


async def handle_join_room(websocket, data, user_id):
    name = data.get("name")

    room = db.get_room_by_name(name)

    # Room does not exist
    if room is None:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "room not found",
        }))
        return

    # Private rooms cannot be joined without an invite
    if room.is_private:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "cannot join private room without invite",
        }))
        return

    # Add user to the public room
    db.add_room_member(
        room.id,
        user_id,
    )

    await websocket.send(json.dumps({
        "type": "success",
        "message": "joined room",
    }))


async def handle_list_rooms(websocket, user_id):
    rooms = db.get_public_rooms()

    room_list = []

    for room in rooms:
        room_list.append({
            "id": room.id,
            "name": room.room_name,
            "is_private": room.is_private,
            "owner_id": room.owner_id,
        })

    await websocket.send(json.dumps({
        "type": "room_list",
        "rooms": room_list,
    }))


# ============================================================
# SURYANSH BIKRAM SHAH - WEEK 1 + WEEK 2 FRIENDS + BLOCK
# ============================================================


async def handle_add_friend(websocket, data, user_id):
    username = data.get("username")

    target = db.get_user_by_username(username)

    if target is None:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "user not found",
        }))
        return

    if target.id == user_id:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "cannot add yourself as a friend",
        }))
        return

    db.send_friend_request(user_id, target.id)

    await websocket.send(json.dumps({
        "type": "success",
        "message": "friend request sent",
    }))

    if target.id in connected_clients:
        sender = db.get_user_by_id(user_id)
        send_to_client(target.id, {
            "type": "success",
            "message": f"{sender.username} sent you a friend request",
        })


async def handle_accept_friend(websocket, data, user_id):
    username = data.get("username")

    other = db.get_user_by_username(username)

    if other is None:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "user not found",
        }))
        return

    if other.id == user_id:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "cannot add yourself as a friend",
        }))
        return

    db.accept_friend_request(user_id, other.id)

    await websocket.send(json.dumps({
        "type": "success",
        "message": "friend request accepted",
    }))

    if other.id in connected_clients:
        accepter = db.get_user_by_id(user_id)
        send_to_client(other.id, {
            "type": "success",
            "message": f"{accepter.username} accepted your friend request",
        })


async def handle_online_friends(websocket, user_id):
    users = db.get_online_friends(user_id)

    user_list = []

    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "is_online": user.is_online,
        })

    await websocket.send(json.dumps({
        "type": "online_friends_result",
        "users": user_list,
    }))


async def handle_block(websocket, data, user_id):
    username = data.get("username")

    target = db.get_user_by_username(username)

    if target is None:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "user not found",
        }))
        return

    if target.id == user_id:
        await websocket.send(json.dumps({
            "type": "error",
            "message": "cannot block yourself",
        }))
        return

    db.block_user(user_id, target.id)

    await websocket.send(json.dumps({
        "type": "success",
        "message": "user blocked",
    }))