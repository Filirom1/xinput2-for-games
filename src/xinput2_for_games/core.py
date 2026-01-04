"""
Core XInput2 functionality for multiplayer gaming setup.

This module provides the low-level functions for interacting with XInput2
devices, including device discovery, master creation, and device reattachment.
"""

import struct
import subprocess
from Xlib import display
from Xlib.ext import xinput


# XInput2 device types
MASTER_POINTER = 1
MASTER_KEYBOARD = 2
SLAVE_POINTER = 3
SLAVE_KEYBOARD = 4
FLOATING_SLAVE = 5

# Virtual core device IDs
VIRTUAL_CORE_POINTER = 2
VIRTUAL_CORE_KEYBOARD = 3

# Enter key keycode
ENTER_KEYCODE = 36


def get_display():
    """Get X display connection."""
    return display.Display()


def get_all_devices(dpy):
    """Query all XInput2 devices."""
    return dpy.xinput_query_device(xinput.AllDevices).devices


def get_slave_keyboards(dpy):
    """Get all slave keyboard devices."""
    devices = get_all_devices(dpy)
    return [d for d in devices if d.use == SLAVE_KEYBOARD]


def get_slave_pointers(dpy):
    """Get all slave pointer devices."""
    devices = get_all_devices(dpy)
    return [d for d in devices if d.use == SLAVE_POINTER]


def get_master_keyboards(dpy):
    """Get all master keyboard devices."""
    devices = get_all_devices(dpy)
    return [d for d in devices if d.use == MASTER_KEYBOARD]


def get_master_pointers(dpy):
    """Get all master pointer devices."""
    devices = get_all_devices(dpy)
    return [d for d in devices if d.use == MASTER_POINTER]


def find_master_keyboard_by_name(dpy, name):
    """Find master keyboard device by name (e.g., 'Player1 keyboard')."""
    master_keyboards = get_master_keyboards(dpy)
    for device in master_keyboards:
        if device.name == f"{name} keyboard":
            return device
    return None


def find_master_pointer_by_name(dpy, name):
    """Find master pointer device by name (e.g., 'Player1 pointer')."""
    master_pointers = get_master_pointers(dpy)
    for device in master_pointers:
        if device.name == f"{name} pointer":
            return device
    return None


def create_master(name):
    """Create a new master pointer/keyboard pair."""
    subprocess.run(['xinput', 'create-master', name], check=True)


def reattach_device(device_id, master_id):
    """Reattach a slave device to a master."""
    subprocess.run(['xinput', 'reattach', str(device_id), str(master_id)], check=True)


def remove_master(master_pointer_id, return_pointer_id, return_keyboard_id):
    """
    Remove a master device pair, reattaching its slaves to specified masters.
    
    Args:
        master_pointer_id: ID of the master pointer to remove
        return_pointer_id: Master pointer ID to reattach orphaned pointers to
        return_keyboard_id: Master keyboard ID to reattach orphaned keyboards to
    """
    subprocess.run([
        'xinput', 'remove-master', str(master_pointer_id),
        'AttachToMaster', str(return_pointer_id), str(return_keyboard_id)
    ], check=True)


def get_extra_masters(dpy):
    """
    Get all master devices that are not Virtual core (i.e., created by this tool).
    Returns list of (pointer_device, keyboard_device) tuples.
    """
    devices = get_all_devices(dpy)
    master_pointers = [d for d in devices if d.use == MASTER_POINTER and d.name != 'Virtual core pointer']
    master_keyboards = [d for d in devices if d.use == MASTER_KEYBOARD and d.name != 'Virtual core keyboard']
    
    # Match pointer/keyboard pairs by name prefix
    pairs = []
    for pointer in master_pointers:
        # Extract name prefix (e.g., "Player2" from "Player2 pointer")
        if pointer.name.endswith(' pointer'):
            prefix = pointer.name[:-8]  # Remove ' pointer'
            for keyboard in master_keyboards:
                if keyboard.name == f"{prefix} keyboard":
                    pairs.append((pointer, keyboard))
                    break
    return pairs


def cleanup_extra_masters(dpy, keep_names, log_func=None):
    """
    Remove all extra masters except those in keep_names.
    Reattaches their slaves to Virtual core.
    
    Args:
        dpy: X display connection
        keep_names: List of master name prefixes to keep (e.g., ['Player2', 'Player3'])
        log_func: Optional function to log messages (default: print)
    """
    if log_func is None:
        log_func = print
    
    extra_masters = get_extra_masters(dpy)
    
    for pointer, keyboard in extra_masters:
        # Extract name prefix
        prefix = pointer.name[:-8] if pointer.name.endswith(' pointer') else pointer.name
        
        if prefix not in keep_names:
            log_func(f"Removing master '{prefix}' (pointer ID: {pointer.deviceid})...")
            remove_master(pointer.deviceid, VIRTUAL_CORE_POINTER, VIRTUAL_CORE_KEYBOARD)


def get_slave_keyboard_ids(dpy):
    """Get set of slave keyboard device IDs, excluding XTEST keyboards."""
    slave_keyboards = get_slave_keyboards(dpy)
    return {d.deviceid for d in slave_keyboards if 'XTEST' not in d.name}


def get_slave_pointer_ids(dpy):
    """Get set of slave pointer device IDs, excluding XTEST pointers."""
    slave_pointers = get_slave_pointers(dpy)
    return {d.deviceid for d in slave_pointers if 'XTEST' not in d.name}


def wait_for_enter_key(dpy, slave_keyboard_ids):
    """
    Wait for Enter key press and return the source keyboard device ID.
    Uses RawKeyPress events to detect which physical keyboard was used.
    Only accepts events from slave keyboards (not masters).
    """
    root = dpy.screen().root
    
    # Select raw key press events on root window
    root.xinput_select_events([
        (xinput.AllDevices, xinput.RawKeyPressMask)
    ])
    
    while True:
        event = dpy.next_event()
        
        # Check if it's an XInput2 RawKeyPress event
        if event.type == dpy.extension_event.GenericEvent:
            # For xinput events, check evtype
            if hasattr(event, 'evtype') and event.evtype == xinput.RawKeyPress:
                # Parse raw event data bytes
                # RawKeyPress structure:
                # - offset 0: deviceid (2 bytes, uint16)
                # - offset 2: time (4 bytes, uint32)  
                # - offset 6: detail/keycode (4 bytes, uint32)
                data = event.data
                device_id, time, keycode = struct.unpack('<HII', data[:10])
                
                # Only accept slave keyboards, not masters
                if device_id not in slave_keyboard_ids:
                    continue
                
                # Check if Enter key was pressed
                if keycode == ENTER_KEYCODE:
                    return device_id


def wait_for_mouse_click(dpy, slave_pointer_ids):
    """
    Wait for mouse click and return the source pointer device ID.
    Uses RawButtonPress events to detect which physical mouse was used.
    Only accepts events from slave pointers (not masters).
    """
    root = dpy.screen().root
    
    # Select raw button press events on root window
    root.xinput_select_events([
        (xinput.AllDevices, xinput.RawButtonPressMask)
    ])
    
    while True:
        event = dpy.next_event()
        
        # Check if it's an XInput2 RawButtonPress event
        if event.type == dpy.extension_event.GenericEvent:
            # For xinput events, check evtype
            if hasattr(event, 'evtype') and event.evtype == xinput.RawButtonPress:
                # Parse raw event data bytes
                # RawButtonPress structure (same as RawKeyPress):
                # - offset 0: deviceid (2 bytes, uint16)
                # - offset 2: time (4 bytes, uint32)  
                # - offset 6: detail/button (4 bytes, uint32)
                data = event.data
                device_id, time, button = struct.unpack('<HII', data[:10])
                
                # Only accept slave pointers, not masters
                if device_id not in slave_pointer_ids:
                    continue
                
                # Accept any button click
                return device_id


def get_device_name_by_id(dpy, device_id):
    """Get device name by device ID."""
    devices = get_all_devices(dpy)
    for device in devices:
        if device.deviceid == device_id:
            return device.name
    return f"Unknown (ID: {device_id})"


def setup_players(dpy, player_names, player_keyboards, player_mice=None, log_func=None):
    """
    Set up master devices and reattach keyboards/mice for all players.
    
    Args:
        dpy: X display connection
        player_names: List of player names
        player_keyboards: Dict mapping player names to keyboard device IDs
        player_mice: Optional dict mapping player names to mouse device IDs
        log_func: Optional function to log messages (default: print)
    """
    if log_func is None:
        log_func = print
    
    # Clean up extra masters that won't be needed
    masters_to_keep = player_names[1:]  # All except first player
    cleanup_extra_masters(dpy, masters_to_keep, log_func)
    
    # Create master devices only for players beyond Player1
    for i, player_name in enumerate(player_names):
        if i == 0:
            log_func(f"{player_name} will use existing 'Virtual core keyboard'")
        else:
            existing_master = find_master_keyboard_by_name(dpy, player_name)
            if existing_master:
                log_func(f"{player_name} master already exists (ID: {existing_master.deviceid})")
            else:
                log_func(f"Creating master for {player_name}...")
                create_master(player_name)
    
    # Reattach keyboards to their respective masters
    for i, (player_name, keyboard_id) in enumerate(player_keyboards.items()):
        if i == 0:
            master_id = VIRTUAL_CORE_KEYBOARD
            log_func(f"Reattaching keyboard {keyboard_id} to Virtual core keyboard...")
        else:
            master_keyboard = find_master_keyboard_by_name(dpy, player_name)
            if master_keyboard:
                master_id = master_keyboard.deviceid
                log_func(f"Reattaching keyboard {keyboard_id} to {player_name}...")
            else:
                log_func(f"  ⚠ Could not find master for {player_name}")
                continue
        reattach_device(keyboard_id, master_id)
    
    # Reattach mice to their respective masters
    if player_mice:
        for i, (player_name, mouse_id) in enumerate(player_mice.items()):
            if i == 0:
                master_id = VIRTUAL_CORE_POINTER
                log_func(f"Reattaching mouse {mouse_id} to Virtual core pointer...")
            else:
                master_pointer = find_master_pointer_by_name(dpy, player_name)
                if master_pointer:
                    master_id = master_pointer.deviceid
                    log_func(f"Reattaching mouse {mouse_id} to {player_name}...")
                else:
                    log_func(f"  ⚠ Could not find master pointer for {player_name}")
                    continue
            reattach_device(mouse_id, master_id)


def get_configuration(dpy):
    """
    Get current device configuration.
    
    Returns list of dicts with master info and attached slaves.
    """
    devices = get_all_devices(dpy)
    master_keyboards = [d for d in devices if d.use == MASTER_KEYBOARD]
    master_pointers = [d for d in devices if d.use == MASTER_POINTER]
    
    config = []
    
    for mk in master_keyboards:
        # Find matching pointer
        mp = None
        if mk.name == 'Virtual core keyboard':
            name = 'Virtual core'
            mp = next((d for d in master_pointers if d.name == 'Virtual core pointer'), None)
        elif mk.name.endswith(' keyboard'):
            name = mk.name[:-9]
            mp = next((d for d in master_pointers if d.name == f"{name} pointer"), None)
        else:
            name = mk.name
        
        # Get attached slaves
        attached_keyboards = [
            {'id': d.deviceid, 'name': d.name}
            for d in devices 
            if d.use == SLAVE_KEYBOARD and d.attachment == mk.deviceid
        ]
        
        attached_pointers = []
        if mp:
            attached_pointers = [
                {'id': d.deviceid, 'name': d.name}
                for d in devices 
                if d.use == SLAVE_POINTER and d.attachment == mp.deviceid
            ]
        
        config.append({
            'name': name,
            'keyboard_master_id': mk.deviceid,
            'pointer_master_id': mp.deviceid if mp else None,
            'keyboards': attached_keyboards,
            'pointers': attached_pointers,
        })
    
    return config
