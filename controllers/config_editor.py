import core.main as main
from core.main import log_info, log_error
import os
from views.config_editor import config_summary_view, preset_editor_screen, preset_edit_view

def _config_editor_flow(stdscr):
    state = "config"

    while True:
        if state == "config":
            result = config_summary_view(stdscr, main.config)
            if result == "presets":
                state = "presets"
            else:
                break # exit flow
        elif state == "presets":
            result, payload = preset_editor_screen(stdscr)
            if result == "add":
                new_data = payload
                if payload:
                    new_preset = preset_edit_view(stdscr, new_data, is_new=True)
                    if new_preset:
                        main.reload_config()
                state = "presets" # get back to preset editing state
            elif result == "edit":
                if payload:
                    selected_id, preset_data = payload
                    updated = preset_edit_view(stdscr, preset_data.copy(), is_new=False)
                    if updated:
                        main.reload_config()
                state = "presets"
            elif result == "import":
                state = "presets"
            elif result == "back":
                state = "config"
            else:
                raise ValueError(f"Unexpected result {result}")
                # break

