import curses
import core.main as main
import views.ui_parts as ui
import textwrap

def config_summary_view(stdscr, config):
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
        {"y": 6, "x": 3, "label": "Liveries Folder", "hint": "Enter the folder path to your liveries folder. Use '/' instead of '\\' in the path.", "value": config["environment"]["liveries_folder"], "can_edit": True, "edit_type": "text", "validator": None},
        {"y": 7, "x": 3, "label": "Default Preset", "hint": "", "value": config["default_aircraft_id"], "can_edit": True, "edit_type": "selection", "validator": validate_url},
        {"y": 9, "x": 2, "label": "Aircraft Presets", "hint": "", "value": "Add/Edit Presets", "can_edit": True, "edit_type": "presets", "validator": None}
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
            if line["value"] != "" or not None:
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
                edit_field = popup(stdscr, popup_data)
                if edit_field is None:
                    break # cancelled
            
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
        popup_modal.erase()
        popup_modal.refresh()
        del popup_modal
        return result # caller can save to JSON
    elif action == "cancel":
        popup_modal.erase()
        popup_modal.refresh()
        del popup_modal
        return None # caller ignore changes
    
    
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