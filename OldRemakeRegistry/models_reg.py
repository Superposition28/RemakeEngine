import os
import json
import hashlib
import uuid
import time

def printc(message, color=None):
    """
    Simple color support for Windows/cmd using ANSI escape codes.
    Note: On Windows, you might need `os.system('color')` or `colorama` for full support in older terminals.
    Newer Windows Terminal supports ANSI codes by default.
    """
    colors = {
        'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'white': '\033[97m', 'darkcyan': '\033[36m', 'darkyellow': '\033[33m',
        'darkred': '\033[31m'
    }
    endc = '\033[0m'
    if color and color.lower() in colors:
        print(f"{colors[color.lower()]}{message}{endc}")
    else:
        print(message)

def generate_unique_id(main_uuid=None, preinstanced_uuid=None):
    """Generates a unique ID based on main and preinstanced UUIDs."""
    try:
        if main_uuid and preinstanced_uuid:
            # Use a consistent separator and length for reliability
            combined_string = f"{main_uuid[:20]}_{preinstanced_uuid[:20]}"
            printc(f"Generating unique ID: {combined_string} from main UUID: {main_uuid} and preinstanced UUID: {preinstanced_uuid}", color="cyan")
            return combined_string
        elif main_uuid:
             # Handle cases where preinstanced UUID might be missing but main UUID is present
             combined_string = f"{main_uuid[:20]}_no_preinstanced"
             printc(f"Generating unique ID: {combined_string} from main UUID: {main_uuid} (no preinstanced)", color="cyan")
             return combined_string
        else:
            printc(f"Failed to generate unique ID: main UUID is None", color="red")
            return None
    except Exception as e:
        printc(f"Error generating unique ID: {e}", color="red")
        return None

def calculate_file_hash(file_path):
    """Calculates the SHA256 hash of a file."""
    try:
        printc(f"Calculating SHA256 for: {file_path}", color="darkyellow")
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()
    except FileNotFoundError:
        printc(f"File not found for hash calculation: {file_path}", color="yellow")
        return None
    except Exception as e:
        printc(f"Error calculating file hash for {file_path}: {e}", color="red")
        return None

def calculate_path_hash(path):
    """Calculates the MD5 hash of a path string."""
    if path is None:
        return None
    printc(f"Calculating MD5 for path: {path}", color="darkyellow")
    return hashlib.md5(path.encode('utf-8')).hexdigest()

def process_model_entries(asset_index_path, uv_maps_path):
    """
    Reads the asset_index.json and uv_maps.json, processes model entries,
    generates IDs, and creates model_reg.json with UV map fixes applied
    based on matching entryid, main uuid, or stage uuids.
    """
    try:
        with open(asset_index_path, 'r', encoding='utf-8') as f:
            asset_index = json.load(f)
        printc(f"Successfully loaded {asset_index_path}", color="green")
    except FileNotFoundError:
        printc(f"Error: {asset_index_path} not found.", color="red")
        return
    except json.JSONDecodeError:
        printc(f"Error: Could not decode JSON from {asset_index_path}.", color="red")
        return
    except Exception as e:
        printc(f"An error occurred while loading {asset_index_path}: {e}", color="red")
        return

    uv_map_fixes = {}
    try:
        with open(uv_maps_path, 'r', encoding='utf-8') as f:
            uv_maps_data = json.load(f)
            # Populate uv_map_fixes dictionary with asset_uuid as key
            for uv_map in uv_maps_data.get("uv_maps", []):
                asset_uuid = uv_map.get("asset_uuid")
                if asset_uuid:
                    uv_map_fixes[asset_uuid] = {
                        "uv_map_uuid": uv_map.get("uuid"),
                        "fileHash": uv_map.get("json", {}).get("fileHashSHA256"),
                        "pathNameHashMD5": uv_map.get("json", {}).get("pathNameHashMD5"),
                        "sourcePath": uv_map.get("json", {}).get("path"),
                        "asset_uuid": asset_uuid,
                    }
            printc(f"Successfully loaded {uv_maps_path} with {len(uv_map_fixes)} fixes.", color="green")
    except FileNotFoundError:
        printc(f"Warning: {uv_maps_path} not found. UV map fixes will not be included.", color="yellow")
    except json.JSONDecodeError:
        printc(f"Error: Could not decode JSON from {uv_maps_path}.", color="red")
        # Continue processing without UV fixes
    except Exception as e:
        printc(f"An error occurred while loading {uv_maps_path}: {e}", color="red")
        # Continue processing without UV fixes

    printc("Processing model entries...", color="green")

    # Temporary storage for entries with generated IDs but without applied fixes
    processed_entries_temp = []
    stage_stats = {}

    model_entries = asset_index.get("models", [])

    for entry in model_entries:
        main_uuid = entry.get("uuid")
        source_path = entry.get("sourcePath")
        printc(f"Processing entry: {main_uuid or 'Unknown'} (Source: {source_path})", color="blue")

        model_reg_entry_temp = {
            "entryid": None, # Will be generated after stages
            "uuid": main_uuid,
            "sourcePath": source_path,
            "stages": {},
            "dependant_assets": {
                "textures": [
                    # Placeholder - actual texture dependency logic is not in provided code
                    {
                        "uuid": "placeholder",
                        "meshName": "placeholder"
                    }
                ]
            },
            "fixes": {
                "UV_Map": {
                    "fileHash": None,
                    "pathNameHashMD5": None,
                    "sourcePath": None
                }
            }
        }

        preinstanced_stage_uuid = None

        for stage, stage_data in entry.get("stages", {}).items():
            printc(f"Processing stage: {stage} for entry: {main_uuid or 'Unknown'}", color="darkcyan")
            stage_path = stage_data.get("path")
            # stage_uuid_from_index = stage_data.get("uuid") # This UUID from asset_index might not be the one we generate

            if stage_path:
                file_hash_SHA256 = calculate_file_hash(stage_path)
                path_name_hash_md5 = calculate_path_hash(stage_path)

                # Generate a consistent UUID based on content and path
                # Using first 16 chars of SHA256 and first 16 chars of MD5
                generated_stage_uuid = f"{file_hash_SHA256[:16] if file_hash_SHA256 else '0'*16}_{path_name_hash_md5[:16] if path_name_hash_md5 else '0'*16}"

                model_reg_entry_temp["stages"][stage] = {
                    "exists": os.path.exists(stage_path),
                    "uuid": generated_stage_uuid, # Use our generated UUID
                    "path": stage_path,
                    "fileHashSHA256": file_hash_SHA256,
                    "pathNameHashMD5": path_name_hash_md5
                }

                if stage == ".preinstanced":
                    preinstanced_stage_uuid = generated_stage_uuid

                stage_stats[stage] = stage_stats.get(stage, 0) + 1
            else:
                printc(f"Warning: stage path is None for stage '{stage}' in entry: {main_uuid or 'Unknown'}", color="yellow")
                # Add entry even if path is None, with exists: False
                path_name_hash_md5 = calculate_path_hash(stage_data.get("path"))
                generated_stage_uuid = f"{'0'*16}_{path_name_hash_md5[:16] if path_name_hash_md5 else '0'*16}"

                model_reg_entry_temp["stages"][stage] = {
                    "exists": False,
                    "uuid": generated_stage_uuid,
                    "path": stage_data.get("path"), # Keep the original potentially None path
                    "fileHashSHA256": None,
                    "pathNameHashMD5": path_name_hash_md5
                }
                if stage == ".preinstanced":
                    preinstanced_stage_uuid = generated_stage_uuid
                stage_stats[stage] = stage_stats.get(stage, 0) + 1


        # Generate entryid after stage UUIDs are determined
        model_reg_entry_temp["entryid"] = generate_unique_id(main_uuid, preinstanced_stage_uuid)
        printc(f"Generated entryid: {model_reg_entry_temp['entryid']} for entry: {main_uuid or 'Unknown'}", color="cyan")

        processed_entries_temp.append(model_reg_entry_temp)

    printc("Completed processing all entries. Applying UV map fixes...", color="green")

    # Now, iterate through the processed entries and apply UV map fixes
    model_registry = []
    uv_fixes_applied_count = 0

    for entry in processed_entries_temp:
        applied_fix = None

        # Prioritize lookup: entryid, then main uuid, then stage uuids
        entryid = entry.get("entryid")
        main_uuid = entry.get("uuid")

        if entryid and entryid in uv_map_fixes:
            applied_fix = uv_map_fixes[entryid]
            printc(f"UV Map fix applied via entryid: {entryid}", color="green")
        elif main_uuid and main_uuid in uv_map_fixes:
            applied_fix = uv_map_fixes[main_uuid]
            printc(f"UV Map fix applied via main uuid: {main_uuid}", color="green")
        else:
            for stage, stage_data in entry.get("stages", {}).items():
                stage_uuid = stage_data.get("uuid")
                if stage_uuid and stage_uuid in uv_map_fixes:
                    applied_fix = uv_map_fixes[stage_uuid]
                    printc(f"UV Map fix applied via stage '{stage}' uuid: {stage_uuid}", color="green")
                    break # Apply the first stage fix found and stop checking stages

        if applied_fix:
            entry["fixes"]["UV_Map"] = applied_fix
            uv_fixes_applied_count += 1
            printc(f"UV Map fix applied for entry: {entryid or main_uuid or 'Unknown'}", color="green")
        # else:
            #printc(f"No UV Map fix found for entry: {entryid or main_uuid or 'Unknown'}", color="yellow")


        model_registry.append(entry)

    printc(f"Total UV map fixes applied: {uv_fixes_applied_count}", color="green")
    printc("Completed applying UV map fixes.", color="green")

    output_dir = "RemakeRegistry"
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, "model_reg.json")
    try:
        with open(output_file_path, "w", encoding='utf-8') as outfile:
            json.dump(model_registry, outfile, indent=4)
        printc(f"Generated {output_file_path}", color="green")
    except IOError as e:
        printc(f"Error writing to {output_file_path}: {e}", color="red")


    printc("Stage statistics:", color="yellow")
    for stage, count in sorted(stage_stats.items()):
        printc(f"'{stage}': {count}", color="cyan")


if __name__ == "__main__":
    asset_index_file = "RemakeRegistry/asset_index.json"
    uv_maps_file = "RemakeRegistry/Manual_Repair/UV_Maps.json"

    process_model_entries(asset_index_file, uv_maps_file)