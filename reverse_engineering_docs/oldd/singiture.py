import string
import os
import struct # Needed for potential future parsing, not strictly needed for finding patterns

def log(message: str):
    """
    Simple logging function to print messages to the console and log.txt.
    """
    print(message)
    # Ensure the directory for the log file exists if necessary
    # log_dir = os.path.dirname("log.txt")
    # if log_dir and not os.path.exists(log_dir):
    #     os.makedirs(log_dir)
    try:
        with open("log.txt", "a") as log_file:
            log_file.write(message + "\n")
    except IOError as e:
        print(f"Error writing to log file: {e}")


# Characters typically allowed in programmer-defined strings
ALLOWED_CHARS = string.ascii_letters + string.digits + '_-.'
ALLOWED_CHARS_BYTES = ALLOWED_CHARS.encode('ascii') # Convert allowed chars to bytes

# Keep the find_strings_by_signature function as is
def find_strings_by_signature(file_path: str, signature: bytes, relative_string_offset: int, max_string_length: int, min_string_length: int, context_bytes: int, string_context_bytes: int):
    """
    Searches a binary file for a specific byte signature. If found, attempts to
    extract a string located at a fixed offset relative to the signature's start.
    Outputs the string and context around the signature and the string itself.
    ... (docstring remains the same) ...
    """
    results = []

    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        log(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        log(f"Error reading file: {e}")
        return []

    data_len = len(data)
    signature_len = len(signature)
    current_offset = 0

    log(f"Searching for fixed signature: {signature.hex()} in {file_path}...")

    while current_offset < data_len:
        # Search for the next occurrence of the signature
        signature_offset = data.find(signature, current_offset)

        if signature_offset == -1:
            # Signature not found further in the file
            break

        # Calculate the potential string start offset
        string_start_offset = signature_offset + relative_string_offset

        # Check if the potential string start is within file bounds
        # Also ensure there's enough data to potentially contain the string
        if string_start_offset < 0 or string_start_offset >= data_len:
             # log(f"Warning: Calculated string offset {string_start_offset:08X} for signature at {signature_offset:08X} is out of file bounds in {file_path}.") # Suppress frequent warning
             current_offset = signature_offset + signature_len
             continue


        # --- Attempt to extract string ---
        extracted_string_bytes = b""
        # Limit string search to not go past max_string_length OR file end
        string_search_end = min(data_len, string_start_offset + max_string_length)
        string_end_offset = string_start_offset # Initialize end offset to start

        # Ensure we don't read past the end of the file
        if string_start_offset < data_len:
            for i in range(string_start_offset, string_search_end):
                byte = data[i]
                if byte in ALLOWED_CHARS_BYTES:
                    extracted_string_bytes += bytes([byte])
                    string_end_offset = i + 1 # Update end offset (exclusive)
                else:
                    # Non-allowed character ends the string
                    break


        extracted_string_text = None
        is_valid_string = False
        string_context_before_data = None
        string_context_after_data = None


        if extracted_string_bytes:
            try:
                extracted_string_text = extracted_string_bytes.decode('ascii')
                if len(extracted_string_text) >= min_string_length:
                    is_valid_string = True
                    # --- Extract context bytes around the STRING ---
                    string_context_before_start = max(0, string_start_offset - string_context_bytes)
                    string_context_after_end = min(data_len, string_end_offset + string_context_bytes)
                    string_context_before_data = data[string_context_before_start : string_start_offset]
                    string_context_after_data = data[string_end_offset : string_context_after_end]

            except UnicodeDecodeError:
                 # log(f"Warning: UnicodeDecodeError at {string_start_offset:08X} in {file_path}.") # Suppress frequent warning
                 pass


        # --- Extract context bytes around the SIGNATURE ---
        context_before_start = max(0, signature_offset - context_bytes)
        context_after_end = min(data_len, signature_offset + signature_len + context_bytes)

        context_before_data = data[context_before_start : signature_offset]
        context_after_data = data[signature_offset + signature_len : context_after_end]

        results.append({
            'type': 'fixed_signature_string', # Indicate result type
            'file_path': file_path,
            'signature_offset': signature_offset,
            'signature': signature.hex(),
            'context_before': context_before_data.hex(),
            'context_after': context_after_data.hex(),
            'string_found': is_valid_string,
            'string_offset': string_start_offset if is_valid_string else None,
            'string': extracted_string_text if is_valid_string else None,
            'string_context_before': string_context_before_data.hex() if string_context_before_data is not None else None,
            'string_context_after': string_context_after_data.hex() if string_context_after_data is not None else None
        })

        # Continue search *after* the current signature occurrence
        current_offset = signature_offset + signature_len

    return results

# --- New function for detecting start-and-end patterns ---
def find_start_end_pattern(file_path: str, start_marker: bytes, end_marker: bytes, max_search_distance: int, context_bytes: int = 16):
    """
    Searches a binary file for a start marker, then searches for an end marker
    within a maximum distance after the start marker. Outputs the start and
    end offsets and context around the start marker.

    Args:
        file_path (str): The path to the binary file.
        start_marker (bytes): The byte sequence that starts the pattern.
        end_marker (bytes): The byte sequence that ends the pattern.
        max_search_distance (int): Maximum distance (in bytes) to search for the
                                     end_marker after the start_marker's beginning.
        context_bytes (int): The number of bytes to show before and after the START marker.

    Returns:
        list: A list of dictionaries for found patterns in this file, where each contains:
              'type': 'start_end_pattern'
              'file_path': The path of the file where the pattern was found.
              'start_offset': The starting byte offset of the start marker.
              'end_offset': The ending byte offset (exclusive) of the end marker.
              'start_marker': The start marker (as hex string).
              'end_marker': The end marker (as hex string).
              'context_before': Bytes before the start marker (as hex string).
              'context_after': Bytes after the start marker (as hex string).
              'pattern_length': The total length of the pattern from start marker start to end marker end.
    """
    results = []

    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        log(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        log(f"Error reading file: {e}")
        return []

    data_len = len(data)
    start_marker_len = len(start_marker)
    end_marker_len = len(end_marker)
    current_offset = 0

    log(f"Searching for start-end pattern: Start={start_marker.hex()}, End={end_marker.hex()} in {file_path} (max distance {max_search_distance})...")

    while current_offset < data_len:
        # Search for the next occurrence of the start marker
        start_offset = data.find(start_marker, current_offset)

        if start_offset == -1:
            # Start marker not found further in the file
            break

        # Define the search range for the end marker
        search_start = start_offset + start_marker_len
        search_end = min(data_len, start_offset + max_search_distance + start_marker_len) # Search up to max_search_distance *after* start marker *start*

        # Ensure search_start is not out of bounds
        if search_start >= data_len:
             current_offset = start_offset + start_marker_len # Move past the found start marker
             continue

        # Search for the end marker within the defined range
        end_offset_in_range = data.find(end_marker, search_start, search_end)


        if end_offset_in_range != -1:
            # End marker found! This is a complete pattern occurrence.
            pattern_end_exclusive = end_offset_in_range + end_marker_len
            pattern_length = pattern_end_exclusive - start_offset

            # Extract context bytes around the START marker
            context_before_start = max(0, start_offset - context_bytes)
            context_after_end = min(data_len, start_offset + start_marker_len + context_bytes) # Context after START marker

            context_before_data = data[context_before_start : start_offset]
            context_after_data = data[start_offset + start_marker_len : context_after_end]


            results.append({
                'type': 'start_end_pattern', # Indicate result type
                'file_path': file_path,
                'start_offset': start_offset,
                'end_offset': pattern_end_exclusive,
                'start_marker': start_marker.hex(),
                'end_marker': end_marker.hex(),
                'context_before': context_before_data.hex(),
                'context_after': context_after_data.hex(), # Context after the START marker
                'pattern_length': pattern_length
            })

            # Continue search for the *next* start marker *after* the end of the pattern found
            current_offset = pattern_end_exclusive
        else:
            # End marker not found within the distance. Move past the found start marker
            # and continue searching for the next potential start marker.
            current_offset = start_offset + start_marker_len

    return results


# --- Configuration ---

file_list = [
    'lodmodel1.rws.PS3.preinstanced',
    'lisa_hog.dff.PS3.preinstanced',
    'prop_lodmodel1.rws.PS3.preinstanced'
]

# IMPORTANT: You need to determine the correct signature bytes (as bytes)
# and the relative offset (in bytes) from the SIGNATURE START to the STRING START.
# Use your previous script's output and a hex editor to find these.

# Fixed Signatures to check (often indicate block headers)
fixed_signatures_to_check = [
    {'signature': bytes.fromhex('0211010002000000'), 'relative_string_offset': 16, 'description': 'String Block Header (General, 8 bytes)'},
    {'signature': bytes.fromhex('0211010002000000140000002d00021c'), 'relative_string_offset': 16, 'description': 'String Block Header (Subtype A, 16 bytes)'},
    {'signature': bytes.fromhex('0211010002000000180000002d00021c'), 'relative_string_offset': 16, 'description': 'String Block Header (Subtype B, 16 bytes) - Hypothesized'},
    {'signature': bytes.fromhex('905920010000803f0000803f0000803f'), 'relative_string_offset': 16, 'description': 'Another Block Type Header (16 bytes)'} # Corrected based on common 803f pattern, PLACEHOLDER: Verify exact bytes and offset
]

# Start-and-End Patterns to check (often indicate variable-length structures like chunks)
start_end_patterns_to_check = [
    {
        'start_marker': bytes.fromhex('33ea0000'),
        'end_marker': bytes.fromhex('2d00021c'),
        'max_search_distance': 512, # Maximum distance to search for the end marker
        'description': 'Mesh Chunk Header Pattern'
    }
    # Add other start-end patterns you identify here
]


# --- Analysis Settings ---
max_potential_string_length = 64 # Increased slightly, common string names can be longer
min_extracted_string_length = 4
context_size = 16 # Bytes around the SIGNATURE / START marker to show
string_context_size = 5 # Bytes around the STRING to show


# --- Perform Analysis ---

grand_all_results = [] # Combined list of all results (fixed signatures and start-end patterns)

log("Starting analysis across all files...")
log("-" * 40)
# Clear previous log content if running multiple times
if os.path.exists("log.txt"):
    try:
        os.remove("log.txt")
        log("Cleared previous log.txt")
    except Exception as e:
        log(f"Warning: Could not clear log.txt: {e}")


# Use dictionaries to track counts per pattern/signature type globally
fixed_signature_counts = {sig['signature'].hex(): {'description': sig['description'], 'total_occurrences': 0, 'total_strings': 0} for sig in fixed_signatures_to_check}
start_end_pattern_counts = {f"{pat['start_marker'].hex()}...{pat['end_marker'].hex()}": {'description': pat['description'], 'total_occurrences': 0} for pat in start_end_patterns_to_check}


for file_path in file_list:
    if not os.path.exists(file_path):
        log(f"\nSkipping file {file_path}: Not found.")
        continue

    log(f"\n--- Analyzing {file_path} ---")

    # --- Search for Fixed Signatures ---
    for sig_info in fixed_signatures_to_check:
        results_for_signature = find_strings_by_signature(
            file_path,
            sig_info['signature'],
            sig_info['relative_string_offset'],
            max_potential_string_length,
            min_extracted_string_length,
            context_size,
            string_context_size
        )
        grand_all_results.extend(results_for_signature)

        # Update global counters for this signature
        sig_hex = sig_info['signature'].hex()
        fixed_signature_counts[sig_hex]['total_occurrences'] += len(results_for_signature)
        fixed_signature_counts[sig_hex]['total_strings'] += sum(1 for item in results_for_signature if item['string_found'])


    # --- Search for Start-and-End Patterns ---
    for pattern_info in start_end_patterns_to_check:
        results_for_pattern = find_start_end_pattern(
            file_path,
            pattern_info['start_marker'],
            pattern_info['end_marker'],
            pattern_info['max_search_distance'],
            context_size # Use the same context size for now
        )
        grand_all_results.extend(results_for_pattern)

        # Update global counters for this pattern
        pattern_key = f"{pattern_info['start_marker'].hex()}...{pattern_info['end_marker'].hex()}"
        start_end_pattern_counts[pattern_key]['total_occurrences'] += len(results_for_pattern)


# --- Print Consolidated Results ---

log("\n\n" + "="*80)
log(" CONSOLIDATED ANALYSIS RESULTS")
log("="*80 + "\n")

log(f"Searched in {len(file_list)} file(s).")
log(f"Configured {len(fixed_signatures_to_check)} fixed signature(s) and {len(start_end_patterns_to_check)} start-end pattern(s).")

log("\n--- Fixed Signature Summary Across All Files ---")
grand_total_fixed_occurrences = 0
grand_total_fixed_strings = 0
for sig_hex, counts in fixed_signature_counts.items():
    log(f"Signature '{counts['description']}' ({sig_hex}):")
    log(f"  Total Occurrences Found: {counts['total_occurrences']}")
    log(f"  Total Valid Strings Found at Relative Offset: {counts['total_strings']}") # Offset is per-config, not in summary
    grand_total_fixed_occurrences += counts['total_occurrences']
    grand_total_fixed_strings += counts['total_strings']


log("\n--- Start-End Pattern Summary Across All Files ---")
grand_total_start_end_occurrences = 0
for pattern_key, counts in start_end_pattern_counts.items():
    start_hex, end_hex = pattern_key.split('...')
    log(f"Pattern '{counts['description']}' (Starts with {start_hex}, Ends with {end_hex}):")
    log(f"  Total Occurrences Found: {counts['total_occurrences']}")
    grand_total_start_end_occurrences += counts['total_occurrences']


log("\n--- Grand Totals ---")
log(f"Total Fixed Signature Occurrences (all types, all files): {grand_total_fixed_occurrences}")
log(f"Total Start-End Pattern Occurrences (all types, all files): {grand_total_start_end_occurrences}")
log(f"Total Valid Strings Found (associated with fixed signatures at relative offsets): {grand_total_fixed_strings}")


log("\n--- Detailed Match List ---")
if not grand_all_results:
    log("No matches found across any files for the configured patterns.")
else:
    # Optional: Sort results for easier viewing, e.g., by file then by offset
    # Sort by file path, then by offset (using the appropriate offset key for each type)
    grand_all_results.sort(key=lambda x: (x['file_path'], x['signature_offset'] if x['type'] == 'fixed_signature_string' else x['start_offset']))


    for i, item in enumerate(grand_all_results):
        log(f"\n--- Match {i+1} / {len(grand_all_results)} ---")
        log(f"  Type           : {item['type'].replace('_', ' ').title()}") # Nicer type name
        log(f"  File Path      : {item['file_path']}")

        if item['type'] == 'fixed_signature_string':
            log(f"  Signature Offset: {item['signature_offset']:08X}")
            log(f"  Signature       : {item['signature']}")
            log(f"  Context Before  : {item['context_before']}")
            log(f"  Context After   : {item['context_after']}") # Context after Signature
            if item['string_found']:
                log(f"  String Offset   : {item['string_offset']:08X}")
                log(f"  Found String    : {item['string_context_before']} | {item['string']} | {item['string_context_after']}") # Context around String
            else:
                # string_offset might be None if not valid, but signature_offset is always valid here
                log(f"  String Offset   : (Expected at {item['signature_offset'] + fixed_signatures_to_check[[s['signature'].hex() for s in fixed_signatures_to_check].index(item['signature'])]['relative_string_offset']:08X}, but no valid string found)")
                log("  Found String    : (No valid string found at relative offset)")

        elif item['type'] == 'start_end_pattern':
            log(f"  Pattern Start Offset: {item['start_offset']:08X}")
            log(f"  Pattern End Offset  : {item['end_offset']:08X}")
            log(f"  Pattern Length    : {item['pattern_length']}")
            log(f"  Start Marker      : {item['start_marker']}")
            log(f"  End Marker        : {item['end_marker']}")
            log(f"  Context Before    : {item['context_before']}") # Context before Start Marker
            log(f"  Context After     : {item['context_after']}") # Context after Start Marker

# --- Execute Analysis ---
log("-" * 40)
log("Configuration:")
log(f"Max String Length: {max_potential_string_length}")
log(f"Min String Length: {min_extracted_string_length}")
log(f"Signature/Start Context Size: {context_size}")
log(f"String Context Size: {string_context_size}")
for pattern_info in start_end_patterns_to_check:
    log(f"Mesh Chunk Pattern Search Max Distance: {pattern_info['max_search_distance']}")
log("-" * 40)


# Call the main analysis loop
# The logic is already structured above the print section

log("Analysis complete. Check the detailed match list and summaries.")
log("="*80)