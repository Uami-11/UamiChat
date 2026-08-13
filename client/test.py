"""
Test client — tests Week 1 Room functionality.

Tests:
1. Connect
2. Register
3. Login
4. Create a public room
5. List public rooms
6. Join the room
7. Disconnect
"""

import asyncio
import sys
import uuid

sys.path.insert(0, "client")

import connection


async def main():
    # Random suffix so repeated runs don't collide
    suffix = uuid.uuid4().hex[:8]
    username = f"testuser_{suffix}"
    room_name = f"Test Room {suffix}"

    # Connect
    ws = await connection.connect("ws://localhost:8765")
    print("Connected to server\n")

    # -------------------------
    # 1. Ping
    # -------------------------
    print("=== TEST 1: PING ===")

    await connection.send(ws, {
        "type": "ping"
    })

    resp = await connection.receive(ws)
    print(f"Ping response: {resp}\n")

    # -------------------------
    # 2. Register
    # -------------------------
    print("=== TEST 2: REGISTER ===")

    await connection.send(ws, {
        "type": "register",
        "username": username,
        "password": "testpass",
    })

    resp = await connection.receive(ws)
    print(f"Register response: {resp}\n")

    # -------------------------
    # 3. Login
    # -------------------------
    print("=== TEST 3: LOGIN ===")

    await connection.send(ws, {
        "type": "login",
        "username": username,
        "password": "testpass",
    })

    resp = await connection.receive(ws)
    print(f"Login response: {resp}\n")

    # -------------------------
    # 4. Create Room
    # -------------------------
    print("=== TEST 4: CREATE ROOM ===")

    await connection.send(ws, {
        "type": "create_room",
        "name": room_name,
        "is_private": False,
    })

    resp = await connection.receive(ws)
    print(f"Create room response: {resp}\n")

    # -------------------------
    # 5. List Public Rooms
    # -------------------------
    print("=== TEST 5: LIST ROOMS ===")

    await connection.send(ws, {
        "type": "list_rooms",
    })

    resp = await connection.receive(ws)
    print(f"Room list response: {resp}\n")

    # -------------------------
    # 6. Join Room
    # -------------------------
    print("=== TEST 6: JOIN ROOM ===")

    await connection.send(ws, {
        "type": "join_room",
        "name": room_name,
    })

    resp = await connection.receive(ws)
    print(f"Join room response: {resp}\n")

    # -------------------------
    # 7. Disconnect
    # -------------------------
    await connection.disconnect(ws)
    print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())