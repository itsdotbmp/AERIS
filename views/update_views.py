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
    pad_bottom = max_y - 8
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
        stdscr.hline(max_y - 7, 2, curses.ACS_HLINE, max_x - 4)

        #Footer note:
        if delete_folders:
            stdscr.addstr(max_y - 6, 2, "Note: You will have a chance to confirm before any files are deleted.", curses.A_DIM)

        options = ["(A)pply update", "(C)ancel update"]
        options_total_width = len(options[0]) + 5 + len(options[1])
        options_start_x = (max_x - options_total_width) // 2
        options_x = options_start_x, options_start_x + len(options[0]) + 5
        
        # Draw pseudo buttons at bottom
        ui.draw_pseudo_button(stdscr, max_y - 4, options_x[0], options[0])
        ui.draw_pseudo_button(stdscr, max_y - 4, options_x[1], options[1])

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
    max_text_width = pad_width - 4

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

        pad.addstr(line_y, 2, text[:max_text_width], attr)

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
        pad.move(line_y, 2)
        pad.clrtoeol()
        pad.addstr(line_y, 2, text, attr)
        
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

    stdscr.hline(max_y - 2, 2, curses.ACS_HLINE, max_x -4)
    stdscr.addstr(max_y - 3, 2, "All files finished downloading, press any key  to continue",
                curses.color_pair(ui.COLOR_PAIRS["status green"]) | curses.A_BOLD)
    stdscr.refresh()


    # wait for user confirm
    stdscr.getch()
    return file_statuses
    

def show_delete_screen(stdscr, delete_folders):
    """
    Display delete confirmation menu.
    Returns True if confirmed, False otherwise.
    """
    pass
