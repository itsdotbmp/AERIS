import curses
import main

"""
Copyright (c) 2025 YourHandle
Released under the MIT License.
See LICENSE.txt for full license text.
"""

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
    """
    Start screen for application, shows the current selected aircraft information and menu
    """
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
        ("Local Version", local_version),
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

    draw_disclaimer(stdscr)
    stdscr.refresh()

    menu_y = 9
    menu_x = 4
    return menu_y, menu_x
    
def menu_vertical(stdscr, menu_y, menu_x, options):
    """
    Reusable vertical selection menu, takes input for location.
    """
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
    """
    Check for available updates on the remote version text file.
    Shows what files would be downloaded and deleted by the update. 
    """
    try:
        status, data = main.get_remote_updates(aircraft_id)
    except Exception as e:
        # Unexpected exception caught! ~~(__^·>
        show_popup(stdscr, [
            "Error: Cannot fetch updates.",
            f"Check the log file: {main.config["logging"]["log_file_name"]}",
            f"Exception: {e}"
        ], msg_type="error")
        return # exits back, doesn't render screen.
    if status == "error":
        show_popup(stdscr, [
            "Error: Cannot fetch updates.",
            f"Check the log file: {main.config["logging"]["log_file_name"]}"
        ], msg_type="error")
        return # exits back, doesn't render screen.
    stdscr.clear()

    stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(1, 2, title)
    stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)

    draw_disclaimer(stdscr)
    stdscr.refresh()
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
        stdscr.addstr(y, 2, "Files marked for deletion (you will be asked to confirm):", curses.A_BOLD)
        y += 1
        for folder in delete_folders:
            stdscr.addstr(y, 3, f"- {folder}")
            y += 1
        y += 1
        stdscr.addstr(y, 2, "Note: You will have a chance to confirm before any files are deleted.", curses.A_ITALIC)
        y += 2


    update_options = [
        "Apply update",
        "Cancel update"
    ]
    # Show a vertical menu at a given position
    selection = menu_vertical(stdscr, y, 2, update_options)
    if selection == "Apply update":
        download_status = None
        if download_files:
            download_status = show_download_status(stdscr, download_files, aircraft_id)
        if download_status =="downloads_complete" and delete_folders:
            confirmed = show_delete_screen(stdscr, delete_folders, aircraft_id)
            if confirmed:
                show_delete_status(stdscr, delete_folders, aircraft_id)
            else:
                return
            # main.process_deletes(delete_folders, aircraft_id)
        main.clean_up_operation(False, False, False)
        return        
    
    elif selection == "Cancel update":
        # Return to main menu!
        return
    
def show_delete_screen(stdscr, delete_folders, aircraft_id):
    """
    Show the list of folders to delete, confirm action, and process deletions
    with live updates using the callback system.
    """
    curses.curs_set(0)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    # Draw header
    stdscr.attron(curses.A_BOLD | curses.A_UNDERLINE)
    stdscr.addstr(1, 2, "Confirm Folders to Delete")
    stdscr.attroff(curses.A_BOLD | curses.A_UNDERLINE)
    
    # List folders
    y = 3
    for folder in delete_folders:
        stdscr.addstr(y, 4, f"- {folder}")
        y += 1
    
    # Add menu for confirmation
    confirm_options = ["Confirm Delete", "Cancel"]
    choice = menu_vertical(stdscr, y + 1, 2, confirm_options)
    
    return choice == "Confirm Delete"


def show_download_status(stdscr, files_to_download, aircraft_id):
    """
    Show the download progress and status of the files in the update
    """
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

        pad.refresh(pad_y, 0, 0, 0, max_y -2, max_x -1)
        draw_disclaimer(stdscr)
        stdscr.refresh()
    

    # call process downloads with the callback
    main.process_downloads(files_to_download, aircraft_id, update_callback=update_callback)

    #last line in the pad
    last_line = max(file_lines.values()) + 2

    # When downloads are complete
    pad.addstr(last_line, 2, "All downloads and extractions complete!", curses.A_BOLD | curses.color_pair(2) | curses.A_REVERSE)
    pad.addstr(last_line + 2, 2, "[Press any key to continue]", curses.A_DIM)

    # Ensure the pad viewport shows these lines
    if last_line + 3 > max_y - 1:
        pad_y = last_line + 3 - max_y + 1  # scroll down if necessary
    pad.refresh(pad_y, 0, 0, 0, max_y - 2, max_x - 1)
    
    draw_disclaimer(stdscr)
    stdscr.refresh()
    stdscr.getch()
    return "downloads_complete"

def show_delete_status(stdscr, delete_folders, aircraft_id):
    """
    Show the status and progress of deleting the folders from folders_delete.
    """
    max_y, max_x = stdscr.getmaxyx()
    pad_height = max(len(delete_folders) * 2 + 10, max_y)
    pad_width = max_x - 4
    pad = curses.newpad(pad_height, pad_width)
    pad_y = 0
    y = 2

    # define callback
    folder_lines = {}
    def update_callback(text, folder=None, done=False, error=False):
        nonlocal y, pad_y
        if folder not in folder_lines:
            folder_lines[folder] = y
            line_y = y
            y += 1
        else:
            line_y = folder_lines[folder]

        if error:
            attr = curses.A_BOLD | curses.color_pair(3)
        elif done:
            attr = curses.color_pair(2)
        else:
            attr = curses.color_pair(1)

        pad.move(line_y, 2)
        pad.clrtoeol()
        pad.addstr(line_y, 2, text, attr)
        pad.refresh(pad_y, 0, 0, 0, max_y - 2, max_x - 1)
        draw_disclaimer(stdscr)

    # call process_deletes with callback
    main.process_deletes(delete_folders, aircraft_id, update_callback=update_callback)

    pad.addstr(y + 1, 2, "Deletion complete! Press any key to continue.", curses.A_BOLD)
    pad.refresh(pad_y, 0, 0, 0, max_y - 2, max_x - 1)
    draw_disclaimer(stdscr)
    stdscr.refresh()  
    stdscr.getch()  

def show_popup(stdscr, message_lines, msg_type="info"):
    # Display a centered popup screen with border and styled text
    # Args:
    #       stdscr: The main curses screen
    #       message: List of strings to display inside the popup.
    #       type: type of message, "error" gives a red background, "info" a white background.

    curses.curs_set(0)

    max_y, max_x = stdscr.getmaxyx()

    # Set popup size
    width = max(len(line) for line in message_lines) + 4
    height = len(message_lines) + 4

    # center the popup
    start_y = max((max_y - height)// 2, 0)
    start_x = max((max_x - width)// 2, 0)
    
    # create a window for the popup
    win = curses.newwin(height, width, start_y, start_x)

    # Define colours
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED) # error style
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE) # normal info style

    if msg_type == "error":
        attr = curses.color_pair(1) | curses.A_BOLD
        border_ch = curses.ACS_DIAMOND
    else:
        attr = curses.color_pair(2)
        border_ch = curses.ACS_VLINE
    
    # Fill the background
    win.bkgd(" ", attr)
    win.clear()

    # Draw Border
    win.border()

    # Add text lines
    for idx, line in enumerate(message_lines):
        win.addstr(2 + idx, 2, line[:width-4], attr)

    # User hint to press any key to continue
    hint = "Press any key to return"
    hint_x = (width - len(hint)) // 2
    win.addstr(height-1, hint_x, hint, attr | curses.A_BOLD)
    
    # Refresh the popup
    win.refresh()

    # Wait for user input
    stdscr.getch()

    # Clear popup after key press
    win.clear()
    stdscr.refresh()

def draw_disclaimer(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    disclaimer = "Software provided 'AS IS' with no warranty. See LICENSE for details."
    x = (max_x - len(disclaimer)) // 2
    y = max_y - 1
    stdscr.attron(curses.A_DIM)
    stdscr.addstr(y, x, disclaimer)
    stdscr.attroff(curses.A_DIM)
    
if __name__ == "__main__":
    main.startup()
    curses.wrapper(main_curses)

    ## FOR NEXT TIME, ADD A WAY TO SEE THE DELETES LIKE THE DOWNLOADS CURRENTLY ARE