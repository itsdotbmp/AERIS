import curses
import main
from main import log_info, log_error
import os
import views.ui_parts as ui
from views.ui_parts import QUIT
from views.main_menu_views import _splash_screen, main_menu
from controllers.exceptions import QuitFlow
import logging
import sys

from controllers.update_controller import _update_flow
# from controllers.select_preset import _choose_preset

def _startup(stdscr):
    try:
        ui.init_ui()
        main.load_config()
    except Exception as e:
        logging.ERROR(f"INIT FAILED DO TO: {e}")
    
    _splash_screen(stdscr)
    _main_menu_flow(stdscr)


def _main_menu_flow(stdscr):
    while True:
        choice = main_menu(stdscr)
        if choice.lower() == "update":
            _update_flow(stdscr, main.current_aircraft_id)
        #elif choice.lower() == "choose preset":
           # _choose_preset(stdscr)
        elif choice == QUIT or choice.lower() == "quit":
            sys.exit()