# XInput2 for Games - Kodi Addon

This folder contains a ready-to-use Kodi addon template.

## Installation

### Option 1: Copy from pip package

1. Install the pip package:
   ```bash
   pip install xinput2-for-games
   ```

2. Copy the module to Kodi addon:
   ```bash
   # Find where pip installed it
   python -c "import xinput2_for_games; print(xinput2_for_games.__path__[0])"
   
   # Copy to addon
   cp -r /path/to/xinput2_for_games kodi-addon/script.xinput2-for-games/resources/lib/
   ```

3. Install python-xlib for Kodi's Python:
   ```bash
   # Copy xlib to addon lib folder
   pip install --target=kodi-addon/script.xinput2-for-games/resources/lib python-xlib
   ```

4. Copy the addon folder to Kodi:
   ```bash
   cp -r script.xinput2-for-games ~/.kodi/addons/
   ```

### Option 2: Manual setup

1. Create the folder structure:
   ```
   script.xinput2-for-games/
   ├── addon.xml
   ├── addon.py
   └── resources/
       └── lib/
           ├── xinput2_for_games/
           │   ├── __init__.py
           │   ├── core.py
           │   └── kodi_gui.py
           └── Xlib/  (from python-xlib)
   ```

2. Copy from this repository:
   - `addon.xml` and `addon.py` are ready
   - Copy `src/xinput2_for_games/` to `resources/lib/`
   - Download python-xlib and copy `Xlib/` folder to `resources/lib/`

3. Add icon and fanart (optional):
   - `resources/icon.png` (256x256 or 512x512)
   - `resources/fanart.jpg` (1280x720 or 1920x1080)

## Usage

1. Open Kodi
2. Go to Add-ons → Program add-ons
3. Launch "XInput2 Multiplayer Setup"
4. Follow the on-screen wizard

## Requirements

- Linux with X11 (Wayland not supported)
- `xinput` command available
- Kodi running on X11

## Troubleshooting

**"Failed to connect to X11 display"**
- Make sure Kodi is running on X11, not Wayland
- Check that `$DISPLAY` environment variable is set

**"xinput: command not found"**
- Install xinput: `sudo apt install xinput` or equivalent
