#!/usr/bin/env python3
"""
XInput2 CLI tool for multiplayer gaming setup.

Creates separate master devices for each player and assigns keyboards
to their respective masters for isolated input handling.
"""

import argparse
import subprocess
from Xlib import display
from Xlib.ext import xinput


# XInput2 device types
MASTER_POINTER = 1
MASTER_KEYBOARD = 2
SLAVE_POINTER = 3
SLAVE_KEYBOARD = 4
FLOATING_SLAVE = 5

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


def cleanup_extra_masters(dpy, keep_names):
    """
    Remove all extra masters except those in keep_names.
    Reattaches their slaves to Virtual core.
    
    Args:
        dpy: X display connection
        keep_names: List of master name prefixes to keep (e.g., ['Player2', 'Player3'])
    """
    # Virtual core IDs
    VIRTUAL_CORE_POINTER = 2
    VIRTUAL_CORE_KEYBOARD = 3
    
    extra_masters = get_extra_masters(dpy)
    
    for pointer, keyboard in extra_masters:
        # Extract name prefix
        prefix = pointer.name[:-8] if pointer.name.endswith(' pointer') else pointer.name
        
        if prefix not in keep_names:
            print(f"Removing master '{prefix}' (pointer ID: {pointer.deviceid})...")
            remove_master(pointer.deviceid, VIRTUAL_CORE_POINTER, VIRTUAL_CORE_KEYBOARD)


def wait_for_enter_key(dpy, slave_keyboard_ids):
    """
    Wait for Enter key press and return the source keyboard device ID.
    Uses RawKeyPress events to detect which physical keyboard was used.
    Only accepts events from slave keyboards (not masters).
    """
    import struct
    
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
    import struct
    
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


def display_configuration(dpy, player_names, show_pointers=False):
    """Display the final device configuration."""
    print("\n" + "=" * 50)
    print("Final Configuration:")
    print("=" * 50)
    
    devices = get_all_devices(dpy)
    
    for player_name in player_names:
        master_keyboard = find_master_keyboard_by_name(dpy, player_name)
        master_pointer = find_master_pointer_by_name(dpy, player_name)
        
        if master_keyboard or master_pointer:
            print(f"\n{player_name}:")
            
            if master_keyboard:
                print(f"  Master keyboard: {master_keyboard.name} (ID: {master_keyboard.deviceid})")
                
                # Find attached slave keyboards
                attached_keyboards = [
                    d for d in devices 
                    if d.use == SLAVE_KEYBOARD and d.attachment == master_keyboard.deviceid
                ]
                for slave in attached_keyboards:
                    print(f"    └─ {slave.name} (ID: {slave.deviceid})")
            
            if show_pointers and master_pointer:
                print(f"  Master pointer: {master_pointer.name} (ID: {master_pointer.deviceid})")
                
                # Find attached slave pointers
                attached_pointers = [
                    d for d in devices 
                    if d.use == SLAVE_POINTER and d.attachment == master_pointer.deviceid
                ]
                for slave in attached_pointers:
                    print(f"    └─ {slave.name} (ID: {slave.deviceid})")


def run_gui():
    """Run the graphical user interface using GTK."""
    # Lazy load GTK
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import Gtk, GLib
    import threading
    
    class XInput2GUI(Gtk.Window):
        def __init__(self):
            super().__init__(title="XInput2 Multiplayer Setup")
            self.set_default_size(550, 650)
            self.set_border_width(10)
            
            self.dpy = get_display()
            self.dpy.xinput_query_version()
            
            self.player_keyboards = {}
            self.player_mice = {}
            self.player_names = []
            self.current_player_index = 0
            self.detecting_mice = False
            self.detection_active = False
            
            self.create_widgets()
        
        def create_widgets(self):
            # Main vertical box
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(vbox)
            
            # Setup frame
            setup_frame = Gtk.Frame(label="Setup")
            vbox.pack_start(setup_frame, False, False, 0)
            
            setup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            setup_box.set_margin_start(10)
            setup_box.set_margin_end(10)
            setup_box.set_margin_top(10)
            setup_box.set_margin_bottom(10)
            setup_frame.add(setup_box)
            
            # Number of players
            setup_box.pack_start(Gtk.Label(label="Number of players:"), False, False, 0)
            
            self.num_players_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
            self.num_players_spin.set_value(2)
            setup_box.pack_start(self.num_players_spin, False, False, 0)
            
            # Mice checkbox
            self.mice_check = Gtk.CheckButton(label="Also detect mice")
            setup_box.pack_start(self.mice_check, False, False, 10)
            
            # Start button
            self.start_btn = Gtk.Button(label="Start Detection")
            self.start_btn.connect("clicked", self.start_detection)
            setup_box.pack_end(self.start_btn, False, False, 0)
            
            # Status frame
            status_frame = Gtk.Frame(label="Status")
            vbox.pack_start(status_frame, False, False, 0)
            
            self.status_label = Gtk.Label(label="Ready. Click 'Start Detection' to begin.")
            self.status_label.set_line_wrap(True)
            self.status_label.set_margin_start(10)
            self.status_label.set_margin_end(10)
            self.status_label.set_margin_top(10)
            self.status_label.set_margin_bottom(10)
            self.status_label.set_xalign(0)
            status_frame.add(self.status_label)
            
            # Configuration frame with scrollable text
            config_frame = Gtk.Frame(label="Configuration")
            vbox.pack_start(config_frame, True, True, 0)
            
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_margin_start(5)
            scrolled.set_margin_end(5)
            scrolled.set_margin_top(5)
            scrolled.set_margin_bottom(5)
            config_frame.add(scrolled)
            
            self.text_view = Gtk.TextView()
            self.text_view.set_editable(False)
            self.text_view.set_monospace(True)
            self.text_buffer = self.text_view.get_buffer()
            scrolled.add(self.text_view)
            
            # Button box
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            vbox.pack_start(btn_box, False, False, 0)
            
            self.cleanup_btn = Gtk.Button(label="Reset to 1 Player")
            self.cleanup_btn.connect("clicked", self.cleanup_masters)
            btn_box.pack_start(self.cleanup_btn, False, False, 0)
            
            self.refresh_btn = Gtk.Button(label="Refresh View")
            self.refresh_btn.connect("clicked", self.refresh_configuration)
            btn_box.pack_start(self.refresh_btn, False, False, 0)
        
        def log(self, message):
            """Add message to text view."""
            end_iter = self.text_buffer.get_end_iter()
            self.text_buffer.insert(end_iter, message + "\n")
            # Scroll to end
            mark = self.text_buffer.create_mark(None, self.text_buffer.get_end_iter(), False)
            self.text_view.scroll_to_mark(mark, 0, False, 0, 0)
        
        def clear_log(self):
            """Clear text view."""
            self.text_buffer.set_text("")
        
        def set_status(self, message):
            """Update status label."""
            self.status_label.set_text(message)
        
        def set_controls_sensitive(self, sensitive):
            """Enable/disable controls."""
            self.start_btn.set_sensitive(sensitive)
            self.num_players_spin.set_sensitive(sensitive)
            self.mice_check.set_sensitive(sensitive)
        
        def start_detection(self, button):
            """Start the keyboard/mouse detection process."""
            num_players = int(self.num_players_spin.get_value())
            
            self.clear_log()
            self.player_names = [f"Player{i+1}" for i in range(num_players)]
            self.player_keyboards = {}
            self.player_mice = {}
            self.current_player_index = 0
            self.detecting_mice = False
            self.detection_active = True
            
            # Disable controls during detection
            self.set_controls_sensitive(False)
            
            self.log(f"Setting up {num_players} player(s): {', '.join(self.player_names)}")
            self.log("")
            
            # Start keyboard detection in background thread
            threading.Thread(target=self.detect_next_keyboard, daemon=True).start()
        
        def detect_next_keyboard(self):
            """Detect keyboard for current player."""
            if self.current_player_index >= len(self.player_names):
                # Done with keyboards, move to mice or finish
                if self.mice_check.get_active():
                    self.current_player_index = 0
                    self.detecting_mice = True
                    GLib.idle_add(self.log, "")
                    threading.Thread(target=self.detect_next_mouse, daemon=True).start()
                else:
                    GLib.idle_add(self.finish_setup)
                return
            
            player_name = self.player_names[self.current_player_index]
            GLib.idle_add(self.set_status, f"{player_name}: Press ENTER on your keyboard...")
            GLib.idle_add(self.log, f"{player_name}: Press ENTER on your keyboard...")
            
            # Get slave keyboard IDs
            slave_keyboards = get_slave_keyboards(self.dpy)
            slave_keyboard_ids = {d.deviceid for d in slave_keyboards if 'XTEST' not in d.name}
            already_assigned = set(self.player_keyboards.values())
            
            while self.detection_active:
                keyboard_id = wait_for_enter_key(self.dpy, slave_keyboard_ids)
                
                if keyboard_id in already_assigned:
                    keyboard_name = get_device_name_by_id(self.dpy, keyboard_id)
                    GLib.idle_add(self.log, f"  ⚠ Keyboard '{keyboard_name}' (ID: {keyboard_id}) already assigned. Try another.")
                    continue
                
                keyboard_name = get_device_name_by_id(self.dpy, keyboard_id)
                self.player_keyboards[player_name] = keyboard_id
                GLib.idle_add(self.log, f"  ✓ Detected: {keyboard_name} (ID: {keyboard_id})")
                break
            
            self.current_player_index += 1
            threading.Thread(target=self.detect_next_keyboard, daemon=True).start()
        
        def detect_next_mouse(self):
            """Detect mouse for current player."""
            if self.current_player_index >= len(self.player_names):
                GLib.idle_add(self.finish_setup)
                return
            
            player_name = self.player_names[self.current_player_index]
            GLib.idle_add(self.set_status, f"{player_name}: CLICK with your mouse...")
            GLib.idle_add(self.log, f"{player_name}: CLICK with your mouse...")
            
            # Get slave pointer IDs
            slave_pointers = get_slave_pointers(self.dpy)
            slave_pointer_ids = {d.deviceid for d in slave_pointers if 'XTEST' not in d.name}
            already_assigned = set(self.player_mice.values())
            
            while self.detection_active:
                mouse_id = wait_for_mouse_click(self.dpy, slave_pointer_ids)
                
                if mouse_id in already_assigned:
                    mouse_name = get_device_name_by_id(self.dpy, mouse_id)
                    GLib.idle_add(self.log, f"  ⚠ Mouse '{mouse_name}' (ID: {mouse_id}) already assigned. Try another.")
                    continue
                
                mouse_name = get_device_name_by_id(self.dpy, mouse_id)
                self.player_mice[player_name] = mouse_id
                GLib.idle_add(self.log, f"  ✓ Detected: {mouse_name} (ID: {mouse_id})")
                break
            
            self.current_player_index += 1
            threading.Thread(target=self.detect_next_mouse, daemon=True).start()
        
        def finish_setup(self):
            """Apply the configuration and display results."""
            self.detection_active = False
            self.log("")
            self.log("Assigning devices to masters...")
            self.log("")
            
            # Cleanup extra masters
            masters_to_keep = self.player_names[1:]
            cleanup_extra_masters(self.dpy, masters_to_keep)
            
            # Create masters for players beyond Player1
            for i, player_name in enumerate(self.player_names):
                if i == 0:
                    self.log(f"{player_name} will use existing 'Virtual core keyboard'")
                else:
                    existing_master = find_master_keyboard_by_name(self.dpy, player_name)
                    if existing_master:
                        self.log(f"{player_name} master already exists (ID: {existing_master.deviceid})")
                    else:
                        self.log(f"Creating master for {player_name}...")
                        create_master(player_name)
            
            # Reattach keyboards
            for i, (player_name, keyboard_id) in enumerate(self.player_keyboards.items()):
                if i == 0:
                    master_id = 3  # Virtual core keyboard
                    self.log(f"Reattaching keyboard {keyboard_id} to Virtual core keyboard...")
                else:
                    master_keyboard = find_master_keyboard_by_name(self.dpy, player_name)
                    if master_keyboard:
                        master_id = master_keyboard.deviceid
                        self.log(f"Reattaching keyboard {keyboard_id} to {player_name}...")
                    else:
                        continue
                reattach_device(keyboard_id, master_id)
            
            # Reattach mice
            if self.mice_check.get_active():
                for i, (player_name, mouse_id) in enumerate(self.player_mice.items()):
                    if i == 0:
                        master_id = 2  # Virtual core pointer
                        self.log(f"Reattaching mouse {mouse_id} to Virtual core pointer...")
                    else:
                        master_pointer = find_master_pointer_by_name(self.dpy, player_name)
                        if master_pointer:
                            master_id = master_pointer.deviceid
                            self.log(f"Reattaching mouse {mouse_id} to {player_name}...")
                        else:
                            continue
                    reattach_device(mouse_id, master_id)
            
            self.log("")
            self.log("=" * 40)
            self.log("Setup complete!")
            self.log("=" * 40)
            
            self.set_status("Setup complete!")
            
            # Re-enable controls
            self.set_controls_sensitive(True)
            
            self.refresh_configuration(None)
        
        def cleanup_masters(self, button):
            """Remove all extra masters, returning to single player setup."""
            self.clear_log()
            self.log("Cleaning up extra masters...")
            cleanup_extra_masters(self.dpy, [])
            self.log("Reset to single player configuration.")
            self.set_status("Reset complete.")
            self.refresh_configuration(None)
        
        def refresh_configuration(self, button):
            """Refresh and display current device configuration."""
            self.log("")
            self.log("Current Device Configuration:")
            self.log("-" * 40)
            
            devices = get_all_devices(self.dpy)
            master_keyboards = [d for d in devices if d.use == MASTER_KEYBOARD]
            master_pointers = [d for d in devices if d.use == MASTER_POINTER]
            
            for mk in master_keyboards:
                # Find matching pointer
                mp = None
                if mk.name == 'Virtual core keyboard':
                    mp = next((d for d in master_pointers if d.name == 'Virtual core pointer'), None)
                elif mk.name.endswith(' keyboard'):
                    prefix = mk.name[:-9]
                    mp = next((d for d in master_pointers if d.name == f"{prefix} pointer"), None)
                
                self.log(f"\n{mk.name.replace(' keyboard', '')}:")
                self.log(f"  Keyboard (ID: {mk.deviceid}):")
                for d in devices:
                    if d.use == SLAVE_KEYBOARD and d.attachment == mk.deviceid:
                        self.log(f"    └─ {d.name} (ID: {d.deviceid})")
                
                if mp:
                    self.log(f"  Pointer (ID: {mp.deviceid}):")
                    for d in devices:
                        if d.use == SLAVE_POINTER and d.attachment == mp.deviceid:
                            self.log(f"    └─ {d.name} (ID: {d.deviceid})")
    
    win = XInput2GUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


def main():
    parser = argparse.ArgumentParser(
        description='XInput2 CLI tool for multiplayer gaming setup'
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
        help='Launch graphical user interface'
    )
    
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        run_gui()
        return
    
    # CLI mode requires num_players
    if args.num_players is None:
        parser.error("num_players is required in CLI mode (or use --gui)")
    
    # Generate player names
    if args.names and len(args.names) >= args.num_players:
        player_names = args.names[:args.num_players]
    else:
        player_names = [f"Player{i+1}" for i in range(args.num_players)]
        if args.names:
            # Use provided names for first players, default for rest
            for i, name in enumerate(args.names):
                player_names[i] = name
    
    dpy = get_display()
    
    # Verify XInput2 is available
    dpy.xinput_query_version()
    
    # Get slave keyboard IDs for filtering (exclude XTEST keyboards)
    slave_keyboards = get_slave_keyboards(dpy)
    slave_keyboard_ids = {
        d.deviceid for d in slave_keyboards 
        if 'XTEST' not in d.name
    }
    
    # Get slave pointer IDs for filtering (exclude XTEST pointers)
    slave_pointers = get_slave_pointers(dpy)
    slave_pointer_ids = {
        d.deviceid for d in slave_pointers 
        if 'XTEST' not in d.name
    }
    
    print(f"Setting up {args.num_players} player(s): {', '.join(player_names)}")
    if args.mice:
        print("(with mice detection enabled)")
    print()
    
    # Step 1: Detect keyboards for each player
    player_keyboards = {}
    already_assigned_keyboards = set()
    
    for player_name in player_names:
        while True:
            print(f"{player_name}: Press ENTER on your keyboard...")
            keyboard_id = wait_for_enter_key(dpy, slave_keyboard_ids)
            
            if keyboard_id in already_assigned_keyboards:
                keyboard_name = get_device_name_by_id(dpy, keyboard_id)
                print(f"  ⚠ Keyboard '{keyboard_name}' (ID: {keyboard_id}) already assigned. Try another.")
                continue
            
            keyboard_name = get_device_name_by_id(dpy, keyboard_id)
            print(f"  ✓ Detected: {keyboard_name} (ID: {keyboard_id})")
            
            player_keyboards[player_name] = keyboard_id
            already_assigned_keyboards.add(keyboard_id)
            break
    
    # Step 2: Detect mice for each player (if --mice flag is set)
    player_mice = {}
    if args.mice:
        print()
        already_assigned_mice = set()
        
        for player_name in player_names:
            while True:
                print(f"{player_name}: CLICK with your mouse...")
                mouse_id = wait_for_mouse_click(dpy, slave_pointer_ids)
                
                if mouse_id in already_assigned_mice:
                    mouse_name = get_device_name_by_id(dpy, mouse_id)
                    print(f"  ⚠ Mouse '{mouse_name}' (ID: {mouse_id}) already assigned. Try another.")
                    continue
                
                mouse_name = get_device_name_by_id(dpy, mouse_id)
                print(f"  ✓ Detected: {mouse_name} (ID: {mouse_id})")
                
                player_mice[player_name] = mouse_id
                already_assigned_mice.add(mouse_id)
                break
    
    print()
    print("Assigning devices to masters...")
    print()
    
    # Step 2: Clean up extra masters that won't be needed
    # Keep only masters for Player2, Player3, etc. (not Player1, which uses Virtual core)
    masters_to_keep = player_names[1:]  # All except first player
    cleanup_extra_masters(dpy, masters_to_keep)
    
    # Step 3: Create master devices only for players beyond Player1
    # Player1 uses the existing "Virtual core keyboard"
    for i, player_name in enumerate(player_names):
        if i == 0:
            print(f"{player_name} will use existing 'Virtual core keyboard'")
        else:
            # Check if master already exists
            existing_master = find_master_keyboard_by_name(dpy, player_name)
            if existing_master:
                print(f"{player_name} master already exists (ID: {existing_master.deviceid})")
            else:
                print(f"Creating master for {player_name}...")
                create_master(player_name)
    
    # Step 5: Reattach keyboards to their respective masters
    for i, (player_name, keyboard_id) in enumerate(player_keyboards.items()):
        if i == 0:
            # Player1 uses Virtual core keyboard (ID 3)
            master_id = 3
            print(f"Reattaching keyboard {keyboard_id} to Virtual core keyboard (master ID: {master_id})...")
        else:
            master_keyboard = find_master_keyboard_by_name(dpy, player_name)
            if master_keyboard:
                master_id = master_keyboard.deviceid
                print(f"Reattaching keyboard {keyboard_id} to {player_name} (master ID: {master_id})...")
            else:
                print(f"  ⚠ Could not find master for {player_name}")
                continue
        reattach_device(keyboard_id, master_id)
    
    # Step 6: Reattach mice to their respective masters (if --mice flag is set)
    if args.mice:
        for i, (player_name, mouse_id) in enumerate(player_mice.items()):
            if i == 0:
                # Player1 uses Virtual core pointer (ID 2)
                master_id = 2
                print(f"Reattaching mouse {mouse_id} to Virtual core pointer (master ID: {master_id})...")
            else:
                master_pointer = find_master_pointer_by_name(dpy, player_name)
                if master_pointer:
                    master_id = master_pointer.deviceid
                    print(f"Reattaching mouse {mouse_id} to {player_name} (master ID: {master_id})...")
                else:
                    print(f"  ⚠ Could not find master pointer for {player_name}")
                    continue
            reattach_device(mouse_id, master_id)
    
    # Step 7: Display final configuration
    # Update player_names for display - first player uses "Virtual core"
    display_names = ["Virtual core"] + player_names[1:]
    display_configuration(dpy, display_names, show_pointers=args.mice)
    
    print()
    print("Setup complete!")


if __name__ == '__main__':
    main()
