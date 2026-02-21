#!/usr/bin/env python3
"""Tendrils CLI Client — Entry point."""

import argparse
import sys

from cli.client import TendrilsClient, TendrilsAPIError
from cli.game_session import GameSession
from cli.commands import handle_command
from cli import display

DEFAULT_SERVER = "https://web-production-969c8.up.railway.app"


def game_main(args):
    """Run the interactive game client."""
    if not args.token:
        print("Error: --token is required for game mode.", file=sys.stderr)
        sys.exit(1)

    client = TendrilsClient(args.server, args.token)
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
    display.console.print("Type 'help' for commands.\n")

    # Main loop
    try:
        while True:
            # Context-aware prompt
            if session.game_status == "active" and session.has_character:
                try:
                    state = client.get_state()

                    status = state.get("status", "")
                    if status == "completed" or (status == "waiting" and state.get("winner_id")):
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


def main():
    parser = argparse.ArgumentParser(description="Tendrils CLI Client")
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"Server URL (default: {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="API key for authentication (e.g. sk_...)",
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Launch admin panel instead of game client",
    )
    parser.add_argument(
        "--admin-secret",
        default=None,
        help="Admin secret for admin mode",
    )
    args = parser.parse_args()

    if args.admin:
        from cli.admin import admin_main

        secret = args.admin_secret
        if not secret:
            try:
                secret = input("Admin secret: ").strip()
            except (EOFError, KeyboardInterrupt):
                sys.exit(0)
            if not secret:
                print("Error: admin secret is required.", file=sys.stderr)
                sys.exit(1)

        admin_main(args.server, secret)
    else:
        game_main(args)


if __name__ == "__main__":
    main()
