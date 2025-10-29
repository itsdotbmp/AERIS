import curses
import core.main as main
import views.ui_parts as ui
from views.ui_parts import QUIT

def preset_selection_screen(stdscr, aircraft_presets_list):
    current_aircraft_id = main.current_aircraft_id
    current_aircraft_data = main.get_aircraft_info(current_aircraft_id)

    curses.curs_set(0)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()


    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    current_preset_name = f"Current Selected Preset: {current_aircraft_data['name']}"
    current_preset_path = f"Target folder: {ui.truncate_path(current_aircraft_data['target_folder'], 50)}"

    y = 4
    stdscr.addstr(y, 2, current_preset_name, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, current_preset_path, curses.A_DIM)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    

    pad_view_top = y + 1
    pad_view_bottom = max_y - 8
    pad_view_left = 2
    pad_view_right = max_x - 3
    pad_view_height = pad_view_bottom - pad_view_top + 1
    pad_height = max(pad_view_height, len(aircraft_presets_list) + 1 )
    pad_width = max_x - 5
    _y = pad_view_bottom + 1

    
    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))
    
    pad_pos_y = 0
    pad_cursor_y = 0

    # Line renders below pad
    stdscr.hline(_y, 2, curses.ACS_HLINE, max_x - 4)

    labels = [ui.ACCEPT_PROMPT, "(E)dit preset", ui.CANCEL_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, _y + 5, pos_x, label)

    while True:
        pad.erase()
        for idx, preset in enumerate(aircraft_presets_list):
            preset_id = preset.get("id", "")
            preset_name = preset.get("name", "")
            preset_folder = preset.get("folder", "")
            preset_url = preset.get("url", "")
            if idx == pad_cursor_y:
                display_folder = preset_folder
                display_url = preset_url
                attr = curses.A_REVERSE
                pre = "> "
            else:
                attr = curses.A_NORMAL
                pre = "  "
            preset_line = f"{pre}{preset_id:<15} '{preset_name}'"
            pad.addstr(idx, 0, f"{preset_line:<{pad_width}}", attr)
            
        

        
        stdscr.addstr(_y + 1, 2, f"Highlighted Preset Paths:", curses.A_BOLD)

        stdscr.move(_y + 2, 2)
        stdscr.clrtoeol()
        stdscr.addstr(_y + 2, 2, f"File Path: ./liveries/{display_folder}")

        stdscr.move(_y + 3, 2)
        stdscr.clrtoeol()
        stdscr.addstr(_y + 3, 2, f"Download URL: {display_url}")    
   
        
        scroll_height = len(aircraft_presets_list) - 1
        
        if scroll_height >= pad_view_height:
            ui.draw_scroll_hint(stdscr, pad_view_bottom +1, max_x)
        
        ui.draw_pad_scrollbar(stdscr,
            pad_pos_y,
            pad_height,
            scroll_height,
            pad_view_top,
            pad_view_bottom,
            pad_view_right
            )

        
        stdscr.noutrefresh()
        pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
        curses.doupdate()

        key = stdscr.getch()
        # Handle scrolling input
        pad_cursor_y = ui.handle_scroll(key, pad_cursor_y, scroll_height)
        # Adjust pad_pos_y to scroll if cursor goes past visible window
        if pad_cursor_y < pad_pos_y:
            pad_pos_y = pad_cursor_y  # scroll up
        elif pad_cursor_y >= pad_pos_y + pad_view_height:
            pad_pos_y = pad_cursor_y - pad_view_height + 1  # scroll down
        
        if ui.is_quit(key):
            return False, None
        if ui.is_cancel(key):
            return False, None
        if ui.is_accept(key):
            return True, aircraft_presets_list[pad_cursor_y]["id"]
            