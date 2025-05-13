
import json

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Utils')))
from printer import print, Colours, print_error, print_verbose, print_debug, printc

def main(project_dir, module_dir) -> None:

    # Load configuration from JSON file
    with open(os.path.join(project_dir, 'project.json'), 'r') as f:
        config = json.load(f)

    # Directory where the files are located
    strdirectory = config['Extract']['Directories']['StrDirectory']

    print(Colours.YELLOW, f"Processing directory: {strdirectory}")

    # Mapping of old names to new names
    rename_map = {
        "audiostreams": "Assets_1_Audio_Streams",
        "movies": "Assets_1_Video_Movies",
        "frontend": "Assets_2_Frontend",
        "simpsons_chars": "Assets_2_Characters_Simpsons",
        "spr_hub": "Map_3-00_SprHub",
        "loc": "Map_3-01_LandOfChocolate",
        "brt": "Map_3-02_BartmanBegins",
        "eighty_bites": "Map_3-03_HungryHungryHomer",
        "tree_hugger": "Map_3-04_TreeHugger",
        "mob_rules": "Map_3-05_MobRules",
        "cheater": "Map_3-06_EnterTheCheatrix",
        "dayofthedolphins": "Map_3-07_DayOfTheDolphin",
        "colossaldonut": "Map_3-08_TheColossalDonut",
        "dayspringfieldstoodstill": "Map_3-09_Invasion",
        "bargainbin": "Map_3-10_BargainBin",
        "gamehub": "Map_3-00_GameHub",
        "neverquest": "Map_3-11_NeverQuest",
        "grand_theft_scratchy": "Map_3-12_GrandTheftScratchy",
        "medal_of_homer": "Map_3-13_MedalOfHomer",
        "bigsuperhappy": "Map_3-14_BigSuperHappy",
        "rhymes": "Map_3-15_Rhymes",
        "meetthyplayer": "Map_3-16_MeetThyPlayer",
    }

    # Initialize counters for debugging
    total_items = 0
    renamed_items = 0
    skipped_items = 0

    # Get all directories in the directory
    for item in os.listdir(strdirectory):
        item_path = os.path.join(strdirectory, item)
        if os.path.isdir(item_path):
            total_items += 1
            #print(f"Processing item: {item}")

            # Check if the old name exists in the mapping
            if item in rename_map:
                new_name = rename_map[item]
                new_path = os.path.join(strdirectory, new_name)
                print(Colours.GRAY, f"Old path: {item_path}")
                print(Colours.GRAY, f"New path: {new_path}")

                # Perform the renaming
                os.rename(item_path, new_path)
                print(Colours.GREEN, f"Renamed '{item}' to '{new_name}'")
                renamed_items += 1
            else:
                print(Colours.CYAN, f"Skipped '{item}' - no matching key in rename map")
                skipped_items += 1

    # Log summary
    print(Colours.GREEN, f"Processing complete. Total items: {total_items}, Renamed: {renamed_items}, Skipped: {skipped_items}")

    # Output all variables for debugging
    #print("\n--- Debugging Outputs ---")
    #print(f"Directory: {strdirectory}")
    #print("Rename Map:")
    #for old_name, new_name in rename_map.items():
    #    print(f"  {old_name} = {new_name}")
    #print(f"Total Items Processed: {total_items}")
    #print(f"Items Renamed: {renamed_items}")
    #print(f"Items Skipped: {skipped_items}")
