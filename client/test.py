"""
Test client — proves the server works.

TEAM MEMBERS: This file is an example only.
Replace it with your own client/main.py when building the real client.
"""

import asyncio
import sys

sys.path.insert(0, "client")

import connection


async def main():
    ws = await connection.connect("ws://localhost:8765")
    print("Connected to server")

    await connection.send(ws, {"type": "ping"})
    resp = await connection.receive(ws)
    print(f"Ping response: {resp}")

    await connection.send(ws, {
        "type": "register",
        "username": "testuser",
        "password": "testpass",
    })
    resp = await connection.receive(ws)
    print(f"Register response: {resp}")

    await connection.send(ws, {
        "type": "login",
        "username": "testuser",
        "password": "testpass",
    })
    resp = await connection.receive(ws)
    print(f"Login response: {resp}")

    await connection.disconnect(ws)
    print("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
