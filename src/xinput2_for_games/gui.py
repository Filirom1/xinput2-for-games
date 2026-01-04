"""
GTK graphical user interface for XInput2 multiplayer gaming setup.
Retro arcade style with neon colors and pixel aesthetics!
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

# Retro color palette
COLORS = {
    'bg_dark': '#0a0a12',
    'bg_panel': '#12121f',
    'neon_pink': '#ff00ff',
    'neon_cyan': '#00ffff',
    'neon_green': '#39ff14',
    'neon_yellow': '#ffff00',
    'neon_orange': '#ff6600',
    'neon_red': '#ff0044',
    'neon_blue': '#0088ff',
    'text_dim': '#666688',
    'text_bright': '#ffffff',
    'scanline': 'rgba(0,0,0,0.15)',
}

# Player colors for visual distinction
PLAYER_COLORS = [
    '#ff0044',  # Red
    '#00ffff',  # Cyan
    '#39ff14',  # Green
    '#ffff00',  # Yellow
    '#ff00ff',  # Pink
    '#ff6600',  # Orange
    '#0088ff',  # Blue
    '#ff88ff',  # Light pink
    '#88ffff',  # Light cyan
    '#ffff88',  # Light yellow
]

# ASCII art logo
LOGO_ART = """
╔═══════════════════════════════════════════════════════╗
║  ██╗  ██╗██╗███╗   ██╗██████╗ ██╗   ██╗████████╗██████╗ ║
║  ╚██╗██╔╝██║████╗  ██║██╔══██╗██║   ██║╚══██╔══╝╚════██╗║
║   ╚███╔╝ ██║██╔██╗ ██║██████╔╝██║   ██║   ██║    █████╔╝║
║   ██╔██╗ ██║██║╚██╗██║██╔═══╝ ██║   ██║   ██║   ██╔═══╝ ║
║  ██╔╝ ██╗██║██║ ╚████║██║     ╚██████╔╝   ██║   ███████╗║
║  ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝    ╚═╝   ╚══════╝║
║            ★ MULTIPLAYER ARCADE SETUP ★                 ║
╚═══════════════════════════════════════════════════════╝
"""

CSS_STYLE = """
/* Main window - dark arcade cabinet style */
window {
    background-color: #0a0a12;
}

/* Retro frame styling */
frame {
    border: 2px solid #ff00ff;
    border-radius: 0px;
    background-color: #12121f;
    padding: 5px;
}

frame > label {
    color: #00ffff;
    font-weight: bold;
    font-size: 14px;
    text-shadow: 0 0 10px #00ffff;
}

/* Neon button styling */
button {
    background: linear-gradient(180deg, #2a2a4a 0%, #1a1a2a 100%);
    border: 2px solid #ff00ff;
    border-radius: 0px;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 16px;
    font-size: 13px;
    text-shadow: 0 0 5px #ff00ff;
    min-height: 36px;
}

button:hover {
    background: linear-gradient(180deg, #3a3a6a 0%, #2a2a4a 100%);
    border-color: #00ffff;
    text-shadow: 0 0 10px #00ffff;
}

button:active {
    background: #ff00ff;
    color: #000000;
}

button:disabled {
    background: #1a1a2a;
    border-color: #333355;
    color: #555577;
    text-shadow: none;
}

/* Start button - special neon green */
button.start-btn {
    border-color: #39ff14;
    text-shadow: 0 0 5px #39ff14;
    font-size: 14px;
}

button.start-btn:hover {
    border-color: #00ffff;
    text-shadow: 0 0 10px #00ffff;
}

/* Spinbutton styling */
spinbutton {
    background-color: #12121f;
    border: 2px solid #ff00ff;
    color: #39ff14;
    font-weight: bold;
    font-size: 16px;
    padding: 4px;
    min-width: 60px;
}

spinbutton text {
    background-color: #12121f;
    color: #39ff14;
}

spinbutton button {
    background: #1a1a2a;
    border: 1px solid #ff00ff;
    min-width: 24px;
    min-height: 24px;
    padding: 2px;
}

/* Checkbox styling */
checkbutton {
    color: #ffffff;
    font-weight: bold;
}

checkbutton check {
    background-color: #12121f;
    border: 2px solid #ff00ff;
    border-radius: 0px;
    min-width: 20px;
    min-height: 20px;
}

checkbutton:checked check {
    background-color: #39ff14;
    border-color: #39ff14;
}

/* Labels */
label {
    color: #ffffff;
    font-size: 13px;
}

label.title-label {
    color: #00ffff;
    font-size: 11px;
    font-family: monospace;
}

label.status-label {
    color: #ffff00;
    font-weight: bold;
    font-size: 15px;
    text-shadow: 0 0 8px #ffff00;
}

label.waiting-label {
    color: #ff00ff;
    animation: blink 1s infinite;
}

/* Text view - terminal style */
textview {
    background-color: #0a0a12;
    color: #39ff14;
    font-family: monospace;
    font-size: 12px;
}

textview text {
    background-color: #0a0a12;
    color: #39ff14;
}

/* Scrolled window */
scrolledwindow {
    border: 2px solid #333355;
    background-color: #0a0a12;
}

scrollbar {
    background-color: #12121f;
}

scrollbar slider {
    background-color: #ff00ff;
    border-radius: 0px;
    min-width: 8px;
}

/* Player indicator boxes */
.player-box {
    border: 2px solid #ff00ff;
    border-radius: 0px;
    padding: 10px;
    margin: 5px;
    background-color: #12121f;
}

.player-box.active {
    border-color: #39ff14;
    box-shadow: 0 0 15px #39ff14;
}

.player-box.done {
    border-color: #00ffff;
}

/* Scanline overlay effect */
.scanlines {
    background: repeating-linear-gradient(
        0deg,
        rgba(0, 0, 0, 0.15),
        rgba(0, 0, 0, 0.15) 1px,
        transparent 1px,
        transparent 2px
    );
}
"""


def run_gui():
    """Run the GTK graphical user interface."""
    # Lazy load GTK
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import Gtk, GLib, Gdk, Pango
    
    # Apply CSS styling
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS_STYLE.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    
    class XInput2GUI(Gtk.Window):
        def __init__(self):
            super().__init__(title="🕹️ XInput2 - Multiplayer Arcade Setup")
            self.set_default_size(650, 750)
            self.set_border_width(15)
            
            self.dpy = get_display()
            self.dpy.xinput_query_version()
            
            self.player_keyboards = {}
            self.player_mice = {}
            self.player_names = []
            self.current_player_index = 0
            self.detecting_mice = False
            self.detection_active = False
            self.blink_state = True
            self.blink_timeout_id = None
            self.player_boxes = []
            
            self.create_widgets()
        
        def create_widgets(self):
            # Main vertical box
            main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(main_vbox)
            
            # ASCII Logo
            logo_frame = Gtk.Frame()
            main_vbox.pack_start(logo_frame, False, False, 0)
            
            logo_label = Gtk.Label()
            logo_label.set_markup(f'<span font_family="monospace" size="7000" foreground="#00ffff">{LOGO_ART}</span>')
            logo_label.get_style_context().add_class('title-label')
            logo_label.set_margin_top(5)
            logo_label.set_margin_bottom(5)
            logo_frame.add(logo_label)
            
            # Setup frame
            setup_frame = Gtk.Frame(label="⚙ CONFIGURATION")
            main_vbox.pack_start(setup_frame, False, False, 0)
            
            setup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            setup_box.set_margin_start(15)
            setup_box.set_margin_end(15)
            setup_box.set_margin_top(15)
            setup_box.set_margin_bottom(15)
            setup_frame.add(setup_box)
            
            # Number of players with icon
            players_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            setup_box.pack_start(players_box, False, False, 0)
            
            players_icon = Gtk.Label()
            players_icon.set_markup('<span size="16000">👥</span>')
            players_box.pack_start(players_icon, False, False, 0)
            
            players_label = Gtk.Label(label="PLAYERS:")
            players_box.pack_start(players_label, False, False, 0)
            
            self.num_players_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
            self.num_players_spin.set_value(2)
            self.num_players_spin.connect("value-changed", self.update_player_preview)
            players_box.pack_start(self.num_players_spin, False, False, 0)
            
            # Mice checkbox with icon
            mice_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            setup_box.pack_start(mice_box, False, False, 10)
            
            mice_icon = Gtk.Label()
            mice_icon.set_markup('<span size="14000">🖱️</span>')
            mice_box.pack_start(mice_icon, False, False, 0)
            
            self.mice_check = Gtk.CheckButton(label="DETECT MICE")
            mice_box.pack_start(self.mice_check, False, False, 0)
            
            # Start button - bigger and neon green
            self.start_btn = Gtk.Button()
            start_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            start_icon = Gtk.Label()
            start_icon.set_markup('<span size="14000">▶</span>')
            start_box.pack_start(start_icon, False, False, 0)
            start_label = Gtk.Label(label="INSERT COIN")
            start_box.pack_start(start_label, False, False, 0)
            self.start_btn.add(start_box)
            self.start_btn.get_style_context().add_class('start-btn')
            self.start_btn.connect("clicked", self.start_detection)
            setup_box.pack_end(self.start_btn, False, False, 0)
            
            # Player preview area
            preview_frame = Gtk.Frame(label="🎮 PLAYERS")
            main_vbox.pack_start(preview_frame, False, False, 0)
            
            self.players_preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.players_preview_box.set_margin_start(10)
            self.players_preview_box.set_margin_end(10)
            self.players_preview_box.set_margin_top(10)
            self.players_preview_box.set_margin_bottom(10)
            self.players_preview_box.set_homogeneous(True)
            preview_frame.add(self.players_preview_box)
            
            # Initialize player preview
            self.update_player_preview(None)
            
            # Status frame with big blinking text
            status_frame = Gtk.Frame(label="📡 STATUS")
            main_vbox.pack_start(status_frame, False, False, 0)
            
            status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            status_box.set_margin_start(15)
            status_box.set_margin_end(15)
            status_box.set_margin_top(15)
            status_box.set_margin_bottom(15)
            status_frame.add(status_box)
            
            self.status_label = Gtk.Label()
            self.status_label.set_markup('<span size="13000" foreground="#ffff00">★ READY - INSERT COIN TO START ★</span>')
            self.status_label.get_style_context().add_class('status-label')
            self.status_label.set_line_wrap(True)
            status_box.pack_start(self.status_label, False, False, 0)
            
            # Terminal output frame
            terminal_frame = Gtk.Frame(label="💻 TERMINAL")
            main_vbox.pack_start(terminal_frame, True, True, 0)
            
            terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            terminal_frame.add(terminal_box)
            
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_margin_start(5)
            scrolled.set_margin_end(5)
            scrolled.set_margin_top(5)
            scrolled.set_margin_bottom(5)
            terminal_box.pack_start(scrolled, True, True, 0)
            
            self.text_view = Gtk.TextView()
            self.text_view.set_editable(False)
            self.text_view.set_monospace(True)
            self.text_view.set_left_margin(10)
            self.text_view.set_right_margin(10)
            self.text_view.set_top_margin(10)
            self.text_view.set_bottom_margin(10)
            self.text_buffer = self.text_view.get_buffer()
            
            # Create text tags for colored output
            self.text_buffer.create_tag("green", foreground="#39ff14")
            self.text_buffer.create_tag("cyan", foreground="#00ffff")
            self.text_buffer.create_tag("pink", foreground="#ff00ff")
            self.text_buffer.create_tag("yellow", foreground="#ffff00")
            self.text_buffer.create_tag("red", foreground="#ff0044")
            self.text_buffer.create_tag("orange", foreground="#ff6600")
            self.text_buffer.create_tag("dim", foreground="#666688")
            self.text_buffer.create_tag("bold", weight=Pango.Weight.BOLD)
            
            scrolled.add(self.text_view)
            
            # Button box with arcade style buttons
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_box.set_margin_top(5)
            main_vbox.pack_start(btn_box, False, False, 0)
            
            # Reset button
            self.cleanup_btn = Gtk.Button()
            cleanup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            cleanup_icon = Gtk.Label()
            cleanup_icon.set_markup('<span size="12000">🔄</span>')
            cleanup_box.pack_start(cleanup_icon, False, False, 0)
            cleanup_label = Gtk.Label(label="RESET")
            cleanup_box.pack_start(cleanup_label, False, False, 0)
            self.cleanup_btn.add(cleanup_box)
            self.cleanup_btn.connect("clicked", self.cleanup_masters)
            btn_box.pack_start(self.cleanup_btn, False, False, 0)
            
            # Refresh button
            self.refresh_btn = Gtk.Button()
            refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            refresh_icon = Gtk.Label()
            refresh_icon.set_markup('<span size="12000">🔍</span>')
            refresh_box.pack_start(refresh_icon, False, False, 0)
            refresh_label = Gtk.Label(label="SCAN")
            refresh_box.pack_start(refresh_label, False, False, 0)
            self.refresh_btn.add(refresh_box)
            self.refresh_btn.connect("clicked", self.refresh_configuration)
            btn_box.pack_start(self.refresh_btn, False, False, 0)
            
            # Credits/version text
            credits_label = Gtk.Label()
            credits_label.set_markup('<span size="9000" foreground="#666688">v1.0 • Made with ❤️ for couch gaming</span>')
            btn_box.pack_end(credits_label, False, False, 0)
            
            # Show welcome message
            self.show_welcome()
        
        def show_welcome(self):
            """Display welcome message in terminal."""
            self.log_colored("═" * 50, "cyan")
            self.log_colored("  🕹️  WELCOME TO XINPUT2 MULTIPLAYER SETUP  🕹️", "cyan", bold=True)
            self.log_colored("═" * 50, "cyan")
            self.log_colored("", "green")
            self.log_colored("  Set up multiple input devices for local", "dim")
            self.log_colored("  multiplayer gaming on Linux!", "dim")
            self.log_colored("", "green")
            self.log_colored("  HOW TO PLAY:", "yellow", bold=True)
            self.log_colored("  1. Select number of players", "green")
            self.log_colored("  2. Click 'INSERT COIN' to start", "green")
            self.log_colored("  3. Each player presses ENTER on their keyboard", "green")
            self.log_colored("  4. Enjoy your multiplayer game! 🎮", "green")
            self.log_colored("", "green")
            self.log_colored("─" * 50, "dim")
        
        def update_player_preview(self, widget):
            """Update the player preview boxes."""
            # Clear existing boxes
            for child in self.players_preview_box.get_children():
                self.players_preview_box.remove(child)
            
            self.player_boxes = []
            num_players = int(self.num_players_spin.get_value())
            
            for i in range(num_players):
                player_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                player_box.get_style_context().add_class('player-box')
                
                # Player icon
                icon_label = Gtk.Label()
                icon_label.set_markup(f'<span size="24000">🎮</span>')
                player_box.pack_start(icon_label, False, False, 0)
                
                # Player name
                name_label = Gtk.Label()
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                name_label.set_markup(f'<span font_weight="bold" foreground="{color}">P{i+1}</span>')
                player_box.pack_start(name_label, False, False, 0)
                
                # Status indicator
                status_label = Gtk.Label()
                status_label.set_markup('<span size="9000" foreground="#666688">WAITING</span>')
                player_box.pack_start(status_label, False, False, 0)
                
                self.player_boxes.append({
                    'box': player_box,
                    'icon': icon_label,
                    'name': name_label,
                    'status': status_label,
                    'color': color
                })
                
                self.players_preview_box.pack_start(player_box, True, True, 0)
            
            self.players_preview_box.show_all()
        
        def set_player_status(self, player_index, status, detecting=False):
            """Update a player's status in the preview."""
            if player_index < len(self.player_boxes):
                box_info = self.player_boxes[player_index]
                color = box_info['color']
                
                if status == "detecting":
                    box_info['status'].set_markup(f'<span size="9000" foreground="{color}">⚡ PRESS ENTER</span>')
                    box_info['icon'].set_markup('<span size="24000">⌨️</span>')
                elif status == "detecting_mouse":
                    box_info['status'].set_markup(f'<span size="9000" foreground="{color}">⚡ CLICK MOUSE</span>')
                    box_info['icon'].set_markup('<span size="24000">🖱️</span>')
                elif status == "done":
                    box_info['status'].set_markup('<span size="9000" foreground="#39ff14">✓ READY!</span>')
                    box_info['icon'].set_markup('<span size="24000">✅</span>')
                elif status == "waiting":
                    box_info['status'].set_markup('<span size="9000" foreground="#666688">WAITING</span>')
                    box_info['icon'].set_markup('<span size="24000">🎮</span>')
        
        def log(self, message):
            """Add message to text view (default green)."""
            self.log_colored(message, "green")
        
        def log_colored(self, message, color="green", bold=False):
            """Add colored message to text view."""
            end_iter = self.text_buffer.get_end_iter()
            if bold:
                self.text_buffer.insert_with_tags_by_name(end_iter, message + "\n", color, "bold")
            else:
                self.text_buffer.insert_with_tags_by_name(end_iter, message + "\n", color)
            # Scroll to end
            mark = self.text_buffer.create_mark(None, self.text_buffer.get_end_iter(), False)
            self.text_view.scroll_to_mark(mark, 0, False, 0, 0)
        
        def clear_log(self):
            """Clear text view."""
            self.text_buffer.set_text("")
        
        def set_status(self, message, color="#ffff00"):
            """Update status label with blinking effect."""
            self.status_label.set_markup(f'<span size="13000" foreground="{color}">{message}</span>')
        
        def start_blink(self):
            """Start status blinking."""
            if self.blink_timeout_id is None:
                self.blink_timeout_id = GLib.timeout_add(500, self.toggle_blink)
        
        def stop_blink(self):
            """Stop status blinking."""
            if self.blink_timeout_id is not None:
                GLib.source_remove(self.blink_timeout_id)
                self.blink_timeout_id = None
        
        def toggle_blink(self):
            """Toggle blink state."""
            self.blink_state = not self.blink_state
            if self.blink_state:
                self.status_label.set_opacity(1.0)
            else:
                self.status_label.set_opacity(0.3)
            return True
        
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
            
            # Reset player preview
            for i, box_info in enumerate(self.player_boxes):
                self.set_player_status(i, "waiting")
            
            self.log_colored("═" * 50, "pink")
            self.log_colored(f"  🎮 STARTING {num_players} PLAYER SETUP 🎮", "pink", bold=True)
            self.log_colored("═" * 50, "pink")
            self.log_colored("", "green")
            
            self.start_blink()
            
            # Start keyboard detection in background thread
            threading.Thread(target=self.detect_next_keyboard, daemon=True).start()
        
        def detect_next_keyboard(self):
            """Detect keyboard for current player."""
            if self.current_player_index >= len(self.player_names):
                # Done with keyboards, move to mice or finish
                if self.mice_check.get_active():
                    self.current_player_index = 0
                    self.detecting_mice = True
                    GLib.idle_add(self.log_colored, "", "green")
                    GLib.idle_add(self.log_colored, "─" * 50, "dim")
                    GLib.idle_add(self.log_colored, "  🖱️  NOW DETECTING MICE...", "orange", True)
                    GLib.idle_add(self.log_colored, "─" * 50, "dim")
                    # Reset player status for mouse detection
                    for i in range(len(self.player_boxes)):
                        GLib.idle_add(self.set_player_status, i, "waiting")
                    threading.Thread(target=self.detect_next_mouse, daemon=True).start()
                else:
                    GLib.idle_add(self.finish_setup)
                return
            
            player_name = self.player_names[self.current_player_index]
            color = PLAYER_COLORS[self.current_player_index % len(PLAYER_COLORS)]
            
            GLib.idle_add(self.set_status, f"⌨️ {player_name}: PRESS ENTER! ⌨️", color)
            GLib.idle_add(self.set_player_status, self.current_player_index, "detecting")
            GLib.idle_add(self.log_colored, f"  ⌨️  {player_name}: Press ENTER on your keyboard...", "yellow")
            
            # Get slave keyboard IDs
            slave_keyboards = get_slave_keyboards(self.dpy)
            slave_keyboard_ids = {d.deviceid for d in slave_keyboards if 'XTEST' not in d.name}
            already_assigned = set(self.player_keyboards.values())
            
            while self.detection_active:
                keyboard_id = wait_for_enter_key(self.dpy, slave_keyboard_ids)
                
                if keyboard_id in already_assigned:
                    keyboard_name = get_device_name_by_id(self.dpy, keyboard_id)
                    GLib.idle_add(self.log_colored, f"      ⚠️  '{keyboard_name}' already taken! Try another.", "red")
                    continue
                
                keyboard_name = get_device_name_by_id(self.dpy, keyboard_id)
                self.player_keyboards[player_name] = keyboard_id
                GLib.idle_add(self.log_colored, f"      ✓ {keyboard_name}", "green")
                GLib.idle_add(self.set_player_status, self.current_player_index, "done")
                break
            
            self.current_player_index += 1
            threading.Thread(target=self.detect_next_keyboard, daemon=True).start()
        
        def detect_next_mouse(self):
            """Detect mouse for current player."""
            if self.current_player_index >= len(self.player_names):
                GLib.idle_add(self.finish_setup)
                return
            
            player_name = self.player_names[self.current_player_index]
            color = PLAYER_COLORS[self.current_player_index % len(PLAYER_COLORS)]
            
            GLib.idle_add(self.set_status, f"🖱️ {player_name}: CLICK MOUSE! 🖱️", color)
            GLib.idle_add(self.set_player_status, self.current_player_index, "detecting_mouse")
            GLib.idle_add(self.log_colored, f"  🖱️  {player_name}: Click with your mouse...", "yellow")
            
            # Get slave pointer IDs
            slave_pointers = get_slave_pointers(self.dpy)
            slave_pointer_ids = {d.deviceid for d in slave_pointers if 'XTEST' not in d.name}
            already_assigned = set(self.player_mice.values())
            
            while self.detection_active:
                mouse_id = wait_for_mouse_click(self.dpy, slave_pointer_ids)
                
                if mouse_id in already_assigned:
                    mouse_name = get_device_name_by_id(self.dpy, mouse_id)
                    GLib.idle_add(self.log_colored, f"      ⚠️  '{mouse_name}' already taken! Try another.", "red")
                    continue
                
                mouse_name = get_device_name_by_id(self.dpy, mouse_id)
                self.player_mice[player_name] = mouse_id
                GLib.idle_add(self.log_colored, f"      ✓ {mouse_name}", "green")
                GLib.idle_add(self.set_player_status, self.current_player_index, "done")
                break
            
            self.current_player_index += 1
            threading.Thread(target=self.detect_next_mouse, daemon=True).start()
        
        def finish_setup(self):
            """Apply the configuration and display results."""
            self.detection_active = False
            self.stop_blink()
            self.status_label.set_opacity(1.0)
            
            self.log_colored("", "green")
            self.log_colored("─" * 50, "dim")
            self.log_colored("  ⚡ CONFIGURING DEVICES...", "cyan", True)
            self.log_colored("─" * 50, "dim")
            
            # Set up players using core function
            setup_players(
                self.dpy,
                self.player_names,
                self.player_keyboards,
                self.player_mice if self.mice_check.get_active() else None,
                log_func=lambda msg: self.log_colored(f"  {msg}", "cyan")
            )
            
            self.log_colored("", "green")
            self.log_colored("═" * 50, "green")
            self.log_colored("  🎉 SETUP COMPLETE! GAME ON! 🎉", "green", True)
            self.log_colored("═" * 50, "green")
            
            self.set_status("✅ READY TO PLAY! ✅", "#39ff14")
            
            # Update all player boxes to done
            for i in range(len(self.player_boxes)):
                self.set_player_status(i, "done")
            
            # Re-enable controls
            self.set_controls_sensitive(True)
            
            self.refresh_configuration(None)
        
        def cleanup_masters(self, button):
            """Remove all extra masters, returning to single player setup."""
            self.clear_log()
            self.log_colored("═" * 50, "orange")
            self.log_colored("  🔄 RESETTING TO SINGLE PLAYER...", "orange", True)
            self.log_colored("═" * 50, "orange")
            self.log_colored("", "green")
            
            cleanup_extra_masters(self.dpy, [], log_func=lambda msg: self.log_colored(f"  {msg}", "orange"))
            
            self.log_colored("", "green")
            self.log_colored("  ✓ Reset complete!", "green")
            self.set_status("🔄 RESET COMPLETE", "#ff6600")
            self.refresh_configuration(None)
        
        def refresh_configuration(self, button):
            """Refresh and display current device configuration."""
            self.log_colored("", "green")
            self.log_colored("─" * 50, "dim")
            self.log_colored("  📋 CURRENT DEVICE CONFIGURATION", "cyan", True)
            self.log_colored("─" * 50, "dim")
            
            config = get_configuration(self.dpy)
            
            for i, master in enumerate(config):
                color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
                self.log_colored("", "green")
                self.log_colored(f"  🎮 {master['name']}", "cyan", True)
                
                self.log_colored(f"     ⌨️  Keyboard (ID: {master['keyboard_master_id']})", "dim")
                for kb in master['keyboards']:
                    self.log_colored(f"        └─ {kb['name']}", "green")
                
                if master['pointer_master_id']:
                    self.log_colored(f"     🖱️  Pointer (ID: {master['pointer_master_id']})", "dim")
                    for ptr in master['pointers']:
                        self.log_colored(f"        └─ {ptr['name']}", "green")
    
    win = XInput2GUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
