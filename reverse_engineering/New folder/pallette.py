import string
import os

def find_strings_with_keywords_and_context(file_path: str, keywords: list[str], min_length: int = 8, context_bytes: int = 16):
    """
    Searches a binary file for sequences of allowed characters (potential strings)
    that contain any of the specified keywords. Outputs the string and its
    surrounding bytes for context.

    Args:
        file_path (str): The path to the binary file.
        keywords (list[str]): A list of lowercase strings to search for within
                               extracted strings.
        min_length (int): The minimum length of an extracted string to consider.
        context_bytes (int): The number of bytes to show before and after the string.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
              'start_offset': The starting byte offset of the string.
              'end_offset': The ending byte offset of the string (exclusive).
              'string': The extracted string.
              'context_before': Bytes before the string (as hex string).
              'context_after': Bytes after the string (as hex string).
    """
    # Characters typically allowed in programmer-defined strings in binary data
    allowed_chars = string.ascii_letters + string.digits + '_-.'

    results = []
    current_string_bytes = b""
    start_offset = None

    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    data_len = len(data)

    for idx, byte in enumerate(data):
        char = chr(byte)

        if char in allowed_chars:
            if start_offset is None:
                start_offset = idx
            current_string_bytes += bytes([byte])
        else:
            # Non-allowed character encountered or end of data
            if current_string_bytes: # If we have accumulated bytes
                end_offset = idx # The string ends just before this non-allowed byte

                # Decode the accumulated bytes
                try:
                    current_string_text = current_string_bytes.decode('ascii')

                    # Check if the string meets criteria (min length and contains keyword)
                    if len(current_string_text) >= min_length and any(kw in current_string_text.lower() for kw in keywords):

                        # Extract context bytes
                        context_before_start = max(0, start_offset - context_bytes)
                        context_after_end = min(data_len, end_offset + context_bytes)

                        context_before = data[context_before_start : start_offset]
                        context_after = data[end_offset : context_after_end]

                        results.append({
                            'start_offset': start_offset,
                            'end_offset': end_offset,
                            'string': current_string_text,
                            'context_before': context_before.hex(),
                            'context_after': context_after.hex()
                        })

                except UnicodeDecodeError:
                    # This block handles cases where the accumulated bytes
                    # could not be decoded as ASCII. We'll skip these as
                    # they aren't valid ASCII strings.
                    pass
                except Exception as e:
                    print(f"Error processing string at offset {start_offset:08X}: {e}")


                # Reset for the next potential string
                current_string_bytes = b""
                start_offset = None

    # Handle case where the file ends with a valid string
    if current_string_bytes:
        end_offset = data_len
        try:
            current_string_text = current_string_bytes.decode('ascii')
            if len(current_string_text) >= min_length and any(kw in current_string_text.lower() for kw in keywords):
                context_before_start = max(0, start_offset - context_bytes)
                context_before = data[context_before_start : start_offset]
                # No context_after in this case as the string goes to the end
                results.append({
                    'start_offset': start_offset,
                    'end_offset': end_offset,
                    'string': current_string_text,
                    'context_before': context_before.hex(),
                    'context_after': "" # Empty context after
                })
        except UnicodeDecodeError:
             pass # Skip if not valid ASCII

    return results

# --- Usage ---

file_to_analyze = 'lodmodel1.rws.PS3.preinstanced'
# Replace with the path to your second larger file for testing
second_file_to_check = 'lisa_hog.dff.PS3.preinstanced'
# Add the path to your third file here
third_file_to_check = 'prop_lodmodel1.rws.PS3.preinstanced'

keywords_to_find = ["simp"] # Keywords to look for (case-insensitive check)
min_string_length = 4 # Minimum length of the string
context_size = 16 # Number of bytes before and after to show
max_duplicate_prints = 5 # Allow each unique string to be printed up to this many times

print(f"Searching for strings containing {keywords_to_find} in {file_to_analyze}...")
found_strings_with_context = find_strings_with_keywords_and_context(
    file_to_analyze,
    keywords_to_find,
    min_length=min_string_length,
    context_bytes=context_size
)

if found_strings_with_context:
    print(f"Found {len(found_strings_with_context)} strings meeting the criteria (allowing up to {max_duplicate_prints} prints per unique string):")
    printed_string_counts = {} # Keep track of printed string counts
    printed_count = 0
    for item in found_strings_with_context:
        current_string = item['string']
        current_count = printed_string_counts.get(current_string, 0)
        if current_count < max_duplicate_prints:
            print(f"Offset {item['start_offset']:08X} - {item['end_offset']:08X}: {current_string} (Print #{current_count + 1})")
            print(f"  Before: {item['context_before']}")
            print(f"  After : {item['context_after']}")
            print("-" * 30) # Separator for clarity
            printed_string_counts[current_string] = current_count + 1
            printed_count += 1
    print(f"Total strings printed: {printed_count}")
    print(f"Total unique strings found: {len(printed_string_counts)}")
else:
    print(f"No strings containing {keywords_to_find} meeting the criteria found in {file_to_analyze}.")

print("\n" + "="*40 + "\n") # Separator

# Uncomment the following block to test with your second file
print(f"Searching for strings containing {keywords_to_find} in {second_file_to_check}...")
found_strings_second_file = find_strings_with_keywords_and_context(
    second_file_to_check,
    keywords_to_find,
    min_length=min_string_length,
    context_bytes=context_size
)

if found_strings_second_file:
    print(f"Found {len(found_strings_second_file)} strings meeting the criteria in the second file (allowing up to {max_duplicate_prints} prints per unique string):")
    printed_string_counts_second = {} # Keep track for the second file
    printed_count_second = 0
    for item in found_strings_second_file:
        current_string = item['string']
        current_count = printed_string_counts_second.get(current_string, 0)
        if current_count < max_duplicate_prints:
            print(f"Offset {item['start_offset']:08X} - {item['end_offset']:08X}: {current_string} (Print #{current_count + 1})")
            print(f"  Before: {item['context_before']}")
            print(f"  After : {item['context_after']}")
            print("-" * 30) # Separator for clarity
            printed_string_counts_second[current_string] = current_count + 1
            printed_count_second += 1
    print(f"Total strings printed in second file: {printed_count_second}")
    print(f"Total unique strings found in second file: {len(printed_string_counts_second)}")
else:
    print(f"No strings containing {keywords_to_find} meeting the criteria found in the second file.")

print("\n" + "="*40 + "\n") # Separator

# --- Analysis for the third file ---
print(f"Searching for strings containing {keywords_to_find} in {third_file_to_check}...")
found_strings_third_file = find_strings_with_keywords_and_context(
    third_file_to_check,
    keywords_to_find,
    min_length=min_string_length,
    context_bytes=context_size
)

if found_strings_third_file:
    print(f"Found {len(found_strings_third_file)} strings meeting the criteria in the third file (allowing up to {max_duplicate_prints} prints per unique string):")
    printed_string_counts_third = {} # Keep track for the third file
    printed_count_third = 0
    for item in found_strings_third_file:
        current_string = item['string']
        current_count = printed_string_counts_third.get(current_string, 0)
        if current_count < max_duplicate_prints:
            print(f"Offset {item['start_offset']:08X} - {item['end_offset']:08X}: {current_string} (Print #{current_count + 1})")
            print(f"  Before: {item['context_before']}")
            print(f"  After : {item['context_after']}")
            print("-" * 30) # Separator for clarity
            printed_string_counts_third[current_string] = current_count + 1
            printed_count_third += 1
    print(f"Total strings printed in third file: {printed_count_third}")
    print(f"Total unique strings found in third file: {len(printed_string_counts_third)}")
else:
    print(f"No strings containing {keywords_to_find} meeting the criteria found in the third file.")

