#!/usr/bin/env python3
"""
XInput2 CLI/GUI tool for multiplayer gaming setup.

Creates separate master devices for each player and assigns keyboards
(and optionally mice) to their respective masters for isolated input handling.

Supports three modes:
- CLI: Command-line interface (default)
- GUI: GTK graphical interface (--gui)
- Kodi: Kodi addon interface (--kodi)
"""

import argparse


def main():
    parser = argparse.ArgumentParser(
        description='XInput2 CLI/GUI tool for multiplayer gaming setup'
    )
    parser.add_argument(
        'num_players',
        type=int,
        nargs='?',
        help='Number of players'
    )
    parser.add_argument(
        '--names',
        nargs='*',
        help='Custom player names (default: Player1, Player2, ...)'
    )
    parser.add_argument(
        '--mice',
        action='store_true',
        help='Also detect and assign mice/pointers to players'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch GTK graphical user interface'
    )
    parser.add_argument(
        '--kodi',
        action='store_true',
        help='Launch Kodi addon interface (only works inside Kodi)'
    )
    
    args = parser.parse_args()
    
    # Launch Kodi GUI if requested
    if args.kodi:
        from .kodi_gui import run_kodi_gui
        run_kodi_gui()
        return
    
    # Launch GTK GUI if requested
    if args.gui:
        from .gui import run_gui
        run_gui()
        return
    
    # CLI mode requires num_players
    if args.num_players is None:
        parser.error("num_players is required in CLI mode (or use --gui / --kodi)")
    
    from .cli import run_cli
    run_cli(args.num_players, args.names, args.mice)


if __name__ == '__main__':
    main()
