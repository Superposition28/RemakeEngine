import os
import json
import hashlib

def generate_uuid_from_path(file_path):
    """Generates a UUID based on the path hash."""
    path_hash = hashlib.md5(file_path.encode()).hexdigest()
    return f"0000000000000000_{path_hash[:16]}" # Placeholder file hash

def generate_file_hash(file_path):
    """Generates the SHA256 hash of the file content."""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def generate_path_hash(file_path):
    """Generates the MD5 hash of the file path."""
    return hashlib.md5(file_path.encode()).hexdigest()

def create_texture_registry(asset_index_path="RemakeRegistry/asset_index.json", output_path="RemakeRegistry/texture_reg.json"):
    """
    Reads the asset_index.json, scans .png_directory entries, and creates texture_reg.json.
    """
    try:
        with open(asset_index_path, 'r') as f:
            asset_index = json.load(f)
    except FileNotFoundError:
        print(f"Error: {asset_index_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {asset_index_path}.")
        return

    textures = []
    for texture_entry in asset_index.get("textures", []):
        print(f"Processing texture entry: {texture_entry.get('uuid', 'Unknown')}")
        if ".txd" in texture_entry["stages"]:
            print(f"Found .txd stage for texture entry: {texture_entry.get('uuid', 'Unknown')}")
            txd_stage = texture_entry["stages"][".txd"]
            txd_path = txd_stage["path"]
            txd_uuid = texture_entry["uuid"]

            png_directory = texture_entry["stages"].get(".png_directory")
            if png_directory:
                print(f"Found .png_directory for texture entry: {texture_entry.get('uuid', 'Unknown')}")
                png_dir_path = png_directory["path"]
                if png_dir_path and os.path.isdir(png_dir_path):
                    print(f"Processing PNG directory: {png_dir_path}")
                    for filename in os.listdir(png_dir_path):
                        print(f"Processing file: {filename}")
                        if filename.lower().endswith(".png"):
                            print(f"Found PNG file: {filename}")
                            png_file_path = os.path.join(png_dir_path, filename)
                            relative_png_path = os.path.relpath(png_file_path, os.getcwd())
                            file_hash = generate_file_hash(png_file_path)
                            path_name_hash_md5 = generate_path_hash(relative_png_path)
                            png_uuid = f"{file_hash[:16]}_{path_name_hash_md5[:16]}" if file_hash else generate_uuid_from_path(relative_png_path)
                            textures_path = os.path.relpath(png_dir_path, os.path.join(os.getcwd(), "Modules", "Texture", "GameFiles", "Textures_out"))

                            textures.append({
                                "uuid": png_uuid, # uuid from the file hash and path hash
                                "filename": filename, # Original filename
                                "path": textures_path, # path with Modules\\Texture\\GameFiles\\Textures_out\\ removed
                                "sourcePath": relative_png_path, # Relative path to the PNG file
                                "fileHash": file_hash, # SHA256 hash of the file content
                                "pathNameHashMD5": path_name_hash_md5, # MD5 hash of the file path
                                "sourceDictinary": {
                                    "uuid": txd_uuid # UUID from the TXD entry
                                }
                            })
                else:
                    print(f"Warning: Predicted PNG directory '{png_dir_path}' for '{txd_path}' is not a valid directory.")
            else:
                print(f"Warning: No valid '.png_directory' found for '{txd_path}'.")

    output_data = {"textures": textures}
    try:
        with open(output_path, 'w') as outfile:
            json.dump(output_data, outfile, indent=4)
        print(f"Successfully created {output_path}")
        if len(textures) != 7318:
            print(f"Warning: Expected 7318 textures, but found {len(textures)}.")
        else:
            print(f"{len(textures)} texture entries found.")
    except IOError:
        print(f"Error: Could not write to {output_path}.")

if __name__ == "__main__":
    create_texture_registry()
