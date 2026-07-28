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
    cur.execute("SELECT user_id FROM room_members WHERE room_id=%s", (room_id,))
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
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"unknown message type: {msg_type}",
        }))


async def handle_register(websocket, data: dict):
    result = auth.register_user(data["username"], data["password"])
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
    result = auth.login_user(data["username"], data["password"])
    if result["success"]:
        register_client(result["user"].id, websocket)
        db.set_user_online(result["user"].id, True)
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
    await websocket.send(json.dumps({"type": "pong"}))
