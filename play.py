#!/usr/bin/env python3
"""Tendrils CLI Client — Entry point."""

import argparse
import sys

from cli.client import TendrilsClient, TendrilsAPIError
from cli.game_session import GameSession
from cli.commands import handle_command
from cli import display

DEFAULT_SERVER = "https://web-production-969c8.up.railway.app"


def main():
    parser = argparse.ArgumentParser(description="Tendrils CLI Client")
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"Server URL (default: {DEFAULT_SERVER})",
    )
    args = parser.parse_args()

    client = TendrilsClient(args.server)
    session = GameSession()

    # Ping server
    try:
        info = client.ping()
    except Exception as e:
        display.print_error(f"Cannot reach server at {args.server}. Is it running?")
        display.print_error(str(e))
        sys.exit(1)

    display.console.print()
    display.print_banner(info)
    display.console.print(f"\nConnected to {args.server}")
    display.console.print("Type 'help' for commands, 'demo' for a quick match.\n")

    # Main loop
    try:
        while True:
            # Context-aware prompt
            if session.game_status == "active" and session.game_id and session.active_character:
                try:
                    state = client.get_state(session.game_id, session.active_character)

                    status = state.get("status", "")
                    if status == "completed":
                        session.game_status = "completed"
                        cmd = display.prompt(session)
                    else:
                        round_num = state.get("round_number", state.get("round", 0))
                        is_my_turn = state.get("is_your_turn", False)
                        mine = state.get("your_character", {})
                        my_name = mine.get("name", "?") if mine else "?"

                        cmd = display.combat_prompt(round_num, my_name, is_my_turn)
                except TendrilsAPIError:
                    cmd = display.prompt(session)
            else:
                cmd = display.prompt(session)

            if not handle_command(cmd, client, session):
                break

    except KeyboardInterrupt:
        display.console.print("\n[dim]Goodbye![/dim]")
    finally:
        client.close()


if __name__ == "__main__":
    main()
