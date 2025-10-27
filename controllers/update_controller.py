import curses
import main
from main import log_info, log_error
import os
import views.ui_parts as ui
from views.update_views import check_updates_screen, download_status_screen, downloads_summary_screen, show_delete_screen

def check_for_updates(stdscr, aircraft_id):
    """
    Handles the update check flow
    Fetches remote updates and passes results to the view for processing
    """
    try:
        status, data = main.get_remote_updates(aircraft_id)
    
    except FileNotFoundError as e:
        ui.show_popup(stdscr, [
            "Error: Configuration or local data missing.",
            f"Details: {e}",
            f"Check config path: {getattr(main, 'config_path', 'unknown')}"
        ], msg_type="error")
        return None
    
    except ConnectionError as e:
        ui.show_popup(stdscr, [
            "Network Error: Could not reach update server.",
            f"Details: {e}",
            f"Server URL: {main.config.get('server_url', 'unknown')}"
        ], msg_type="error")
        return None
    
    except Exception as e:
        ui.show_popup(stdscr, [
            "Unexpected error occured while fetching updates.",
            f"Exception: {e}",
            f"Log file: {main.config['logging'].get('log_file_name', 'unknown')}"
        ], msg_type="error")
        return None
    
    # handle explicit error state
    if status == "error":
        ui.show_popup(stdscr, [
            "Update check failed.",
            f"Log file: {main.config['logging'].get('log_file_name', 'unknown')}",
            f"Details: {data}"
        ], msg_type="error")
        return None
    
    #Data should contain (download_files, delete_folders)
    if not isinstance(data, tuple) or len(data) != 2:
        ui.show_popup(stdscr, [
            "Invalid response format from update check.",
            f"Recieved: {data}"
        ], msg_type="error")
        log_error(f"Invalid response format from update check. Recieved: {data}")
        return None
    
    download_files, delete_folders = data

    return {
        "download_files": download_files,
        "delete_folders": delete_folders
    }


def _update_flow(stdscr, aircraft_id):
    """
    Controller for orchestrating the update flow synchronously.
    Handles user choice, directs to download view, and returns control to main screen.
    """
    aircraft_data = main.get_aircraft_info(aircraft_id)
    update_info = check_for_updates(stdscr, aircraft_id)
    if not update_info:
        # either an error occured or user canceled
        return
    
    download_files = update_info["download_files"]
    delete_folders = update_info["delete_folders"]

    user_choice = check_updates_screen(stdscr, download_files, delete_folders, aircraft_data)
    
    if user_choice.lower() != "apply update":
        log_info("User canceled update process")
        return
    
    if download_files:
        download_statuses = download_status_screen(stdscr, aircraft_data, download_files)
        # return file_statuses[key] = {
        # "text": text, 
        # "done": done, 
        # "error": error, 
        # "action": action
        # }
    if download_files and download_statuses:
        downloads_summary_screen(stdscr, aircraft_data, download_statuses)
    
    # TODO, show results screen
    
    
    # Step 5: (Future) handle deletions if needed
    # if delete_folders:
    #     handle_folder_deletions(stdscr, delete_folders)

    # Step Final: Clean up
    main.clean_up_operation(False, False, False)
    log_info("Update flow complete, returning to main screen", tag="UPDATE_FLOW")
    return