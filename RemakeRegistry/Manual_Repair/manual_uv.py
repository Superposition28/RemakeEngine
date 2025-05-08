import os
import hashlib
import json

def hash_file_sha256(file_path):
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def hash_string_md5(string):
    """Compute MD5 hash of a string."""
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def main():
    uv_map_dir = input("Enter uv_map_dir: ").strip()
    asset_uuid = input("Enter asset_uuid: ").strip()

    metadata_file = os.path.join(uv_map_dir, "blend_metadata.json")
    buvd_path = os.path.join(uv_map_dir, "uv_export.buvd")

    # Check if files exist
    for file_path in [metadata_file, buvd_path]:
        if not os.path.isfile(file_path):
            print(f"Error: File not found - {file_path}")
            return

    # Hashes
    metadata_file_hash = hash_file_sha256(metadata_file)
    metadata_path_hash = hash_string_md5(metadata_file)

    buvd_file_hash = hash_file_sha256(buvd_path)
    buvd_path_hash = hash_string_md5(buvd_path)

    # uuid based on metadata_file's sha256 and path md5
    uuid = f"{metadata_file_hash[:16]}_{metadata_path_hash[:16]}"

    output = {
        "uuid": uuid,
        "uv_map_dir": uv_map_dir,
        "metadata_file": metadata_file,
        "metadata_file_hash": metadata_file_hash,
        "metadata_path_hash": metadata_path_hash,
        "buvd": {
            "path": buvd_path,
            "fileHashSHA256": buvd_file_hash,
            "pathNameHashMD5": buvd_path_hash
        },
        "asset_uuid": asset_uuid
    }

    print(json.dumps(output, indent=4))

if __name__ == "__main__":
    main()
