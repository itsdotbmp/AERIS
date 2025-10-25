import curses
import views.ui_parts as ui

def check_updates_screen(stdscr, download_files, delete_folders, aircraft_name, current_version, remote_version, target_folder):
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

    update_for = f"Update available for: {aircraft_name}"
    update_from = f"Current version: {current_version}"
    update_to = f" → New version: {remote_version}"
    update_in = f"Target folder: {target_folder}"
    

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
        #if pad_height > pad_height_visible:
        if True:
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
            return None


def show_download_status(stdscr, files_to_download, update_callback):
    """
    Display the download progress pad using the callback provided by the controller.
    Controller passes a callback for updating the pad.
    """
    pass



def show_delete_screen(stdscr, delete_folders):
    """
    Display delete confirmation menu.
    Returns True if confirmed, False otherwise.
    """
    pass
