"""
Command-line interface for XInput2 multiplayer gaming setup.
"""

from .core import (
    get_display,
    get_slave_keyboard_ids,
    get_slave_pointer_ids,
    wait_for_enter_key,
    wait_for_mouse_click,
    get_device_name_by_id,
    setup_players,
    get_configuration,
    SLAVE_KEYBOARD,
    SLAVE_POINTER,
)


def display_configuration(config, show_pointers=False):
    """Display the device configuration."""
    print("\n" + "=" * 50)
    print("Final Configuration:")
    print("=" * 50)
    
    for master in config:
        print(f"\n{master['name']}:")
        print(f"  Master keyboard: {master['name']} keyboard (ID: {master['keyboard_master_id']})")
        
        for kb in master['keyboards']:
            print(f"    └─ {kb['name']} (ID: {kb['id']})")
        
        if show_pointers and master['pointer_master_id']:
            print(f"  Master pointer: {master['name']} pointer (ID: {master['pointer_master_id']})")
            
            for ptr in master['pointers']:
                print(f"    └─ {ptr['name']} (ID: {ptr['id']})")


def run_cli(num_players, player_names=None, detect_mice=False):
    """
    Run the CLI setup process.
    
    Args:
        num_players: Number of players to set up
        player_names: Optional list of custom player names
        detect_mice: Whether to also detect and assign mice
    """
    # Generate player names
    if player_names and len(player_names) >= num_players:
        names = player_names[:num_players]
    else:
        names = [f"Player{i+1}" for i in range(num_players)]
        if player_names:
            for i, name in enumerate(player_names):
                names[i] = name
    
    dpy = get_display()
    dpy.xinput_query_version()
    
    slave_keyboard_ids = get_slave_keyboard_ids(dpy)
    slave_pointer_ids = get_slave_pointer_ids(dpy)
    
    print(f"Setting up {num_players} player(s): {', '.join(names)}")
    if detect_mice:
        print("(with mice detection enabled)")
    print()
    
    # Detect keyboards
    player_keyboards = {}
    already_assigned_keyboards = set()
    
    for player_name in names:
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
    
    # Detect mice if requested
    player_mice = {}
    if detect_mice:
        print()
        already_assigned_mice = set()
        
        for player_name in names:
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
    
    # Set up players
    setup_players(dpy, names, player_keyboards, player_mice if detect_mice else None)
    
    # Display final configuration
    config = get_configuration(dpy)
    display_configuration(config, show_pointers=detect_mice)
    
    print()
    print("Setup complete!")
