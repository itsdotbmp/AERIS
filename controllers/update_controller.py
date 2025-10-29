import curses
import core.main as main
from core.main import log_info, log_error
import os
import views.ui_parts as ui
from views.update_views import check_updates_screen, download_status_screen, downloads_summary_screen, confirm_deletion_screen, delete_status_screen, delete_summary_screen
from controllers.exceptions import QuitFlow

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


def if_updates(download_files, delete_folders):
    update_available = bool(download_files or delete_folders)

    info_message = """
    No updates are available for this aircraft preset.
    Your local installation is already up-to-date.
    """
    if not update_available:
    # split into lines
        info_lines = [line.strip() for line in info_message.strip().splitlines() if line.strip()]
        # inject as a synthetic "file statuses" 
        download_files = [line for line in info_lines]

        return download_files, False
    return download_files, True


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

    download_files, is_updates = if_updates(download_files, delete_folders)

    try:
        # remove folders that are already missing from delete_folders
        delete_folders = main.filter_existing_folders(delete_folders, aircraft_id)  
        user_choice = check_updates_screen(stdscr, download_files, delete_folders, aircraft_data)
        
        if user_choice != True:
            log_info("User canceled update process")
            return
        
        if download_files and is_updates:
            download_statuses = download_status_screen(stdscr, aircraft_data, download_files)
            if download_statuses:
                downloads_summary_screen(stdscr, aircraft_data, download_statuses)
        
        if delete_folders:
            delete_confirmation = confirm_deletion_screen(stdscr, delete_folders, aircraft_data)
            if delete_confirmation == "delete":
                folder_statuses = delete_status_screen(stdscr, delete_folders, aircraft_data)
                if folder_statuses:
                    delete_summary_screen(stdscr, folder_statuses, aircraft_data)
        main.clean_up_operation(True, True, False)
        log_info("Update flow complete, returning to main screen", tag="UPDATE_FLOW")
    except QuitFlow:
        log_info("User quit the update flow")
        return
    return