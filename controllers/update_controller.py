import curses
import main
import os
import views.ui_parts as ui
from views.update_views import check_updates_screen, show_download_status, show_delete_screen

def update_controller(stdscr, aircraft_id):
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
        return
    
    except ConnectionError as e:
        ui.show_popup(stdscr, [
            "Network Error: Could not reach update server.",
            f"Details: {e}",
            f"Server URL: {main.config.get('server_url', 'unknown')}"
        ], msg_type="error")
        return
    
    except Exception as e:
        ui.show_popup(stdscr, [
            "Unexpected error occured while fetching updates.",
            f"Exception: {e}",
            f"Log file: {main.config['logging'].get('log_file_name', 'unknown')}"
        ], msg_type="error")
        return
    
    # handle explicit error state
    if status == "error":
        ui.show_popup(stdscr, [
            "Update check failed.",
            f"Log file: {main.config['logging'].get('log_file_name', 'unknown')}",
            f"Details: {data}"
        ], msg_type="error")
        return
    
    #Data should contain (download_files, delete_folders)
    if not isinstance(data, tuple) or len(data) != 2:
        ui.show_popup(stdscr, [
            "Invalid response format from update check.",
            f"Recieved: {data}"
        ], msg_type="error")
        return
    
    download_files, delete_folders = data
    aircraft_data = main.get_aircraft_info(aircraft_id)
    aircraft_name = aircraft_data["name"]
    current_version = aircraft_data["local_version"]
    remote_version = aircraft_data["remote_version"]
    target_folder = aircraft_data["target_folder"]

    #Show check updates screen and get user choice
    selection = check_updates_screen(stdscr, download_files, delete_folders, aircraft_name, current_version, remote_version, target_folder)

    if selection == "Apply update":
        _handle_update_flow(stdscr, aircraft_id, download_files, delete_folders)
    elif selection == "Cancel update":
        return

def _handle_update_flow(stdscr, aircraft_id, download_files, delete_folders):
    """
    Manages the flow after user selects "apply update"
    """
    #Step 1: Download
    download_status = None
    if download_files:
        from views.update_views import show_download_status
        download_status = show_download_status(stdscr, download_files, aircraft_id)

    #Step 2: Delete (only if downloads completed)
    if download_status == "downloads_complete" and delete_folders:
        from views.update_views import show_delete_screen, show_delete_status
        confirmed = show_delete_screen(stdscr, delete_folders, aircraft_id)
        if confirmed:
            show_delete_status(stdscr, delete_folders, aircraft_id)
        else:
            return
    
    #Step 3: clean up
    main.clean_up_operation(False, False, False)