import os
import json

# Function to create key-value pairs from nested folder structure
def generate_key_value_pairs(path):
    # Get the directory name
    folder_name = os.path.basename(path)
    
    # Initialize the result dictionary with the directory name as both key and value
    result = {folder_name: folder_name}
    
    # List all items in the folder
    items = os.listdir(path)
    
    for item in items:
        item_path = os.path.join(path, item)
        
        # If the item is a directory, recurse into it and add it as a nested dictionary
        if os.path.isdir(item_path):
            result[item] = generate_key_value_pairs(item_path)
        else:
            # If it's a file, add the file name as value
            result[item] = item
    
    return result

# Function to initiate the process and save the result to a JSON file
def save_key_value_pairs(base_folder, output_filename="output.json"):
    # Generate the key-value pairs from the base folder
    key_value_pairs = generate_key_value_pairs(base_folder)
    
    # Save the result to a JSON file
    with open(output_filename, "w") as outfile:
        json.dump(key_value_pairs, outfile, indent=2)

    print(f"Key-value pairs saved to {output_filename}")

# Provide the base folder path where your folders are located
base_folder = r"Modules\Extract\GameFiles\quickbms_out\Map_3-01_LandOfChocolate"
save_key_value_pairs(base_folder)
