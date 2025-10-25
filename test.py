import curses
import traceback
import main
from controllers.update_controller import update_controller

# You can change this to any valid aircraft identifier
TEST_AIRCRAFT_ID = "f-4e-45mc"

def main_screen(stdscr):
    curses.curs_set(0)
    try:
        main.load_config()
    except Exception as e:
        stdscr.addstr(2, 2, f"Failed to load config: {e}")
        stdscr.addstr(4, 2, "Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    stdscr.clear()
    stdscr.addstr(0, 2, "=== Update Controller (REAL DATA TEST) ===", curses.A_BOLD)
    stdscr.addstr(2, 2, f"Testing aircraft ID: {TEST_AIRCRAFT_ID}")
    stdscr.addstr(4, 2, "Press any key to start...", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()

    try:
        update_controller(stdscr, TEST_AIRCRAFT_ID)
    except Exception:
        stdscr.clear()
        stdscr.addstr(2, 2, "Unhandled Exception in test:", curses.A_BOLD)
        for i, line in enumerate(traceback.format_exc().splitlines(), start=4):
            if i >= curses.LINES - 1:
                break
            stdscr.addstr(i, 2, line[:curses.COLS - 4])
        stdscr.refresh()
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main_screen)
