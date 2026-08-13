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

    # /invite username
    elif command == "/invite":
        if len(parts) < 2:
            return {
                "type": "error",
                "message": "Usage: /invite username"
            }

        return {
            "type": "invite",
            "username": parts[1]
        }

    # /inbox
    elif command == "/inbox":
        return {
            "type": "inbox"
        }

    # /online
    elif command == "/online":
        return {
            "type": "online_friends"
        }

    # /addfriend username
    elif command == "/addfriend":
        if len(parts) < 2:
            return {
                "type": "error",
                "message": "Usage: /addfriend username"
            }

        return {
            "type": "add_friend",
            "username": parts[1]
        }

    # /block username
    elif command == "/block":
        if len(parts) < 2:
            return {
                "type": "error",
                "message": "Usage: /block username"
            }

        return {
            "type": "block",
            "username": parts[1]
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
        "/dm username message     Send a direct message",
        "/rooms                   List all public rooms",
        "/join room_name          Join a public room",
        "/create room_name        Create a new room",
        "/invite username         Invite someone to your room",
        "/inbox                   Show unread direct messages",
        "/online                  Show online friends",
        "/addfriend username      Send a friend request",
        "/block username          Block a user",
        "/help                    Show available commands",
        "/quit                    Exit UamiChat"
    ]