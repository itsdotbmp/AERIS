import curses
import core.main as main
from core.main import log_info, log_error
import os
import views.ui_parts as ui
from views.ui_parts import QUIT
from views.main_menu_views import _splash_screen, main_menu
from controllers.exceptions import QuitFlow
import logging
import sys


# from controllers.select_preset import _choose_preset

def _startup(stdscr):
    try:
        ui.init_ui()
        main.load_config()
    except Exception as e:
        logging.ERROR(f"INIT FAILED DO TO: {e}")
    
    _splash_screen(stdscr)
    _main_menu_flow(stdscr)

def quit_program(stdscr=None, message="Exiting program..."):
    """
    Cleanly exit the program with optional curses and console cleanup.
    """
    try:
        if stdscr:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
    except Exception:
        pass  # Safe to ignore if curses isn't active

    # Clear the console screen
    os.system('cls' if os.name == 'nt' else 'clear')

    print(message)
    sys.exit(0)

def _main_menu_flow(stdscr):
    while True:
        choice = main_menu(stdscr)
        if choice is QUIT:
            quit_program(stdscr)
        if choice.lower() == "start update" and main.current_aircraft_id:
            from controllers.update_controller import _update_flow
            _update_flow(stdscr, main.current_aircraft_id)
        elif choice.lower() == "choose preset" and main.current_aircraft_id:
            from controllers.preset_selection_controller import _preset_selection_flow
            _preset_selection_flow(stdscr)
        # elif choice.lower() == "delete":
        #     main.delete_manifest_files(main.current_aircraft_id)
        elif choice.lower() == "config":
            from controllers.config_editor import _config_editor_flow
            _config_editor_flow(stdscr)
        elif choice == QUIT or choice.lower() == "quit":
            quit_program(stdscr)

            