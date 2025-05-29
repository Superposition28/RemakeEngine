"""
This module provides an interactive tool for managing and executing operations
for various games. It includes functionality for discovering games, loading
operations, validating scripts, and running selected operations interactively.
"""

import questionary
from pathlib import Path
import re
import json
import subprocess

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
OPERATIONS_FILENAME = "operations.json" # Standard name for ops file per game
ENGINE_CONFIG_FILENAME = "project.json"


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

    for game_dir_path in games_collection_path.iterdir():
        if game_dir_path.is_dir(): # Ensure it's a directory
            potential_ops_file = game_dir_path / ops_file_name
            if potential_ops_file.is_file():
                try:
                    with open(potential_ops_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and len(data) == 1:
                        game_name_from_json = list(data.keys())[0] # Get the single top-level key

                        # Validate that the value associated with the game name is a list (of operations)
                        if isinstance(data[game_name_from_json], list):
                            if game_name_from_json in games:
                                # Handle duplicate game names, e.g. if two JSONs define the same game name
                                print(Colours.YELLOW, f"Warning: Duplicate game name '{game_name_from_json}' defined in '{potential_ops_file}'. Overwriting previous entry from {games[game_name_from_json]['ops_file']}.")

                            games[game_name_from_json] = {
                                "ops_file": potential_ops_file.resolve(), # Store absolute path
                                "game_root": game_dir_path.resolve() # Store absolute path to game's root
                            }
                        else:
                            print(Colours.RED, f"Error: Operations data for game '{game_name_from_json}' in '{potential_ops_file}' is not a list.")
                    else:
                        print(Colours.RED, f"Error: Operations file '{potential_ops_file}' should be a JSON object with a single top-level key (the game name), and its value should be a list of operations.")
                except json.JSONDecodeError:
                    print(Colours.RED, f"Error: Could not decode JSON from '{potential_ops_file}'. Ensure it's valid JSON.")
                except Exception as e:
                    print(Colours.RED, f"Error processing file '{potential_ops_file}': {e}")
    return games

def load_operations(file_path: Path, game_name_key: str) -> list:
    """Loads operations list from a JSON file, using game_name_key to access it."""
    if not file_path.is_file():
        print(Colours.RED, f"Error: Operations file '{file_path}' not found or is not a file.")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            operations_list = data.get(game_name_key)
            if isinstance(operations_list, list):
                return operations_list
            else:
                print(Colours.RED, f"Error: Did not find a list of operations under key '{game_name_key}' in '{file_path}'. Found: {type(operations_list)}")
                return []
        else:
            # This case should ideally be caught by discover_games structure validation
            print(Colours.RED, f"Error: Operations file '{file_path}' is not structured as a dictionary with game name as key.")
            return []
    except json.JSONDecodeError:
        print(Colours.RED, f"Error: Could not decode JSON from '{file_path}'. Ensure it's valid JSON.")
        return []
    except Exception as e:
        print(Colours.RED, f"Error loading operations from '{file_path}': {e}")
        return []

def resolve_placeholders(value_with_placeholders, context_data: dict):
	"""
	Recursively resolves placeholders in strings, lists, or dictionaries.
	Placeholders are in the format {{path.to.value}}.
	"""
	placeholder_pattern = re.compile(r"\{\{(.*?)\}\}")

	def replace_match(match):
		key_path_str = match.group(1)
		# Handle special direct context keys first (like Game.RootPath)
		if key_path_str in context_data.get("_direct_mapping_", {}):
			return str(context_data["_direct_mapping_"][key_path_str])


		key_path = key_path_str.split('.')
		current_value = context_data
		try:
			for key_part in key_path:
				if isinstance(current_value, dict):
					current_value = current_value[key_part]
				# elif isinstance(current_value, list): # Handle list indexing if needed: e.g. {{list.0.value}}
				# current_value = current_value[int(key_part)]
				else:
					raise KeyError(f"Path part '{key_part}' not found or parent is not a dictionary.")
			return str(current_value)
		except (KeyError, IndexError, ValueError, TypeError) as e:
			# print(Colours.YELLOW, f"Warning: Placeholder '{{{{{match.group(1)}}}}}' not found or invalid path: {e}")
			return match.group(0) # Return the original placeholder if key not found or error in path

	print("Before resolving placeholders:", value_with_placeholders)

	if isinstance(value_with_placeholders, str):
		# Iteratively replace to handle nested placeholders if necessary, though simple substitution is usually enough.
		# For {{A}} where A is {{B}}, this might need multiple passes or more complex regex.
		# For now, one pass should cover most cases like {{RemakeEngine.Path}}
		resolved_string = placeholder_pattern.sub(replace_match, value_with_placeholders)
		# If the entire string was a placeholder that resolved to a non-string (e.g. number, boolean from JSON),
		# we might want to return that type. But args are usually strings. For simplicity, keep as string.
		print("After resolving placeholders:", resolved_string)
		return resolved_string
	elif isinstance(value_with_placeholders, list):
		resolved_list = [resolve_placeholders(item, context_data) for item in value_with_placeholders]
		print("After resolving placeholders (list):", resolved_list)
		return resolved_list
	elif isinstance(value_with_placeholders, dict):
		resolved_dict = {k: resolve_placeholders(v, context_data) for k, v in value_with_placeholders.items()}
		print("After resolving placeholders (dict):", resolved_dict)
		return resolved_dict
	else:
		print("After resolving placeholders (unchanged):", value_with_placeholders)
		return value_with_placeholders

def check_scripts_exist(operations: list, ops_file_path_for_logging: Path) -> bool:
    """
    Checks whether all scripts referenced in the operations list exist as files.

    Args:
        operations (list): List of operation dictionaries, each potentially containing a 'script' key.
        ops_file_path_for_logging (Path): Path to the operations file, used for logging purposes.

    Returns:
        bool: True if all scripts exist or are not required, False if any script is missing.
    """
    all_exist = True
    if not operations:
        return True

    for op_idx, op in enumerate(operations):
        op_display_name = op.get("Name") or f"Unnamed Operation #{op_idx+1}"
        script_path_str = op.get("script")

        if not script_path_str: # Covers script: "" or script key not present
            # This is fine, means it's an info step or handled internally
            continue

        if not Path(script_path_str).is_file():
            print(Colours.RED, f"Error: Script for operation '{op_display_name}' not found at: {script_path_str}")
            print(Colours.YELLOW, f"       (Defined in '{ops_file_path_for_logging}', script base path: '{script_path_str}')")
            all_exist = False
    return all_exist

def main_tool_logic():
    """Main function to run the interactive tool."""
    tool_root_path = Path.cwd()
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
            print(Colours.RED, f"Error: Could not decode JSON from '{engine_config_file_path}'. Placeholders might not resolve.")
        except Exception as e:
            print(Colours.RED, f"Error loading engine configuration '{engine_config_file_path}': {e}")
    else:
        print(Colours.YELLOW, f"Info: Engine configuration file '{engine_config_file_path}' not found. Only game-specific placeholders will be available if defined.")

    print(Colours.CYAN, f"Scanning for games in: {games_registry_full_path}")
    available_games_map = discover_games(games_registry_full_path, OPERATIONS_FILENAME)

    if not available_games_map:
        print(Colours.RED, f"No valid game configurations found in subdirectories of '{games_registry_full_path}'.")
        print(Colours.YELLOW, f"Ensure each game has a directory containing an '{OPERATIONS_FILENAME}' formatted correctly (JSON object with game name as key).")
        input("Press Enter to close.")
        return False # Signal to exit main loop

    game_names_sorted = sorted(list(available_games_map.keys()))

    selected_game_name = questionary.select(
        "Select a game to work with:",
        choices=game_names_sorted + [questionary.Separator(), "Exit Tool"],
        style=custom_style_fancy
    ).ask()

    if selected_game_name is None or selected_game_name == "Exit Tool":
        print(Colours.CYAN, "Exiting tool...")
        return False # Signal to exit main loop

    selected_game_data = available_games_map[selected_game_name]
    operations_file_for_game = selected_game_data["ops_file"]
    # --- CORRECTED game_root_path ----
    game_root_path = selected_game_data["game_root"] # This was correctly stored by discover_games
    # path to the game's root directory
    # game_root_path = Path(__file__).parent.resolve() # This line was incorrect for the game's root

    print(Colours.CYAN, f"Selected game's root path: {game_root_path}") # Good to confirm
    print(Colours.CYAN, f"Loading operations for game: '{selected_game_name}' from {operations_file_for_game}")
    operations = load_operations(operations_file_for_game, selected_game_name)
    if not operations:
        print(Colours.RED, f"No valid operations found for '{selected_game_name}'. Check content of '{operations_file_for_game}' under the key '{selected_game_name}'.")
        input("Press Enter to return to game selection.")
        return True # Signal to change game (go back to game selection)

    # Validate all scripts exist before proceeding further (including potential init scripts)
    if not check_scripts_exist(operations, operations_file_for_game):
        print(Colours.RED, f"One or more essential scripts for '{selected_game_name}' are missing or misconfigured.")
        input("Press Enter to return to game selection.")
        return True # Signal to change game

    # --- Create the dynamic context for placeholder resolution ---
    # This context will be used for resolving placeholders in args.
    current_resolution_context = engine_config_data.copy() # Start with global engine config
    current_resolution_context["Game"] = { # Add game-specifics under a "Game" key
        "RootPath": str(game_root_path),    # Absolute path to the selected game's root
        "Name": selected_game_name,         # Name of the selected game
        # Add other game-specific values if needed for placeholders
    }
    # For direct access like {{GameRootPath}} (less structured, but possible)
    # You could create a flat "_direct_mapping_" if desired for specific, frequently used values.
    # current_resolution_context["_direct_mapping_"] = {
    #     "GameRootPath": str(game_root_path),
    #     "SelectedGameName": selected_game_name
    # }

    # --- Execute Init Script if defined ---
    init_script_executed_successfully = True # Assume success if no init script found or needed
    found_init_script_to_run = False

    for op_idx, op_config in enumerate(operations):
        if op_config.get("init") is True:
            found_init_script_to_run = True
            op_title_for_log = op_config.get("Name") or f"Init Operation #{op_idx+1}"
            print(Colours.MAGENTA, f"\nFound initialization script: '{op_title_for_log}' for {selected_game_name}. Attempting to run...")

            #init_instructions = op_config.get("Instructions")
            #if init_instructions:
            #    print(Colours.CYAN, "\nInstructions for this initialization step:")
            #    print(Colours.WHITE, init_instructions)

            python_exe = op_config.get("python_executable", "python")
            script_rel_path_str = op_config.get("script")

            if not script_rel_path_str:
                print(Colours.YELLOW, f"Warning: Init operation '{op_title_for_log}' has no 'script' defined. Skipping this init script.")
                continue

            script_abs_path = Path(script_rel_path_str)

            if not script_abs_path.is_file():
                print(Colours.RED, f"Error: Init script file for operation '{op_title_for_log}' not found at expected location: {script_abs_path}")
                print(Colours.YELLOW, f"       (Defined in '{operations_file_for_game}', relative to game root '{game_root_path}')")
                init_script_executed_successfully = False
                break

            command_parts = [python_exe, str(script_abs_path)]

            # Add static args from JSON for init script
            static_args = op_config.get("args", [])
            if isinstance(static_args, list):
                # --- RESOLVE PLACEHOLDERS FOR INIT ARGS ---
                resolved_static_args = resolve_placeholders(static_args, current_resolution_context)
                command_parts.extend([str(arg) for arg in resolved_static_args])
            elif static_args:
                print(Colours.YELLOW, f"Warning: 'args' for init operation '{op_title_for_log}' is not a list. Ignoring static args.")


            print(Colours.BLUE, "\nExecuting init command:")
            print(Colours.BLUE, f"  {' '.join(command_parts)}")

            try:
                process = subprocess.Popen(command_parts)
                process.wait()
                if process.returncode == 0:
                    print(Colours.GREEN, f"\nInitialization script '{op_title_for_log}' completed successfully.")
                else:
                    print(Colours.RED, f"\nInitialization script '{op_title_for_log}' failed with exit code {process.returncode}.")
                    init_script_executed_successfully = False
                break # Only run the first init script found
            except FileNotFoundError:
                print(Colours.RED, f"\nError: Executable '{python_exe}' or script '{script_abs_path}' for init operation '{op_title_for_log}' not found.")
                init_script_executed_successfully = False
                break
            except PermissionError:
                print(Colours.RED, f"\nError: Permission denied for init script '{script_abs_path}' or executable '{python_exe}'.")
                init_script_executed_successfully = False
                break
            except Exception as e:
                print(Colours.RED, f"\nError running init script '{op_title_for_log}': {e}")
                init_script_executed_successfully = False
                break

    if found_init_script_to_run and not init_script_executed_successfully:
        print(Colours.RED, f"Due to initialization failure for '{selected_game_name}', returning to game selection.")
        input("Press Enter to continue.")
        return True # Signal to change game

    if found_init_script_to_run and init_script_executed_successfully:
        print(Colours.GREEN, f"\nInitialization for '{selected_game_name}' completed successfully. Press Enter to continue.")
        input()
    elif not found_init_script_to_run:
        print(Colours.CYAN, f"\nNo initialization scripts marked to autorun for '{selected_game_name}'. Press Enter to continue.")
        input()


    # -- Main operations loop --
    while True: # Operations loop for the selected game
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Colours.MAGENTA, f"--- Operations for: {selected_game_name} ---")

        menu_choices = []
        # Prepare menu choices, "Name" is used for display
        for op_idx, op in enumerate(operations):
            op_name = op.get("Name")
            is_init_task = op.get("init") is True

            # If it's an init task AND it doesn't have a specific Name,
            # it's considered an auto-run init script and shouldn't be in the manual menu.
            if is_init_task and not op_name:
                continue # Skip this operation from being added to menu_choices

            if op_name:
                menu_choices.append(op_name)
            else:
                # This operation is not an init-only unnamed task, but still lacks a Name.
                # It could be a regular task that's just missing a Name.
                unnamed_op_label = f"Unnamed Operation #{op_idx+1}"
                menu_choices.append(unnamed_op_label)
                # Optional: Keep warning for genuinely unnamed non-init ops
                print(Colours.YELLOW, f"Warning: Operation #{op_idx+1} (script: {op.get('script', 'N/A')}) in '{operations_file_for_game}' has no 'Name'. Displaying as '{unnamed_op_label}'.")


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
            return True

        selected_op_config = None
        for op_idx, op in enumerate(operations):
            current_op_display_name = op.get("Name")
            is_unnamed_and_added = False
            if not current_op_display_name:
                # Check if this unnamed op would have been added to menu_choices
                if not (op.get("init") is True and not op.get("Name")): # It wasn't a skipped init-only op
                    current_op_display_name = f"Unnamed Operation #{op_idx+1}"
                    is_unnamed_and_added = True

            if current_op_display_name == selected_op_display_name:
                selected_op_config = op
                break

        if not selected_op_config:
            print(Colours.RED, f"Error: Could not find configuration for selected operation '{selected_op_display_name}'. This might be an internal error.")
            input("\nPress Enter to return to the menu.")
            continue

        op_title_for_log = selected_op_config.get("Name") or "Unnamed Operation"
        print(Colours.GREEN, f"\nPreparing to run: '{op_title_for_log}' for {selected_game_name}")

        #instructions = selected_op_config.get("Instructions")
        #if instructions:
        #    print(Colours.CYAN, "\nInstructions for this step:")
        #    print(Colours.WHITE, instructions)

        python_exe = selected_op_config.get("python_executable", "python")
        script_rel_path = selected_op_config.get("script")

        if not script_rel_path:
            print(Colours.YELLOW, f"\nInfo: Operation '{op_title_for_log}' has no script to execute.")
            #if not instructions:
            #    print(Colours.YELLOW, "       This operation may be for informational purposes only or is misconfigured.")
            input("\nPress Enter to return to the menu.")
            continue

        script_abs_path = Path(script_rel_path)
        if not script_abs_path.is_file():
            print(Colours.RED, f"Error: Script file for operation '{op_title_for_log}' ('{script_rel_path}') not found at: {script_abs_path}")
            print(Colours.YELLOW, f"       (Relative to game root: '{game_root_path}')")
            input("\nPress Enter to return to the menu.")
            continue

        command_parts = [python_exe, str(script_abs_path)]

        # Add static args from JSON *before* processing prompts
        static_args = selected_op_config.get("args", [])
        if isinstance(static_args, list):
            # --- RESOLVE PLACEHOLDERS FOR OPERATION ARGS ---
            resolved_static_args = resolve_placeholders(static_args, current_resolution_context)
            command_parts.extend([str(arg) for arg in resolved_static_args])
        elif static_args:
            print(Colours.YELLOW, f"Warning: 'args' for operation '{op_title_for_log}' is not a list. Ignoring static args.")


        prompt_answers = {}
        operation_cancelled_by_user = False

        if "prompts" in selected_op_config:
            for prompt_config in selected_op_config["prompts"]:
                if "condition" in prompt_config:
                    condition_prompt_name = prompt_config["condition"]
                    if not prompt_answers.get(condition_prompt_name, False):
                        continue
                prompt_name = prompt_config["Name"]
                prompt_message = prompt_config["message"]
                answer = None
                prompt_type = prompt_config.get("type", "text")

                if prompt_type == "confirm":
                    answer = questionary.confirm(prompt_message, default=prompt_config.get("default", False), style=custom_style_fancy).ask()
                    if answer is None: operation_cancelled_by_user = True; break
                    prompt_answers[prompt_name] = answer
                    if answer and "cli_arg" in prompt_config: command_parts.append(prompt_config["cli_arg"])
                elif prompt_type == "checkbox":
                    choices_for_checkbox = prompt_config.get("choices", [])
                    validate_func = None
                    validation_rules = prompt_config.get("validation")
                    if validation_rules and validation_rules.get("required"):
                        val_msg = validation_rules.get("message", "Selection required.")
                        validate_func = lambda x: True if len(x) > 0 else val_msg

                    answer = questionary.checkbox(
                        prompt_message,
                        choices=choices_for_checkbox,
                        style=custom_style_fancy,
                        validate=validate_func
                    ).ask()
                    if answer is None: operation_cancelled_by_user = True; break
                    prompt_answers[prompt_name] = answer
                    if answer and "cli_prefix" in prompt_config:
                        command_parts.append(prompt_config["cli_prefix"])
                        command_parts.extend([str(a) for a in answer]) # Ensure all parts are strings
                elif prompt_type == "text":
                    default_val = prompt_config.get("default", "")
                    validate_func = None
                    validation_rules = prompt_config.get("validation")
                    if validation_rules and validation_rules.get("required") and not default_val:
                        val_msg = validation_rules.get("message", "Input required.")
                        validate_func = lambda x: True if len(x.strip()) > 0 else val_msg

                    answer = questionary.text(prompt_message, default=str(default_val), style=custom_style_fancy, validate=validate_func).ask()
                    if answer is None: operation_cancelled_by_user = True; break
                    prompt_answers[prompt_name] = answer
                    if "cli_arg_template" in prompt_config and answer.strip():
                        command_parts.append(prompt_config["cli_arg_template"].replace("{value}", answer.strip()))
                    elif "cli_arg_prefix" in prompt_config and answer.strip():
                        command_parts.append(prompt_config["cli_arg_prefix"])
                        command_parts.append(answer.strip())
                    elif "cli_arg" in prompt_config and answer.strip():
                        command_parts.append(prompt_config["cli_arg"])
                        command_parts.append(answer.strip())
                # Add other prompt types (select, path, etc.) here if needed

        if operation_cancelled_by_user:
            print(Colours.RED, f"Configuration for '{op_title_for_log}' cancelled by user. Skipping operation.")
            input("\nPress Enter to return to the menu.")
            continue

        print(Colours.BLUE, "\nExecuting command:")
        print(Colours.BLUE, f"  {' '.join(command_parts)}")

        try:
            process = subprocess.Popen(command_parts)
            process.wait()
            if process.returncode == 0:
                print(Colours.GREEN, f"\nOperation '{op_title_for_log}' completed successfully.")
            else:
                print(Colours.RED, f"\nOperation '{op_title_for_log}' failed with exit code {process.returncode}.")
        except FileNotFoundError:
            print(Colours.RED, f"\nError: Script '{script_abs_path}' or Python executable '{python_exe}' not found.")
        except PermissionError:
            print(Colours.RED, f"\nError: Permission denied for script '{script_abs_path}' or executable '{python_exe}'.")
        except Exception as e:
            print(Colours.RED, f"\nError running operation '{op_title_for_log}': {e}")

        print(Colours.MAGENTA, "\nOperation finished. Press Enter to return to the operations menu.")
        input()


if __name__ == "__main__":
    should_continue_main_loop = True
    while should_continue_main_loop:
        should_continue_main_loop = main_tool_logic()

    print(Colours.MAGENTA, "\nTool has been closed. Press any key to exit window.")
    input()
