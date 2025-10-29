import curses
import core.main as main
import views.ui_parts as ui
from views.ui_parts import QUIT
import time


def _splash_screen(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    stdscr.bkgd(' ', curses.color_pair(ui.COLOR_PAIRS["bluescreen"]))
    copyright = f"© 2025 dotbmp"
    copy_offset_x = max_x - len(copyright) - 2
    copy_offset_y = max_y - 3
    stdscr.addstr(copy_offset_y, copy_offset_x, copyright, curses.A_BOLD)
    ui.draw_disclaimer(stdscr)

    stdscr.refresh()
    time.sleep(.25)

def main_menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    current_index = 0
    selections = ["Choose Preset", "Start Update", "Quit"]
    while True:
        ui.new_menu_vertical(stdscr, 4, 2, selections, current_index)
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