import json

import websockets


async def connect(server_url: str):
    websocket = await websockets.connect(server_url)
    return websocket


async def send(websocket, message: dict):
    await websocket.send(json.dumps(message))


async def receive(websocket) -> dict:
    raw = await websocket.recv()
    return json.loads(raw)


async def disconnect(websocket):
    await websocket.close()
