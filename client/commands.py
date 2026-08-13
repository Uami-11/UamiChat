def parse_input(raw: str) -> dict:
    """
    Parse user input into a structured command dictionary.

    Commands start with '/'.
    Anything else is treated as a room message.
    """

    raw = raw.strip()

    # Empty input
    if not raw:
        return {
            "type": "error",
            "message": "Input cannot be empty."
        }

    # Normal room message
    if not raw.startswith("/"):
        return {
            "type": "room_message",
            "content": raw
        }

    # Split command and arguments
    parts = raw.split()
    command = parts[0].lower()

    # /dm username message
    if command == "/dm":
        if len(parts) < 3:
            return {
                "type": "error",
                "message": "Usage: /dm username message"
            }

        username = parts[1]
        content = " ".join(parts[2:])

        return {
            "type": "direct_message",
            "to": username,
            "content": content
        }

    # /rooms
    elif command == "/rooms":
        return {
            "type": "list_rooms"
        }

    # /join room_name
    elif command == "/join":
        if len(parts) < 2:
            return {
                "type": "error",
                "message": "Usage: /join room_name"
            }

        return {
            "type": "join_room",
            "name": parts[1]
        }

    # /create room_name
    elif command == "/create":
        if len(parts) < 2:
            return {
                "type": "error",
                "message": "Usage: /create room_name"
            }

        return {
            "type": "create_room",
            "name": parts[1]
        }

    # /help
    elif command == "/help":
        return {
            "type": "help"
        }

    # /quit
    elif command == "/quit":
        return {
            "type": "quit"
        }

    # Unknown command
    else:
        return {
            "type": "error",
            "message": f"Unknown command: {command}"
        }


def get_command_list() -> list[str]:
    """
    Return all available commands and their descriptions.
    """

    return [
        "/dm username message    Send a direct message",
        "/rooms                  List all public rooms",
        "/join room_name         Join a room",
        "/create room_name       Create a new room",
        "/help                   Show available commands",
        "/quit                   Exit UamiChat"
    ]