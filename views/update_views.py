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
    update_in = f"Target folder: {aircraft_data["target_folder"]}"
    

    y = 4
    stdscr.addstr(y, 2, update_for, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_from, curses.A_DIM)
    stdscr.addstr(y, 2 + len(update_from), update_to, curses.A_BOLD)
    y += 1
    stdscr.addstr(y, 2, update_in, curses.A_DIM)
    y += 2
    stdscr.addstr(y, 2, "The following changes will be applied", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)
    pad_top = y + 1
    pad_bottom = max_y - 7
    pad_height_visible = pad_bottom - pad_top + 1

    pad_lines = []
    
    if download_files:
        pad_lines.append("Files to download:")
        for file in download_files:
            pad_lines.append(f"- {file}")
        pad_lines.append("")
    
    if delete_folders:
        pad_lines.append("Files marked for deletion:")
        for folder in delete_folders:
            pad_lines.append(f"- {folder}")

    for i in range(len(pad_lines), len(pad_lines) + 50):
        pad_lines.append(f"Line {i}")
    
    pad_height = max(len(pad_lines), pad_height_visible)
    pad_width = max_x - 5
    pad = curses.newpad(pad_height, pad_width)

    for i, line in enumerate(pad_lines):
        pad.addstr(i, 0, line)
    
    pad_y = 0
    
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

        # Horizontal line under pad
        stdscr.hline(max_y - 6, 2, curses.ACS_HLINE, max_x - 4)

        #Footer note:
        if delete_folders:
            stdscr.addstr(max_y - 5, 2, "Note: You will have a chance to confirm before any files are deleted.", curses.A_DIM)

        options = ["(A)pply update", "(C)ancel update"]
        options_total_width = len(options[0]) + 5 + len(options[1])
        options_start_x = (max_x - options_total_width) // 2
        options_x = options_start_x, options_start_x + len(options[0]) + 5
        
        # Draw pseudo buttons at bottom
        ui.draw_pseudo_button(stdscr, max_y - 3, options_x[0], options[0])
        ui.draw_pseudo_button(stdscr, max_y - 3, options_x[1], options[1])

        # Show scroll hint if required
        if pad_height > pad_height_visible:
            ui.draw_scroll_hint(stdscr, pad_bottom + 1, max_x)

        stdscr.refresh()

        key = stdscr.getch()
        if key in [curses.KEY_UP, ord('k')] and pad_y > 0:
            pad_y -= 1
        elif key in [curses.KEY_DOWN, ord('j')] and pad_y < pad_height - pad_height_visible:
            pad_y += 1
        elif key in [ord('a'), ord('\n'), curses.KEY_ENTER]:
            return "Apply update"
        elif key in [ord('c'), 27]:  # ESC
            return "Cancel update"


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
    update_in = f"Target folder: {aircraft_data["target_folder"]}"
    
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
    file_lines = {} # maps (file, action) -> line number
    file_statuses = {} # maps (file, action) -> {"text": ..., "done": ..., "error": ..., "action": ...}
    
    # --- Add filler lines before callback starts ---
    filler_count = 50
    max_text_width = pad_width - 5

    for i in range(filler_count):
        if i >= pad.getmaxyx()[0] - 1:
            pad.resize(i + 5, pad_width)

        file = f"filler_file_{i+1}.zip"
        action = "download"
        text = f"Filler entry {i+1}: Simulating {file}"

        error = (i % 7 == 0)
        done = not error

        if error:
            attr = curses.color_pair(ui.COLOR_PAIRS["status red"]) | curses.A_BOLD
        else:
            attr = curses.color_pair(ui.COLOR_PAIRS["status green"])

        line_y = i
        file_lines[(file, action)] = line_y
        file_statuses[(file, action)] = {"text": text, "done": done, "error": error, "action": action}

        pad.addstr(line_y, 0, text[:max_text_width], attr)

    # After writing filler, scroll to bottom so new updates append visibly
    pad_y = max(0, len(file_lines) - pad_height_visible)
    pad.refresh(pad_y, 0, pad_top, 2, pad_bottom, max_x - 2)
        
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
            file_statuses[key] = {"text": text, "done": done, "error": error, "action": action}
        else:
            line_y = line_offset + len(file_lines)

        # Resize pad if needed
        current_pad_height = pad.getmaxyx()[0]
        if line_y >= current_pad_height:
            pad.resize(line_y + 5, pad_width)

        # Clear and write line to pad
        pad.move(line_y, 0)
        pad.clrtoeol()
        pad.addstr(line_y, 0, text, attr)
        
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
    update_in = f"Target folder: {aircraft_data["target_folder"]}"
    
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

    for key, status in file_statuses.items():
        text = status.get("text", "Unknown file")
        action = status.get("action", "unknown")
        done = status.get("done", False)
        error = status.get("error", False)

        # Build display text
        display_text = f"{action.upper():<10} {text}"

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

    continue_message = "[press any key  to continue]"
    x = max_x // 2 - (len(continue_message) // 2)
    stdscr.addstr(max_y - 3, x, continue_message, curses.A_BOLD | curses.A_REVERSE)

    # Create pad scrolling area
    pad_height = len(file_lines)
    pad_height_visible = max_y - (y + 8) # Leave room for the footer
    pad_y = y + 1
    pad_top = 0
    pad_bottom = min(pad_height_visible, pad_height)
    pad_width = max_x - 5
    pad = curses.newpad(pad_height, pad_width)

    # Draw content to pad
    for i, (line_text, line_attr) in enumerate(file_lines):
        try:
            pad.addstr(i, 0, line_text[:pad_width - 5], line_attr)
        except curses.error:
            pass
    
    
    #refresh pad
    pad.refresh(pad_top, 0, pad_y, 2, pad_y + pad_height_visible, max_x - 2)

    # Scrolling refresh handler
    pad_pos = 0
    key = 0

    while True:
        # Refresh pad based on current scroll offset
        pad.refresh(
            pad_pos, 0,
            pad_y, 2,
            pad_y + pad_height_visible,
            max_x - 3
        )

        # Draw scrollbar only if current content exceeds visible area
        if pad_height > pad_height_visible:
            ui.draw_pad_scrollbar(
                stdscr,
                pad_pos,
                pad_height,
                pad_height_visible,
                pad_y,
                pad_y + pad_height_visible,
                pad_width = max_x - 3
            )
            #show scroll hint at the bottom
            ui.draw_scroll_hint(stdscr, pad_y + pad_height_visible + 1, max_x)
        
        stdscr.refresh()

        key = stdscr.getch()

        # handle scrolling
        if key in (curses.KEY_DOWN, ord("j")):
            if pad_pos < pad_height - pad_height_visible:
                pad_pos += 1
        elif key in (curses.KEY_UP, ord("k")):
            if pad_pos > 0:
                pad_pos -= 1
        elif key in (ord("q"), 27, ord("\n")): # q, Esc, or Enter == exit
            break
        elif key not in (curses.KEY_UP, ord("k"), curses.KEY_DOWN, ord("j"), ord("q"), 27, ord("\n")):
            return


def show_delete_screen(stdscr, delete_folders):
    """
    Display delete confirmation menu.
    Returns True if confirmed, False otherwise.
    """
    pass
