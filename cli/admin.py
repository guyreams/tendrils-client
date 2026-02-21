"""Interactive admin panel for managing Tendrils Server users and tokens."""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.client import AdminClient, TendrilsAPIError

console = Console()


MENU = """
[bold cyan]1.[/bold cyan] List users
[bold cyan]2.[/bold cyan] Get user token
[bold cyan]3.[/bold cyan] Register new user
[bold cyan]4.[/bold cyan] Update user name
[bold cyan]5.[/bold cyan] Rotate user token
[bold cyan]6.[/bold cyan] Delete user
[bold cyan]0.[/bold cyan] Exit
"""


def _print_menu():
    console.print(Panel(MENU.strip(), title="[bold]TENDRILS ADMIN PANEL[/bold]", border_style="cyan"))


def _input(prompt: str) -> str:
    """Prompt for input, return stripped string. Returns empty on EOF."""
    try:
        return input(f"  {prompt}: ").strip()
    except EOFError:
        return ""


def _pause():
    """Wait for user to press Enter before returning to menu."""
    try:
        input("\n  Press Enter to continue...")
    except EOFError:
        pass


# ── Menu Actions ────────────────────────────────────────────────────────────


def _action_list_users(client: AdminClient):
    users = client.list_users()
    if not users:
        console.print("\n  [dim]No registered users.[/dim]")
        return

    table = Table(title="Registered Users", show_lines=False)
    table.add_column("Owner ID", style="bold")
    table.add_column("Name", style="cyan")
    for user in users:
        table.add_row(user["owner_id"], user["name"])

    console.print()
    console.print(table)


def _action_get_token(client: AdminClient):
    owner_id = _input("Owner ID")
    if not owner_id:
        return

    result = client.get_token(owner_id)
    console.print(f"\n  [bold]Owner:[/bold]   {result['owner_id']}")
    console.print(f"  [bold]API Key:[/bold] [green]{result['api_key']}[/green]")


def _action_register(client: AdminClient):
    owner_id = _input("Owner ID")
    if not owner_id:
        return
    name = _input("Display name")
    if not name:
        return

    result = client.register_user(owner_id, name)
    console.print(f"\n  [green]Registered:[/green] {result['owner_id']}")
    console.print(f"  [bold]API Key:[/bold] [green]{result['api_key']}[/green]")


def _action_update(client: AdminClient):
    owner_id = _input("Owner ID")
    if not owner_id:
        return
    name = _input("New display name")
    if not name:
        return

    result = client.update_user(owner_id, name)
    console.print(f"\n  [green]Updated:[/green] {result['owner_id']} -> {result['name']}")


def _action_rotate(client: AdminClient):
    owner_id = _input("Owner ID")
    if not owner_id:
        return

    confirm = _input(f"Rotate token for '{owner_id}'? Old key will be invalidated (y/N)")
    if confirm.lower() != "y":
        console.print("  [dim]Cancelled.[/dim]")
        return

    result = client.rotate_token(owner_id)
    console.print(f"\n  [green]Rotated:[/green] {result['owner_id']}")
    console.print(f"  [bold]New API Key:[/bold] [green]{result['api_key']}[/green]")


def _action_delete(client: AdminClient):
    owner_id = _input("Owner ID")
    if not owner_id:
        return

    confirm = _input(f"Delete user '{owner_id}' and their character? (y/N)")
    if confirm.lower() != "y":
        console.print("  [dim]Cancelled.[/dim]")
        return

    result = client.delete_user(owner_id)
    console.print(f"\n  [green]{result['message']}[/green]")
    if result.get("character_removed"):
        console.print("  [yellow]In-game character was also removed.[/yellow]")


# ── Main Loop ───────────────────────────────────────────────────────────────

ACTIONS = {
    "1": ("List users", _action_list_users),
    "2": ("Get user token", _action_get_token),
    "3": ("Register new user", _action_register),
    "4": ("Update user name", _action_update),
    "5": ("Rotate user token", _action_rotate),
    "6": ("Delete user", _action_delete),
}


def admin_main(server_url: str, admin_secret: str):
    """Run the interactive admin panel."""
    client = AdminClient(server_url, admin_secret)

    # Verify connection + secret
    try:
        client.ping()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Cannot reach server at {server_url}")
        console.print(f"  {e}")
        sys.exit(1)

    try:
        client.list_users()
    except TendrilsAPIError as e:
        if e.status_code == 403:
            console.print("[bold red]Error:[/bold red] Invalid admin secret.")
            sys.exit(1)
        raise

    console.print(f"\n[bold]Connected to {server_url}[/bold]\n")

    try:
        while True:
            _print_menu()
            choice = _input("Choose")

            if choice == "0":
                break

            action = ACTIONS.get(choice)
            if action is None:
                console.print("  [red]Invalid choice.[/red]")
                continue

            label, func = action
            try:
                func(client)
            except TendrilsAPIError as e:
                console.print(f"\n  [bold red]Error:[/bold red] {e.message}")

            _pause()

    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    finally:
        client.close()
