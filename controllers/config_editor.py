import core.main as main
from core.main import log_info, log_error
import os
from views.config_editor import config_summary_view, preset_editor_screen, preset_edit_view, import_presets_view, _first_time_config_system

def _config_editor_flow(stdscr, start_state="config", payload=None):
    """
    start_state: "config" | "presets" | "import"
    payload: optional data for the state (e.g., preset to edit)
    """
    state = start_state

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
                candidates = get_candidate_presets()
                result, import_presets = import_presets_view(stdscr, candidates)
                if result == "quit":
                    state = "presets"
                elif result == "import":
                    for preset_id, preset_path in import_presets.items():
                        main.import_preset(preset_id, preset_path)

                    state = "presets"
            elif result == "back":
                state = "config"
            else:
                raise ValueError(f"Unexpected result {result}")
                # break
            payload = None


def get_candidate_presets():
    """
    Scan presets folder and return a list of candidate presets not already in main.config["aircrafts"]

    Returns: a list of dicts ordered each: {
    "id" : "<preset_id>",
    "name": "<human name>",
    "path": "<abs path to file>",
    }
    """
    aircrafts_dict = main.config["aircrafts"]
    presets_dir = main.preset_dir
    candidates = []
    log_info(f"DEBUG: contents of presets folder: {os.listdir(main.preset_dir)}")
    for filename in os.listdir(presets_dir):
        # skip hidden files
        if filename.startswith("."):
            continue

        # build a full path
        path = os.path.join(presets_dir, filename)

        # skip directories (we only want files)
        if not os.path.isfile(path):
            continue

        # get id from filename, strip the extension
        preset_id, ext = os.path.splitext(filename)

        # Skip if already in aircrafts (we don't want to import an already existing preset!)
        existing_ids = {k.lower() for k in aircrafts_dict}
        if preset_id.lower() in existing_ids:
            continue
        
        # Try loading the file
        try:
            data = main.load_conf(path) # can handle yaml, json, *.set files
        except Exception as e:
            log_error(f"Failed to load preset '{filename}': {e}")
            continue # We continue and fail silently to log
        
        if len(data) == 1 and isinstance(next(iter(data.values())), dict):
            inner_id, inner_data = next(iter(data.items()))
            data = inner_data
            if inner_id.lower() != preset_id.lower():
                log_error(f"Preset ID mismatch between filename and root key: {filename}")
                continue

        # Validate structure
        if not isinstance(data, dict):
            log_error(f"Invalid preset format: {filename}")
            continue 
        if not data.get("name"):
            log_error(f"Preset is missing a name, or has a blank name: {filename}")
            continue

        # Valid candidate!
        candidates.append({
            "id": preset_id,
            "name": data["name"],
            "path": path
        })
    
    return candidates
    

def _first_time_flow(stdscr):
    """
    Run the first-time configuration flow.
    Prompts user for required data and sets up initial presets.
    """
    if main.first_time == True:
        next_state = _first_time_config_system(stdscr)
        if next_state == "presets":
            _config_editor_flow(stdscr, start_state="presets")
        main.first_time = False
        if "first_time" in main.config:
            del main.config["first_time"]
            main.save_conf(main.config_file, main.config)
            main.reload_config()
    
    return "main_menu"  # return control to main menu
