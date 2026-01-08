# xinput2-for-games

A CLI, GUI, and Kodi addon tool to easily set up multiple input devices for local multiplayer gaming on Linux using XInput2.

## Features

- **Automatic keyboard detection**: Press Enter to assign a keyboard to a player
- **Automatic mouse detection**: Click to assign a mouse to a player (optional)
- **Master device management**: Creates separate XInput2 master devices for each player
- **Cleanup support**: Automatically removes unused masters when reducing player count
- **GUI mode**: GTK-based graphical interface with retro arcade styling
- **CLI mode**: Terminal-based interface for scripting and quick setup
- **Kodi addon**: Native Kodi integration for media center setups

## How it works

On Linux with X11, all input devices are attached to a single "Virtual core" master by default. This means all keyboards and mice control the same cursor and send input to the same focused window.

This tool creates separate master devices for each player and attaches their physical input devices to these masters. This enables true local multiplayer where each player has independent input.

## Installation

### NixOS / Nix

Using flakes:

```bash
# Run directly
nix run github:Filirom1/xinput2-for-games -- --gui

# Or install in your system
# In your flake.nix:
{
  inputs.xinput2-for-games.url = "github:Filirom1/xinput2-for-games";
}

# Then in your configuration:
{ inputs, ... }:
{
  imports = [ inputs.xinput2-for-games.nixosModules.default ];
  programs.xinput2-for-games.enable = true;
}
```

Development shell:

```bash
nix develop
```

### pip

```bash
# CLI only
pip install xinput2-for-games

# With GUI support
pip install xinput2-for-games[gui]
```

### From source

```bash
git clone https://github.com/Filirom1/xinput2-for-games
cd xinput2-for-games
pip install -e .[gui]
```

### Kodi Addon

1. **Download the addon files** from `kodi-addon/script.xinput2-for-games/` in this repository

2. **Install dependencies** into the addon:
   ```bash
   # Copy the Python module
   cp -r src/xinput2_for_games kodi-addon/script.xinput2-for-games/resources/lib/
   
   # Install python-xlib into the addon
   pip install --target=kodi-addon/script.xinput2-for-games/resources/lib python-xlib
   ```

3. **Copy to Kodi**:
   ```bash
   cp -r kodi-addon/script.xinput2-for-games ~/.kodi/addons/
   ```

4. **Enable the addon** in Kodi: Add-ons → My add-ons → Program add-ons → XInput2 Multiplayer Setup

The addon will appear in Programs and provides a wizard to set up multiplayer input devices.

## Usage

### GUI Mode

```bash
xinput2-for-games --gui
```

1. Select the number of players
2. Check "Also detect mice" if needed
3. Click "Start Detection"
4. Each player presses Enter on their keyboard
5. (If mice enabled) Each player clicks with their mouse
6. Done! Devices are now assigned to separate masters

### CLI Mode

```bash
# 2 players, keyboards only
xinput2-for-games 2

# 4 players with mice
xinput2-for-games 4 --mice

# Custom player names
xinput2-for-games 2 --names Alice Bob
```

### Reset to single player

```bash
# Reset all masters back to default (1 player)
xinput2-for-games 1
```

Or use the "Reset to 1 Player" button in the GUI.

### Kodi Mode

Launch the addon from Kodi's Programs menu, or run directly:

```bash
xinput2-for-games --kodi
```

**Note**: The `--kodi` flag only works when running inside Kodi (it requires Kodi's Python modules).

## Requirements

- Linux with X11 (Wayland is not supported)
- Python 3.9+
- `xinput` command-line tool
- For GUI: GTK3 and PyGObject

## How games detect multiple inputs

After running this tool, each player will have their own master device. Games that support XInput2 or read from specific device files can distinguish between players.

Some games and engines that work well with this setup:
- Games using SDL2 with proper multi-device support
- Godot engine games
- Some RetroArch cores

## Troubleshooting

### Keyboard not detected

Make sure you're pressing Enter on a physical keyboard, not a virtual one. XTEST keyboards (used for automation) are filtered out.

### Mouse not detected

Click with your mouse, not a touchpad gesture. Some touchpad drivers may report as a different device type.

### Devices not isolating properly

Some games may only listen to the Virtual core master. This is a game-side limitation. Check if the game has settings for multiple input devices.

### Resetting after a crash

If the program crashes during setup, you may have orphaned master devices. Run:

```bash
xinput2-for-games 1
```

Or manually:

```bash
xinput list  # Find extra masters
xinput remove-master "Player2 pointer" AttachToMaster 2 3
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.
