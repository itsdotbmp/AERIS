import core.main as main
from core.main import log_info, log_error
import views.ui_parts as ui
from views.ui_parts import QUIT
from views.preset_selection_views import preset_selection_screen
from controllers.exceptions import QuitFlow


def _preset_selection_flow(stdscr):
    main.reload_config()
    aircraft_preset_list = main.get_aircraft_preset_list()
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
    


