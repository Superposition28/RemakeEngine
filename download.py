"""
This module provides an interactive tool for managing and executing downloads
and other operations for various games based on JSON configurations.
"""

import questionary
from pathlib import Path
import re
import json
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import zipfile
import tarfile
import shutil

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Utils')))
from printer import print, Colours, print_error, print_verbose, print_debug, printc


# --- Define your custom style (as per your example) ---
custom_style_fancy = questionary.Style([
    ('question', 'white'),
    ('answer', '#4688f1'),
    ('pointer', 'green'),
    ('highlighted', 'blue'),
    ('selected', '#cc241d'),
    ('separator', 'white'),
    ('instruction', ''),
    ('text', 'darkmagenta'),
    ('disabled', '#858585 italic')
])

# Configuration
GAMES_REGISTRY_DIR_NAME = "RemakeRegistry"
GAMES_COLLECTION_DIR_NAME = "Games"
DOWNLOADS_FILENAME = "tools.json" # This file now defines various operations, including downloads
ENGINE_CONFIG_FILENAME = "project.json" # Assuming this holds global config like engine paths

def discover_games(games_collection_path: Path, ops_file_name: str) -> dict:
    """
    Discovers games by looking for ops_file_name in subdirectories.
    The game name is read from the top-level key within the JSON file.
    Returns a dictionary: {game_name_from_json: {'ops_file': Path, 'game_root': Path}}
    """
    games = {}
    if not games_collection_path.is_dir():
        print(Colours.YELLOW, f"Info: Games collection directory not found or is not a directory: {games_collection_path}")
        return games

    print_verbose(f"Scanning directory: {games_collection_path}")
    try:
        for game_dir_path in games_collection_path.iterdir():
            print_debug(f"Checking item: {game_dir_path}")
            if game_dir_path.is_dir(): # Ensure it's a directory
                potential_ops_file = game_dir_path / ops_file_name
                print_debug(f"Checking for ops file: {potential_ops_file}")
                if potential_ops_file.is_file():
                    try:
                        with open(potential_ops_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if isinstance(data, dict) and len(data) == 1:
                            game_name_from_json = list(data.keys())[0] # Get the single top-level key

                            # Validate that the value associated with the game name is a list (of operations)
                            if isinstance(data.get(game_name_from_json), list):
                                if game_name_from_json in games:
                                    # Handle duplicate game names
                                    print(Colours.YELLOW, f"Warning: Duplicate game name '{game_name_from_json}' defined in '{potential_ops_file}'. Overwriting previous entry from {games[game_name_from_json]['ops_file']}.")

                                games[game_name_from_json] = {
                                    "ops_file": potential_ops_file.resolve(), # Store absolute path
                                    "game_root": game_dir_path.resolve() # Store absolute path to game's root
                                }
                                print_verbose(f"Found game '{game_name_from_json}' at '{game_dir_path.resolve()}'")
                            else:
                                print_error(f"Error: Operations data for game '{game_name_from_json}' in '{potential_ops_file}' is not a list. Found: {type(data.get(game_name_from_json))}")
                        else:
                            print_error(f"Error: Operations file '{potential_ops_file}' should be a JSON object with a single top-level key (the game name), and its value should be a list of operations.")
                    except json.JSONDecodeError:
                        print_error(f"Error: Could not decode JSON from '{potential_ops_file}'. Ensure it's valid JSON.")
                    except Exception as e:
                        print_error(f"Error processing file '{potential_ops_file}': {e}")
    except Exception as e:
        print_error(f"Error during directory iteration: {e}")
    return games

def load_downloads(file_path: Path, game_name_key: str) -> list:
    """Loads operations list from a JSON file, using game_name_key to access it."""
    if not file_path.is_file():
        print_error(f"Error: Operations file '{file_path}' not found or is not a file.")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            operations_list = data.get(game_name_key)
            if isinstance(operations_list, list):
                return operations_list
            else:
                print_error(f"Error: Did not find a list of operations under key '{game_name_key}' in '{file_path}'. Found: {type(operations_list)}")
                return []
        else:
            # This case should ideally be caught by discover_games structure validation
            print_error(f"Error: Operations file '{file_path}' is not structured as a dictionary with game name as key.")
            return []
    except json.JSONDecodeError:
        print_error(f"Error: Could not decode JSON from '{file_path}'. Ensure it's valid JSON.")
        return []
    except Exception as e:
        print_error(f"Error loading operations from '{file_path}': {e}")
        return []

def resolve_placeholders(value_with_placeholders: str, context_data: dict) -> list:
    """
    Recursively resolves placeholders in strings, lists, or dictionaries.
    Placeholders are in the format {{path.to.value}}.
    Looks up values in the context_data dictionary.
    """
    placeholder_pattern = re.compile(r"\{\{(.*?)\}\}")

    def replace_match(match):
        """
        Replaces a regex match object representing a placeholder with its resolved value from context_data.

        Args:
            match: The regex match object for a placeholder in the format {{path.to.value}}.

        Returns:
            The string representation of the resolved value if found, otherwise the original placeholder.
        """
        key_path_str = str(match.group(1).strip()) # Strip whitespace from key path
        if not key_path_str:
            print_verbose("Warning: Empty placeholder '{{}}' found.")
            return match.group(0) # Return original if key path is empty

        key_path = key_path_str.split('.')
        current_value = context_data
        try:
            for key_part in key_path:
                if isinstance(current_value, dict):
                    current_value = current_value.get(key_part)
                    if current_value is None:
                        raise KeyError(f"Key '{key_part}' not found in path '{'.'.join(key_path)}'")
                elif isinstance(current_value, list):
                    # Allow list indexing like {{list_name.0}}
                    try:
                        index = int(key_part)
                        current_value = current_value[index]
                    except (ValueError, IndexError):
                        raise KeyError(f"Invalid index or key '{key_part}' in path '{'.'.join(key_path)}'. Expected integer index for list.")
                else:
                    raise TypeError(f"Path part '{key_part}' accessed on a non-container type (was {type(current_value).__name__}) in path '{'.'.join(key_path)}'.")

            # Found the value, return its string representation
            return str(current_value)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            print_verbose(f"Warning: Placeholder '{{{{{match.group(1)}}}}}' not found or invalid path: {e}")
            return match.group(0) # Return the original placeholder if key not found or error in path

    # print_debug("Before resolving placeholders:", value_with_placeholders)

    if isinstance(value_with_placeholders, str):
        resolved_string = placeholder_pattern.sub(replace_match, value_with_placeholders)
        # print_debug("After resolving placeholders:", resolved_string)
        return resolved_string
    elif isinstance(value_with_placeholders, list):
        resolved_list = [resolve_placeholders(item, context_data) for item in value_with_placeholders]
        # print_debug("After resolving placeholders (list):", resolved_list)
        return resolved_list
    elif isinstance(value_with_placeholders, dict):
        resolved_dict = {k: resolve_placeholders(v, context_data) for k, v in value_with_placeholders.items()}
        # print_debug("After resolving placeholders (dict):", resolved_dict)
        return resolved_dict
    else:
        # For non-string, non-list, non-dict types (numbers, booleans, None), return them as is.
        # print_debug("After resolving placeholders (unchanged):", value_with_placeholders)
        return value_with_placeholders

def download_progress_hook(count: int, block_size: int, total_size: int) -> None:
    """A hook function for urllib.request.urlretrieve to display download progress."""
    percent = int(count * block_size * 100 / total_size)
    if percent > 100:
        percent = 100 # Cap at 100%
    sys.stdout.write(f"\rDownloading... {percent}% ")
    sys.stdout.flush()
    if percent == 100:
        sys.stdout.write("\n") # New line after download is complete

def perform_download(op_config: dict, game_root_path: Path, context: dict) -> bool:
    """Handles the download operation with security checks for archive unpacking."""
    op_name = op_config.get("Name", "Unnamed Download Operation")
    print(Colours.GREEN, f"\nExecuting download: '{op_name}'")

    # Thresholds for archive bomb protection - can be overridden by op_config
    # Max number of entries in an archive
    THRESHOLD_ENTRIES = op_config.get("unpack_threshold_entries", 10000)
    # Max total uncompressed size of an archive in bytes (e.g., 1GB)
    THRESHOLD_SIZE = op_config.get("unpack_threshold_size_bytes", 1 * 1024 * 1024 * 1024)
    # Max compression ratio for individual ZIP file members (uncompressed_size / compressed_size)
    THRESHOLD_RATIO = op_config.get("unpack_threshold_compression_ratio", 10)

    resolved_url = resolve_placeholders(op_config.get("url", ""), context)
    if not resolved_url:
        print_error(f"Error: Download operation '{op_name}' has no 'url' defined after placeholder resolution.")
        return False

    resolved_destination_str = Path(str(resolve_placeholders(op_config.get("destination", "."), context)))
    resolved_filename = str(resolve_placeholders(op_config.get("filename", ""), context))
    unpack = op_config.get("unpack", False)
    resolved_unpack_destination_str = Path(str(resolve_placeholders(op_config.get("unpack_destination", "."), context)))

    full_destination_dir = game_root_path / resolved_destination_str
    full_unpack_path = game_root_path / resolved_unpack_destination_str

    if not resolved_filename:
        try:
            resolved_filename = os.path.basename(urllib.parse.urlparse(resolved_url).path)
            if not resolved_filename or resolved_filename.endswith('/'):
                print_verbose(f"Warning: Could not determine filename from URL '{resolved_url}'. Defaulting to 'downloaded_file'.")
                resolved_filename = "downloaded_file"
        except Exception as e:
            print_verbose(f"Warning: Error parsing URL '{resolved_url}' for filename: {e}. Defaulting to 'downloaded_file'.")
            resolved_filename = "downloaded_file"

    final_file_path = full_destination_dir / resolved_filename

    print_verbose(f"Downloading from: {resolved_url}")
    print_verbose(f"Saving to: {final_file_path}")
    if unpack:
        print_verbose(f"Unpacking to: {full_unpack_path}")
        print_verbose(f"Archive security thresholds: Entries={THRESHOLD_ENTRIES}, Size={THRESHOLD_SIZE}B, ZipRatio={THRESHOLD_RATIO}")

    try:
        os.makedirs(full_destination_dir, exist_ok=True)
    except OSError as e:
        print_error(f"Error creating destination directory '{full_destination_dir}': {e}")
        return False

    USER_AGENT = "curl/8.11.1" # As per original code
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', USER_AGENT)]
    urllib.request.install_opener(opener)

    try:
        print(Colours.CYAN, "Starting download...")
        urllib.request.urlretrieve(resolved_url, final_file_path, reporthook=download_progress_hook)
        print(Colours.GREEN, "Download complete.")
    except urllib.error.HTTPError as e:
        print_error(f"HTTP Error during download from '{resolved_url}' to '{final_file_path}': {e.code} - {e.reason}")
        if os.path.exists(final_file_path):
            try: os.remove(final_file_path); print_verbose(f"Removed incomplete file: {final_file_path}")
            except OSError as cleanup_e: print_verbose(f"Warning: Could not remove incomplete file '{final_file_path}': {cleanup_e}")
        exit(1) # Original code uses exit(1)
    except urllib.error.URLError as e:
        print_error(f"URL Error during download from '{resolved_url}' to '{final_file_path}': {e.reason}")
        if os.path.exists(final_file_path):
            try: os.remove(final_file_path); print_verbose(f"Removed incomplete file: {final_file_path}")
            except OSError as cleanup_e: print_verbose(f"Warning: Could not remove incomplete file '{final_file_path}': {cleanup_e}")
        exit(1) # Original code uses exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred during download from '{resolved_url}' to '{final_file_path}': {e}")
        if os.path.exists(final_file_path):
            try: os.remove(final_file_path); print_verbose(f"Removed incomplete file: {final_file_path}")
            except OSError as cleanup_e: print_verbose(f"Warning: Could not remove incomplete file '{final_file_path}': {cleanup_e}")
        exit(1) # Original code uses exit(1)

    if unpack:
        print(Colours.CYAN, "Starting unpacking...")

        try:
            os.makedirs(full_unpack_path, exist_ok=True)
            file_extension = final_file_path.suffix.lower()

            if file_extension == '.zip':
                with zipfile.ZipFile(final_file_path, 'r') as zip_ref:
                    member_list = zip_ref.infolist()
                    num_members = len(member_list)
                    print_verbose(f"Found {num_members} members in the zip archive.")

                    if num_members > THRESHOLD_ENTRIES:
                        print_error(f"Error: Zip archive '{final_file_path}' exceeds entry threshold ({num_members}/{THRESHOLD_ENTRIES}). Potential zip bomb.")
                        return False

                    current_total_uncompressed_size = 0
                    for i, member_info in enumerate(member_list):
                        if member_info.compress_size > 0: # Avoid division by zero
                            ratio = member_info.file_size / member_info.compress_size
                            if ratio > THRESHOLD_RATIO:
                                print_error(f"Error: Member '{member_info.filename}' in zip '{final_file_path}' exceeds compression ratio threshold ({ratio:.2f}/{THRESHOLD_RATIO}). Potential zip bomb.")
                                return False

                        current_total_uncompressed_size += member_info.file_size
                        if current_total_uncompressed_size > THRESHOLD_SIZE:
                            print_error(f"Error: Zip archive '{final_file_path}' would exceed total size threshold ({current_total_uncompressed_size}/{THRESHOLD_SIZE}) with member '{member_info.filename}'. Potential zip bomb.")
                            return False

                        # Path traversal check (ZipFile.extract has some protections, but good to be aware)
                        # Target path for member
                        # member_target_path = full_unpack_path / member_info.filename
                        # resolved_member_target_path = member_target_path.resolve()
                        # resolved_full_unpack_path = full_unpack_path.resolve()
                        # if not str(resolved_member_target_path).startswith(str(resolved_full_unpack_path)):
                        #     print_error(f"Error: Member '{member_info.filename}' attempts to extract outside target directory. Aborting.")
                        #     return False

                        zip_ref.extract(member_info, full_unpack_path)
                        percent = int((i + 1) * 100 / num_members) if num_members > 0 else 100
                        sys.stdout.write(f"\rUnpacking zip... {percent}% ({i+1}/{num_members})")
                        sys.stdout.flush()
                    sys.stdout.write("\n")
                    if num_members == 0:
                        print(Colours.GREEN, "Zip archive is empty but processed successfully.")
                    else:
                        print(Colours.GREEN, "Zip archive unpacked successfully after security checks.")

            elif file_extension in ['.tar', '.gz', '.tgz', '.bz2', '.xz']: # .gz, .tgz etc. are often tar files
                # For .gz, .bz2, .xz that are not tar files, tarfile.open will fail.
                # This logic assumes these extensions imply a tar archive.
                try:
                    with tarfile.open(final_file_path, 'r:*') as tar_ref:
                        member_list = tar_ref.getmembers()
                        num_members = len(member_list)
                        print_verbose(f"Found {num_members} members in the tar archive.")

                        if num_members > THRESHOLD_ENTRIES:
                            print_error(f"Error: Tar archive '{final_file_path}' exceeds entry threshold ({num_members}/{THRESHOLD_ENTRIES}). Potential tar bomb.")
                            return False

                        current_total_uncompressed_size = 0
                        for member_info in member_list:
                            current_total_uncompressed_size += member_info.size # member_info.size is uncompressed

                        if current_total_uncompressed_size > THRESHOLD_SIZE:
                            print_error(f"Error: Tar archive '{final_file_path}' exceeds total uncompressed size threshold ({current_total_uncompressed_size}/{THRESHOLD_SIZE}). Potential tar bomb.")
                            return False

                        print_verbose("Tar security checks passed. Starting extraction.")
                        for i, member_info in enumerate(member_list):
                            # tarfile.extract has built-in protections against common path traversal (absolute paths, '..')
                            # For symlinks, ensure behavior is understood (default is to extract them if they point within the archive)
                            try:
                                tar_ref.extract(member_info, full_unpack_path, numeric_owner=True)
                            except Exception as e_extract:
                                sys.stdout.write("\n")
                                print_error(f"Error extracting member '{member_info.name}' from tar: {e_extract}")
                                return False # Fail entire operation if one member fails

                            percent = int((i + 1) * 100 / num_members) if num_members > 0 else 100
                            sys.stdout.write(f"\rUnpacking tar... {percent}% ({i+1}/{num_members})")
                            sys.stdout.flush()
                        sys.stdout.write("\n")
                        if num_members == 0:
                            print(Colours.GREEN, "Tar archive is empty but processed successfully.")
                        else:
                            print(Colours.GREEN, "Tar archive unpacked successfully after security checks.")
                except tarfile.ReadError as te: # Catch if it's not a valid tar file (e.g. plain .gz)
                    sys.stdout.write("\n")
                    print(Colours.YELLOW + f"Warning: File '{final_file_path}' with extension '{file_extension}' could not be opened as a tar archive: {te}. If it's a single compressed file, it won't be unpacked by this routine.")
                    print_verbose(f"File left at: {final_file_path}")
                    return False # Treat as failure if unpacking requested but format not fully handled for non-tar compressed files

            else:
                print(Colours.YELLOW + f"Warning: Unpacking requested but file extension '{file_extension}' is not supported for automatic unpacking (.zip or .tar.*).")
                print_verbose(f"File left at: {final_file_path}")
                return False # Unpacking requested but not supported

            cleanup_archive = op_config.get("cleanup_archive", False)
            if cleanup_archive:
                try:
                    os.remove(final_file_path)
                    print_verbose(f"Cleaned up downloaded archive: {final_file_path}")
                except OSError as cleanup_e:
                    print_verbose(f"Warning: Could not clean up archive '{final_file_path}': {cleanup_e}")

            return True # Unpacking process (if attempted for supported type) was successful

        except (zipfile.BadZipFile, tarfile.TarError, Exception) as e: # tarfile.TarError is base for tar issues
            # Ensure a newline is printed if the progress was interrupted by an error
            # Check if progress was being printed (total_members might not be defined if error was early)
            # A simple sys.stdout.write("\n") should be safe here.
            sys.stdout.write("\n")
            print_error(f"Error during unpacking '{final_file_path}': {e}")
            return False
    else:
        print(Colours.GREEN, "Download completed successfully, not unpacked.")
        return True


def main_tool_logic():
    """Main function to run the interactive tool."""
    tool_root_path = Path(__file__).parent.resolve() # Get path of the script itself
    games_registry_full_path = tool_root_path / GAMES_REGISTRY_DIR_NAME / GAMES_COLLECTION_DIR_NAME

    # --- Load Engine Configuration ---
    engine_config_data = {}
    engine_config_file_path = tool_root_path / ENGINE_CONFIG_FILENAME
    if engine_config_file_path.is_file():
        try:
            with open(engine_config_file_path, 'r', encoding='utf-8') as f:
                engine_config_data = json.load(f)
            print(Colours.GREEN, f"Loaded engine configuration from: {engine_config_file_path}")
        except json.JSONDecodeError:
            print_error(f"Error: Could not decode JSON from '{engine_config_file_path}'. Placeholders might not resolve correctly.")
        except Exception as e:
            print_error(f"Error loading engine configuration '{engine_config_file_path}': {e}")
    else:
        print(Colours.YELLOW, f"Info: Engine configuration file '{engine_config_file_path}' not found. Only game-specific placeholders will be available if defined.")

    print(Colours.CYAN, f"Scanning for games in: {games_registry_full_path}")
    available_games_map = discover_games(games_registry_full_path, DOWNLOADS_FILENAME)

    if not available_games_map:
        print_error(f"No valid game configurations found in subdirectories of '{games_registry_full_path}'.")
        print(Colours.YELLOW, f"Ensure each game has a directory containing an '{DOWNLOADS_FILENAME}' formatted correctly (JSON object with game name as key).")
        input("Press Enter to close.")
        return False

    game_names_sorted = sorted(list(available_games_map.keys()))

    selected_game_name = questionary.select(
        "Select a game to work with:",
        choices=game_names_sorted + [questionary.Separator(), "Exit Tool"],
        style=custom_style_fancy
    ).ask()

    if selected_game_name is None or selected_game_name == "Exit Tool":
        print(Colours.CYAN, "Exiting tool...")
        return False

    selected_game_data = available_games_map[selected_game_name]
    operations_file_for_game = selected_game_data["ops_file"]
    game_root_path = Path(__file__).parent.resolve()

    print(Colours.CYAN, f"Selected game's root path: {game_root_path}")
    print(Colours.CYAN, f"Loading operations for game: '{selected_game_name}' from {operations_file_for_game}")
    operations = load_downloads(operations_file_for_game, selected_game_name) # Renamed from downloads for clarity

    if not operations:
        print_error(f"No valid operations found for '{selected_game_name}'. Check content of '{operations_file_for_game}' under the key '{selected_game_name}'.")
        input("Press Enter to return to game selection.")
        return True # Signal to change game (go back to game selection)

    # --- Create the dynamic context for placeholder resolution ---
    # This context will be updated with prompt answers as they are gathered.
    # Start with global engine config and game specifics.
    # Use a copy so prompt answers don't leak between game selections
    current_resolution_context = engine_config_data.copy()
    current_resolution_context["Game"] = { # Add game-specifics under a "Game" key
        "RootPath": str(game_root_path),    # Absolute path to the selected game's root
        "Name": selected_game_name,         # Name of the selected game
    }

    # -- Main operations loop --
    while True: # Operations loop for the selected game
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Colours.MAGENTA, f"--- Operations for: {selected_game_name} ---")
        print(Colours.CYAN, f"(Root: {game_root_path})")

        menu_choices = []
        # Prepare menu choices, "Name" is used for display
        # Filter out operations without a 'Name' unless they are designed as init/hidden steps (not implemented in this version)
        for op_idx, op in enumerate(operations):
            op_name = op.get("Name")
            op_type = op.get("Type", "unknown") # Default type for filtering

            # Decide which operations to show in the menu.
            # For now, show anything with a Name. Could later add a "hidden": true flag.
            if op_name:
                # Add a type hint to the menu item for clarity? (Optional)
                # menu_choices.append(f"{op_name} ({op_type.capitalize()})")
                menu_choices.append(op_name)
            else:
                # Operations without a name are skipped for the manual menu
                print_verbose(f"Skipping unnamed operation #{op_idx+1} (Type: {op_type}) from menu.")
                continue


        menu_choices.extend([questionary.Separator(), "Change Game", "Exit Tool"])

        selected_op_display_name = questionary.select(
            "Select operation to perform:",
            choices=menu_choices,
            use_shortcuts=True,
            style=custom_style_fancy
        ).ask()

        if selected_op_display_name is None or selected_op_display_name == "Exit Tool":
            print(Colours.CYAN, "Exiting tool...")
            return False

        if selected_op_display_name == "Change Game":
            return True # Signal to change game

        # Find the selected operation configuration by display name
        selected_op_config = None
        for op_idx, op in enumerate(operations):
            current_op_display_name = op.get("Name")
            if current_op_display_name == selected_op_display_name:
                selected_op_config = op
                break

        if not selected_op_config:
            # This should ideally not happen if the menu was built correctly
            print_error(f"Error: Could not find configuration for selected operation '{selected_op_display_name}'. This might be an internal error.")
            input("\nPress Enter to return to the menu.")
            continue

        op_title_for_log = selected_op_config.get("Name") or "Unnamed Operation"
        op_type = selected_op_config.get("Type", "unknown")

        print(Colours.GREEN, f"\nPreparing to run: '{op_title_for_log}' (Type: {op_type}) for {selected_game_name}")

        # instructions = selected_op_config.get("Instructions")
        # if instructions:
        #    print(Colours.CYAN, "\nInstructions for this step:")
        #    # Resolve placeholders in instructions too? Maybe not necessary, but possible.
        #    # resolved_instructions = resolve_placeholders(instructions, current_resolution_context)
        #    print(Colours.WHITE, instructions)

        # --- Process Prompts and Update Context ---
        # Create a temporary context copy for this operation to add prompt answers to
        # This allows prompts to use answers from previous prompts in the *same* operation.
        op_resolution_context = current_resolution_context.copy()

        operation_cancelled_by_user = False

        if "prompts" in selected_op_config:
            print(Colours.MAGENTA, "\nGathering required information...")
            for prompt_config in selected_op_config.get("prompts", []):
                try:
                    # Resolve placeholders in prompt configuration itself
                    resolved_prompt_config = resolve_placeholders(prompt_config, op_resolution_context)

                    # Check condition BEFORE asking the prompt
                    if "condition" in resolved_prompt_config:
                        condition_prompt_name = resolved_prompt_config["condition"]
                        # Condition is met if the corresponding prompt name exists in context AND its value is truthy
                        # (e.g., a 'confirm' prompt answered True, or a 'checkbox' with non-empty selection)
                        if not op_resolution_context.get(condition_prompt_name):
                            print_verbose(f"Skipping prompt '{resolved_prompt_config.get('Name', 'Unnamed Prompt')}' based on condition '{condition_prompt_name}'.")
                            continue # Skip this prompt

                    prompt_name = resolved_prompt_config["Name"]
                    prompt_message = resolved_prompt_config["message"]
                    prompt_type = resolved_prompt_config.get("type", "text")

                    answer = None
                    # Use resolved_prompt_config for default, choices, validation etc.
                    # Ensure defaults are handled appropriately for each type

                    if prompt_type == "confirm":
                        default_val = resolved_prompt_config.get("default", False)
                        answer = questionary.confirm(prompt_message, default=default_val, style=custom_style_fancy).ask()
                    elif prompt_type == "checkbox":
                        choices_for_checkbox = resolved_prompt_config.get("choices", [])
                        # Ensure choices are simple strings/values for questionary
                        choices_for_checkbox = [str(c) for c in choices_for_checkbox]

                        validate_func = None
                        validation_rules = resolved_prompt_config.get("validation")
                        if validation_rules and validation_rules.get("required"):
                            val_msg = validation_rules.get("message", "Selection required.")
                            validate_func = lambda x: True if len(x) > 0 else val_msg

                        answer = questionary.checkbox(
                            prompt_message,
                            choices=choices_for_checkbox,
                            style=custom_style_fancy,
                            validate=validate_func
                        ).ask()
                    elif prompt_type == "text":
                        default_val = resolved_prompt_config.get("default", "")
                        validate_func = None
                        validation_rules = resolved_prompt_config.get("validation")
                        if validation_rules and validation_rules.get("required"):
                            val_msg = validation_rules.get("message", "Input required.")
                            validate_func = lambda x: True if len(x.strip()) > 0 else val_msg

                        answer = questionary.text(prompt_message, default=str(default_val), style=custom_style_fancy, validate=validate_func).ask()
                    # Add other prompt types (select, path, etc.) here if needed
                    else:
                        print_error(f"Warning: Unknown prompt type '{prompt_type}' for prompt '{prompt_name}'. Skipping.")
                        continue # Skip this prompt

                    if answer is None: # User cancelled the prompt (Ctrl+C)
                        operation_cancelled_by_user = True
                        break

                    # Add the new answer to the operation-specific context for subsequent steps/prompts
                    op_resolution_context[prompt_name] = answer
                    print_debug(f"Prompt '{prompt_name}' answered with: {answer}") # Log prompt answer

                except KeyError as e:
                    print_error(f"Error processing prompt configuration for '{prompt_config.get('Name', 'Unnamed Prompt')}': Missing required key - {e}")
                    operation_cancelled_by_user = True # Treat misconfigured prompt as cancellation
                    break
                except Exception as e:
                    print_error(f"Unexpected error during prompt '{prompt_config.get('Name', 'Unnamed Prompt')}' processing: {e}")
                    operation_cancelled_by_user = True
                    break

        if operation_cancelled_by_user:
            print(Colours.RED, f"Operation '{op_title_for_log}' cancelled by user or due to configuration error.")
            input("\nPress Enter to return to the menu.")
            continue # Go back to game operations menu

        # --- Execute the Operation based on Type ---
        if op_type == "download":
            # Pass the operation config, game root, and the updated context (including prompt answers)
            success = perform_download(selected_op_config, game_root_path, op_resolution_context)
            if success:
                print(Colours.GREEN, f"\nOperation '{op_title_for_log}' completed successfully.")
            else:
                print_error(f"\nOperation '{op_title_for_log}' failed.")
        else:
            print_error(f"Error: Unknown operation type '{op_type}' for '{op_title_for_log}'.")
            print(Colours.YELLOW, "Please check the 'Type' field in the JSON configuration.")

        print(Colours.MAGENTA, "\nOperation finished. Press Enter to return to the operations menu.")
        input()

if __name__ == "__main__":
    should_continue_main_loop = True
    while should_continue_main_loop:
        should_continue_main_loop = main_tool_logic()

    print(Colours.MAGENTA, "\nTool has been closed. Press any key to exit window.")
    # Keep window open until user presses Enter
    input()
