import curses
import core.main as main
import views.ui_parts as ui
import textwrap
import os
import time

def config_summary_view(stdscr, config):
    main.reload_config()
    stdscr.clear()
    curses.curs_set(0)    # hide cursor
    stdscr.move(0, 0)
    
    max_y, max_x = stdscr.getmaxyx()
    
    current_selected_index = 0

    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)    

    ri = [
        {"y": 4, "x": 2, "label": "Program Configuration", "hint": "", "value": "", "can_edit": False},
        {"y": 5, "x": 3, "label": "Server URL", "hint": "Enter the full URL to your server",  "value": config["program"]["server_url"], "can_edit": True, "edit_type": "text", "validator": validate_url},
        {"y": 6, "x": 3, "label": "Liveries Folder", "hint": "Enter the folder path to your liveries folder. Use '/' instead of '\\' in the path.", "value": config["environment"]["liveries_folder"], "can_edit": True, "edit_type": "text", "validator": validate_filepath},
        {"y": 7, "x": 3, "label": "Default Preset", "hint": "", "value": config["default_aircraft_id"], "can_edit": True, "edit_type": "text", "validator": None},
        {"y": 9, "x": 2, "label": "Aircraft Presets", "hint": "", "value": "Add/Edit Presets", "can_edit": True, "edit_type": "presets", "validator": None},
        {"y": 12, "x": 1, "label": "", "hint": "", "value": "Save Changes", "can_edit" : True, "edit_type": "save", "validator": None},
        {"y": 13, "x": 1, "label": "", "hint": "", "value": "Discard Changes", "can_edit" : True, "edit_type": "cancel", "validator": None}
    ]
    editable_indices = [i for i, line in enumerate(ri) if line.get("can_edit", False)]
    attrs = {
        "can_edit": curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_NORMAL,
        "selected": curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_REVERSE,
        "label": curses.A_BOLD
    }
    
    label_padding = 1

    while True:
        for i, line in enumerate(ri):
            stdscr.addstr(line["y"], line["x"], line["label"], attrs["label"])
            if line.get("value"):
                if i == editable_indices[current_selected_index]:
                    attr = attrs["selected"]
                else:
                    attr = attrs["can_edit"]
                stdscr.addstr(line["y"], line["x"] + len(line["label"]) + label_padding, line["value"], attr)
        stdscr.refresh()

        key = stdscr.getch()
        if ui.is_cancel(key):
            return
        try:
            ui.is_quit(key)
        except ui.QuitFlow:
            return

        if ui.is_accept(key):
            current_index = editable_indices[current_selected_index]
            current_field = ri[current_index]

            popup_data = {
                "title": f"Edit {current_field['label']}",
                "hint": current_field['hint'],
                "target": current_field['value'],
            }
            while True:
                edit_type = current_field.get("edit_type")
                if edit_type == "text":
                    edit_field = popup(stdscr, popup_data)
                    if edit_field is None:
                        break # cancelled
                    
                elif edit_type == "presets":
                    return "presets"
                    # preset_editor_screen(stdscr)
                    # stdscr.clear()
                    # stdscr.refresh()
                    # ui.show_title(stdscr)
                    # ui.draw_disclaimer(stdscr)
                    # break
                elif edit_type == "cancel":
                    return
                elif edit_type == "save":
                    # merge updated values from ri back into config
                    for line in ri:
                        if line.get("edit_type") in ("text", "select"):
                            label = line["label"]
                            val = line["value"]
                            if label == "Server URL":
                                config["program"]["server_url"] = val
                            elif label == "Liveries Folder":
                                config["environment"]["liveries_folder"] = val
                            elif label == "Default Preset":
                                config["default_aircraft_id"] = val
                    main.save_conf(main.config_file, config)
                    break
                validator = current_field.get("validator")
                if validator:
                    ok, msg = validator(edit_field)
                    if ok:
                        ri[current_index]['value'] = edit_field
                        break  # validation succeeded, exit retry loop
                    else:
                        popup_data["hint"] = current_field['hint'] + "\n" + msg
                else:
                    ri[current_index]['value'] = edit_field
                    break # no validator, accept value

        current_selected_index = ui.handle_scroll(key, current_selected_index, len(editable_indices) - 1)
        
      

def popup(stdscr, popup_data):
    field_label = ">_"
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()
    popup_width = min(max_x - 6, 60)

    hint_lines = textwrap.wrap(popup_data["hint"], popup_width - 4)
    n_hint_lines = len(hint_lines)
    popup_height = 8 + n_hint_lines
    
    start_y = (max_y - popup_height) // 2
    start_x = (max_x - popup_width) // 2

    popup_modal = curses.newwin(popup_height, popup_width, start_y, start_x)
    
    popup_modal.bkgd(' ', curses.color_pair(ui.COLOR_PAIRS["amberscreen"]) )
    popup_modal.box()

    title_x = 2
    popup_modal.addstr(1, title_x, popup_data["title"], curses.A_BOLD)
    
    hint_lines = textwrap.wrap(popup_data["hint"], popup_width - 4)
    for idx, line in enumerate(hint_lines):
        popup_modal.addstr(3 + idx, 2, line)

    input_y = 3 + n_hint_lines + 1

    input_start_x = 2 + len(field_label) + 1
    popup_modal.addstr(input_y, 2, field_label, curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_BOLD)
    field_len = popup_width - 5 - len(field_label)
    current_text = popup_data["target"].ljust(field_len)
    # popup_modal.addstr(input_y, 2 + len(field_label), f" {current_text}", curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_NORMAL)
    

    labels = [ui.ENTER_PROMPT, ui.ESC_PROMPT]
    positions = ui.centered_buttons_x(popup_width, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(popup_modal, popup_height - 2, pos_x, label)
    
    # popup_modal.move(input_y, 2 + len(field_label) + len(popup_data['target']))
    current_text = popup_data["target"]
    result, action = ui.text_input(popup_modal, current_text, curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_NORMAL, input_y, 2 + len(field_label), field_len)    
    curses.curs_set(0)
    popup_modal.refresh()
    if action == "confirm":
        popup_modal.clear()
        popup_modal.refresh
        del popup_modal
        stdscr.touchwin()
        stdscr.refresh()
        return result # caller can save to JSON
    elif action == "cancel":
        popup_modal.clear()
        popup_modal.refresh
        del popup_modal
        stdscr.touchwin()
        stdscr.refresh()
        return None # caller ignore changes
    
      
def preset_editor_screen(stdscr):
    main.reload_config()
    aircraft_presets_dict = main.get_aircraft_preset_list()
    stdscr.clear()
    curses.curs_set(0)    # hide cursor
    stdscr.move(0, 0)
    max_y, max_x = stdscr.getmaxyx()

    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)

    y = 3
    stdscr.addstr(y, 2, f"Preset Editor", curses.A_BOLD)
    y += 1
    stdscr.hline(y, 2, curses.ACS_HLINE, max_x - 4)

    pad_view_top = y + 1
    pad_view_bottom = max_y - 8
    pad_view_left = 2
    pad_view_right = max_x - 3
    pad_view_height = pad_view_bottom - pad_view_top + 1
    pad_height = max(pad_view_height, len(aircraft_presets_dict) + 1 )
    pad_width = max_x - 5
    _y = pad_view_bottom + 1

    pad = curses.newpad(pad_height, pad_width)
    pad.bkgd(" ", curses.color_pair(ui.COLOR_PAIRS["dark amber"]))
    
    pad_pos_y = 0
    pad_cursor_y = 0

    # Line renders below pad
    stdscr.hline(_y, 2, curses.ACS_HLINE, max_x - 4)

    labels = ["[A]dd Preset", "(E)dit preset", "(I)mport preset", ui.QUIT_PROMPT]
    positions = ui.centered_buttons_x(max_x, *labels)
    for label, pos_x in zip(labels, positions):
        ui.draw_pseudo_button(stdscr, _y + 5, pos_x, label)

    while True:
        pad.erase()
        for idx, (preset_id, preset) in enumerate(aircraft_presets_dict.items()):
            
            preset_name = preset.get("name", "")
            preset_folder = preset.get("folder", "")
            preset_url = preset.get("url", "")
            if idx == pad_cursor_y:
                display_folder = preset_folder
                display_url = preset_url
                attr = curses.A_REVERSE
                pre = "> "
            else:
                attr = curses.A_NORMAL
                pre = "  "
            preset_line = f"{pre}{preset_id:<15} '{preset_name}'"
            pad.addstr(idx, 0, f"{preset_line:<{pad_width}}", attr)
            
        stdscr.addstr(_y + 1, 2, f"Highlighted Preset Paths:", curses.A_BOLD)

        stdscr.move(_y + 2, 2)
        stdscr.clrtoeol()
        stdscr.addstr(_y + 2, 2, f"File Path: ./liveries/{display_folder}")

        stdscr.move(_y + 3, 2)
        stdscr.clrtoeol()
        stdscr.addstr(_y + 3, 2, f"Download URL: {display_url}")    
   
        scroll_height = len(aircraft_presets_dict) - 1
        
        if scroll_height >= pad_view_height:
            ui.draw_scroll_hint(stdscr, pad_view_bottom +1, max_x)
        
        ui.draw_pad_scrollbar(stdscr,
            pad_pos_y,
            pad_height,
            scroll_height,
            pad_view_top,
            pad_view_bottom,
            pad_view_right
            )

        stdscr.noutrefresh()
        pad.noutrefresh(pad_pos_y, 0, pad_view_top, pad_view_left, pad_view_bottom, pad_view_right)
        curses.doupdate()

        key = stdscr.getch()
        # Handle scrolling input
        pad_cursor_y = ui.handle_scroll(key, pad_cursor_y, scroll_height)
        # Adjust pad_pos_y to scroll if cursor goes past visible window
        if pad_cursor_y < pad_pos_y:
            pad_pos_y = pad_cursor_y  # scroll up
        elif pad_cursor_y >= pad_pos_y + pad_view_height:
            pad_pos_y = pad_cursor_y - pad_view_height + 1  # scroll down
        
        preset_ids = list(aircraft_presets_dict.keys())
        selected_id = preset_ids[pad_cursor_y]
        if ui.is_cancel(key):
            return "back", None
        try:
            ui.is_quit(key)
        except ui.QuitFlow:
            return "back", None
        if key in (ord("a"),ord("A")): # add new preset
            new_data = {"id": "", "name": "", "folder": "", "remote_subfolder": ""}
            return "add", new_data
        if key in (ord("i"),ord("I")): # import preset
            return "import", None
        if key in (ord("e"),ord("E")): # edit preset
            selected_id = list(aircraft_presets_dict.keys())[pad_cursor_y]
            preset_data = aircraft_presets_dict[selected_id]
            return "edit", (selected_id, preset_data)
        if key in (ord("d"),ord("D")): # delete preset
            selected_id = list(aircraft_presets_dict.keys())[pad_cursor_y]
            main.delete_preset(selected_id)
            main.load_config()
            curses.doupdate()
                

def preset_edit_view(stdscr, preset_data, is_new=False):
    """
    preset_data: dict with keys, id, name, folder, remote_subfolder
    is_new: bool, if True no preloaded data (new preset)
    """
    override_save = False
    def safe_strip(v):
        return v.strip() if isinstance(v, str) else v
    
    stdscr.clear()
    curses.curs_set(0)    # hide cursor
    stdscr.move(0, 0)
    
    max_y, max_x = stdscr.getmaxyx()
    min_width = 20 # minimum width for selectable values
    
    current_selected_index = 0

    ui.show_title(stdscr)
    ui.draw_disclaimer(stdscr)    

    fields = [
        {"y": 4, "x": 2, "label": "Preset ID", "hint": "Unique identifier (used for config & version file).", "value": preset_data.get("id", ""), "edit_type": "text", "validator": validate_preset_id, "can_edit": True},
        {"y": 5, "x": 2, "label": "Preset Name", "hint": "Human-readable name for this preset.", "value": preset_data.get("name", ""), "edit_type": "text", "validator": None, "can_edit": True},
        {"y": 6, "x": 2, "label": "Folder", "hint": "Local DCS aircraft folder to sync to", "value": preset_data.get("folder", ""), "edit_type": "text", "validator": validate_child_folder, "can_edit": True},
        {"y": 7, "x": 2, "label": "Remote Folder", "hint": "Relative or absolute path to server location for this preset (leave blank if not used)", "value": preset_data.get("remote_subfolder", ""), "edit_type": "text", "validator": None, "can_edit": True},
        {"y": 10, "x": 2, "label": "", "edit_type": "save", "hint": "", "value": "Save changes", "validator": None, "can_edit": True},
        {"y": 11, "x": 2, "label": "", "edit_type": "cancel", "hint": "", "value": "Discard changes", "validator": None, "can_edit": True},
        {"y": 13, "x": 2, "label": "", "edit_type": "label", "hint": "", "value": "", "validator": None, "can_edit": False}
    ]
    right_justify = max(len(line.get("label")) for line in fields)
    editable_indices = [i for i, line in enumerate(fields) if line.get("can_edit", False)]
    attrs = {
        "can_edit": curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_NORMAL,
        "selected": curses.color_pair(ui.COLOR_PAIRS["edit field"]) | curses.A_REVERSE,
        "label": curses.A_BOLD
    }
    
    label_padding = 1

    while True:
        for i, line in enumerate(fields):
            label = line.get("label", "")
            padded_label = label.rjust(right_justify) if label else ""
            stdscr.addstr(line["y"], line["x"], padded_label, attrs["label"])
            val = line.get("value")
            if line.get("can_edit", False) or (val is not None and val !=""):

                if i == editable_indices[current_selected_index]:
                    attr = attrs["selected"]
                else:
                    attr = attrs["can_edit"]
                label_offset = line["x"] + (right_justify + label_padding if label else 0)
                if line.get("can_edit", False):
                    ## Always render field even if empty, let the user know there is a field.
                    label_offset = line["x"] + (right_justify + label_padding if label else 0)
                    left_justify = (val or "").ljust(min_width)
                    stdscr.addstr(line["y"], label_offset, left_justify, attr)
            if line.get("edit_type") == "label" and val:
                max_width = max_x - line["x"] - 4
                hint_lines = textwrap.wrap(val, max_width)
                for j, hint_line in enumerate(hint_lines):
                    y_pos = line["y"] + j
                    if y_pos < max_y - 1:
                        stdscr.addstr(y_pos, line["x"], hint_line)


        stdscr.refresh()

        key = stdscr.getch()
        if ui.is_cancel(key):
            return
        try:
            ui.is_quit(key)
        except ui.QuitFlow:
            return

        if ui.is_accept(key):
            current_index = editable_indices[current_selected_index]
            current_field = fields[current_index]

            popup_data = {
                "title": f"Edit {current_field['label']}",
                "hint": current_field['hint'],
                "target": current_field['value'],
            }
            while True:
                edit_type = current_field.get("edit_type")
                if edit_type == "text":
                    edit_field = popup(stdscr, popup_data)
                    if edit_field is None:
                        break # cancelled
                    validator = current_field.get("validator")
                    if validator:
                        ok, msg = validator(edit_field)
                        if ok:
                            fields[current_index]['value'] = edit_field
                            break #validation passed
                        else:
                            # update popup hint to show the error.
                            popup_data["hint"] = current_field['hint'] + "\n" + msg
                    else:
                        fields[current_index]['value'] = edit_field
                        break
                    
                elif edit_type == "save":
                    # Build updated dict from editable fields
                    t = time.gmtime()
                    timestamp = f"{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02}T{t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}Z"
                    new_id = safe_strip(fields[0]["value"])
                    updated = {
                        "preset_version": preset_data.get("preset_version", 2),
                        "name": safe_strip(fields[1]["value"]),
                        "folder": safe_strip(fields[2]["value"]),
                        "remote_subfolder": safe_strip(fields[3]["value"]) or None,  # convert empty string to None
                        "date_created": preset_data.get("date_created", timestamp),
                        "last_edited": timestamp
                    }
                    old_id = preset_data.get("id")
                    new_rel_file = f"presets/{new_id}.set"
                    new_path = os.path.join(main.base_dir, new_rel_file)

                    ok, msg = validate_remote_versions(updated)
                    if not ok and not override_save:
                        fields[6]["value"] = (
                            "Error reaching the remote_subfolder versions.\n"
                            "Hitting save again will override this validation.\n"
                            "Use this if you are building a new preset."
                        )
                        ui.show_popup(stdscr, [
                            f"Cannot save preset:",
                            msg
                        ], msg_type="error")
                        
                        override_save = True # next save will allow it to work despite errors

                        break

                    fields[6]["value"] = "" # clear if validation passes
                    main.save_conf(new_path, {new_id: updated})

                    if old_id: # a preset was there, not a new one.
                        if new_id != old_id:
                            main.delete_preset(old_id)
                            main.import_preset(new_id, new_path)

                            if main.config.get("default_aircraft_id") == old_id:
                                main.config["default_aircraft_id"] = new_id
                                main.save_conf(main.config_file, main.config)
                    else:
                        main.import_preset(new_id, new_path)
                    
                    main.reload_config()

                    # Redraw and return    
                    stdscr.clear()
                    stdscr.refresh()
                    ui.show_title(stdscr)
                    ui.draw_disclaimer(stdscr)
                    return True
                elif edit_type == "cancel":
                    stdscr.clear()
                    stdscr.refresh()
                    ui.show_title(stdscr)
                    ui.draw_disclaimer(stdscr)
                    return False
                validator = current_field.get("validator")
                if validator:
                    ok, msg = validator(edit_field)
                    if ok:
                        fields[current_index]['value'] = edit_field
                        break  # validation succeeded, exit retry loop
                    else:
                        popup_data["hint"] = current_field['hint'] + "\n" + msg
                else:
                    fields[current_index]['value'] = edit_field
                    break

        current_selected_index = ui.handle_scroll(key, current_selected_index, len(editable_indices) - 1)


def import_presets_view(stdscr):
    # Discover presets in /presets folder
    # filter out ones already in config["aircrafts"]
    # Display selection list
    # allow marking items for import with I, I again to unmark
    # press A to accept and import all selected
    # Escape or Q to quit.

    presets_dir = None
    pass

def validate_url(url: str) -> bool:
    """
    Validates url on syntax scheme and connection
    """
    import re
    import urllib
    timeout = 5
    url = url.strip()
    pattern = re.compile(
        r'^(https?://)' #must start with http or https
        r'([A-Za-z0-9-]+\.)+[A-Za-z]{2,}' # domain
        r'(:\d+)?'  # optional port
        r'(/.*)?$'  # optional path
    )    
    if not pattern.match(url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            code = response.getcode()
            if 200 <= code < 400:
                return True, f"Server reachable (HTTP {code})"
            else:
                return False, f"Server responded with HTTP {code}"
    except urllib.error.URLError as e:
        return False, f"Connection failed: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}"
   
  
def validate_preset_id(preset):
    # Check for alphanumeric + underscore only.
    # Ensure it doesn’t collide with an existing preset if is_new=True.
    return True, ""

def validate_filepath(path):
    # Check it’s not empty and likely points to a valid path pattern.
    if not path or not path.strip():
        return False, "Path cannot be empty."
    
    # normalize slashes
    norm_path = os.path.normpath(path).replace("\\", "/")

    # Check absolute
    if not os.path.isabs(norm_path):
        return False, 'Path must be absolute.'
    
    # Lowercase for comparison
    norm_lower = norm_path.lower()
    if not norm_lower.endswith("/liveries"):
        return False, f'Path must end with "{norm_path}" folder.'

    return True, ""


def validate_child_folder(path):
    if not path or path.strip() == "":
        return False, "Folder cannot be empty."
    if ".." in path or path.startswith(("/", "\\")):
        return False, "Invalid folder path."
    return True, ""


def validate_remote_versions(updated: dict):
    """
    Validate that our remote subfolder points to a valid version file
    allows override
    returns True, "" if success,
    returns False, message if failure
    can save again if failed to overwrite.
    """
    preset_id = updated.get("id")
    remote_subfolder = updated.get("remote_subfolder", "") or ""
    server_url = main.server_url
    
    # build an absolute URL from the remote subfolder
    if remote_subfolder.startswith(("http://", "https://")):
        base_url = remote_subfolder.rstrip("/") + "/"
    else:
        base_url = f"{server_url}/{remote_subfolder.lstrip('/').rstrip('/')}/"

    # construct version file url
    version_file_name = main.config["program"]["version_filename"]
    full_version_file = f"{preset_id}_{version_file_name}"
    full_url = f"{base_url}{full_version_file}"

    try:
        if main.get_remote_version(full_url):
            return True, ""
        else:
            msg = f"Cannot find version file at {full_url}"
            return False, msg
    except Exception as e:
        msg =  f"Faled to access remote versions file: {type(e).__name__}: {e}"
        return False, msg