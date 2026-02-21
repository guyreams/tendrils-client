"""Command parsing and dispatch for the interactive CLI."""

import math
import time

from cli.client import TendrilsClient, TendrilsAPIError
from cli.game_session import GameSession, PRESETS
from cli import display
from cli.display import _all_characters


def handle_command(cmd: str, client: TendrilsClient, session: GameSession) -> bool:
    """Parse and dispatch a command. Returns False to quit, True to continue."""
    if not cmd:
        return True

    parts = cmd.split()
    verb = parts[0].lower()
    args = parts[1:]

    try:
        if verb in ("quit", "exit", "q"):
            return False
        elif verb in ("help", "h", "?"):
            display.print_help()
        elif verb == "join":
            _cmd_join(args, client, session)
        elif verb == "start":
            _cmd_start(client, session)
        elif verb in ("games", "game"):
            _cmd_game_info(client, session)
        elif verb in ("status", "s"):
            _cmd_status(client, session)
        elif verb in ("map", "m"):
            _cmd_map(client, session)
        elif verb == "log":
            _cmd_log(client, session)
        elif verb == "move":
            _cmd_move(args, client, session)
        elif verb == "attack":
            _cmd_attack(args, client, session)
        elif verb == "dodge":
            _cmd_dodge(client, session)
        elif verb == "dash":
            _cmd_dash(args, client, session)
        elif verb == "disengage":
            _cmd_disengage(client, session)
        elif verb in ("end", "done"):
            _cmd_end_turn(client, session)
        elif verb == "switch":
            _cmd_switch(args, session)
        elif verb == "auto":
            _cmd_auto(client, session)
        elif verb == "demo":
            _cmd_demo(client, session)
        else:
            display.print_error(f"Unknown command: '{verb}'. Type 'help' for commands.")
    except TendrilsAPIError as e:
        display.print_error(e.message)
    except Exception as e:
        display.print_error(str(e))

    return True


# ── Game Setup ──────────────────────────────────────────────────────────────


def _cmd_join(args: list, client: TendrilsClient, session: GameSession):
    if not args:
        display.print_error("Usage: join <fighter|rogue|barbarian|monk|custom>")
        return

    preset_name = args[0].lower()

    if preset_name == "custom":
        char_data = _build_custom_character()
    elif preset_name in PRESETS:
        char_data = PRESETS[preset_name].copy()
    else:
        display.print_error(f"Unknown preset '{preset_name}'. Options: fighter, rogue, barbarian, monk, custom")
        return

    display.print_info(f"Joining as {char_data['name']}...")
    result = client.join_game(char_data)
    char_id = result["character_id"]
    message = result.get("message", "")
    session.add_character(char_data["owner_id"], char_id, char_data["name"])
    if message:
        display.print_success(message)
    else:
        display.print_success(f"Joined! Character ID: {char_id}")


def _build_custom_character() -> dict:
    display.console.print("\n[bold]Custom Character Builder[/bold]\n")
    name = input("  Name: ").strip() or "Custom Hero"
    owner_id = input("  Owner ID: ").strip() or "custom_player"

    def _int_input(prompt: str, default: int) -> int:
        val = input(f"  {prompt} [{default}]: ").strip()
        try:
            return int(val) if val else default
        except ValueError:
            return default

    max_hp = _int_input("Max HP", 25)
    armor_class = _int_input("Armor Class", 14)
    speed = _int_input("Speed", 30)

    display.console.print("\n  [dim]Ability Scores (default 10):[/dim]")
    abilities = {}
    for stat in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
        abilities[stat] = _int_input(f"  {stat.capitalize()}", 10)

    display.console.print("\n  [dim]Weapon:[/dim]")
    weapon_name = input("  Weapon name [Shortsword]: ").strip() or "Shortsword"
    attack_bonus = _int_input("Attack bonus", 4)
    damage_dice = input("  Damage dice [1d6]: ").strip() or "1d6"
    damage_bonus = _int_input("Damage bonus", 2)
    damage_type = input("  Damage type [slashing]: ").strip() or "slashing"

    return {
        "name": name,
        "owner_id": owner_id,
        "max_hp": max_hp,
        "armor_class": armor_class,
        "speed": speed,
        "ability_scores": abilities,
        "attacks": [
            {
                "name": weapon_name,
                "attack_bonus": attack_bonus,
                "damage_dice": damage_dice,
                "damage_bonus": damage_bonus,
                "damage_type": damage_type,
                "reach": 5,
            }
        ],
    }


def _cmd_start(client: TendrilsClient, session: GameSession):
    display.print_info("Starting combat...")
    result = client.start_game()
    session.game_status = "active"
    display.print_success(result.get("message", "Combat started!"))

    initiative = result.get("initiative_order", [])
    if initiative:
        display.console.print(f"  Initiative: {', '.join(str(i) for i in initiative)}")

    _show_current_state(client, session)


def _cmd_game_info(client: TendrilsClient, session: GameSession):
    result = client.get_game()
    display.console.print(f"\n[bold]Game Status:[/bold] {result.get('status', '?')}")
    session.game_status = result.get("status", session.game_status)

    winner_id = result.get("winner_id")
    if winner_id:
        display.console.print(f"  Winner: {winner_id}")

    chars = result.get("characters", [])
    if chars:
        display.console.print(f"  Characters: {len(chars)}")
        for c in chars:
            if isinstance(c, dict):
                cid = c.get("character_id", c.get("id", "?"))
                display.console.print(f"    - {c.get('name', '?')} (ID: {cid})")
            else:
                display.console.print(f"    - {c}")
    display.console.print()


# ── Combat ──────────────────────────────────────────────────────────────────


def _require_active(session: GameSession) -> str | None:
    """Return active character_id or print error and return None."""
    if not session.active_character:
        display.print_error("No active character. Join a game first.")
        return None
    return session.active_character


def _cmd_move(args: list, client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return
    if len(args) < 2:
        display.print_error("Usage: move X Y")
        return
    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        display.print_error("Coordinates must be integers.")
        return

    result = client.submit_action({
        "character_id": char_id,
        "action_type": "move",
        "target_position": [x, y],
    })
    display.print_action_result(result)
    _check_game_over(client, session)


def _cmd_attack(args: list, client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return

    action = {
        "character_id": char_id,
        "action_type": "attack",
    }

    if len(args) >= 1:
        action["target_id"] = args[0]
    if len(args) >= 2:
        action["weapon_name"] = args[1]

    result = client.submit_action(action)
    display.print_action_result(result)
    _check_game_over(client, session)


def _cmd_dodge(client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return
    result = client.submit_action({
        "character_id": char_id,
        "action_type": "dodge",
    })
    display.print_action_result(result)
    _check_game_over(client, session)


def _cmd_dash(args: list, client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return
    if len(args) < 2:
        display.print_error("Usage: dash X Y")
        return
    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        display.print_error("Coordinates must be integers.")
        return

    result = client.submit_action({
        "character_id": char_id,
        "action_type": "dash",
        "target_position": [x, y],
    })
    display.print_action_result(result)
    _check_game_over(client, session)


def _cmd_disengage(client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return
    result = client.submit_action({
        "character_id": char_id,
        "action_type": "disengage",
    })
    display.print_action_result(result)
    _check_game_over(client, session)


def _cmd_end_turn(client: TendrilsClient, session: GameSession):
    char_id = _require_active(session)
    if not char_id:
        return
    result = client.submit_action({
        "character_id": char_id,
        "action_type": "end_turn",
    })
    display.print_action_result(result)
    _check_game_over(client, session)


# ── Info ────────────────────────────────────────────────────────────────────


def _cmd_status(client: TendrilsClient, session: GameSession):
    char_id = session.active_character or (session.get_all_character_ids()[0] if session.characters else None)
    if not char_id:
        display.print_error("No characters joined yet.")
        return
    state = client.get_state(char_id)
    _update_session_from_state(state, session)
    display.print_state(state)


def _cmd_map(client: TendrilsClient, session: GameSession):
    char_id = session.active_character or (session.get_all_character_ids()[0] if session.characters else None)
    if not char_id:
        display.print_error("No characters joined yet.")
        return
    state = client.get_state(char_id)
    _update_session_from_state(state, session)
    display.print_map(state)


def _cmd_log(client: TendrilsClient, session: GameSession):
    events = client.get_log()
    if not events:
        # Log is archived after combat ends; fall back to combat history
        try:
            history = client.get_history()
            if history:
                # Show the most recent combat log
                latest = history[-1] if isinstance(history, list) else history
                events = latest.get("events", latest.get("log", []))
                if events:
                    display.console.print("[dim](Showing last combat log)[/dim]")
        except TendrilsAPIError:
            pass
    display.print_log(events)


# ── Utility ─────────────────────────────────────────────────────────────────


def _cmd_switch(args: list, session: GameSession):
    if not args:
        display.print_error("Usage: switch OWNER_ID")
        display.console.print("  Available owners:")
        for oid, char in session.characters.items():
            marker = " <-- active" if char["character_id"] == session.active_character else ""
            display.console.print(f"    {oid}: {char['name']}{marker}")
        return

    owner_id = args[0]
    if owner_id in session.characters:
        session.active_character = session.characters[owner_id]["character_id"]
        display.print_success(f"Switched to {session.characters[owner_id]['name']}")
    else:
        display.print_error(f"No character with owner_id '{owner_id}'. Use 'switch' to list.")


def _cmd_auto(client: TendrilsClient, session: GameSession):
    """Auto-play current character with simple AI."""
    char_id = _require_active(session)
    if not char_id:
        return

    display.print_info("Auto-playing... (Ctrl+C to stop)")
    try:
        _auto_play_loop(client, session, char_ids=[char_id])
    except KeyboardInterrupt:
        display.console.print("\n[yellow]Auto-play stopped.[/yellow]")


def _cmd_demo(client: TendrilsClient, session: GameSession):
    """Full automated demo game."""
    display.console.print()

    # 1. Join fighter and rogue
    session.characters.clear()
    session.active_character = None
    for preset_name in ("fighter", "rogue"):
        char_data = PRESETS[preset_name]
        display.print_info(f"Joining {char_data['name']}...")
        join_result = client.join_game(char_data)
        char_id = join_result["character_id"]
        message = join_result.get("message", "")
        session.add_character(char_data["owner_id"], char_id, char_data["name"])
        if message:
            display.print_success(message)
        else:
            display.print_success(f"Joined! (ID: {char_id})")

    # 2. Start combat
    display.print_info("Starting combat...")
    start_result = client.start_game()
    session.game_status = "active"
    display.print_success(start_result.get("message", "Combat started!"))

    initiative = start_result.get("initiative_order", [])
    if initiative:
        display.console.print(f"  Initiative: {', '.join(str(i) for i in initiative)}")

    # 3. Show initial state + map
    _show_current_state(client, session)

    # 4. Auto-play
    display.console.print()
    all_char_ids = session.get_all_character_ids()
    try:
        _auto_play_loop(client, session, char_ids=all_char_ids, delay=0.5)
    except KeyboardInterrupt:
        display.console.print("\n[yellow]Demo stopped.[/yellow]")


# ── Internal Helpers ────────────────────────────────────────────────────────


def _show_current_state(client: TendrilsClient, session: GameSession):
    """Fetch and display current state + map."""
    char_id = session.active_character or (session.get_all_character_ids()[0] if session.characters else None)
    if not char_id:
        return
    try:
        state = client.get_state(char_id)
        _update_session_from_state(state, session)
        display.print_state(state)
        display.print_map(state)
    except TendrilsAPIError:
        pass


def _update_session_from_state(state: dict, session: GameSession):
    """Update session status from a state response."""
    status = state.get("status")
    if status:
        # Server auto-transitions completed→waiting, so winner_id in waiting means game over
        if status == "waiting" and state.get("winner_id"):
            session.game_status = "completed"
        else:
            session.game_status = status


def _check_game_over(client: TendrilsClient, session: GameSession):
    """After an action, check if the game ended."""
    try:
        char_id = session.active_character or session.get_all_character_ids()[0]
        state = client.get_state(char_id)
        _update_session_from_state(state, session)

        status = state.get("status")
        if status == "completed" or (status == "waiting" and state.get("winner_id")):
            _print_game_result(state, client, session)
    except TendrilsAPIError:
        pass


def _print_game_result(state: dict, client: TendrilsClient, session: GameSession):
    """Print the winner and final summary."""
    session.game_status = "completed"
    # _all_characters works with /game/state responses; fall back to
    # the "characters" list from /game responses.
    characters = _all_characters(state) or state.get("characters", [])
    round_num = state.get("round_number", state.get("round", 0))
    winner_id = state.get("winner_id")

    # Find winner by winner_id or by who's alive
    winner = None
    if winner_id:
        for c in characters:
            cid = c.get("id") or c.get("character_id")
            if cid == winner_id:
                winner = c
                break

    if not winner:
        alive = [c for c in characters if c.get("current_hp", c.get("hp", 0)) > 0]
        if alive:
            winner = alive[0]

    if winner:
        name = winner.get("name", "Unknown")
        hp = winner.get("current_hp", winner.get("hp", 0))
        max_hp = winner.get("max_hp", 0)
    else:
        name = "Unknown"
        hp = 0
        max_hp = 0

    display.console.print()
    display.print_winner(name, hp, max_hp, round_num if isinstance(round_num, int) else 0)


def _auto_play_loop(
    client: TendrilsClient,
    session: GameSession,
    char_ids: list[str],
    delay: float = 0.3,
):
    """Simple AI loop: move toward nearest enemy, attack if adjacent."""
    last_round = 0
    max_iterations = 200  # safety limit

    for _ in range(max_iterations):
        # Try each of our character IDs until we find one where is_your_turn is True
        state = None
        turn_char_id = None

        for cid in char_ids:
            try:
                s = client.get_state(cid)
            except TendrilsAPIError:
                # Character may no longer exist after combat reset;
                # check if the game ended via get_game().
                try:
                    game = client.get_game()
                    if game.get("winner_id"):
                        _print_game_result(game, client, session)
                        return
                except TendrilsAPIError:
                    pass
                continue

            _update_session_from_state(s, session)

            s_status = s.get("status")
            if s_status == "completed" or (s_status == "waiting" and s.get("winner_id")):
                _print_game_result(s, client, session)
                return

            if s.get("is_your_turn"):
                state = s
                turn_char_id = cid
                break

        if not state or not turn_char_id:
            # Not any of our characters' turn — wait and retry
            time.sleep(delay)
            continue

        # Round header + status summary
        round_num = state.get("round_number", state.get("round", 0))
        if isinstance(round_num, int) and round_num > last_round:
            last_round = round_num
            display.print_round_header(round_num)
            display.print_state(state)

        # Get all characters
        characters = _all_characters(state)

        # Find my character and enemies
        me = state.get("your_character")
        enemies = []
        for c in characters:
            cid = c.get("id")
            if cid != turn_char_id and c.get("current_hp", c.get("hp", 0)) > 0:
                enemies.append(c)

        if not me or not enemies:
            _auto_end_turn(client, session, turn_char_id)
            time.sleep(delay)
            continue

        my_pos = me.get("position", [0, 0])
        my_name = me.get("name", "?")

        # Find nearest enemy
        nearest = min(enemies, key=lambda e: _dist(my_pos, e.get("position", [0, 0])))
        enemy_pos = nearest.get("position", [0, 0])
        enemy_id = nearest.get("id")
        dist = _dist(my_pos, enemy_pos)

        # Simple AI: if adjacent (distance <= ~1.5 grid), attack. Otherwise move closer.
        if dist <= 1.5:
            # Attack
            action = {
                "character_id": turn_char_id,
                "action_type": "attack",
                "target_id": enemy_id,
            }
            display.console.print(f"  [{my_name}] Attacks {nearest.get('name', '?')}!")
            try:
                result = client.submit_action(action)
                display.print_action_result(result)
            except TendrilsAPIError as e:
                display.print_error(e.message)

            # End turn after attacking
            time.sleep(delay)
            _auto_end_turn(client, session, turn_char_id)
        else:
            # Move toward enemy
            speed = me.get("speed", 30)
            max_squares = speed // 5
            target = _move_toward(my_pos, enemy_pos, max_squares)

            display.console.print(f"  [{my_name}] Moves to ({target[0]}, {target[1]})")
            action = {
                "character_id": turn_char_id,
                "action_type": "move",
                "target_position": target,
            }
            try:
                result = client.submit_action(action)
                display.print_action_result(result)
            except TendrilsAPIError as e:
                display.print_error(e.message)
                _auto_end_turn(client, session, turn_char_id)
                time.sleep(delay)
                continue

            time.sleep(delay)

            # After moving, check if now adjacent and can attack
            try:
                state2 = client.get_state(turn_char_id)
            except TendrilsAPIError:
                _auto_end_turn(client, session, turn_char_id)
                time.sleep(delay)
                continue

            me2 = state2.get("your_character")
            if me2:
                new_pos = me2.get("position", target)
                # Recalculate enemy position from updated state
                chars2 = _all_characters(state2)
                enemy2 = None
                for c in chars2:
                    if c.get("id") == enemy_id:
                        enemy2 = c
                        break
                ep = enemy2.get("position", enemy_pos) if enemy2 else enemy_pos
                new_dist = _dist(new_pos, ep)
                if new_dist <= 1.5 and state2.get("is_your_turn"):
                    display.console.print(f"  [{my_name}] Attacks {nearest.get('name', '?')}!")
                    attack_action = {
                        "character_id": turn_char_id,
                        "action_type": "attack",
                        "target_id": enemy_id,
                    }
                    try:
                        attack_result = client.submit_action(attack_action)
                        display.print_action_result(attack_result)
                    except TendrilsAPIError as e:
                        display.print_error(e.message)

            _auto_end_turn(client, session, turn_char_id)

        time.sleep(delay)


def _auto_end_turn(client: TendrilsClient, session: GameSession, char_id: str):
    """End a character's turn, ignoring errors."""
    try:
        client.submit_action({
            "character_id": char_id,
            "action_type": "end_turn",
        })
    except TendrilsAPIError:
        pass


def _dist(a: list, b: list) -> float:
    """Euclidean distance between two grid positions."""
    ax = a[0] if isinstance(a, (list, tuple)) and len(a) >= 2 else 0
    ay = a[1] if isinstance(a, (list, tuple)) and len(a) >= 2 else 0
    bx = b[0] if isinstance(b, (list, tuple)) and len(b) >= 2 else 0
    by = b[1] if isinstance(b, (list, tuple)) and len(b) >= 2 else 0
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _move_toward(my_pos: list, target_pos: list, max_squares: int) -> list[int]:
    """Calculate the best position to move toward the target within movement range."""
    mx, my = my_pos[0], my_pos[1]
    tx, ty = target_pos[0], target_pos[1]

    dx = tx - mx
    dy = ty - my
    dist = math.sqrt(dx ** 2 + dy ** 2)

    if dist <= max_squares:
        # Move adjacent to target (1 square away)
        if dist <= 1:
            return [mx, my]  # already adjacent
        ratio = (dist - 1) / dist
        nx = mx + dx * ratio
        ny = my + dy * ratio
        return [int(round(nx)), int(round(ny))]
    else:
        # Move max distance toward target
        ratio = max_squares / dist
        nx = mx + dx * ratio
        ny = my + dy * ratio
        return [int(round(nx)), int(round(ny))]
