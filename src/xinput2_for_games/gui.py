"""
GTK graphical user interface for XInput2 multiplayer gaming setup.
"""

import threading

from .core import (
    get_display,
    get_slave_keyboards,
    get_slave_pointers,
    wait_for_enter_key,
    wait_for_mouse_click,
    get_device_name_by_id,
    setup_players,
    get_configuration,
    cleanup_extra_masters,
    MASTER_KEYBOARD,
    MASTER_POINTER,
    SLAVE_KEYBOARD,
    SLAVE_POINTER,
)


def run_gui():
    """Run the GTK graphical user interface."""
    # Lazy load GTK
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import Gtk, GLib
    
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
            
            # Set up players using core function
            setup_players(
                self.dpy,
                self.player_names,
                self.player_keyboards,
                self.player_mice if self.mice_check.get_active() else None,
                log_func=self.log
            )
            
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
            cleanup_extra_masters(self.dpy, [], log_func=self.log)
            self.log("Reset to single player configuration.")
            self.set_status("Reset complete.")
            self.refresh_configuration(None)
        
        def refresh_configuration(self, button):
            """Refresh and display current device configuration."""
            self.log("")
            self.log("Current Device Configuration:")
            self.log("-" * 40)
            
            config = get_configuration(self.dpy)
            
            for master in config:
                self.log(f"\n{master['name']}:")
                self.log(f"  Keyboard (ID: {master['keyboard_master_id']}):")
                for kb in master['keyboards']:
                    self.log(f"    └─ {kb['name']} (ID: {kb['id']})")
                
                if master['pointer_master_id']:
                    self.log(f"  Pointer (ID: {master['pointer_master_id']}):")
                    for ptr in master['pointers']:
                        self.log(f"    └─ {ptr['name']} (ID: {ptr['id']})")
    
    win = XInput2GUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
