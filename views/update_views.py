import curses
import main
import views.ui_parts as ui

def check_updates_screen(stdscr, download_files, delete_folders, aircraft_data):
    """
    Just display the update info and get the user's choice: "Apply update" or "Cancel update".
    Returns the choice.
    """
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    update_for = f"Update available for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 50)}"
    

    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following changes will be applied:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)
    pad_top = y + 1
    pad_bottom = max_y - 7
    pad_height_visible = pad_bottom - pad_top + 1

    pad_lines = []
    
    if download_files:
        pad_lines.append("Files to download:")
        for file in download_files:
            pad_lines.append(f"- {ui.truncate_path(file, max_x - 7)}")
        pad_lines.append("")
    
    if delete_folders:
        pad_lines.append("Files marked for deletion:")
        for folder in delete_folders:
            pad_lines.append(f"- {ui.truncate_path(folder, max_x - 7)}")
    
    pad_height = max(len(pad_lines), pad_height_visible)
    pad_width = max_x - 5
    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))

    for i, line in enumerate(pad_lines):
        pad.addstr(i, 0, line)
    
    pad_pos = 0

    labels = [ui.ACCEPT_PROMPT, ui.CANCEL_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, max_y - 3, pos_x, label)
    
    while True:
        #display pad portion
        pad.refresh(pad_pos, 0, pad_top, 2, pad_bottom, max_x - 2)

        ui.draw_pad_scrollbar(
            stdscr,
            pad_pos,
            pad_height,
            pad_height_visible,
            pad_top,
            pad_bottom,
            pad_width=max_x-3
        )

        # Horizontal line under pad
        stdscr.hline(max_y - 6, 2, curses.ACS_HLINE, max_x - 4)

        #Footer note:
        if delete_folders:
            stdscr.addstr(max_y - 5, 2, "Note: You will have to confirm before any files are deleted.", curses.A_DIM)

        # Show scroll hint if required
        if pad_height > pad_height_visible:
            ui.draw_scroll_hint(stdscr, pad_bottom + 1, max_x)

        stdscr.refresh()

        key = stdscr.getch()
        # handle scrolling
        pad_pos = ui.handle_scroll(key, pad_pos, pad_height - pad_height_visible)
        # continue
        if ui.is_accept(key):
            return True
        if ui.is_cancel(key):
            return False
        # quit
        if ui.is_quit(key):
            break


def download_status_screen(stdscr, aircraft_data, download_files):
    """
    Display the download progress pad using the callback provided by the controller.
    Controller passes a callback for updating the pad.

    return file_statuses[key] = {
        "text": text, 
        "done": done, 
        "error": error, 
        "action": action
        }
    """
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)
    
    update_for = f"Update available for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 50)}"
    
    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following changes will be applied:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    stdscr.hline(max_y - 2, 2, curses.ACS_HLINE, max_x -4)


    pad_top = y + 1
    pad_bottom = max_y - 3
    pad_height_visible = pad_bottom - pad_top + 1
    pad_width = max_x - 5
    pad_y = 0

    # initialize pad
    pad = curses.newpad(pad_height_visible, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))

    file_lines = {} # maps (file, action) -> line number
    file_statuses = {} # maps (file, action) -> {"text": ..., "done": ..., "error": ..., "action": ...}
           
    def update_callback(text, file=None, action=None, done=False, error=False):
        nonlocal pad_y, pad

        if error:
            attr = curses.color_pair(ui.COLOR_PAIRS["status red"]) | curses.A_BOLD
        elif done:
            attr = curses.color_pair(ui.COLOR_PAIRS["status green"])
        elif action in ("download","extract"):
            attr = curses.A_REVERSE
        else:
            attr = curses.A_NORMAL

        # Determine line
        if file is not None and action is not None:
            key = (file, action)
            if key not in file_lines:
                line_y = len(file_lines)
                file_lines[key] = line_y
            else:
                line_y = file_lines[key]
            # Update final status
            file_statuses[key] = {"text": file, "done": done, "error": error, "action": action}
        else:
            line_y = len(file_lines)

        # Resize pad if needed
        current_pad_height = pad.getmaxyx()[0]
        if line_y >= current_pad_height:
            pad.resize(line_y + 5, pad_width)
        tab_width = max(len(status.get("action", "")) for status in file_statuses.values()) + 2

        # Clear and write line to pad
        pad.move(line_y, 0)
        line_action = file_statuses.get(key, {}).get("action", action)
        formatted_line = f"{line_action.upper():<10} {ui.truncate_path(text, max_x - 7)}"  # left-align to 10 chars
        pad.addstr(line_y, 0, f"{formatted_line:<{tab_width}}", attr)
        
        # auto scroll pad
        pad_y = max(0, line_y - pad_height_visible + 1)
        pad.refresh(pad_y, 0, pad_top, 2, pad_bottom, max_x - 2)


        # draw scrollbar when needed
        ui.draw_pad_scrollbar(
            stdscr,
            pad_y,
            len(file_lines),
            pad_height_visible,
            pad_top,
            pad_bottom,
            pad_width=max_x-3
        )
        
        ui.draw_disclaimer(stdscr)
        stdscr.refresh()
    
    # call downloads synchronously
    main.process_downloads(download_files, aircraft_data["id"], update_callback=update_callback)

    
    stdscr.refresh()
    return file_statuses
    
    
def downloads_summary_screen(stdscr, aircraft_data, file_statuses):
    """
    Display a summary of download process during the update
    Allows the user to scroll through individual results if they exceed the visible area
    """
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)
    
    update_for = f"Updated summary for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 50)}"
    
    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following changes have been applied:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    # Prepare pad data from file_statuses
    file_lines = []
    files_success = 0
    files_fail = 0
    files_partial = 0

    tab_width = max(len(status.get("action", "")) for status in file_statuses.values()) + 2
    for key, status in file_statuses.items():
        text = status.get("text", "Unknown file")
        action = status.get("action", "unknown")
        done = status.get("done", False)
        error = status.get("error", False)

        # Build display text
        display_text = f"{action.upper():<{tab_width}}{ui.truncate_path(text, max_x - 7)}"

        # Correct status color
        if error:
            attr = curses.color_pair(ui.COLOR_PAIRS["status red"])
            files_fail += 1
        elif done:
            attr = curses.color_pair(ui.COLOR_PAIRS["status green"])
            files_success += 1
        else:
            attr = curses.color_pair(ui.COLOR_PAIRS["status yellow"])
            files_partial += 1
        file_lines.append((display_text, attr))

    success_message = f"Success : {files_success}"
    failed_message = f"Failed: {files_fail}"
    partial_message = f"Partial: {files_partial}"

    ## Content under the scroll area
    stdscr.hline(max_y - 6, 2, curses.ACS_HLINE, max_x -4)

    x = 2
    message_y = max_y - 5
    if files_success:
        stdscr.addstr(message_y, x, success_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status green"]))
        x += len(success_message) + 4
    if files_fail:
        stdscr.addstr(message_y, x, failed_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status red"]))
        x += len(failed_message) + 4
    if files_partial:    
        stdscr.addstr(message_y, x, partial_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status yellow"]))

    labels = [ui.CONTINUE_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, max_y - 3, pos_x, label)

    pad_view_top = y + 1
    pad_view_bottom = max_y - 7
    pad_view_left = 2
    pad_view_right = max_x - 3
    pad_view_height = pad_view_bottom - pad_view_top + 1
    pad_height = max(pad_view_height, len(file_lines))
    pad_width = max_x - 5

    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))

    pad_pos_y = 0

    # Draw content to pad
    for i, (line_text, line_attr) in enumerate(file_lines):
        try:
            pad.addstr(i, 0, line_text, line_attr)
        except curses.error:
            pass
    
    
    #refresh pad
    pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
    stdscr.noutrefresh()
    curses.doupdate()

    # Scrolling refresh handler
    pad_pos = 0
    key = 0

    while True:
        pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
        stdscr.noutrefresh()
        curses.doupdate()
        ui.draw_pad_scrollbar(
            stdscr,
            pad_pos_y,
            pad_height,
            pad_view_height,
            pad_view_top,
            pad_view_bottom,
            pad_width = max_x - 3
        )

        if pad_height > pad_view_height:
            ui.draw_scroll_hint(stdscr, pad_view_bottom + 1, max_x)

        
        stdscr.refresh()

        key = stdscr.getch()

        # handle scrolling
        pad_pos_y = ui.handle_scroll(key, pad_pos_y, pad_height - pad_view_height)
        
        # continue
        if ui.is_continue(key):
            return True
        # quit
        if ui.is_quit(key):
            break


def confirm_deletion_screen(stdscr, delete_folders, aircraft_data):
    """
    Display delete confirmation menu.
    Returns True if confirmed, False otherwise.
    """
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    update_for = f"Update available for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 40)}"
    

    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following folders/files will be permanently deleted:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)
    pad_top = y + 1
    pad_bottom = max_y - 6
    pad_height_visible = pad_bottom - pad_top + 1

    pad_lines = []
    
    if delete_folders:
        for folder in delete_folders:
            pad_lines.append(f"- {ui.truncate_path(folder, max_x - 7)}")
    
    pad_height = max(len(pad_lines), pad_height_visible)
    pad_width = max_x - 5
    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))

    for i, line in enumerate(pad_lines):
        pad.addstr(i, 0, line)
    
    pad_y = 0

    # Horizontal line under pad
    stdscr.hline(max_y - 5, 2, curses.ACS_HLINE, max_x - 4)

    labels = [ui.DELETE_PROMPT, ui.CANCEL_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, max_y - 3, pos_x, label)

    
    while True:
        #display pad portion
        pad.refresh(pad_y, 0, pad_top, 2, pad_bottom, max_x - 2)

        ui.draw_pad_scrollbar(
            stdscr,
            pad_y,
            pad_height,
            pad_height_visible,
            pad_top,
            pad_bottom,
            pad_width=max_x-3
        )

        # Show scroll hint if required
        if pad_height > pad_height_visible:
            ui.draw_scroll_hint(stdscr, pad_bottom + 1, max_x)

        stdscr.refresh()

        key = stdscr.getch()
        # handle scrolling
        pad_y = ui.handle_scroll(key, pad_y, pad_height - pad_height_visible)
        # continue
        if ui.is_delete(key):
            return 'delete'
        if ui.is_cancel(key):
            return False
        # quit
        if ui.is_quit(key):
            break

def delete_status_screen(stdscr, delete_folders, aircraft_data):
    """
    Display the deletion progress pad using the callback provided by the controller.
    Controller passes a callback for updating the pad.

    return folder_statuses[key] = {
        "text": text, 
        "done": done, 
        "error": error, 
        "action": action,
        "folder": folder_name
        }
    """
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)
    
    update_for = f"Update available for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 40)}"
    
    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following folders/files will be permanently deleted:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    stdscr.hline(max_y - 2, 2, curses.ACS_HLINE, max_x -4)


    pad_top = y + 1
    pad_bottom = max_y - 3
    pad_height_visible = pad_bottom - pad_top + 1
    pad_width = max_x - 5
    pad_y = 0

    # initialize pad
    pad = curses.newpad(pad_height_visible, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))

    file_lines = {} # maps (file, action) -> line number
    folder_statuses = {} # maps (file, action) -> {"text": ..., "done": ..., "error": ..., "action": ...}
        
    def update_callback(text, action=None, done=False, error=False, folder=None):
        nonlocal pad_y, pad

        if error:
            attr = curses.color_pair(ui.COLOR_PAIRS["status red"]) | curses.A_BOLD
        elif done:
            attr = curses.color_pair(ui.COLOR_PAIRS["status green"])
        elif action == "delete":
            attr = curses.A_REVERSE
        else:
            attr = curses.A_NORMAL

        # Determine line
        if folder is not None and action is not None:
            key = (folder, action)
            if key not in file_lines:
                line_y = len(file_lines)
                file_lines[key] = line_y
            else:
                line_y = file_lines[key]
            # Update final status
            folder_statuses[key] = {"text": folder, "done": done, "error": error, "action": action}
        else:
            line_y = len(file_lines)
        
        # Resize pad if needed
        current_pad_height = pad.getmaxyx()[0]
        if line_y >= current_pad_height:
            pad.resize(line_y + 5, pad_width)

        # Clear and write line to pad
        pad.move(line_y, 0)
        pad.clrtoeol()
        action = folder_statuses.get(key, {}).get("action", action)
        formatted_line = f"{action.upper():<5} {ui.truncate_path(text, max_x - 7)}"  # left-align to 10 chars
        pad.addstr(line_y, 0, formatted_line, attr)
        
        # auto scroll pad
        pad_y = max(0, line_y - pad_height_visible + 1)
        pad.refresh(pad_y, 0, pad_top, 2, pad_bottom, max_x - 2)


        # draw scrollbar when needed
        if len(file_lines) > pad_height_visible:
            ui.draw_pad_scrollbar(
                stdscr,
                pad_y,
                len(file_lines),
                pad_height_visible,
                pad_top,
                pad_bottom,
                pad_width=max_x-3
            )
        
        ui.draw_disclaimer(stdscr)
        stdscr.refresh()
    
    # call downloads synchronously
    main.process_deletes(delete_folders, aircraft_data["id"], update_callback=update_callback)
    
    stdscr.refresh()
    return folder_statuses


def delete_summary_screen(stdscr, folder_statuses, aircraft_data):
    """
    Displays the results summary of our main.process_deletes() function
    """ 
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    # title and disclaimer
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)
    
    update_for = f"Updated summary for: {aircraft_data["name"]}"
    update_from = f"Current version: {aircraft_data["local_version"]}"
    update_to = f" → New version: {aircraft_data["remote_version"]}"
    update_in = f"Target folder: {ui.truncate_path(aircraft_data["target_folder"], 40)}"
    
    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following changes have been applied:", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    # Prepare pad data from folder_statuses
    folder_lines = []
    folders_success = 0
    folders_fail = 0
    folders_partial = 0

    for key, status in folder_statuses.items():
        text = status.get("text", "Unknown folder")
        action = status.get("action", "unknown")
        done = status.get("done", False)
        error = status.get("error", False)

        # Build display text
        display_text = f"{action.upper():<5} {ui.truncate_path(text, max_x - 7)}"

        # Correct status color
        if error:
            attr = curses.color_pair(ui.COLOR_PAIRS["status red"])
            folders_fail += 1
        elif done:
            attr = curses.color_pair(ui.COLOR_PAIRS["status green"])
            folders_success += 1
        else:
            attr = curses.color_pair(ui.COLOR_PAIRS["status yellow"])
            folders_partial += 1
        
        folder_lines.append((display_text, attr))

    success_message = f"Success : {folders_success}"
    failed_message = f"Failed: {folders_fail}"
    partial_message = f"Partial: {folders_partial}"

    ## Content under the scroll area
    stdscr.hline(max_y - 6, 2, curses.ACS_HLINE, max_x -4)

    x = 2
    message_y = max_y - 5
    if folders_success:
        stdscr.addstr(message_y, x, success_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status green"]))
        x += len(success_message) + 4
    if folders_fail:
        stdscr.addstr(message_y, x, failed_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status red"]))
        x += len(failed_message) + 4
    if folders_partial:    
        stdscr.addstr(message_y, x, partial_message, curses.A_BOLD | curses.color_pair(ui.COLOR_PAIRS["status yellow"]))

    labels = [ui.CONTINUE_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, max_y - 3, pos_x, label)

    # Create pad scrolling area
    pad_view_top = y + 1
    pad_view_bottom = max_y - 8
    pad_view_left = 2
    pad_view_right = max_x - 3
    pad_view_height = pad_view_bottom - pad_view_top + 1
    pad_height = max(pad_view_height, len(folder_lines) + 1)
    pad_width = max_x - 5

    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark blue"]))
    
    pad_pos_y = 0

    # Draw content to pad
    for i, (line_text, line_attr) in enumerate(folder_lines):
        try:
            pad.addstr(i, 0, line_text[:pad_width - 5], line_attr)
        except curses.error:
            pass
    
    
    #refresh pad
    pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
    stdscr.noutrefresh()
    curses.doupdate()
    

    # Scrolling refresh handler
    pad_pos = 0
    key = 0

    while True:
        pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
        stdscr.noutrefresh()
        curses.doupdate()

        ui.draw_pad_scrollbar(
            stdscr,
            pad_pos_y,
            pad_height,
            pad_view_height,
            pad_view_top,
            pad_view_bottom,
            pad_width=max_x - 3
        )
        if pad_height > pad_view_height:
            ui.draw_scroll_hint(stdscr, pad_view_bottom + 1, max_x)

        key = stdscr.getch()

        # handle scrolling
        pad_pos_y = ui.handle_scroll(key, pad_pos_y, pad_height - pad_view_height)
        # continue
        if ui.is_continue(key):
            return
        # quit
        if ui.is_quit(key):
            break