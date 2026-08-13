import asyncio
import logging
import os

import websockets

from . import handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


async def connection_handler(websocket):
    try:
        async for raw_message in websocket:
            await handler.handle_message(websocket, raw_message)
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception:
        logging.exception("unhandled error while handling message")
        try:
            await websocket.send(
                '{"type": "error", "message": "internal server error"}'
            )
        except websockets.exceptions.ConnectionClosed:
            pass
    finally:
        for user_id, ws in list(handler.connected_clients.items()):
            if ws is websocket:
                handler.unregister_client(user_id)
                break


async def main():
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", "8765"))
    async with websockets.serve(connection_handler, host, port):
        print(f"UamiChat server running on ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
