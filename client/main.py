import asyncio
import os
import sys

import websockets
import websockets.exceptions
from rich.prompt import Prompt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import commands, connection, ui  # noqa: E402

SERVER_URL = os.environ.get("UAMICHAT_SERVER_URL", "ws://localhost:8765")

current_room = None


def with_room_context(result: dict, room) -> dict:
    """
    Attach the id of the room the user is currently in to messages that need it.
    Returns an error dict when a message needs a room but there is none.
    """
    msg_type = result.get("type")

    if msg_type in ("room_message", "invite"):
        if room is None:
            return {"type": "error", "message": "you are not in a room yet"}

        result["room_id"] = room["id"]

    return result


def read_input() -> str:
    """Read a line from stdin without printing a prompt."""
    return input("")


def prompt_login() -> dict:
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    return {"username": username, "password": password}


def prompt_register() -> dict:
    while True:
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)
        confirm = Prompt.ask("Confirm password", password=True)

        if password != confirm:
            ui.print_error("Passwords do not match")
            continue

        return {"username": username, "password": password}


async def listen(websocket):
    global current_room

    try:
        while True:
            message = await connection.receive(websocket)
            msg_type = message.get("type")

            ui.console.print()

            if msg_type == "room_message":
                ui.print_message(
                    message.get("from", "?"),
                    message.get("content", ""),
                    message.get("timestamp", ""),
                )

            elif msg_type == "direct_message":
                ui.print_message(
                    message.get("from", "?"),
                    message.get("content", ""),
                    message.get("timestamp", ""),
                )

            elif msg_type == "room_list":
                ui.print_room_list(message.get("rooms", []))

            elif msg_type == "inbox_result":
                ui.print_inbox(message.get("messages", []))

            elif msg_type == "online_friends_result":
                ui.print_online_friends(message.get("users", []))

            elif msg_type == "invite_received":
                ui.print_system(
                    f"{message.get('from')} invited you to room {message.get('room')}"
                )

            elif msg_type == "error":
                ui.print_error(message.get("message", "unknown error"))

            elif msg_type == "success":
                ui.print_system(message.get("message", ""))

                if message.get("room") is not None:
                    current_room = {
                        "id": message["room"].get("id"),
                        "name": message["room"].get("name"),
                    }

            ui.print_prompt()
    except websockets.exceptions.ConnectionClosed:
        ui.print_system("Disconnected from server")


async def input_loop(websocket):
    loop = asyncio.get_event_loop()

    while True:
        raw = await loop.run_in_executor(None, read_input)

        result = commands.parse_input(raw)
        result = with_room_context(result, current_room)

        if result["type"] == "quit":
            await connection.disconnect(websocket)
            break

        elif result["type"] == "error":
            ui.print_error(result["message"])
            ui.print_prompt()

        elif result["type"] == "help":
            ui.print_help(commands.get_command_list())
            ui.print_prompt()

        else:
            try:
                await connection.send(websocket, result)
            except websockets.exceptions.ConnectionClosed:
                ui.print_error("Connection lost")
                break

            if result["type"] == "room_message":
                ui.print_prompt()


async def main():
    ui.clear_screen()
    ui.print_welcome()

    choice = Prompt.ask(
        "Login or register?",
        choices=["login", "register"],
        default="login",
    )

    credentials = prompt_login() if choice == "login" else prompt_register()

    try:
        websocket = await connection.connect(SERVER_URL)
    except (OSError, websockets.exceptions.WebSocketException):
        ui.print_error("could not connect to server")
        return

    await connection.send(websocket, {"type": choice, **credentials})

    response = await connection.receive(websocket)

    if response.get("type") != "success":
        ui.print_error(response.get("message", "authentication failed"))
        await connection.disconnect(websocket)
        return

    if choice == "register":
        await connection.send(websocket, {"type": "login", **credentials})
        response = await connection.receive(websocket)

        if response.get("type") != "success":
            ui.print_error(response.get("message", "login failed"))
            await connection.disconnect(websocket)
            return

    ui.clear_screen()
    ui.print_system(f"Welcome, {response.get('username')}")
    ui.print_prompt()

    listen_task = asyncio.create_task(listen(websocket))

    try:
        await input_loop(websocket)
    finally:
        listen_task.cancel()
        await connection.disconnect(websocket)


if __name__ == "__main__":
    asyncio.run(main())
