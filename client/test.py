"""
Test client — tests the server connection and Week 1 client features.
"""

import asyncio
import sys

sys.path.insert(0, "client")

import connection
from commands import parse_input, get_command_list
from ui import (
    print_welcome,
    print_message,
    print_system,
    print_error,
    print_help,
    print_room_list,
    clear_screen,
)


async def main():

    # -------------------------
    # UI TEST
    # -------------------------

    clear_screen()
    print_welcome()

    print_system("Starting client tests...")

    # -------------------------
    # COMMAND PARSER TEST
    # -------------------------

    print_system("Testing command parser...")

    test_inputs = [
        "/dm nirwan hello",
        "/rooms",
        "/join dev",
        "/create dev",
        "/help",
        "/quit",
        "hello everyone",
        "/dm",
        "/join",
        "/unknown",
    ]

    for raw in test_inputs:
        result = parse_input(raw)
        print(f"Input: {raw}")
        print(f"Result: {result}")
        print()

    # -------------------------
    # HELP TEST
    # -------------------------

    print_system("Testing help display...")
    print_help(get_command_list())

    # -------------------------
    # MESSAGE TEST
    # -------------------------

    print_system("Testing message display...")
    print_message(
        "testuser",
        "Hello everyone!",
        "12:30"
    )

    # -------------------------
    # ROOM LIST TEST
    # -------------------------

    print_system("Testing room list display...")

    test_rooms = [
        {
            "name": "general",
            "members": 5,
            "created": "2026-08-09"
        },
        {
            "name": "dev",
            "members": 3,
            "created": "2026-08-09"
        }
    ]

    print_room_list(test_rooms)

    # -------------------------
    # SERVER CONNECTION TEST
    # -------------------------

    print_system("Connecting to server...")

    ws = await connection.connect("ws://localhost:8765")

    print_system("Connected to server.")

    # -------------------------
    # PING TEST
    # -------------------------

    print_system("Testing ping...")

    await connection.send(ws, {
        "type": "ping"
    })

    resp = await connection.receive(ws)

    print(f"Ping response: {resp}")

    # -------------------------
    # REGISTER TEST
    # -------------------------

    print_system("Testing registration...")

    await connection.send(ws, {
        "type": "register",
        "username": "testuser",
        "password": "testpass",
    })

    resp = await connection.receive(ws)

    print(f"Register response: {resp}")

    # -------------------------
    # LOGIN TEST
    # -------------------------

    print_system("Testing login...")

    await connection.send(ws, {
        "type": "login",
        "username": "testuser",
        "password": "testpass",
    })

    resp = await connection.receive(ws)

    print(f"Login response: {resp}")

    # -------------------------
    # TEST COMMAND DICTIONARIES
    # -------------------------

    print_system("Testing client commands...")

    commands_to_test = [
        parse_input("/dm nirwan hello"),
        parse_input("/rooms"),
        parse_input("/join dev"),
        parse_input("/create dev"),
        parse_input("hello everyone"),
    ]

    for command in commands_to_test:
        print(f"Command: {command}")

    # -------------------------
    # ERROR TEST
    # -------------------------

    print_system("Testing error handling...")

    error_tests = [
        parse_input("/dm"),
        parse_input("/join"),
        parse_input("/create"),
        parse_input("/unknown"),
        parse_input(""),
    ]

    for error in error_tests:
        if error["type"] == "error":
            print_error(error["message"])

    # -------------------------
    # DISCONNECT
    # -------------------------

    await connection.disconnect(ws)

    print_system("Disconnected from server.")
    print_system("All tests completed.")


if __name__ == "__main__":
    asyncio.run(main())