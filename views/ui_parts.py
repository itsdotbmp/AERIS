import curses
import main

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
        "status red"
    ], start=17)}

    curses.init_pair(COLOR_PAIRS["scrollbar"], curses.COLOR_WHITE, 8)
    curses.init_pair(COLOR_PAIRS["status green"], curses.COLOR_GREEN, curses.COLOR_BLACK)  # done text
    curses.init_pair(COLOR_PAIRS["status red"], curses.COLOR_RED, curses.COLOR_BLACK) # error text

def show_title(stdscr, title=None):
    if not title:
        title = main.title
    # Add a bold title
    stdscr.attron(curses.A_UNDERLINE | curses.A_BOLD)
    stdscr.addstr(1, 2, title)
    stdscr.attroff(curses.A_UNDERLINE | curses.A_BOLD)


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
    stdscr.addstr(btn_y, btn_x, btn_text, curses.A_REVERSE)

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
    if pad_height <= pad_height_visible:
        return
    
    # Draw scroll indicators
    if pad_y > 0:
        stdscr.addstr(pad_top, pad_width, "↑", curses.A_REVERSE | curses.A_DIM)  # up indicator
    else:
        stdscr.addstr(pad_top, pad_width, "│", curses.A_REVERSE | curses.A_DIM)  # clear if no scroll above

    if pad_y + pad_height_visible < pad_height:
        stdscr.addstr(pad_bottom, pad_width, "↓", curses.A_REVERSE | curses.A_DIM)  # down indicator
    else:
        stdscr.addstr(pad_bottom, pad_width, "│", curses.A_REVERSE | curses.A_DIM)  # clear if no scroll below

    # Scroll bar track and block
    scroll_top = pad_top
    scroll_bottom = pad_bottom
    scroll_bar_height = scroll_bottom - scroll_top + 1
    scroll_fraction = pad_y / max(1, pad_height - pad_height_visible)
    block_row = scroll_top + int(scroll_fraction * (scroll_bar_height - 1))
    block_row = min(max(block_row, pad_top), pad_bottom)

    # draw track
    for i in range(scroll_top + 1, scroll_bottom):
        stdscr.addstr(i, pad_width, "│", curses.A_REVERSE | curses.A_DIM)
    
    # draw block
    stdscr.addstr(block_row, pad_width, "░", curses.color_pair(COLOR_PAIRS["scrollbar"]))