from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# Rich console instance
console = Console()


def print_welcome():
    """
    Display the UamiChat welcome banner.
    """

    welcome_panel = Panel(
        "[bold cyan]Welcome to UamiChat![/bold cyan]\n\n"
        "A simple terminal-based chat application.\n\n"
        "Type [bold yellow]/help[/bold yellow] "
        "to see the available commands.",
        title="UamiChat",
        border_style="cyan"
    )

    console.print(welcome_panel)


def print_message(username, content, timestamp):
    """
    Display a single chat message.
    """

    console.print(
        f"[bold cyan]{username}[/bold cyan] "
        f"[dim]({timestamp})[/dim]: {content}"
    )


def print_system(message):
    """
    Display a system notification.
    """

    console.print(
        f"[bold yellow][SYSTEM][/bold yellow] {message}"
    )


def print_error(message):
    """
    Display an error message in red.
    """

    console.print(
        f"[bold red][ERROR][/bold red] {message}"
    )


def print_help(commands):
    """
    Display the available commands in a Rich table.
    """

    table = Table(
        title="UamiChat Commands",
        show_header=True
    )

    table.add_column("Command", style="bold cyan")
    table.add_column("Description")

    for command in commands:
        # Split the command from its description
        parts = command.split(maxsplit=1)

        if len(parts) == 2:
            command_name = parts[0]
            description = parts[1]
        else:
            command_name = command
            description = ""

        table.add_row(command_name, description)

    console.print(
        Panel(
            table,
            title="Help",
            border_style="cyan"
        )
    )


def print_room_list(rooms):
    """
    Display a list of public rooms.

    Each room should be a dictionary containing:
    - id
    - name
    - is_private
    """

    table = Table(
        title="Public Rooms",
        show_header=True
    )

    table.add_column("Name", style="bold cyan")
    table.add_column("ID", style="green")
    table.add_column("Type", style="yellow")

    for room in rooms:
        table.add_row(
            str(room.get("name", "")),
            str(room.get("id", "")),
            "private" if room.get("is_private") else "public",
        )

    console.print(table)


def print_inbox(messages):
    """
    Display unread direct messages.

    Each message should be a dictionary containing:
    - from
    - content
    - timestamp (optional)
    """

    table = Table(
        title="Inbox",
        show_header=True
    )

    table.add_column("From", style="bold cyan")
    table.add_column("Message")
    table.add_column("Time", style="yellow")

    for message in messages:
        table.add_row(
            str(message.get("from", "")),
            str(message.get("content", "")),
            str(message.get("timestamp", "")),
        )

    console.print(table)


def print_online_friends(users):
    """
    Display a list of online friends.

    Each user should be a dictionary containing:
    - username
    """

    if not users:
        console.print("[bold yellow]No online friends[/bold yellow]")
        return

    table = Table(
        title="Online Friends",
        show_header=True
    )

    table.add_column("Username", style="bold cyan")

    for user in users:
        table.add_row(str(user.get("username", "")))

    console.print(table)


def clear_screen():
    """
    Clear the terminal screen.
    """

    console.clear()

def input_line_text(draft):
    """
    Return the terminal text used to render the current input draft.
    """
    return "\r\x1b[2K> " + draft


def render_input(draft):
    """
    Render the current input draft.
    """
    console.file.write(input_line_text(draft))
    console.file.flush()


def erase_line():
    """
    Erase the current input line.
    """
    console.file.write("\r\x1b[2K")
    console.file.flush()


def print_prompt():
    """
    Display the input prompt without a trailing newline.
    """

    console.print("> ", end="", highlight=False)