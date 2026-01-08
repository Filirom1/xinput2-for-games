#!/usr/bin/env python3
"""
Kodi addon entry point for XInput2 Multiplayer Setup.

This file should be placed at the root of your Kodi addon folder.
Copy the contents of xinput2_for_games/ to resources/lib/xinput2_for_games/
"""

import sys
import os

# Add the lib folder to Python path
addon_path = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(addon_path, 'resources', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Import and run the Kodi GUI
from xinput2_for_games.kodi_gui import run_kodi_gui

if __name__ == '__main__':
    run_kodi_gui()
