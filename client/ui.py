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
    - name
    - members
    - created
    """

    table = Table(
        title="Public Rooms",
        show_header=True
    )

    table.add_column("Name", style="bold cyan")
    table.add_column("Members", style="green")
    table.add_column("Created", style="yellow")

    for room in rooms:
        name = str(room.get("name", ""))
        members = str(room.get("members", ""))
        created = str(room.get("created", ""))

        table.add_row(
            name,
            members,
            created
        )

    console.print(table)


def clear_screen():
    """
    Clear the terminal screen.
    """

    console.clear()