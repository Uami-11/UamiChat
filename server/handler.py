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