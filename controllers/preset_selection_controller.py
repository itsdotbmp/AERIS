import curses
import main
from main import log_info, log_error
import os
import views.ui_parts as ui
from views.ui_parts import QUIT
from views.preset_selection_views import preset_selection_screen
from controllers.exceptions import QuitFlow

def _preset_selection_flow(stdscr):
    aircraft_preset_list = build_aircraft_preset_list()
    # Assume aircraft_presets_list already exists
    try: # lets us capture the quitflow to exit the screen
        log_info(f"Selecting Aircraft Preset, Current Preset '{main.current_aircraft_id}'")
        response, selected_id = preset_selection_screen(stdscr, aircraft_preset_list)
    except QuitFlow:
        # we just want to return to the main menu
        log_info(f"User quit the selection process, Current Preset ID is '{main.current_aircraft_id}'")
        return
    stdscr.clear()
    stdscr.refresh()


    if response:
        main.set_current_aircraft(selected_id)
        log_info(f"User Selected Preset ID '{selected_id}'")
        return
    else:
        log_info(f"User quit the selection process, Current Preset ID is '{main.current_aircraft_id}'")
        return
    

def build_aircraft_preset_list():
    """
    Gets and builds a list of aircraft presets
    """
    aircrafts = main.config.get("aircrafts", {})

    presets = []
    for aircraft_id, data in aircrafts.items():
        presets.append({
            "id": aircraft_id,
            "name": data.get("name", aircraft_id),
            "folder": data.get("folder", ""),
            "url": main.get_remote_livery_url(aircraft_id)
        })
    
    return presets
