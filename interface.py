import curses
import main

def main_curses(stdscr):
    curses.curs_set(0) 
    title = "86th vFW Livery Tool"
    current_aircraft = main.aircrafts[main.current_aircraft_id]
    working_folder = main.get_working_folder(main.current_aircraft_id)
    local_version = main.get_latest_release(main.get_local_version_file(main.current_aircraft_id))
    current_aircraft_id = main.current_aircraft_id
    # Start screen

    menu_list = ("Change Aircraft", "Check for Updates", "Config", "Quit")

    #show menu
    while True:
        menu_y, menu_x = start_screen(stdscr, title, current_aircraft, working_folder, local_version, current_aircraft_id )
        choice = menu_vertical(stdscr, menu_y, menu_x, menu_list)
        if choice == "Quit":
            break
        elif choice == "Change Aircraft":
            stdscr.addstr(14, 2, f"{choice}")
        elif choice == "Check for Updates":
            check_updates_screen(stdscr, title, current_aircraft_id)
        elif choice == "Config":
            stdscr.addstr(14, 2, f"{choice}")

    

def start_screen(stdscr, title, current_aircraft, working_folder, local_version, current_aircraft_id):
    curses.start_color()
    stdscr.clear()

    # Add a bold title
    stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(1, 2, title)
    stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)

    info = [
        ("Current Aircraft", current_aircraft["name"]),
        ("Aircraft ID", current_aircraft_id),
        ("Livery Folder", working_folder),
        ("Current Version", local_version),
    ]

    # longest column based on longest label
    label_width = max(len(label) for label, _ in info)

    start_y = 4
    for i, (label, value) in enumerate(info):
        y = start_y + i
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(y, 2, f"{label:<{label_width}}")
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(y, 4 + label_width, f": {value}")

    stdscr.refresh()

    menu_y = 9
    menu_x = 4
    return menu_y, menu_x
    
def menu_vertical(stdscr, menu_y, menu_x, options):
    current_index = 0
    num_options = len(options)

    while True:
        for idx, option in enumerate(options):
            line = f"{idx+1}. {option}"
            y = menu_y + idx
            if idx == current_index:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, menu_x, f"> {line}")
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, menu_x, f"  {line}")

        stdscr.refresh()
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')) and current_index > 0:
            current_index -= 1
        elif key in (curses.KEY_DOWN, ord('j')) and current_index < num_options -1:
            current_index += 1
        elif key in (ord('\n'), 10, 13): # Enter Key
            return options[current_index]
        elif ord('1') <= key <= ord(str(num_options)):
            # You pressed a number key!
            current_index = key - ord('1')
            return options[current_index]
        
def check_updates_screen(stdscr, title, aircraft_id):
    stdscr.clear()

    stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(1, 2, title)
    stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)

    stdscr.refresh()

    status, data = main.get_remote_updates(aircraft_id)

    y = 4

    if status == "up_to_date":
        stdscr.addstr(y, 2, "Your files are already up to date.")
        y += 2
        stdscr.addstr(y, 2, "Press any key to return to main menu.")
        stdscr.refresh()
        stdscr.getch()
        return
    elif status == "error":
        stdscr.addstr(y, 2, f"Error, check for updates: {data}")
        y += 2
        stdscr.addstr(y, 2, "Press any key to return to main menu.")
        stdscr.refresh()
        stdscr.getch()
        return
    # Status okay, then we display the files/folders to download/delete
    download_files, delete_folders = data

    stdscr.addstr(y, 2, "The following changes are available:", curses.A_BOLD)
    y += 2

    if download_files:
        stdscr.addstr(y, 2, "Files to download:", curses.A_BOLD)
        y += 1
        for file in download_files:
            stdscr.addstr(y, 3, f"- {file}")
            y += 1
        y += 1
    
    if delete_folders:
        stdscr.addstr(y, 2, "Files to delete:", curses.A_BOLD)
        y += 1
        for folder in delete_folders:
            stdscr.addstr(y, 3, f"- {folder}")
            y += 1
        y += 1

    update_options = [
        "Apply full update (download + delete)",
        "Download new files only (no delete)",
        "Cancel update"
    ]
    # Show a vertical menu at a given position
    selection = menu_vertical(stdscr, y, 2, update_options)
    if selection == "Apply full update (download + delete)":
        if download_files:
            show_download_status(stdscr, download_files, aircraft_id)
        if delete_folders:
            main.process_deletes(delete_folders, aircraft_id)
        main.clean_up_operation(False, False, True)
        return
    
    elif selection == "Download new files only (no delete)":
        if download_files:
            show_download_status(stdscr, download_files, aircraft_id)
        main.clean_up_operation(False, False, True)
        
    
    elif selection == "Cancel update":
        # Return to main menu!
        return
    
def show_download_status(stdscr, files_to_download, aircraft_id):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # downloading bg
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # done text
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK) # error text

    max_y, max_x = stdscr.getmaxyx()

    # Creating a pad slightly taller then the terminal height to allow scrolling
    pad_height = max(len(files_to_download) * 4 + 10, max_y)
    pad_width = max_x - 4
    pad = curses.newpad(pad_height, pad_width)
    pad_y = 0 # Pad display starting line

    pad.addstr(2, 2, "Downloading and extracting files...", curses.A_BOLD)
    file_lines = {}  # maps filename -> line in pad
    y = 4
    pad_y = 0

    # define callback for prcoess_downloads
    def update_callback(text, file=None, action=None, done=False, error=False):
        nonlocal y, pad_y
        if error:
            attr = curses.A_BOLD | curses.color_pair(3)
        elif done:
            attr = curses.color_pair(2)
        elif action == "download" or action == "extract":
            attr = curses.color_pair(1)
        else:
            attr = curses.A_NORMAL
        
        # Determine which line to write on
        if file is not None and action is not None:
            key = (file, action)
            if key not in file_lines:
                file_lines[key] = y
                line_y = y
                y += 1  # only increment when first added
            else:
                line_y = file_lines[key]
        else:
            line_y = y
            y += 1

        pad.move(line_y, 2)
        pad.clrtoeol() # clear to EOL

        pad.addstr(line_y, 2, text, attr)

        if line_y - pad_y >= max_y - 1:
            pad_y += 1

        pad.refresh(pad_y, 0, 0, 0, max_y -1, max_x -1)

    # call process downloads with the callback
    main.process_downloads(files_to_download, aircraft_id, update_callback=update_callback)

    #last line in the pad
    last_line = max(file_lines.values()) + 2

    # When downloads are complete
    pad.addstr(last_line, 2, "All downloads and extractions complete!", curses.A_BOLD | curses.color_pair(2) | curses.A_REVERSE)
    pad.addstr(last_line + 2, 2, "Press any key to return to the main menu...")

    # Ensure the pad viewport shows these lines
    if last_line + 3 > max_y - 1:
        pad_y = last_line + 3 - max_y + 1  # scroll down if necessary
    pad.refresh(pad_y, 0, 0, 0, max_y - 1, max_x - 1)

    stdscr.getch()
        

    

if __name__ == "__main__":
    main.startup()
    curses.wrapper(main_curses)

    ## FOR NEXT TIME, ADD A WAY TO SEE THE DELETES LIKE THE DOWNLOADS CURRENTLY ARE