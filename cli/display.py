"""Output formatting and rendering using rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _all_characters(state: dict) -> list[dict]:
    """Combine your_character + visible_characters into one list."""
    chars = []
    mine = state.get("your_character")
    if mine:
        chars.append(mine)
    for c in state.get("visible_characters", []):
        # Avoid duplicates
        if mine and c.get("id") == mine.get("id"):
            continue
        chars.append(c)
    return chars


def print_banner(server_info: dict):
    name = server_info.get("name", "Tendrils Server")
    version = server_info.get("version", "?")
    status = server_info.get("status", "unknown")
    banner = Text()
    banner.append(f"          {name.upper()}           \n", style="bold white")
    banner.append(f"            v{version} — {status.capitalize()}              ", style="dim white")
    console.print(Panel(banner, style="bold cyan", width=44))


def print_state(state: dict):
    """Show current turn info, character positions, HP bars."""
    round_num = state.get("round_number", state.get("round", "?"))
    is_my_turn = state.get("is_your_turn", False)
    mine = state.get("your_character", {})
    my_name = mine.get("name", "?") if mine else "?"

    if is_my_turn:
        console.print(f"\n[bold]Round {round_num}[/bold] — {my_name}'s turn\n")
    else:
        # Figure out whose turn it is from visible characters or just say waiting
        console.print(f"\n[bold]Round {round_num}[/bold] — Waiting for opponent's turn\n")

    characters = _all_characters(state)
    if not characters:
        return

    for char in characters:
        _print_hp_bar(char)
    console.print()


def _print_hp_bar(char: dict):
    name = char.get("name", "?")
    hp = char.get("current_hp", char.get("hp", 0))
    max_hp = char.get("max_hp", hp)
    pos = char.get("position", [0, 0])

    if max_hp > 0:
        ratio = hp / max_hp
    else:
        ratio = 0
    bar_width = 25
    filled = int(ratio * bar_width)
    empty = bar_width - filled

    if ratio > 0.5:
        color = "green"
    elif ratio > 0.25:
        color = "yellow"
    else:
        color = "red"

    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
    pos_str = f"({pos[0]}, {pos[1]})" if isinstance(pos, (list, tuple)) and len(pos) >= 2 else str(pos)
    console.print(f"  {name:<22} {bar}  {hp}/{max_hp} HP  {pos_str}")


def print_action_result(result: dict):
    """Color-coded combat results."""
    action_type = result.get("action_type", "")
    desc = result.get("description", "")
    success = result.get("success", True)

    if not success:
        error = result.get("error", desc)
        console.print(f"  [red]Failed:[/red] {error}")
        return

    if action_type == "attack":
        roll = result.get("attack_roll")
        hit = result.get("hit", False)
        damage = result.get("damage_dealt")
        target_hp = result.get("target_hp_remaining")

        console.print(f"  {desc}")
        if roll is not None:
            if hit:
                console.print(f"  [green]HIT![/green] {damage} damage dealt", end="")
                if target_hp is not None:
                    if target_hp <= 0:
                        console.print(f" — [bold red]TARGET SLAIN![/bold red]")
                    else:
                        console.print(f" — Target: {target_hp} HP remaining")
                else:
                    console.print()
            else:
                console.print(f"  [red]MISS![/red]")
    elif action_type in ("move", "dash"):
        path = result.get("movement_path", [])
        if path:
            dest = path[-1]
            console.print(f"  [cyan]Moved to ({dest[0]}, {dest[1]})[/cyan]")
        else:
            console.print(f"  [cyan]{desc}[/cyan]")
    elif action_type == "end_turn":
        console.print(f"  [dim]{desc}[/dim]")
    else:
        console.print(f"  [yellow]{desc}[/yellow]")


def print_log(events: list):
    """Formatted battle log."""
    if not events:
        console.print("[dim]No events yet.[/dim]")
        return

    for event in events:
        round_num = event.get("round_number", event.get("round", "?"))
        desc = event.get("description", event.get("message", str(event)))
        action_type = event.get("action_type", "")

        if action_type == "attack":
            style = "green" if event.get("hit") else "red"
        elif action_type in ("move", "dash"):
            style = "cyan"
        else:
            style = "white"

        console.print(f"  [dim]R{round_num}[/dim] [{style}]{desc}[/{style}]")


def print_map(state: dict):
    """Simple ASCII grid showing character positions, zoomed to relevant area."""
    characters = _all_characters(state)
    if not characters:
        console.print("[dim]No characters to display.[/dim]")
        return

    positions = {}
    legend = []
    for char in characters:
        pos = char.get("position", [0, 0])
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            x, y = int(pos[0]), int(pos[1])
        else:
            continue
        name = char.get("name", "?")
        hp = char.get("current_hp", char.get("hp", 0))
        max_hp = char.get("max_hp", hp)
        label = name[0].upper()
        # Avoid duplicate labels
        used = {v for v in positions.values()}
        if label in used:
            for c in name.upper():
                if c not in used and c != " ":
                    label = c
                    break
        positions[(x, y)] = label
        legend.append((label, name, hp, max_hp))

    # Calculate bounds with padding
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    pad = 3
    min_x = max(0, min(xs) - pad)
    max_x = min(19, max(xs) + pad)
    min_y = max(0, min(ys) - pad)
    max_y = min(19, max(ys) + pad)

    # Header row
    header = "    " + "".join(f"{x:>4}" for x in range(min_x, max_x + 1))
    console.print(header)

    # Grid rows
    for y in range(min_y, max_y + 1):
        row = f"{y:>3} "
        for x in range(min_x, max_x + 1):
            if (x, y) in positions:
                row += f" [bold yellow]{positions[(x, y)]}[/bold yellow]  "
            else:
                row += " .  "
        console.print(row)

    # Legend
    console.print()
    for label, name, hp, max_hp in legend:
        console.print(f"  [bold yellow]{label}[/bold yellow] = {name} ({hp}/{max_hp} HP)")
    console.print()


def print_help():
    """Command reference."""
    table = Table(title="Commands", show_header=True, header_style="bold cyan", show_lines=False, pad_edge=False)
    table.add_column("Command", style="bold white", min_width=24)
    table.add_column("Action", style="white")

    table.add_row("[bold]Game Setup[/bold]", "")
    table.add_row("new / create", "Create a new game")
    table.add_row("join <preset>", "Join as fighter, rogue, barbarian, or monk")
    table.add_row("join custom", "Interactive character builder")
    table.add_row("start", "Start combat")
    table.add_row("games", "Show current game info")
    table.add_row("", "")

    table.add_row("[bold]Combat[/bold]", "")
    table.add_row("move X Y", "Move to grid position")
    table.add_row("attack", "Attack nearest enemy")
    table.add_row("attack TARGET WEAPON", "Attack specific target with weapon")
    table.add_row("dodge", "Take the Dodge action")
    table.add_row("dash X Y", "Dash to position")
    table.add_row("disengage", "Take Disengage action")
    table.add_row("end / done", "End turn")
    table.add_row("", "")

    table.add_row("[bold]Info[/bold]", "")
    table.add_row("status / s", "Show game state and HP")
    table.add_row("map / m", "Show ASCII map")
    table.add_row("log", "Show battle log")
    table.add_row("help / h / ?", "This help")
    table.add_row("quit / exit / q", "Exit client")
    table.add_row("", "")

    table.add_row("[bold]Utility[/bold]", "")
    table.add_row("switch OWNER_ID", "Switch active character")
    table.add_row("auto", "Auto-play current character")
    table.add_row("demo", "Full automated demo game")

    console.print(table)
    console.print()


def print_error(msg: str):
    console.print(f"[bold red]Error:[/bold red] {msg}")


def print_success(msg: str):
    console.print(f"[green]{msg}[/green]")


def print_info(msg: str):
    console.print(f"[cyan]{msg}[/cyan]")


def print_round_header(round_num: int):
    console.print(f"\n[bold]{'═' * 6} Round {round_num} {'═' * 6}[/bold]\n")


def print_winner(name: str, hp: int, max_hp: int, rounds: int):
    text = Text()
    text.append(f"  WINNER: {name}          \n", style="bold white")
    text.append(f"      Survived with {hp}/{max_hp} HP             \n", style="white")
    text.append(f"      {rounds} rounds of combat                 ", style="dim white")
    console.print(Panel(text, style="bold yellow", width=44))


def prompt(session) -> str:
    """Context-aware input prompt."""
    if session.game_id is None:
        prefix = "tendrils"
    elif session.game_status == "waiting":
        short_id = session.game_id[:8] if len(session.game_id) > 8 else session.game_id
        prefix = f"tendrils [{short_id}]"
    else:
        prefix = "tendrils"

    try:
        return input(f"{prefix}> ").strip()
    except EOFError:
        return "quit"


def combat_prompt(round_num, turn_name: str, is_my_turn: bool) -> str:
    """Combat-aware prompt."""
    if is_my_turn:
        prefix = f"[R{round_num} -- {turn_name}'s turn]"
    else:
        prefix = f"[R{round_num} -- {turn_name}'s turn (waiting)]"

    try:
        return input(f"{prefix}> ").strip()
    except EOFError:
        return "quit"
