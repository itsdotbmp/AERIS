import curses
from controllers.main_menu_controller import _startup

def main():
    curses.wrapper(_startup)

if __name__ == "__main__":
    main()