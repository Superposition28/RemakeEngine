import os
import csv
import hashlib

# Change this to your directory
root_dir = r"C:\path\to\your\directory"

# Output mapping file
output_csv = "file_mapping.csv"

def generate_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

file_map = []

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        full_path = os.path.join(dirpath, filename)
        # Use the full path as the unique identifier for hashing
        hash_input = full_path
        md5_hash = generate_md5(hash_input)
        file_map.append([full_path, filename, md5_hash])

# Write to CSV
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["full_path", "new_name", "md5"])
    writer.writerows(file_map)

print(f"Mapping with MD5 saved to: {output_csv}")
