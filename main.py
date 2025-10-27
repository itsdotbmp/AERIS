from collections import defaultdict
import json
import os
import sys
import urllib.request
import shutil
import logging
from logging.handlers import RotatingFileHandler
import inspect
import time
import zipfile
import atexit
from urllib.error import HTTPError, URLError, ContentTooShortError
import traceback

software_version = "0.0.1"
current_aircraft_id = None 
title = "86th vFW Livery Tool"
## FOR DOCUMENTATION: Program *must* be in a writable folder to function, so not program files.

def generate_json_boilerplate():
    with open(config_file, "w", encoding="utf-8") as file:
        json.dump({
            "config_version": 1,
            "program": {
                "server_url": None,
                "version_filename": "version.txt",
                "server_version_file": "server_version.txt"
            },
            "logging": {
                "log_file_name": "liveries.log",
                "max_bytes": 500000,
                "backup_count": 5
            },
            "environment": {
                "liveries_folder": None
            },
            "default_aircraft_id": None,
            "aircrafts": {}
        }, file, indent=4)

# Handle getting the local root folder we're in depending if running the script, or the exe
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
    
def load_json():
    #load config JSON
    global config
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

def custom_logging_namer(default_name):
    """
    Transforms default rotated names (base.log.1) into desired format (liveries1.log)
    using config_log_file.
    """
    # default_name may look like '/path/to/base.log.1'
    base_name, ext = os.path.splitext(log_file_name)
    # split from the right-most '.' to get rotation number
    parts = default_name.rsplit('.', 2)
    if len(parts) == 3 and parts[2].isdigit():
        number = parts[2]
        return f"{base_name}{number}{ext}"
    return default_name

try:
    base_dir =  get_base_dir()
    config_file = os.path.join(base_dir, "config.json")

    # Make sure we have a config file
    if not os.path.exists(config_file):
        #Create a boilerplate config
        generate_json_boilerplate()
    
    load_json()

    ## LOGGING CONFIG ##
    log_file_name = config["logging"].get("log_file_name", "liveries.log")
    max_bytes = config["logging"].get("max_bytes", 500000)
    backup_count = config["logging"].get("backup_count", 5)
    # Log file path using our base_dir
    log_file_path = os.path.join(base_dir, log_file_name)

    ## LOGGING SETUP ##
    logging_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    logging_handler.namer = custom_logging_namer
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        handlers=[logging_handler]
    )
    
except Exception as e:
    # if anything up to this point fails, crash - we can't continue
    raise RuntimeError(f"Critical startup failure: {e}")

def load_config():
    """
    Loads config.json, updates the global variables, and handles missing fields.
    Returns true if config is valid, and False if critical fields are missing.
    """
    
    global version_filename
    global liveries_folder
    global server_url
    global server_version_file
    global aircrafts
    global default_aircraft_id
    global current_aircraft_id

    load_json()
    
    #Critial required fields
    try:
        version_filename = config["program"].get("version_filename") or "version.txt"
        log_info(f"version_filename='{version_filename}'",tag="SET CONFIG")
        server_url = config["program"].get("server_url")
        if not server_url:
            log_error("server_url missing in config")
            return False
        server_url = server_url.rstrip("/")
        log_info(f"server_url='{server_url}'",tag="SET CONFIG")
        server_version_file = os.path.join(base_dir, config["program"].get("server_version_file") or "server_version.txt")
        log_info(f"server_version_file='{server_version_file}'",tag="SET CONFIG")

        liveries_folder = config["environment"].get("liveries_folder")
        if not liveries_folder:
            log_error("liveries_folder missing; user must confirm in config editor")
            return False
        log_info(f"liveries_folder = '{liveries_folder}'",tag="SET CONFIG")
        
        #Aircrafts
        aircrafts = config.get("aircrafts", {})
        default_aircraft_id = config.get("default_aircraft_id") or (next(iter(aircrafts)) if aircrafts else None)
        if not default_aircraft_id:
            log_error("No default aircraft ID found in config")
            return False
        log_info(f"default_aircraft_id='{default_aircraft_id}'",tag="SET CONFIG")
        if current_aircraft_id is None or current_aircraft_id not in aircrafts:
            current_aircraft_id = default_aircraft_id
            log_info(f"current_aircraft_id was none or not in aircrafts, set to '{default_aircraft_id}'",tag="SET CONFIG")
        return True
    
    except Exception as e:
        log_error(f"Critical config error: {e}")
        return False


    

def log_info(msg, tag=None, include_args=False):
    # Automatically puts the caller function name, optionally including its args
    frame = inspect.stack()[1]
    func_name = frame.function
    
    if include_args:
        #Get arg names and values for caller
        args, _, _, values = inspect.getargvalues(frame.frame)
        arg_str = ", ".join(f"{a}={values[a]!r}" for a in args)
        context = f"{func_name}({arg_str})"
    else:
        context = f"{func_name}()"    
    if tag:
        logging.info(f"INFO {tag} | {context} | {msg}")
    else:
        logging.info(f"INFO | {context} | {msg}")

def log_error(msg, include_args=False):
    frame = inspect.stack()[1]
    func_name = frame.function

    if include_args:
        #Get arg names and values for caller
        args, _, _, values = inspect.getargvalues(frame.frame)
        arg_str = ", ".join(f"{a}={values[a]!r}" for a in args)
        logging.error(f"ERROR | {func_name}({arg_str}) | {msg}")
    else:
        logging.error(f"ERROR | {func_name}() | {msg}")

def log_warn(msg, tag=None, include_args=False):
    frame = inspect.stack()[1]
    func_name = frame.function

    if include_args:
        #Get arg names and values for caller
        args, _, _, values = inspect.getargvalues(frame.frame)
        arg_str = ", ".join(f"{a}={values[a]!r}" for a in args)
        context = f"{func_name}({arg_str})"
    else:
        context = f"{func_name}()"    
    if tag:
        logging.info(f"WARNING {tag} | {context} | {msg}")
    else:
        logging.info(f"WARNING | {context} | {msg}")

    
# Helper to always get the correct aircraft_id, 
# allows for batch operations in the future, or checking all aircraft for updates etc.
def get_local_version_file(aircraft_id):
    try:
        return os.path.join(base_dir, f"{aircraft_id}_{version_filename}")
    except Exception as e:
        log_error(f"Failed to construct local version file path: {e}", include_args=True)
        return None


# Grab the URL to the remote location a livery exists
def get_remote_livery_url(aircraft_id):
    remote_subfolder = aircrafts[aircraft_id].get("remote_subfolder",None)
    if remote_subfolder:
        if remote_subfolder.startswith(("http://", "https://")):
            # already a full URL, treat as absolute, ensure a trailing slash
            return remote_subfolder.rstrip("/") + "/"
        else:
            # return relative path, appended to server_url
            return f"{server_url}/{remote_subfolder.lstrip("/").rstrip("/")}/"
    else:
        # No subfolder given, return root server_url
        return f"{server_url}/"
    

# Same as local version, grabs the correct URL and file name for each aircraft type
def get_server_version_file(aircraft_id):
    return f"{get_remote_livery_url(aircraft_id)}{aircraft_id}_{version_filename}"


def parse_release(release_str):
    # Converts 'release-5.1.2' to (5, 1, 2)
    release_str = release_str.lower()
    if not release_str.startswith("release-"):
        raise ValueError(f"Invalid release format: {release_str}")
    version_part = release_str[len("release-"):]
    parts = version_part.split(".")
    # Converts to integers, missing part defaults to 0
    return tuple(int(p) for p in parts + ["0"]*(3-len(parts)))


def is_newer(local, remote):
    if local == None:
        return True # treat remote as newer if missing a local file or no release found.
    # Returns true if remote > local
    return parse_release(remote) > parse_release(local)

assert parse_release("release-5.0.9") == (5, 0, 9)
assert parse_release("release-5.1") == (5, 1, 0)
assert is_newer("release-5.0.9", "release-5.1.0")  # True
assert not is_newer("release-5.1.1", "release-5.1.0")  # False


def parse_server_file(filename, local_version, server_version):
    short_filename = os.path.basename(filename)
    log_info(f"Running...", include_args=True)
    download_files = set() #set avoids dupes
    delete_folders = set()
    releases_to_process = [] # how many releases between local and current

    if local_version:
        local_tuple = parse_release(local_version)
    else:
        local_tuple = None

    server_tuple = parse_release(server_version)

    # Step 1: Read all the lines, build blocks for each release
    # looks like a json list, release then all of the lines in it after
    with open(filename, "r", encoding="utf-8") as f: 
        lines = [line.strip() for line in f if line.strip()]

    current_release = None
    release_blocks = defaultdict(list) # release string -> list of action lines, this is the JSON looking part
    for line in lines:
        line_lower = line.lower()
        if line_lower.startswith("release-"):
            current_release = line
            log_info(f"Found {current_release}", tag="PARSE_REMOTE_FILE", include_args=True)
            continue
        if current_release:
            release_blocks[current_release].append(line) # if not a release title, then its a line in the release, add it.

    # Step 2: Check which releases are newer then the local, up to the servers current version
    for release in release_blocks.keys():
        release_tuple = parse_release(release)
        if local_tuple is None or (local_tuple < release_tuple <= server_tuple):
            releases_to_process.append(release) # builds a list of releases we have to go through to collect files
            log_info(f"{release} found in release_blocks, and added to list of releases", include_args=True)
        

    # Step 3: Reverse the list, so we don't download deleted files, but do download them if they are re-added
    releases_to_process.reverse()

    # Step 4: Process releases in order
    for release in releases_to_process:
        for line in release_blocks[release]:
            if ";" not in line:
                continue
            action, file_or_folder = line.split(";",2)[:2]
            action = action.lower().strip()
            file_or_folder = file_or_folder.strip()
            if action in ["new", "update"]:
                download_files.add(file_or_folder)
                delete_folders.discard(file_or_folder)   # no longer scheduled for deletion
                log_info(f"Found '{action}' '{file_or_folder}'")
            elif action == "delete":
                delete_folders.add(file_or_folder)
                download_files.discard(file_or_folder) # remove previously added files
                log_info(f"Found '{action}' '{file_or_folder}'")

    return list (download_files), list(delete_folders)


def get_latest_release(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith("release-"):
                    return line # first-release is newest
        return None
    except Exception as e:
        log_error(f"Failed to read local release file '{filename}': {e}")
        return None


def get_remote_version(url):
    try:
        with urllib.request.urlopen(url) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if line.lower().startswith("release-"):
                    return line
    except Exception as e:
        log_error(f"Failed to get remote version: {e}", include_args=True)
        return None


def get_remote_updates(aircraft_id):
    local_newest = get_latest_release(get_local_version_file(aircraft_id))
    server_newest = get_remote_version(get_server_version_file(aircraft_id))
    if server_newest is None:
        log_error(f"get_remote_updates({aircraft_id}):  Cannot fetch server version", include_args=True)
        return "error", "remote_fetch_failed, server_newest is None"

    if not is_newer(local_newest, server_newest):
        log_info(f"UP_TO_DATE | local version {local_newest} matches {server_newest}. Up to Date!", include_args=True)
        return "up_to_date", ([],[])

    # New Update is available
    log_info(f"Local Version: {local_newest}", include_args=True)
    log_info(f"Server Version: {server_newest}", include_args=True)
    
    # download the full server version file for processing since its newer then local
    try:
        urllib.request.urlretrieve(get_server_version_file(aircraft_id), server_version_file)
        msg = f"Downloaded server version file to: '{server_version_file}'"
        #print(msg)
        log_info(f"{msg}", include_args=True)

        # parse server file and collect updates
        download_files, delete_folders = parse_server_file(server_version_file, local_newest, server_newest)

        #print("\nFiles to download: ", download_files)
        #print("\nFolders to delete: ", delete_folders)

        log_info(f"found the following files to download: {download_files}", include_args=True)
        log_info(f"found the following files or folders to remove: {delete_folders}", include_args=True)
        
        return "ok", (download_files, delete_folders)

    except Exception as e:
         # Capture full traceback
        tb = traceback.format_exc()
        msg = f"Failed to download or parse server file: '{e}' | {tb}"
        log_error(f"{msg}", include_args=True)
        return "error", msg


def clean_up_operation(update = True, delete = True, echo = True):
    #print("\n")
    if update:
        try:
            shutil.copyfile(server_version_file, get_local_version_file(current_aircraft_id))
            log_info(f"ran and replaced '{get_local_version_file(current_aircraft_id)}' with '{server_version_file}'", include_args=True)
        except FileNotFoundError:
            #print(f"File not found: {server_version_file}")
            log_error(f"File not found to copy: '{server_version_file}'", include_args=True)
        if echo:
            print(f"Updated '{get_local_version_file(current_aircraft_id)}' with the version from the server.")
    if delete:
        try:
            safe_delete(server_version_file)
            logging.info(f"clean_up_operation({update},{delete},{echo}):  ran and deleted the local copy of '{server_version_file}'")
            if echo:
                print(f"Deleted {server_version_file} to clean up operations\n")
        except FileNotFoundError:
            log_error(f"File not found to delete: '{server_version_file}'", include_args=True)
    if not delete and not update:
        log_error(f"did not delete or update while update={update} and delete={delete}", include_args=True)
        if echo:
            print(f"{os.path.basename(get_local_version_file(current_aircraft_id))} not updated, {os.path.basename(server_version_file)} file not deleted\n")

def process_downloads(download_files, aircraft_id, update_callback=None):
    # Build our destination folder to use the current_aircraft id for its subfolder
    destination_folder = os.path.normpath(os.path.join(liveries_folder, aircrafts[aircraft_id]["folder"]))
    os.makedirs(destination_folder, exist_ok=True)

    for file in download_files:
        # build a correct URL using the aircraft ID for remote url
        file_url = get_remote_livery_url(aircraft_id) + file
        destination_file = os.path.normpath(os.path.join(destination_folder, file))
        log_info(f"Processing Download for {file}", tag="DOWNLOADING_START")
        log_info(f"File URL:  {file_url}")
        log_info(f"Destination Folder: {destination_file},")
        start_time = time.time()

        try:
            # Download the file
            if update_callback:
                update_callback(f"{file}", file=file, action="download", done=False)
            urllib.request.urlretrieve(file_url, destination_file)
            elapsed = time.time() - start_time
            if update_callback:
                update_callback(f"{file} - Success", file=file, action="download", done=True)
            log_info(f"Download Completed of '{file}' in {elapsed:.2f} seconds", tag="DOWNLOAD_END")

            # Unpack the file
            if zipfile.is_zipfile(destination_file):
                try:
                    with zipfile.ZipFile(destination_file, 'r') as zip_ref:
                        zip_contents = zip_ref.namelist()

                        # Top-level analysis for zip structure
                        # root_files: entries are in the zip root no folders
                        root_files = {
                            e for e in zip_contents
                            if '/' not in e and not e.endswith('/')
                        }
                        # top_level_folders: first path segment for entries containing '/'
                        top_level_folders = {
                            entry.split('/')[0] for entry in zip_contents if '/' in entry
                        }
                        # Decide upack strategy:
                        # 1. Multi-livery pack: Strictly multiple top level folders and no files at root
                        # 2. Single root folder: exactly one top-level folder and no top-level files
                        # 3. Otherwise: create a safe folder named after the zip file
                        is_multi_livery = (
                            len(top_level_folders) > 1
                            and len(root_files) == 0
                            and "description.lua" not in {rf.lower() for rf in root_files}
                        ) # If root files was not zero, then it could just be a common shared folder without a livery.
                        
                        is_single_root = (
                            len(top_level_folders) == 1
                            and len(root_files) == 0
                            and not list(top_level_folders)[0].startswith('__MACOSX')
                        )

                        
                        if is_single_root:
                            root_folder_name = list(top_level_folders)[0]
                            extract_path = destination_folder
                            log_info(f"Unpacking '{file}' (root folder '{root_folder_name}') into '{extract_path}'", tag="EXTRACTING_START")
                            
                            if update_callback:
                                update_callback(f"'{file}'", file=file, action="extract", done=False)
                            
                            safe_unzip(zip_ref, extract_path)

                            if update_callback:
                                update_callback(f"'{file}' - Success", file=file, action="extract", done=True)
                        elif is_multi_livery:
                            # multiple seperate livery folders at top level, and no files at root:
                            # extract these folders directly into destination folder with no extra enclosing folder
                            log_warn(
                                f"Multiple top-level folders detected in '{file}': {top_level_folders}. "
                                f"Extracting each top-level folder directly into destination.",
                                tag="EXTRACTING_MULTI"
                            )

                            if update_callback:
                                update_callback(f"'{file}'", file=file, action="extract", done=False)

                            # Extract only members that start with each top-level folder
                            for folder in sorted(top_level_folders):
                                members = [name for name in zip_contents if name.startswith(folder + '/')]
                                for member in members:
                                    # extract each member path into destination_folder (prevserves subpath)
                                    safe_unzip(zip_ref, member, destination_folder)
                            if update_callback:
                                update_callback(f"'{file}' - Success", file=file, action="extract", done=True)

                        else:
                            #fallback, mixed content or files at root, create a wrapping folder
                            safe_folder_name = os.path.splitext(file)[0]
                            extract_path = os.path.normpath(os.path.join(destination_folder, safe_folder_name))
                            os.makedirs(extract_path, exist_ok=True)
                            
                            log_info(f"Unpacking '{file}' into safe folder '{extract_path}'", tag="EXTRACTING_START")
                            if update_callback:
                                update_callback(f"'{file}'", file=file, action="extract", done=False)
                            safe_unzip(zip_ref, extract_path)
                            if update_callback:
                                update_callback(f"'{file}' - Success", file=file, action="extract", done=True)
                        
                    elapsed = time.time() - start_time
                    log_info(f"Unpack Complete for '{file}' in {elapsed:.2f} seconds", tag="EXTRACTING_END")
                    
                    # Only remove zip if successfully extracted
                    try:
                        safe_delete(destination_file)
                        log_info(f"Removed ZIP file '{file}' after extraction", tag="DELETING_FILE")
                    except Exception as e_rm:
                        # delete errors shouldn't crash the program
                        log_error(f"Failed to remove zip '{destination_file}': {e_rm}")

                except (zipfile.BadZipFile, OSError, PermissionError) as e:
                    # Extraction failed: Keep the zip and log, debugging, mark partial finished
                    log_error(f"Error extracting '{file}': {e}")
                    if update_callback:
                        # Mark as only partial finished
                        update_callback(f"'{file}' - Extract failed - {e}", file=file, action="extract", done=False, error=False)         
                    # Doon't remove destination_file; proceed to next file
                    continue
            else:
                # not a zip file, nothing to extract.
                log_warn(f"Downloaded file '{file}' is not a zip archive; left in place", tag="NON_ZIP")
                if update_callback:
                    update_callback(F"'{file}' is not a zip file", file=file, action="extract", done=False)
                # If we want to remove non zip files uncomment next:
                # safe_delete(destination_file)

        except HTTPError as e:
            log_error(f"HTTP error {e.code} {e.reason} while downloading '{file}'")
            if update_callback:
                update_callback(f"'{file}' - {e.code} {e.reason}", file=file, action="download", error=True)
        except URLError as e:
            log_error(f"Network error while downloading '{file}': {e}")
            if update_callback:
                update_callback(f"'{file}' - Network Error - {e}", file=file, action="download", error=True)
        except ContentTooShortError as e:
            log_error(f"Download incomplete for '{file}': {e}")
            if update_callback:
                update_callback(f"'{file}' - Download Incomplete - {e}", file=file, action="download", error=True)
        except (OSError, PermissionError) as e:
            log_error(f"Local file error for '{file}': {e}")
            if update_callback:
                update_callback(f"'{file}' - local file issue {e}", file=file, action="download", error=True)

def process_deletes(delete_folders, aircraft_id, update_callback=None):
    working_folder = os.path.join(liveries_folder, aircrafts[aircraft_id]["folder"])

    for folder in delete_folders:
        folder_name = os.path.splitext(folder)[0]
        target_folder = os.path.normpath(os.path.join(working_folder, folder_name))
        if os.path.isdir(target_folder):
            try:
                if update_callback:
                    update_callback(f"'{folder_name}'",action="delete", folder=folder_name, done=False)
                safe_delete(target_folder, True)
                if update_callback:
                    update_callback(f"'{folder_name}'",action="delete", folder=folder_name, done=True)
                log_info(f"Deleting {target_folder}", tag="DELETING_FOLDER")
            except Exception as e:
                log_error(f"Failed to delete '{target_folder}': {e}")
                if update_callback:
                    update_callback(f"'{folder_name}': {e}", folder=folder_name, error=True)
        else: 
            log_info(f"Folder does not exist: '{target_folder}'")
            if update_callback:
                update_callback(f"Folder does not exist: '{folder_name}'", folder=folder_name, action="MISSING", done=False)

def get_aircraft_info(aircraft_id):
    """
    Collect and return relevant data for a given aircraft_id.
    Returns a dict with keys:
        - id
        - name
        - folder
        - target_folder
        - local_version
        - remote_version
    """
    aircraft = aircrafts.get(aircraft_id)
    if not aircraft:
        log_error(f"{aircraft_id} not found in aircrafts list.", include_args=True)
        raise ValueError(f"Aircraft ID '{aircraft_id}' not found in aircrafts list.")
    
    name = aircraft.get("name", "Unknown Aircraft Config")
    folder = aircraft.get("folder")
    target_folder = os.path.normpath(os.path.join(liveries_folder, folder))

    try:
        local_version = get_latest_release(get_local_version_file(aircraft_id))
    except Exception as e:
        log_error(f"Unable to get latest local release version: {e}", include_args=True)
        local_version = "Unknown"
    
    try:
        remote_version = get_remote_version(get_server_version_file(aircraft_id))
    except Exception as e:
        log_error(f"Unable to get latest remote release version: {e}", include_args=True)
        remote_version = "Unknown"

    return {
        "id": aircraft_id,
        "name": name,
        "folder": folder,
        "target_folder": target_folder,
        "local_version": local_version,
        "remote_version": remote_version
    }

def get_working_folder(aircraft_id):
    return os.path.normpath(os.path.join(liveries_folder, aircrafts[aircraft_id]["folder"]))

def set_current_aircraft(new_id):
    global current_aircraft_id
    current_aircraft_id = new_id

def startup(show_warning=False):
    logging.info(f"PROGRAM_START | version={software_version}")
    if show_warning:
        print("Please run the program using interface.py, not main.py")

def shutdown():
    logging.info(f"PROGRAM_END | version={software_version}")

def safe_unzip(zip_ref, *args):
    """
    Unified unzip handler for both extractall() and extract(member, dest) use cases.
    Usage:
      safe_unzip(extract_path, all=True)  -> calls extractall
      safe_unzip(member, destination_folder) -> calls extract
    - Calls safe_delete(source) only if the source is a valid zip.
    """
    if zip_ref is None:
        raise ValueError("safe_unzip() requires a ZipFile object as the first argument")
    if len(args) == 1:
        zip_ref.extractall(args[0])
    elif len(args) == 2:
        member, dest = args
        zip_ref.extract(member, dest)
    else:
        raise ValueError(f"safe_unzip() expects 2 or 3 positional arguments including zip_ref, got {1 + len(args)} (zip_ref + {len(args)} additional)")


def safe_delete(path: str, force_delete: bool = False):
    """
    Unified delete function.
    - If 'path' is a file, deletes it.
    - If 'path' is a folder:
        • If force_delete=True, deletes entire folder tree (like shutil.rmtree).
        • If force_delete=False, deletes only if empty.
    Raises same exceptions as os.remove/shutil.rmtree.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)

    elif os.path.isdir(path):
        if force_delete:
            shutil.rmtree(path)
        else:
            #only delete empty folders
            if not os.listdir(path):
                os.rmdir(path)
            else:
                # folder not empty; ignore deletion (intentional no operation)
                pass
    else:
        raise OSError(f"Unsupported file type: {path}")

            
    

### ATOMIZED UNZIP AND TRACKING OF FILES // PSEUDO CODE
# def install_package(zip_path, dest_folder, manifest, package_id):
#     files = extract_with_manifest(zip_path, dest_folder)
#     manifest["installed_packages"][package_id] = {
#         "installed_at": datetime.now().isoformat(),
#         "files": files
#     }
#     save_manifest(manifest)

# Register shutdown to always run at exit
atexit.register(shutdown)

if __name__ == "__main__":
    startup(show_warning=True)
    logging.critical(f"CRITICAL | Program launched from main.py, please run the program from interface.py")

## TO DO :
## ADD basic config editing ability, setting users saved games folder/liveries folder
## updating URL to the correct server URL for the versions file
## adding aircraft configs
## editing aircraft configs
## Changing the base folder where local files for the app are stored ?maybe?
## 
## Further work:
## Readme, other documentation on how to use the client
## Documentation on how to set up the server side and make releases
## Build py exe file environment and test