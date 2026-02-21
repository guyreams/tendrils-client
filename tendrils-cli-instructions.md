# Tendrils CLI Client — Claude Code Build Instructions

## Overview

Build an interactive command-line client for the Tendrils Server API. The client should feel like a text-based RPG — clean prompts, readable output, color-coded combat results. It wraps the REST API so testers never need to write curl commands or raw JSON.

The server is already running at a configurable URL (default: `https://web-production-969c8.up.railway.app`).

---

## Tech Stack

- **Python 3.12+**
- **httpx** — HTTP client (async-capable, already a project dependency)
- **rich** — Terminal formatting, colors, tables (install via pip)
- No other dependencies. Keep it simple.

---

## Project Location

Create all files inside the existing `tendrils-server` project:

```
tendrils-server/
├── cli/
│   ├── __init__.py
│   ├── client.py          # API client wrapper (all HTTP calls)
│   ├── display.py         # Output formatting and rendering
│   ├── commands.py        # Command parsing and dispatch
│   └── game_session.py    # Session state tracking
├── play.py                # Entry point — run this to play
└── requirements.txt       # Add rich and httpx if not already present
```

---

## Entry Point: `play.py`

The main script. Run with:
```bash
python play.py
python play.py --server https://web-production-969c8.up.railway.app
python play.py --server http://localhost:8000
```

On launch:
1. Parse `--server` argument (default to `https://web-production-969c8.up.railway.app`)
2. Ping the server root endpoint to verify connectivity
3. Print a welcome banner with server name and version
4. Drop into the interactive command loop

---

## API Client: `cli/client.py`

A clean wrapper class around all Tendrils API endpoints. Every method returns parsed Python dicts — no raw response handling in other files.

```python
class TendrilsClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(timeout=30.0)

    def ping(self) -> dict
    def create_game(self, name: str = "CLI Arena") -> dict
    def join_game(self, game_id: str, character_data: dict) -> dict
    def start_game(self, game_id: str) -> dict
    def get_state(self, game_id: str, character_id: str) -> dict
    def submit_action(self, game_id: str, action_data: dict) -> dict
    def get_log(self, game_id: str) -> list
```

All methods should raise clear exceptions on HTTP errors with the server's error message included.

---

## Session State: `cli/game_session.py`

Track the current session so users don't have to retype IDs:

```python
class GameSession:
    game_id: str | None
    characters: dict[str, dict]    # owner_id -> {character_id, name, owner_id}
    active_character: str | None   # character_id of the character currently being controlled
    game_status: str | None        # waiting, active, completed
```

---

## Display: `cli/display.py`

Use `rich` for formatting. Create helper functions:

- `print_banner(server_info: dict)` — Welcome message with server name/version
- `print_state(state: dict)` — Show current turn info, character positions, HP bars
- `print_action_result(result: dict)` — Color-coded combat results (green for hits, red for misses, yellow for damage)
- `print_log(events: list)` — Formatted battle log
- `print_map(state: dict)` — Simple ASCII grid showing character positions (doesn't need to be the full 20x20, just the relevant area around the characters)
- `print_help()` — Command reference
- `print_error(msg: str)` — Red error message
- `prompt() -> str` — Input prompt showing current context (round, whose turn)

### ASCII Map Example

When showing the map, render a zoomed-in view around the action:

```
    8   9  10  11  12  13  14
 8  .   .   .   .   .   .   .
 9  .   .   .   .   .   .   .
10  .   .   .   .   .   .   .
11  .   .   .   G   .   .   .
12  .   .   .   .   S   .   .
13  .   .   .   .   .   .   .
14  .   .   .   .   .   .   .

G = Gronk the Fighter (26/30 HP)
S = Shadow the Rogue (16/22 HP)
```

### HP Bar Example

```
Gronk the Fighter  ████████████████████░░░░░  26/30 HP  (11, 12)
Shadow the Rogue   ██████████████░░░░░░░░░░░  16/22 HP  (12, 12)
```

---

## Commands: `cli/commands.py`

Parse user input and dispatch to the appropriate action. Commands should be short and natural.

### Game Setup Commands

| Command | Action |
|---------|--------|
| `new` or `new game` or `create` | Create a new game |
| `join fighter` | Join a preset Fighter character |
| `join rogue` | Join a preset Rogue character |
| `join custom` | Interactive character builder (prompted fields) |
| `start` | Start combat |
| `games` | List any active game info |

### Combat Commands

| Command | Action |
|---------|--------|
| `move X Y` | Move to grid position (X, Y) |
| `attack` | Attack with default weapon (auto-target nearest enemy if only one) |
| `attack TARGET WEAPON` | Attack specific target with specific weapon |
| `dodge` | Take the Dodge action |
| `dash X Y` | Dash and move to position |
| `disengage` | Take Disengage action |
| `end` or `done` | End turn |

### Info Commands

| Command | Action |
|---------|--------|
| `status` or `s` | Show current game state and HP |
| `map` or `m` | Show ASCII map |
| `log` | Show full battle log |
| `help` or `h` or `?` | Show command reference |
| `quit` or `exit` or `q` | Exit the client |

### Quality of Life

| Command | Action |
|---------|--------|
| `switch OWNER_ID` | Switch which character you're controlling |
| `auto` | Auto-play: random legal moves until game ends (for testing) |
| `demo` | Run a full demo game automatically — create, join 2 characters, start, auto-play to completion |

---

## Preset Characters

Include these built-in presets for quick joining:

**Fighter:**
```python
{
    "name": "Gronk the Fighter",
    "owner_id": "player1",
    "ability_scores": {"strength": 16, "dexterity": 12, "constitution": 14, "intelligence": 8, "wisdom": 10, "charisma": 10},
    "max_hp": 30,
    "armor_class": 16,
    "speed": 30,
    "attacks": [{"name": "Longsword", "attack_bonus": 5, "damage_dice": "1d8", "damage_bonus": 3, "damage_type": "slashing", "reach": 5}]
}
```

**Rogue:**
```python
{
    "name": "Shadow the Rogue",
    "owner_id": "player2",
    "ability_scores": {"strength": 10, "dexterity": 16, "constitution": 12, "intelligence": 14, "wisdom": 10, "charisma": 12},
    "max_hp": 22,
    "armor_class": 14,
    "speed": 30,
    "attacks": [{"name": "Dagger", "attack_bonus": 5, "damage_dice": "1d4", "damage_bonus": 3, "damage_type": "piercing", "reach": 5}]
}
```

**Barbarian:**
```python
{
    "name": "Ragna the Barbarian",
    "owner_id": "player3",
    "ability_scores": {"strength": 18, "dexterity": 10, "constitution": 16, "intelligence": 6, "wisdom": 10, "charisma": 8},
    "max_hp": 38,
    "armor_class": 13,
    "speed": 30,
    "attacks": [{"name": "Greataxe", "attack_bonus": 6, "damage_dice": "1d12", "damage_bonus": 4, "damage_type": "slashing", "reach": 5}]
}
```

**Monk:**
```python
{
    "name": "Kira the Monk",
    "owner_id": "player4",
    "ability_scores": {"strength": 10, "dexterity": 18, "constitution": 12, "intelligence": 10, "wisdom": 16, "charisma": 8},
    "max_hp": 20,
    "armor_class": 17,
    "speed": 40,
    "attacks": [{"name": "Unarmed Strike", "attack_bonus": 6, "damage_dice": "1d6", "damage_bonus": 4, "damage_type": "bludgeoning", "reach": 5}]
}
```

---

## Interactive Command Loop

The main loop should:

1. Show a context-aware prompt:
   - Before game: `tendrils> `
   - In lobby: `tendrils [game_abc123]> `
   - In combat: `[R2 — Gronk's turn]> `
   - When it's not your turn: `[R2 — Shadow's turn (waiting)]> `

2. After each action in combat, automatically:
   - Print the action result
   - Check if the game is over (print winner if so)
   - If still active, print whose turn it is next
   - If it's the current player's turn, show a brief status (HP, position)

3. Handle errors gracefully — print the server's error message in red, don't crash

4. Support command history (readline) and Ctrl+C to exit cleanly

---

## The `demo` Command

This is the most important command for testers. When someone types `demo`, the client should:

1. Create a new game
2. Join the Fighter and Rogue presets
3. Start combat
4. Print the initial state and map
5. Auto-play both sides with simple AI:
   - If not adjacent to enemy → move toward them
   - If adjacent → attack with first available weapon
6. Print each round's results with a short delay (0.5s between actions) so it's readable
7. Print the final result and battle log summary
8. Return to the prompt

This lets someone see a full game in action with a single word.

---

## The `auto` Command

Similar to demo but for an already-running game. Plays the currently active character with the same simple AI until the game ends. Useful for testing when you want to manually control one character but auto-play the other.

---

## Example Full Session

```
$ python play.py

╔══════════════════════════════════════════╗
║          TENDRILS ARENA SERVER           ║
║            v0.1.0 — Online              ║
╚══════════════════════════════════════════╝

Connected to https://web-production-969c8.up.railway.app
Type 'help' for commands, 'demo' for a quick match.

tendrils> demo

Creating new game... ✓ (game_id: abc-123)
Joining Gronk the Fighter... ✓
Joining Shadow the Rogue... ✓
Starting combat... ✓

Initiative: Gronk (18), Shadow (15)

    0   1   2   3  ...  17  18  19
 0  .   .   .   .        .   .   .
 1  .   G   .   .        .   .   .
 :                  ...
18  .   .   .   .        .   S   .
19  .   .   .   .        .   .   .

G = Gronk the Fighter    30/30 HP  (1, 1)
S = Shadow the Rogue     22/22 HP  (18, 18)

══════ Round 1 ══════

[Gronk] Moves to (7, 7)
[Shadow] Moves to (12, 12)

══════ Round 2 ══════

[Gronk] Moves to (11, 12)
[Gronk] Attacks Shadow with Longsword!
  Roll: 18+5=23 vs AC 14 — HIT! 6 slashing damage
  Shadow: 16/22 HP

[Shadow] Attacks Gronk with Dagger!
  Roll: 15+5=20 vs AC 16 — HIT! 4 piercing damage
  Gronk: 26/30 HP

... (continues) ...

══════ Round 8 ══════

[Gronk] Attacks Shadow with Longsword!
  Roll: 16+5=21 vs AC 14 — HIT! 9 slashing damage
  Shadow: 0/22 HP — SLAIN!

╔══════════════════════════════════════════╗
║  🏆  WINNER: Gronk the Fighter          ║
║      Survived with 15/30 HP             ║
║      8 rounds of combat                 ║
╚══════════════════════════════════════════╝

tendrils> _
```

---

## Error Handling

- Server unreachable → `"Cannot reach server at {url}. Is it running?"`
- Game not found → `"Game {id} not found. Create one with 'new'."`
- Not your turn → `"It's not your turn. Waiting for {character_name}."`
- Invalid move → Show the server's error message (e.g., "Position out of movement range")
- Target not adjacent → `"Target is too far away. Move closer first."`
- Game already started → `"Game already in progress."`
- HTTP errors → Show status code and message, don't crash

---

## Requirements

Add to `requirements.txt` if not present:
```
rich>=13.0.0
httpx>=0.27.0
```

---

## Implementation Notes

- Use `rich.console.Console` for all output
- Use `rich.prompt.Prompt` or standard `input()` with readline for the command loop
- Parse commands with simple string splitting — no need for argparse or click for the interactive loop
- The `--server` argument on `play.py` can use `argparse`
- Keep the client stateless between commands — always fetch fresh state from the server before displaying
- The client should work against any Tendrils server, not just the production one
- All display logic should be in `display.py`, all HTTP logic in `client.py` — keep them separate
- The `auto` and `demo` AI should calculate the nearest enemy position and move toward it using simple distance (pick the adjacent square closest to the enemy)

---

## What NOT to Build

- No WebSocket support (REST polling is fine for the CLI)
- No saved game state / persistence on the client side
- No configuration files
- No multiplayer networking between two CLI instances (they can share a game_id manually)
- No character sheet editor or level-up system
