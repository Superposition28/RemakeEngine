import os
from collections import defaultdict

# Replace these with your actual folder paths
dirs = [
    r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\ES",
    r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\FR",
    r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\IT",
    r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\GameFiles\USRDIR\Assets_1_Audio_Streams\Main",
]

# Map to track where each folder name appears
folder_locations = defaultdict(set)

# Scan each directory
for i, base_dir in enumerate(dirs):
    for name in os.listdir(base_dir):
        full_path = os.path.join(base_dir, name)
        if os.path.isdir(full_path):
            folder_locations[name].add(i)

# Find folders that exist in only one directory
unique_folders = {
    name: list(locations)[0] for name, locations in folder_locations.items() if len(locations) == 1
}

# Output results
print("Folders unique to a single directory:\n")
for folder, dir_index in unique_folders.items():
    print(f"{folder} -> Only in {dirs[dir_index]}")
