import string
import os # Import the os module

allowed_chars = string.ascii_letters + string.digits + '_-.'

def extract_clean_strings_with_context(file_path, min_length=8, context_bytes=16):
    """
    Extracts clean strings and includes surrounding bytes for context.

    Args:
        file_path (str): The path to the binary file.
        min_length (int): The minimum length of strings to extract.
        context_bytes (int): The number of bytes to show before and after the string.

    Returns:
        list: A list of tuples containing (start_offset, string, context_before, context_after).
    """
    results = []
    current_string = b""
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

    for idx, byte in enumerate(data):
        if chr(byte) in allowed_chars:
            if start_offset is None:
                start_offset = idx
            current_string += bytes([byte])
        else:
            if len(current_string) >= min_length:
                # Get context bytes
                context_start = max(0, start_offset - context_bytes)
                context_end = min(len(data), idx + context_bytes) # Use current index 'idx' as the end of the string was before this byte
                
                context_before = data[context_start:start_offset]
                context_after = data[idx:min(len(data), idx + context_bytes)]


                results.append((start_offset, current_string.decode('ascii'), context_before, context_after))

            current_string = b""
            start_offset = None

    # Handle case where file ends with a valid string
    if len(current_string) >= min_length:
        context_start = max(0, start_offset - context_bytes)
        context_before = data[context_start:start_offset]
        # No context_after in this case as the string goes to the end of the file
        results.append((start_offset, current_string.decode('ascii'), context_before, b""))


    return results

# Usage
file_to_analyze = 'lodmodel1.rws.PS3.preinstanced'
context_size = 16 # Number of bytes before and after to show

results = extract_clean_strings_with_context(file_to_analyze, context_bytes=context_size)

if results:
    print(f"Found {len(results)} strings meeting the criteria with {context_size} bytes of context:")
    for offset, string, context_before, context_after in results:
        print(f"Offset {offset:08X}: {string}")
        print(f"  Before : {context_before.hex()}")
        print(f"  After  : {context_after.hex()}")
        print("-" * 20) # Separator for clarity
else:
    print(f"No strings meeting the criteria found in {file_to_analyze}.")