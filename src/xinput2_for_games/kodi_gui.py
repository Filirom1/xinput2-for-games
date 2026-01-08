"""
Kodi graphical user interface for XInput2 multiplayer gaming setup.

Uses xbmcgui dialogs for a simple, native Kodi experience.
This module is only usable when running inside Kodi.
"""

import threading
import time

from .core import (
    get_display,
    get_slave_keyboards,
    get_slave_pointers,
    wait_for_enter_key,
    wait_for_mouse_click,
    get_device_name_by_id,
    setup_players,
    cleanup_extra_masters,
)


def run_kodi_gui():
    """Run the Kodi graphical user interface."""
    # Import Kodi modules (only available when running in Kodi)
    import xbmc
    import xbmcgui
    import xbmcaddon
    
    addon = xbmcaddon.Addon()
    addon_name = addon.getAddonInfo('name')
    
    # Get X display
    try:
        dpy = get_display()
        dpy.xinput_query_version()
    except Exception as e:
        xbmcgui.Dialog().ok(
            addon_name,
            f"Failed to connect to X11 display: {e}",
            "Make sure you're running on X11 (not Wayland)."
        )
        return
    
    # Main menu loop
    while True:
        menu_choice = xbmcgui.Dialog().select(
            "🕹️ XInput2 Multiplayer Setup",
            [
                "🎮 Set up players (keyboards only)",
                "🎮 Set up players (keyboards + mice)",
                "🔄 Reset to single player",
                "❌ Exit"
            ]
        )
        
        if menu_choice == -1 or menu_choice == 3:
            # Exit
            break
        elif menu_choice == 0:
            # Keyboards only
            setup_multiplayer(dpy, addon_name, detect_mice=False)
        elif menu_choice == 1:
            # Keyboards + mice
            setup_multiplayer(dpy, addon_name, detect_mice=True)
        elif menu_choice == 2:
            # Reset
            reset_to_single_player(dpy, addon_name)
    
    xbmcgui.Dialog().notification(
        addon_name,
        "Goodbye! 🎮",
        xbmcgui.NOTIFICATION_INFO,
        2000
    )


def setup_multiplayer(dpy, addon_name, detect_mice=False):
    """Run the multiplayer setup wizard."""
    import xbmc
    import xbmcgui
    
    # Ask for number of players
    num_players = xbmcgui.Dialog().numeric(
        0,  # Numeric keyboard
        "Number of players (1-10):"
    )
    
    if not num_players:
        return
    
    try:
        num_players = int(num_players)
        if num_players < 1 or num_players > 10:
            raise ValueError()
    except ValueError:
        xbmcgui.Dialog().ok(addon_name, "Please enter a number between 1 and 10")
        return
    
    player_names = [f"Player{i+1}" for i in range(num_players)]
    player_keyboards = {}
    player_mice = {}
    
    # Create progress dialog for keyboard detection
    progress = xbmcgui.DialogProgress()
    progress.create(
        "🎮 Multiplayer Setup",
        f"Setting up {num_players} player(s)..."
    )
    
    monitor = xbmc.Monitor()
    
    # Detect keyboards
    for i, player_name in enumerate(player_names):
        if progress.iscanceled() or monitor.abortRequested():
            progress.close()
            return
        
        percent = int((i / num_players) * 50)
        progress.update(
            percent,
            f"⌨️ {player_name}: Press ENTER on your keyboard!",
            f"({i+1}/{num_players} keyboards)"
        )
        
        # Get slave keyboard IDs
        slave_keyboards = get_slave_keyboards(dpy)
        slave_keyboard_ids = {d.deviceid for d in slave_keyboards if 'XTEST' not in d.name}
        already_assigned = set(player_keyboards.values())
        
        # Detection loop
        detected = False
        while not detected:
            if progress.iscanceled() or monitor.abortRequested():
                progress.close()
                return
            
            # Check for keyboard in a non-blocking way with timeout
            keyboard_id = wait_for_enter_key_with_cancel(
                dpy, slave_keyboard_ids, 
                lambda: progress.iscanceled() or monitor.abortRequested()
            )
            
            if keyboard_id is None:
                progress.close()
                return
            
            if keyboard_id in already_assigned:
                keyboard_name = get_device_name_by_id(dpy, keyboard_id)
                xbmcgui.Dialog().notification(
                    addon_name,
                    f"'{keyboard_name}' already assigned!",
                    xbmcgui.NOTIFICATION_WARNING,
                    2000
                )
                continue
            
            keyboard_name = get_device_name_by_id(dpy, keyboard_id)
            player_keyboards[player_name] = keyboard_id
            
            xbmcgui.Dialog().notification(
                addon_name,
                f"✓ {player_name}: {keyboard_name}",
                xbmcgui.NOTIFICATION_INFO,
                1500
            )
            detected = True
    
    # Detect mice if requested
    if detect_mice:
        for i, player_name in enumerate(player_names):
            if progress.iscanceled() or monitor.abortRequested():
                progress.close()
                return
            
            percent = 50 + int((i / num_players) * 40)
            progress.update(
                percent,
                f"🖱️ {player_name}: CLICK with your mouse!",
                f"({i+1}/{num_players} mice)"
            )
            
            # Get slave pointer IDs
            slave_pointers = get_slave_pointers(dpy)
            slave_pointer_ids = {d.deviceid for d in slave_pointers if 'XTEST' not in d.name}
            already_assigned = set(player_mice.values())
            
            # Detection loop
            detected = False
            while not detected:
                if progress.iscanceled() or monitor.abortRequested():
                    progress.close()
                    return
                
                mouse_id = wait_for_mouse_click_with_cancel(
                    dpy, slave_pointer_ids,
                    lambda: progress.iscanceled() or monitor.abortRequested()
                )
                
                if mouse_id is None:
                    progress.close()
                    return
                
                if mouse_id in already_assigned:
                    mouse_name = get_device_name_by_id(dpy, mouse_id)
                    xbmcgui.Dialog().notification(
                        addon_name,
                        f"'{mouse_name}' already assigned!",
                        xbmcgui.NOTIFICATION_WARNING,
                        2000
                    )
                    continue
                
                mouse_name = get_device_name_by_id(dpy, mouse_id)
                player_mice[player_name] = mouse_id
                
                xbmcgui.Dialog().notification(
                    addon_name,
                    f"✓ {player_name}: {mouse_name}",
                    xbmcgui.NOTIFICATION_INFO,
                    1500
                )
                detected = True
    
    # Apply configuration
    progress.update(95, "⚡ Configuring devices...", "")
    
    setup_players(
        dpy,
        player_names,
        player_keyboards,
        player_mice if detect_mice else None,
        log_func=lambda msg: xbmc.log(f"[XInput2] {msg}", xbmc.LOGINFO)
    )
    
    progress.close()
    
    # Show success message
    mice_text = " and mice" if detect_mice else ""
    xbmcgui.Dialog().ok(
        "🎉 Setup Complete!",
        f"Successfully configured {num_players} player(s).",
        f"Keyboards{mice_text} are now assigned.",
        "Enjoy your multiplayer game! 🎮"
    )


def reset_to_single_player(dpy, addon_name):
    """Reset to single player configuration."""
    import xbmc
    import xbmcgui
    
    confirm = xbmcgui.Dialog().yesno(
        addon_name,
        "Reset all players to single player mode?",
        "This will remove all extra master devices."
    )
    
    if not confirm:
        return
    
    cleanup_extra_masters(
        dpy, [],
        log_func=lambda msg: xbmc.log(f"[XInput2] {msg}", xbmc.LOGINFO)
    )
    
    xbmcgui.Dialog().ok(
        addon_name,
        "Reset complete!",
        "All devices returned to single player mode."
    )


def wait_for_enter_key_with_cancel(dpy, slave_keyboard_ids, is_canceled):
    """
    Wait for Enter key press with cancel check.
    
    Returns keyboard_id on success, None if canceled.
    """
    import struct
    from Xlib.ext import xinput
    
    root = dpy.screen().root
    
    # Select raw key events
    event_mask = xinput.RawKeyPressMask
    xinput.select_events(root, [(xinput.AllDevices, event_mask)])
    
    try:
        while True:
            # Check cancel condition
            if is_canceled():
                return None
            
            # Check for pending events with timeout
            if dpy.pending_events() == 0:
                # Use select to wait with timeout
                import select
                readable, _, _ = select.select([dpy.fileno()], [], [], 0.2)
                if not readable:
                    continue
            
            event = dpy.next_event()
            
            # Check if it's a raw key event
            if hasattr(event, 'data') and len(event.data) >= 10:
                # Parse raw event data
                deviceid, time, keycode = struct.unpack('<HII', event.data[:10])
                
                # Enter key = 36
                if keycode == 36 and deviceid in slave_keyboard_ids:
                    # Deselect events before returning
                    xinput.select_events(root, [(xinput.AllDevices, 0)])
                    # Flush any remaining events
                    dpy.sync()
                    return deviceid
    except Exception:
        # Deselect events on error
        xinput.select_events(root, [(xinput.AllDevices, 0)])
        raise


def wait_for_mouse_click_with_cancel(dpy, slave_pointer_ids, is_canceled):
    """
    Wait for mouse click with cancel check.
    
    Returns mouse_id on success, None if canceled.
    """
    import struct
    from Xlib.ext import xinput
    
    root = dpy.screen().root
    
    # Select raw button events
    event_mask = xinput.RawButtonPressMask
    xinput.select_events(root, [(xinput.AllDevices, event_mask)])
    
    try:
        while True:
            # Check cancel condition
            if is_canceled():
                return None
            
            # Check for pending events with timeout
            if dpy.pending_events() == 0:
                import select
                readable, _, _ = select.select([dpy.fileno()], [], [], 0.2)
                if not readable:
                    continue
            
            event = dpy.next_event()
            
            # Check if it's a raw button event
            if hasattr(event, 'data') and len(event.data) >= 10:
                # Parse raw event data
                deviceid, time, button = struct.unpack('<HII', event.data[:10])
                
                if deviceid in slave_pointer_ids:
                    # Deselect events before returning
                    xinput.select_events(root, [(xinput.AllDevices, 0)])
                    # Flush any remaining events
                    dpy.sync()
                    return deviceid
    except Exception:
        # Deselect events on error
        xinput.select_events(root, [(xinput.AllDevices, 0)])
        raise
