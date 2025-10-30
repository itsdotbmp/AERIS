import curses
import core.main as main
from controllers.exceptions import QuitFlow

"""
Generic parts and pieces of UI that can be reused
"""

def init_ui():
    """
    inits any UI required info that is shared across the program
    """

    curses.start_color()
    curses.use_default_colors()
    
    global COLOR_PAIRS
    COLOR_PAIRS = { name: i for i, name in enumerate([
        "scrollbar",
        "status green",
        "status red",
        "status yellow",
        "bluescreen",
        "dark blue"
    ], start=17)}
    dark_blue = 20

    curses.init_pair(COLOR_PAIRS["scrollbar"], curses.COLOR_WHITE, 8)
    curses.init_pair(COLOR_PAIRS["status green"], curses.COLOR_GREEN, dark_blue)  # done text
    curses.init_pair(COLOR_PAIRS["status red"], curses.COLOR_RED, dark_blue) # error text
    curses.init_pair(COLOR_PAIRS["status yellow"], curses.COLOR_YELLOW, dark_blue) # yellow warning text
    curses.init_pair(COLOR_PAIRS["bluescreen"], curses.COLOR_WHITE, dark_blue) # white on blue
    curses.init_pair(COLOR_PAIRS["dark blue"], curses.COLOR_WHITE, dark_blue) # White on darker blue

def show_title(stdscr, title=None):
    if not title:
        title = main.title
    # Add a bold title
    stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(1, 2, title)
    stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)

def new_menu_vertical(stdscr, menu_y, menu_x, options, current_index):
    """
    Renders a simple vertical menu list.
    Handles drawing only - does not capture input or manage scrolling.
    """
    # Visual marker config
    selected_prefix = "> "
    normal_prefix = "  "

    # preventative
    if not options:
        return
    
    num_options = len(options)

    # safe drawing size
    max_y, max_x = stdscr.getmaxyx()
    current_longest = min(max(len(opt) for opt in options) + len(selected_prefix), max_x - menu_x - 1)
    previous_longest = getattr(menu_vertical, "_last_width", 0)
    menu_vertical._last_width = max(previous_longest,current_longest)
    draw_width = menu_vertical._last_width

    # Track menu lines
    for idx, option in enumerate(options):
        y = menu_y + idx
        is_selected = (idx == current_index)
        prefix = selected_prefix if is_selected else normal_prefix
        attr = curses.A_REVERSE if is_selected else curses.A_NORMAL
        text = f"{prefix}{option}"

        line = text.ljust(draw_width)[:draw_width]
        stdscr.addstr(y, menu_x, line, attr)


def menu_vertical(stdscr, menu_y, menu_x, options, current_index):
    """
    Reusable vertical selection menu, takes input for location.
    """
    current_index = current_index
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

def draw_pseudo_button(stdscr, btn_y, btn_x, btn_text):
    # Draw psuedo button
    stdscr.addstr(btn_y, btn_x, btn_text, curses.A_BOLD | curses.A_REVERSE)

def draw_scroll_hint(stdscr, pos_y, max_x):
    # Draw Scroll hint
    scroll_hint = "Use ↑ ↓ to scroll"
    scroll_hint_width = (max_x //2) - (len(scroll_hint) // 2)
    stdscr.addstr(pos_y, scroll_hint_width, scroll_hint, curses.A_DIM)

def draw_pad_scrollbar(stdscr, pad_y, pad_height, pad_height_visible, pad_top, pad_bottom, pad_width):
    """
    Draws a vertical scrollbar for pad with up/down arrows and a scroll block

    stdscr              : the curses window
    pad_y               : current top line of the pad displayed
    pad_height          : total number of lines in the pad
    pad_height_visible  : number of lines visible on screen
    pad_top             : top y position of pad on screen
    pad_bottom          : bottom y position of pad on screen
    pad_width           : x position to draw the scrollbar (usually right edge of pad)
    """
    attr_track = curses.A_REVERSE | curses.A_DIM
    if pad_height <= pad_height_visible:
        attr_track = curses.A_DIM | curses.A_REVERSE
    
    # Draw scroll indicators
    if pad_y > 0:
        stdscr.addstr(pad_top, pad_width, "↑", attr_track)  # up indicator
    else:
        stdscr.addstr(pad_top, pad_width, "╥", attr_track)  # clear if no scroll above

    if pad_y + pad_height_visible < pad_height:
        stdscr.addstr(pad_bottom, pad_width, "↓", attr_track)  # down indicator
    else:
        stdscr.addstr(pad_bottom, pad_width, "╨", attr_track)  # clear if no scroll below

    # Scroll bar track and block
    scroll_top = pad_top
    scroll_bottom = pad_bottom
    scroll_bar_height = scroll_bottom - scroll_top + 1
    # fraction of the scroll position relative to the total scrollable height
    scroll_fraction = pad_y / max(1, pad_height - pad_height_visible)

    #calculate which row the scrollblock should occupy
    block_row = scroll_top + int(scroll_fraction * (scroll_bar_height - 1))
    block_row = min(max(block_row, pad_top), pad_bottom)

    # draw track
    for i in range(scroll_top + 1, scroll_bottom):
        if pad_height > pad_height_visible:
            stdscr.addstr(i, pad_width, "│", attr_track)
        else:
            stdscr.addstr(i, pad_width, "║", attr_track)
    
    # draw block
    if pad_height > pad_height_visible:
        stdscr.addstr(block_row, pad_width, "▓", curses.color_pair(COLOR_PAIRS["scrollbar"]) | curses.A_REVERSE)


def truncate_path(path, max_len):
    """Truncate a file path from the start if it exceeds max_len."""
    if len(path) <= max_len:
        return path
    
    prefix = "..."
    max(4, max_len - len(prefix))
    sep = "\\"
    parts = path.split(sep)
    # Build result from the end backwards
    truncated = parts[-1]  # start with filename
    for part in reversed(parts[:-1]):
        candidate = part + sep + truncated
        if len(candidate) + 3 > max_len:
            break
        truncated = candidate

    return prefix + truncated

### BUTTON CONSTANTS ###

# Standard labels
CONTINUE_PROMPT = "[Press SPACE to continue]"
ACCEPT_PROMPT = "[A]ccept"
CANCEL_PROMPT = "[C]ancel"
QUIT_PROMPT = "[Q]uit"
DELETE_PROMPT = "[D]elete"

# Standard spacing between buttons
BUTTON_SPACING = 8

def centered_buttons_x(screen_width, *labels, spacing=BUTTON_SPACING):
    """
    Returns a list of x positions for each button label to be rendered centered
    as a group, with the given spacing between them.
    
    Usage:
    labels = [ui.ACCEPT_PROMPT, ui.CANCEL_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, max_y - 3, pos_x, label)
    """
    total_width = sum(len(label) for label in labels) + spacing * (len(labels) - 1)
    start_x = (screen_width - total_width) // 2

    positions = []
    x = start_x
    for label in labels:
        positions.append(x)
        x += len(label) + spacing
    return positions

def is_continue(key):
    """
    Usage:
    key = stdscr.getch()
    if ui.is_continue(key):
        return 
    """
    return key in (ord(" "), ord("\n"), curses.KEY_ENTER)

def is_quit(key):
    """
    Usage:
    key = stdscr.getch()
    if ui.is_quit(key):
        return
    """
    if key in (ord("q"),ord("Q"), 27):
        raise QuitFlow()

class _QuitSentinel:
    pass

QUIT = _QuitSentinel()

def is_accept(key):
    """
    Usage:
    key = stdscr.getch()
    if ui.is_accept(key):
        return True
    """
    return key in (ord("a"),ord("A"))

def is_cancel(key):
    """
    Usage:
    key = stdscr.getch()
    if ui.is_cancel(key):
        return False
    """
    return key in (ord("c"),ord("C"))

def is_delete(key):
    """
    Usage:
    key = stdscr.getch()
    if ui.is_delete(key):
        return 'delete'
    """
    return key in (ord("d"),ord("D"))

def handle_scroll(key, pos, max_pos):
    """
    Usage:
    key = stdscr.getch()
    pad_pos = ui.handle_scroll(key, pos, max_pos)
    """
    if key in (curses.KEY_DOWN, ord("j"), ord("J")) and pos < max_pos:
        return min(pos + 1, max_pos)
    elif key in (curses.KEY_UP, ord("k"), ord("K")) and pos > 0:
        return max(pos - 1, 0)
    return pos