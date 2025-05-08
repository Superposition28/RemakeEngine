import os
import hashlib
import sqlite3
import json

DB_PATH = "RemakeRegistry/asset_registry.db"

def init_db():
    """Initializes the SQLite database and table if not exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asset_registry (
        uuid TEXT PRIMARY KEY,
        sourceFileName TEXT,
        sourcePath TEXT,
        fileHash TEXT,
        pathNameHashMD5 TEXT,
        assetType TEXT,
        stages TEXT,
        lastUpdated TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_entry(entry, asset_type):
    """Inserts or replaces an asset entry into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO asset_registry 
        (uuid, sourceFileName, sourcePath, fileHash, pathNameHashMD5, assetType, stages, lastUpdated)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        entry["uuid"],
        entry["sourceFileName"],
        entry["sourcePath"],
        entry["fileHash"],
        entry["pathNameHashMD5"],
        asset_type,
        json.dumps(entry["stages"])
    ))
    conn.commit()
    conn.close()

def predict_converted_path(source_path, asset_type, stage, source_name):
    source_dir, filename = os.path.split(source_path)
    name, ext = os.path.splitext(filename)

    if asset_type == "models":
        if stage == ".preinstanced":
            return source_path
        elif stage == ".blend":
            return os.path.join(r"Modules\Model\GameFiles\blend_out", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\quickbms_out"), f"{name}.blend")
        elif stage == ".glb":
            return os.path.join(r"Modules\Model\GameFiles\blend_out_glb", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\quickbms_out"), f"{name}.glb")
        elif stage == ".fbx":
            return os.path.join(r"Modules\Model\GameFiles\blend_out_fbx", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\quickbms_out"), f"{name}.fbx")
    elif asset_type == "textures":
        if stage == ".txd":
            return os.path.join(source_dir, f"{name}.txd_files")
        elif stage == ".txd_directory":
            return os.path.join(r"Modules\Extract\GameFiles\quickbms_out", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\quickbms_out"), f"{name}")
        elif stage == ".png_directory":
            return os.path.join(r"Modules\Texture\GameFiles\Textures_out", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\quickbms_out"), f"{name}.txd_files")
    elif asset_type == "audio":
        if stage == ".wav":
            return os.path.join(r"Modules\Audio\GameFiles", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\USRDIR"), f"{name}.wav")
    elif asset_type == "video":
        if stage == ".ogv":
            return os.path.join(r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Video\GameFiles\Assets_1_Video_Movies", os.path.relpath(source_dir, r"Modules\Extract\GameFiles\USRDIR"), f"{name}.ogv")
    return None

def scan_directories(directories):
    for directory in directories:
        print(f"Scanning directory: {directory}")
        for root, _, files in os.walk(directory):
            print(f"Processing directory: {root}")
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "rb") as f:
                        file_hash_full = hashlib.sha256()
                        while chunk := f.read(4096):
                            file_hash_full.update(chunk)
                    file_hash = file_hash_full.hexdigest()
                    relative_path = os.path.relpath(file_path, os.getcwd())
                    path_name_hash_md5 = hashlib.md5(relative_path.encode()).hexdigest()
                    uuid = f"{file_hash[:16]}_{path_name_hash_md5[:16]}"
                    entry = {
                        "uuid": uuid,
                        "sourceFileName": filename,
                        "sourcePath": relative_path,
                        "fileHash": file_hash,
                        "pathNameHashMD5": path_name_hash_md5,
                        "stages": {}
                    }

                    asset_type = "unknown"
                    current_stage = None
                    source_name = os.path.splitext(filename)[0]

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
                        continue

                    entry["stages"][current_stage] = {"path": relative_path}

                    # Predict stages
                    if asset_type == "models":
                        for stage in [".blend", ".glb", ".fbx"]:
                            path = predict_converted_path(relative_path, "models", stage, source_name)
                            if path:
                                entry["stages"][stage] = {"path": path}
                    elif asset_type == "textures":
                        for stage in [".txd_directory", ".png_directory"]:
                            path = predict_converted_path(relative_path, "textures", stage, source_name)
                            if path:
                                entry["stages"][stage] = {"path": path}
                    elif asset_type == "audio":
                        path = predict_converted_path(relative_path, "audio", ".wav", source_name)
                        if path:
                            entry["stages"][".wav"] = {"path": path}
                    elif asset_type == "video":
                        path = predict_converted_path(relative_path, "video", ".ogv", source_name)
                        if path:
                            entry["stages"][".ogv"] = {"path": path}

                    insert_entry(entry, asset_type)

                except Exception as e:
                    print(f"Error processing file: {file_path} - {e}")

if __name__ == "__main__":
    init_db()
    directories_to_scan = [
        "Modules\\Extract\\GameFiles\\quickbms_out",
        "Source\\USRDIR\\Assets_1_Audio_Streams\\EN",
        "Source\\USRDIR\\Assets_1_Audio_Streams\\Global",
        "Source\\USRDIR\\Assets_1_Video_Movies\\en",
        "Source\\USRDIR\\Assets_1_Video_Movies\\sf",
    ]
    scan_directories(directories_to_scan)
    print("Database asset registry updated.")
