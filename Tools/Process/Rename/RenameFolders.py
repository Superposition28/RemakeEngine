
import argparse
import sqlite3
import json # Added for potential future use, e.g., JSON map file

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Utils')))
from printer import print, Colours, print_error, print_verbose, print_debug, printc


def load_map_from_db(db_path: str, table_name: str = "rename_mappings") -> dict:
    """Loads the rename map from a SQLite database."""
    if not os.path.exists(db_path):
        print_error(f"Database file not found: {db_path}")
        return None # Or raise an error

    rename_map = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        if not cursor.fetchone():
            print_error(f"Table '{table_name}' not found in database: {db_path}")
            conn.close()
            return None

        cursor.execute(f"SELECT old_name, new_name FROM {table_name}")
        for row in cursor.fetchall():
            rename_map[row[0]] = row[1]
        conn.close()
        print(Colours.GREEN, f"Successfully loaded rename map from DB: {db_path} (Table: {table_name})")
        return rename_map
    except sqlite3.Error as e:
        print_error(f"SQLite error while reading {db_path}: {e}")
        return None # Or raise error

def load_map_from_cli_args(cli_map_args: list) -> dict:
    """Loads the rename map from direct CLI arguments."""
    rename_map = {}
    if cli_map_args:
        for old_name, new_name in cli_map_args:
            rename_map[old_name] = new_name
        print(Colours.GREEN, "Successfully loaded rename map from CLI arguments.")
    return rename_map

def rename_subdirectories(target_directory: str, rename_map: dict) -> None:
    """
    Renames subdirectories within the target_directory based on the provided map.
    """
    if not rename_map:
        print_error("Rename map is empty. No renaming operations will be performed.")
        return

    print(Colours.YELLOW, f"Processing directory: {target_directory}")

    if not os.path.isdir(target_directory):
        print_error(f"Error: The specified directory '{target_directory}' does not exist or is not a directory.")
        return

    total_dirs_inspected = 0
    renamed_items = 0
    skipped_items = 0

    try:
        items_in_dir = os.listdir(target_directory)
    except PermissionError:
        print_error(f"Error: Permission denied to read directory '{target_directory}'.")
        return
    except FileNotFoundError:
        print_error(f"Error: Directory '{target_directory}' not found during listing.")
        return

    for item_name in items_in_dir:
        item_path = os.path.join(target_directory, item_name)

        if os.path.isdir(item_path):
            total_dirs_inspected += 1
            if item_name in rename_map:
                new_name = rename_map[item_name]
                new_path = os.path.join(target_directory, new_name)

                print(Colours.GRAY, f"  Old name: {item_name} (Path: {item_path})")
                print(Colours.GRAY, f"  New name: {new_name} (Path: {new_path})")

                try:
                    if os.path.exists(new_path):
                        print_error(f"  Skipping rename: Target '{new_path}' already exists.")
                        skipped_items +=1
                    else:
                        os.rename(item_path, new_path)
                        print(Colours.GREEN, f"  Successfully renamed '{item_name}' to '{new_name}'")
                        renamed_items += 1
                except OSError as e:
                    print_error(f"  Error renaming '{item_name}' to '{new_name}': {e}")
                    skipped_items += 1
            else:
                print(Colours.CYAN, f"  Skipped '{item_name}' - no matching key in rename map.")
                skipped_items += 1

    print(Colours.GREEN, "\n--- Processing Summary ---")
    print(Colours.GREEN, f"Total directories inspected: {total_dirs_inspected}")
    print(Colours.GREEN, f"Directories renamed: {renamed_items}")
    print(Colours.GREEN, f"Directories skipped (no match, error, or target exists): {skipped_items}")


def main():
    parser = argparse.ArgumentParser(
        description="Renames subdirectories in a target directory based on a map. "
                    "The map can be provided via a SQLite DB, direct CLI arguments, or a JSON file. "
                    "If no map source is specified, a default internal map is used.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target_directory",
        type=str,
        help="The path to the directory containing the subdirectories to be renamed."
    )

    map_source_group = parser.add_mutually_exclusive_group()
    map_source_group.add_argument(
        "--map-db-file",
        type=str,
        metavar="DB_PATH",
        help="Path to a SQLite .db file containing the rename map. \n"
            "Expected table: 'rename_mappings' with columns 'old_name' and 'new_name'."
    )
    map_source_group.add_argument(
        "--map-cli",
        nargs=2,
        action='append', # Allows specifying this argument multiple times
        metavar=('OLD_NAME', 'NEW_NAME'),
        help="Define a single old_name to new_name mapping. \n"
            "Repeat for multiple entries (e.g., --map-cli old1 new1 --map-cli old2 new2)."
    )
    map_source_group.add_argument(
        "--map-json-file",
        type=str,
        metavar="JSON_PATH",
        help="Path to a JSON file containing the rename map (object with old_name: new_name pairs)."
    )

    parser.add_argument(
        "--db-table-name",
        type=str,
        default="rename_mappings",
        metavar="TABLE_NAME",
        help="Optional: Name of the table in the SQLite DB to use for the map (default: rename_mappings)."
    )

    args = parser.parse_args()

    # Determine the rename map
    active_rename_map = None
    map_source_description = "default internal map"

    if args.map_db_file:
        if not os.path.exists(args.map_db_file):
            print_error(f"Error: Database file specified ('{args.map_db_file}') but not found.")
            return 1 # Exit with error
        active_rename_map = load_map_from_db(args.map_db_file, args.db_table_name)
        map_source_description = f"SQLite DB '{args.map_db_file}' (table: {args.db_table_name})"
    elif args.map_cli:
        active_rename_map = load_map_from_cli_args(args.map_cli)
        map_source_description = "direct CLI arguments"
    elif args.map_json_file:
        if not os.path.exists(args.map_json_file):
            print_error(f"Error: JSON map file specified ('{args.map_json_file}') but not found.")
            return 1 # Exit with error
        try:
            with open(args.map_json_file, 'r') as f:
                active_rename_map = json.load(f)
            print(Colours.GREEN, f"Successfully loaded rename map from JSON file: {args.map_json_file}")
            map_source_description = f"JSON file '{args.map_json_file}'"
        except json.JSONDecodeError as e:
            print_error(f"Error decoding JSON from {args.map_json_file}: {e}")
            return 1 # Exit with error
        except Exception as e:
            print_error(f"Error reading JSON file {args.map_json_file}: {e}")
            return 1
    else:
        print_error("No rename map source specified. Exiting.")
        exit(0)

    if active_rename_map is None: # Indicates an error loading an explicitly specified map
        print_error("Failed to load rename map from the specified source. Exiting.")
        return 1 # Exit with error

    print(Colours.YELLOW, f"Using rename map from: {map_source_description}")
    if not active_rename_map: # If map is empty (e.g. empty db table, no cli args)
        print(Colours.YELLOW, "Warning: The rename map is empty. No renames will occur.")


    rename_subdirectories(args.target_directory, active_rename_map)
    return 0 # Success

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)