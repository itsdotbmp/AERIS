import curses
import core.main as main
import views.ui_parts as ui
from views.ui_parts import QUIT
import time


def _splash_screen(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    stdscr.bkgd(' ', curses.color_pair(ui.COLOR_PAIRS["amberscreen"]))
    aeris_logo="""
       d8888 8888888888 8888888b.  8888888 .d8888b. 
      d88888 888        888   Y88b   888  d88P  Y88b
     d88P888 888        888    888   888  Y88b.     
    d88P 888 8888888    888   d88P   888   "Y888b.  
   d88P  888 888        8888888P"    888      "Y88b.
  d88P   888 888        888 T88b     888        "888
 d8888888888 888        888  T88b    888  Y88b  d88P
d88P     888 8888888888 888   T88b 8888888 "Y8888P" 
  Automated Exchange and Revision Integration System
""" 
    # Logo generated with figlet
    logo_lines = aeris_logo.splitlines()
    logo_start_y = (max_y - len(logo_lines)) // 2 # vertical centering
    logo_start_y -= 2
    logo_attr = curses.A_NORMAL
    for i, line in enumerate(logo_lines):
        logo_start_x = (max_x - len(line)) // 2 # horizontal centering
        stdscr.addstr(logo_start_y + i, logo_start_x, line, logo_attr)
    copyright = f"© 2025 dotbmp"
    copy_offset_x = max_x - len(copyright) - 2
    copy_offset_y = max_y - 3
    stdscr.addstr(copy_offset_y, copy_offset_x, copyright, curses.A_DIM)
    ui.draw_disclaimer(stdscr)

    stdscr.refresh()
    time.sleep(1)

def main_menu(stdscr):
    current_aircraft_id = main.current_aircraft_id
    

    curses.curs_set(0)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    if not current_aircraft_id:
        # Attempt to initialize default aircraft from main.py
        success = main.load_config()  # sets default_aircraft_id if missing
        if success:
            current_aircraft_id = main.current_aircraft_id
        else:
            # fallback if even automatic setup fails
            current_aircraft_id = None

    update_available = main.is_update_available(main.software_version)
    
    if current_aircraft_id:
        current_aircraft_data = main.get_aircraft_info(current_aircraft_id)
        _preset_name_text = current_aircraft_data['name']
        _preset_path_text = ui.truncate_path(current_aircraft_data['target_folder'], 50)
    else: 
        _preset_name_text = "MISSING OR INVALID CONFIG"
        _preset_path_text = "MISSING OR INVALID CONFIG"
    
    current_preset_name = f"Current Selected Preset: {_preset_name_text}"
    current_preset_path = f"Target folder: {_preset_path_text}"
    y = 4
    stdscr.addstr(y, 2, current_preset_name, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, current_preset_path, curses.A_DIM)
    y += 4
    
    if update_available:
        update_message = f"  A newer version of AERIS is available! Check github releases.  "
        centered_message = (max_x - len(update_message)) // 2
        stdscr.addstr(max_y - 3, centered_message, update_message,  curses.color_pair(ui.COLOR_PAIRS["info window"]))
    current_index = 0
    selections = ["Choose Preset", "Config", "Start Update", "Quit"]
    while True:
        ui.new_menu_vertical(stdscr, y, 2, selections, current_index)
        stdscr.refresh()

        key = stdscr.getch()
        # Key inputs
        try:
            ui.is_quit(key)
        except ui.QuitFlow:
            return QUIT
        
        if ui.is_continue(key) or ui.is_accept(key):
            return selections[current_index]
        # Scrolling
        current_index = ui.handle_scroll(key, current_index, len(selections)-1)