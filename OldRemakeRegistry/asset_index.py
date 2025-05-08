import os
import json
import hashlib
import shutil  # For copying directories

def generate_uuid(file_path):
    """Generates a UUID based on the file hash and path hash."""
    with open(file_path, 'rb') as f:
        file_content = f.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
    path_hash = hashlib.md5(file_path.encode()).hexdigest()
    return f"{file_hash[:16]}_{path_hash[:16]}"

def predict_converted_path(source_path, asset_type, stage, source_name):
    """
    Predicts the path of a converted asset based on its source path, type, and stage.
    """
    source_dir, filename = os.path.split(source_path)
    name, ext = os.path.splitext(filename)

    if asset_type == "models":
        if stage == ".preinstanced":
            return source_path  # No change
        elif stage == ".blend":
            return os.path.join(r"Modules\Model\GameFiles\blend_out", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\QbmsOut"), f"{name}.blend")
        elif stage == ".glb":
            return os.path.join(r"Modules\Model\GameFiles\blend_out_glb", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\QbmsOut"), f"{name}.glb")
        elif stage == ".fbx":
            return os.path.join(r"Modules\Model\GameFiles\blend_out_fbx", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\QbmsOut"), f"{name}.fbx")
    elif asset_type == "textures":
        if stage == ".txd":
            # Create folder name based on the source TXD file
            return os.path.join(source_dir, f"{name}.txd_files")
        elif stage == ".txd_directory":
            return os.path.join(r"Modules\Extract\GameFiles\QbmsOut", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\QbmsOut"), f"{name}")
        elif stage == ".png_directory":
            return os.path.join(r"Modules\Texture\GameFiles\Textures_out", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\QbmsOut"), f"{name}.txd_files")

    elif asset_type == "audio":
        if stage == ".wav":
            return os.path.join(r"Modules\Audio\GameFiles", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\USRDIR"), f"{name}.wav")
    elif asset_type == "video":
        if stage == ".ogv":
            return os.path.join(r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Video\GameFiles\Assets_1_Video_Movies", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\USRDIR"), f"{name}.ogv")
    return None

def scan_directories(directories):
    """
    Scans the specified directories for source assets and generates the asset_index.json
    with predicted converted paths.

    Args:
        directories: A list of root directory paths to scan.
    """
    asset_index = {"models": [], "textures": [], "audio": [], "video": [], "unknown": []}

    for directory in directories:
        print(f"Scanning directory: {directory}")
        for root, _, files in os.walk(directory):
            print(f"Processing directory: {root}")
            for filename in files:
                #print(f"Processing file: {filename}")

                file_path = os.path.join(root, filename)
                try:
                    file_hash_full = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        while chunk := f.read(4096):
                            file_hash_full.update(chunk)
                    file_hash = file_hash_full.hexdigest()
                    relative_path = os.path.relpath(file_path, os.getcwd())
                    path_name_hash_md5 = hashlib.md5(relative_path.encode()).hexdigest()
                    uuid = f"{file_hash[:16]}_{path_name_hash_md5[:16]}"
                    entry = {
                        "uuid": uuid, # Unique identifier for the asset
                        "sourceFileName": filename, # Original file name
                        "sourcePath": relative_path, # Relative path from the current working directory
                        "fileHash": file_hash, # SHA256 hash of the file content
                        "pathNameHashMD5": path_name_hash_md5, # MD5 hash of the file relative path
                        "stages": {} # To track different stages of the asset
                    }

                    asset_type = "unknown"
                    current_stage = None
                    source_name = os.path.splitext(filename)[0] # Added source_name

                    if filename.lower().endswith(('.preinstanced')):
                        asset_type = "models"
                        current_stage = ".preinstanced"
                    elif filename.lower().endswith(('.txd')):
                        asset_type = "textures"
                        current_stage = ".txd"
                    elif filename.lower().endswith(('.snu')):
                        asset_type = "audio"
                        current_stage = ".snu"
                    elif filename.lower().endswith(('.vp6')):
                        asset_type = "video"
                        current_stage = ".vp6"
                    else:
                        #asset_index["unknown"].append(entry)
                        continue # Skip the rest of the processing for unknown files

                    entry["stages"][current_stage] = {"path": relative_path}

                    # Predict other stages
                    if asset_type == "models":
                        predicted_blend = predict_converted_path(relative_path, "models", ".blend", source_name)
                        if predicted_blend:
                            entry["stages"][".blend"] = {"path": predicted_blend}
                        predicted_glb = predict_converted_path(relative_path, "models", ".glb", source_name)
                        if predicted_glb:
                            entry["stages"][".glb"] = {"path": predicted_glb}
                        predicted_fbx = predict_converted_path(relative_path, "models", ".fbx", source_name)
                        if predicted_fbx:
                            entry["stages"][".fbx"] = {"path": predicted_fbx}
                    elif asset_type == "textures":
                        # example path, txd dir is the path where the txd file is located and png files are generated
                        # Modules\Extract\GameFiles\QbmsOut\Assets_2_Characters_Simpsons\GlobalFolder\chars\bart_bc0_grp0_ss1_h0_str\EU_EN\ASSET_RWS\Textures\bart_bc0_grp0_ss1_h0.txd_files
                        txd_dir = predict_converted_path(relative_path, "textures", ".txd", source_name)
                        if txd_dir:
                            entry["stages"][".txd_directory"] = {"path": txd_dir}
                        # example path, png dir is the path where the png files are moved to after extraction, maintaining the same structure as the txd dir after the 'QbmsOut\'
                        # Modules\Texture\GameFiles\Textures_out\Assets_2_Characters_Simpsons\GlobalFolder\chars\bart_bc0_grp0_ss1_h0_str\EU_EN\ASSET_RWS\Textures\bart_bc0_grp0_ss1_h0.txd_files
                        png_dir = predict_converted_path(relative_path, "textures", ".png_directory", source_name)
                        if png_dir:
                            entry["stages"][".png_directory"] = {"path": png_dir}
                    elif asset_type == "audio":
                        predicted_wav = predict_converted_path(relative_path, "audio", ".wav", source_name)
                        if predicted_wav:
                            entry["stages"][".wav"] = {"path": predicted_wav}
                    elif asset_type == "video":
                        predicted_ogv = predict_converted_path(relative_path, "video", ".ogv", source_name)
                        if predicted_ogv:
                            entry["stages"][".ogv"] = {"path": predicted_ogv}

                    asset_index[asset_type].append(entry)

                except Exception as e:
                    print(f"Error processing file: {file_path} - {e}")

    with open("RemakeRegistry/asset_index.json", "w") as f:
        json.dump(asset_index, f, indent=4)

if __name__ == "__main__":
    directories_to_scan = [
        r"Modules\Extract\GameFiles\QbmsOut",
        r"Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\EN",
        r"Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\Global",
        r"Modules\Extract\GameFiles\USRDIR\Assets_1_Video_Movies\en",
        r"Modules\Extract\GameFiles\USRDIR\Assets_1_Video_Movies\sf",
    ]

    scan_directories(directories_to_scan)
    print("Generated asset_index.json")