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
    
    # Localization helper
    def _(string_id):
        return addon.getLocalizedString(string_id)
    
    # Get X display
    try:
        dpy = get_display()
        dpy.xinput_query_version()
    except Exception as e:
        xbmcgui.Dialog().ok(
            addon_name,
            _(30030).format(e)
        )
        return
    
    # Single menu - select players or reset, then exit
    options = [
        "🔄 " + _(30001),  # Reset to single player
        "🎮 " + _(30002),  # 1 player (keyboards)
        "🎮 " + _(30003),  # 2 players (keyboards)
        "🎮 " + _(30004),  # 3 players (keyboards)
        "🎮 " + _(30005),  # 4 players (keyboards)
        "🎮 " + _(30006),  # 2 players (keyboards + mice)
        "🎮 " + _(30007),  # 3 players (keyboards + mice)
        "🎮 " + _(30008),  # 4 players (keyboards + mice)
    ]
    
    choice = xbmcgui.Dialog().select("🕹️ " + _(30000), options)
    
    if choice == -1:
        # Cancelled
        return
    elif choice == 0:
        # Reset to single player - no confirmation
        cleanup_extra_masters(
            dpy, [],
            log_func=lambda msg: xbmc.log(f"[XInput2] {msg}", xbmc.LOGINFO)
        )
        xbmcgui.Dialog().notification(
            addon_name,
            _(30020) + " ✓",
            xbmcgui.NOTIFICATION_INFO,
            2000
        )
    elif choice in [1, 2, 3, 4]:
        # Keyboards only: 1-4 players
        num_players = choice
        setup_multiplayer(dpy, addon, num_players, detect_mice=False)
    elif choice in [5, 6, 7]:
        # Keyboards + mice: 2-4 players
        num_players = choice - 3  # 5->2, 6->3, 7->4
        setup_multiplayer(dpy, addon, num_players, detect_mice=True)


def setup_multiplayer(dpy, addon, num_players, detect_mice=False):
    """Run the multiplayer setup wizard."""
    import xbmc
    import xbmcgui
    
    addon_name = addon.getAddonInfo('name')
    
    # Localization helper
    def _(string_id):
        return addon.getLocalizedString(string_id)
    
    player_names = [f"Player{i+1}" for i in range(num_players)]
    player_keyboards = {}
    player_mice = {}
    
    # Create progress dialog for keyboard detection
    progress = xbmcgui.DialogProgress()
    progress.create(
        "🎮 " + _(30000),
        _(30010).format(num_players)
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
            "⌨️ " + _(30011).format(player_name, i+1, num_players)
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
                    _(30022).format(keyboard_name),
                    xbmcgui.NOTIFICATION_WARNING,
                    2000
                )
                continue
            
            keyboard_name = get_device_name_by_id(dpy, keyboard_id)
            player_keyboards[player_name] = keyboard_id
            
            xbmcgui.Dialog().notification(
                addon_name,
                "✓ " + _(30023).format(player_name, keyboard_name),
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
                "🖱️ " + _(30012).format(player_name, i+1, num_players)
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
                        _(30022).format(mouse_name),
                        xbmcgui.NOTIFICATION_WARNING,
                        2000
                    )
                    continue
                
                mouse_name = get_device_name_by_id(dpy, mouse_id)
                player_mice[player_name] = mouse_id
                
                xbmcgui.Dialog().notification(
                    addon_name,
                    "✓ " + _(30023).format(player_name, mouse_name),
                    xbmcgui.NOTIFICATION_INFO,
                    1500
                )
                detected = True
    
    # Apply configuration
    progress.update(95, "⚡ " + _(30013))
    
    setup_players(
        dpy,
        player_names,
        player_keyboards,
        player_mice if detect_mice else None,
        log_func=lambda msg: xbmc.log(f"[XInput2] {msg}", xbmc.LOGINFO)
    )
    
    progress.close()
    
    # Show success notification (non-blocking)
    xbmcgui.Dialog().notification(
        addon_name,
        _(30021).format(num_players) + " 🎮",
        xbmcgui.NOTIFICATION_INFO,
        3000
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
