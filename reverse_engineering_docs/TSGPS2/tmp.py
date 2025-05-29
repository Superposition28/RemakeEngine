import struct
import io
import sys

def read_uint32_le(data_stream):
    """Reads a little-endian unsigned 32-bit integer."""
    # Ensure we have enough bytes before reading
    remaining_bytes = data_stream.getbuffer().nbytes - data_stream.tell()
    if remaining_bytes < 4:
        raise EOFError(f"Not enough data to read uint32_le. Need 4, have {remaining_bytes}")
    return struct.unpack('<I', data_stream.read(4))[0]

def read_uint16_le(data_stream):
    """Reads a little-endian unsigned 16-bit integer."""
    remaining_bytes = data_stream.getbuffer().nbytes - data_stream.tell()
    if remaining_bytes < 2:
        raise EOFError(f"Not enough data to read uint16_le. Need 2, have {remaining_bytes}")
    return struct.unpack('<H', data_stream.read(2))[0]

# No need for read_uint8 for the structure analysis steps below

def analyze_nonstandard_tim2(file_path):
    """
    Analyzes the nonstandard TIM2 file based on observed patterns,
    dynamically searching for the ASUR marker.

    Args:
        file_path: Path to the file to analyze.
    """
    try:
        with open(file_path, 'rb') as f:
            byte_data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    data_stream = io.BytesIO(byte_data)
    total_size = len(byte_data)

    print(f"Analyzing file: {file_path}")
    print(f"File size: {total_size} bytes")
    print("-" * 30)

    # --- Fixed-Layout Header Part 1 (0x00 - 0x7F) ---
    print("--- Fixed-Layout Header Part 1 (0x00 - 0x7F) ---")
    header_part1_end = 0x80
    try:
        if data_stream.tell() + header_part1_end > total_size + 1: # Check if header itself fits + 1 byte for next read position
             print(f"Error reading Fixed Header Part 1: File size {total_size} is too small for header ending at 0x{header_part1_end:04x}.")
             return

        # 0x00: TIM2 Signature
        current_offset = data_stream.tell()
        signature = data_stream.read(4)
        print(f"Offset 0x{current_offset:04x}: Signature: {signature.hex()} ({signature.decode('ascii', errors='ignore')})")
        if signature != b'TIM2':
            print("Warning: Signature is not standard TIM2 ('TIM2').")

        # 0x04: Field 1 (Version/Flags)
        current_offset = data_stream.tell()
        field1 = data_stream.read(4)
        print(f"Offset 0x{current_offset:04x}: Field 1 (Version/Flags?): {field1.hex()} (Raw bytes)")

        # 0x08 - 0x7F: Other fixed header bytes
        fixed_header_remainder_size = header_part1_end - data_stream.tell()
        if fixed_header_remainder_size > 0:
            current_offset = data_stream.tell()
            fixed_header_remainder = data_stream.read(fixed_header_remainder_size)
            print(f"Offset 0x{current_offset:04x}: Remaining Fixed Header (0x08-0x7F, {fixed_header_remainder_size} bytes): {fixed_header_remainder.hex()[:min(fixed_header_remainder_size*2, 128)]}...") # Print first 64 hex chars
        elif fixed_header_remainder_size < 0:
             # This shouldn't happen if the reads above are correct sizes, but as a safety check
             print(f"Warning: Read past expected end of Fixed Header Part 1 (0x{header_part1_end:04x}). Current pos: 0x{data_stream.tell():04x}")


    except EOFError as e:
        print(f"Error reading Fixed Header Part 1: {e}")
        return
    except Exception as e: # Catch other potential errors during header 1 read
        print(f"An unexpected error occurred during Fixed Header Part 1 analysis: {e}")
        return


    # --- Fixed-Layout Header Part 2 (0x80 - 0xAF assumed start) ---
    print("\n--- Fixed-Layout Header Part 2 (assumed start at 0x80) ---")
    # The stream should ideally be at 0x80 here if Header Part 1 read correctly
    expected_part2_start = 0x80
    if data_stream.tell() != expected_part2_start:
        print(f"Warning: Stream offset 0x{data_stream.tell():04x} is not at expected start of Fixed Header Part 2 (0x{expected_part2_start:04x}). Seeking.")
        data_stream.seek(expected_part2_start)

    header_part2_end_fixed = 0xB0 # The offset *after* the expected fixed Block A
    variable_block_a_size = 0xAF - 0x8C + 1 # 36 bytes

    # Variables to hold read data for summary
    field2 = field3 = field4 = None
    variable_block_a_data = b''

    try:
        # 0x80: Field 2 (Total Data Size after 0x80)
        current_offset = data_stream.tell()
        field2 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:04x}: Field 2 (Total Data Size after 0x80): {field2} (0x{field2:x})")
        # Note: Field 2 is the size *of the data starting at 0x80*. So total_size = 0x80 + field2
        if total_size != 0x80 + field2:
             print(f"Warning: Declared total size after 0x80 ({field2}) + 0x80 does not match actual file size ({total_size}).")


        # 0x84: Field 3 (Dim1?)
        current_offset = data_stream.tell()
        field3 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:04x}: Field 3 (Dim1?): {field3} (0x{field3:x}) (Variable)")

        # 0x88: Field 4 (Dim2?)
        current_offset = data_stream.tell()
        field4 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:04x}: Field 4 (Dim2?): {field4} (0x{field4:x}) (Variable)")

        # 0x8C - 0xAF: Variable Header Block A (36 bytes)
        current_offset = data_stream.tell()
        if current_offset + variable_block_a_size <= total_size:
             variable_block_a_data = data_stream.read(variable_block_a_size)
             print(f"Offset 0x{current_offset:04x}: Variable Header Block A (0x8C-0xAF, {variable_block_a_size} bytes): {variable_block_a_data.hex()} (Variable Content)")
        else:
             print(f"Offset 0x{current_offset:04x}: Not enough data for Variable Header Block A ({variable_block_a_size} bytes needed).")
             # Cannot continue robustly without this part based on the structure
             return

    except EOFError as e:
        print(f"Error reading Fixed-Layout Header Part 2: {e}")
        return
    except Exception as e: # Catch other potential errors during header 2 read
        print(f"An unexpected error occurred during Fixed Header Part 2 analysis: {e}")
        return

    # --- Search for ASUR Marker (starting after 0xAF) ---
    print("\n--- Searching for ASUR Marker ---")
    asur_signature = b'ASUR'
    # Start search from the position *after* reading Block A (should be 0xB0 if previous reads were perfect)
    search_start_offset_for_asur = data_stream.tell()
    asur_found_offset = -1
    max_asur_search_distance = 4096 # Search within the next 4KB, heuristic

    print(f"Starting search for '{asur_signature.decode('ascii', errors='ignore')}' from offset 0x{search_start_offset_for_asur:04x}...")

    search_buffer_size = min(total_size - search_start_offset_for_asur, max_asur_search_distance)

    if search_buffer_size > 0:
        # Read a buffer to search within, avoid reading the whole file if it's huge
        original_pos = data_stream.tell()
        search_buffer = data_stream.read(search_buffer_size)
        data_stream.seek(original_pos) # Restore position after reading buffer

        pattern_offset_in_buffer = search_buffer.find(asur_signature)

        if pattern_offset_in_buffer != -1:
            asur_found_offset = search_start_offset_for_asur + pattern_offset_in_buffer
            print(f"Found '{asur_signature.decode('ascii', errors='ignore')}' signature at offset 0x{asur_found_offset:04x}")

            # Report the block between end of Block A (0xAF) and ASUR
            unknown_block_size = asur_found_offset - data_stream.tell() # Size from current position to ASUR
            unknown_block_data = b'' # Initialize in case size is 0
            if unknown_block_size < 0: # Should not happen with correct seek/read, but for robustness
                 print(f"Error: Calculated unknown block size is negative ({unknown_block_size}). Something is wrong.")
                 unknown_block_size = 0 # Reset to 0 to prevent further issues
            if unknown_block_size > 0:
                current_offset = data_stream.tell()
                if current_offset != search_start_offset_for_asur: # Check if we are where we started the search
                     print(f"Warning: Stream not at expected offset 0x{search_start_offset_for_asur:04x} before reading unknown block. Seeking.")
                     data_stream.seek(search_start_offset_for_asur)
                     current_offset = data_stream.tell() # Update after seek
                try:
                    unknown_block_data = data_stream.read(unknown_block_size)
                    print(f"Offset 0x{current_offset:04x}: Unknown Variable Block ({unknown_block_size} bytes): {unknown_block_data.hex()[:min(unknown_block_size*2, 128)]}...") # Print first 64 hex chars
                except EOFError as e:
                    print(f"Error reading Unknown Variable Block: {e}")
                    return

            # Seek to ASUR and read it (data_stream is already at the start of the unknown block, read will advance it)
            current_offset = data_stream.tell() # Should be ASUR offset now
            asur_actual_read = data_stream.read(4) # Read the ASUR tag itself
            if asur_actual_read != asur_signature:
                 # This should not happen if find worked, but defensive check
                 print(f"Error: Read signature at 0x{current_offset:04x} does not match expected '{asur_signature.decode('ascii', errors='ignore')}'.")
            # Print confirmation of reading ASUR is already in the "Found" message

        else:
            print(f"'{asur_signature.decode('ascii', errors='ignore')}' signature not found within {search_buffer_size} bytes after offset 0x{search_start_offset_for_asur:04x}.")
            print("Cannot proceed with parsing structure based on ASUR.")
            return # Cannot parse further based on the assumed structure


    else:
        print(f"No data available to search for '{asur_signature.decode('ascii', errors='ignore')}' marker after offset 0x{search_start_offset_for_asur:04x}.")
        return


    # --- Variable Header Block B (assumed to follow ASUR, 28 bytes) ---
    print("\n--- Variable Header Block B (assumed after ASUR) ---")
    variable_block_b_size = 28 # Based on original script's assumed 0xB4-0xCF size
    start_offset_block_b = data_stream.tell() # Should be ASUR_offset + 4

    variable_block_b_data = b'' # Initialize
    if start_offset_block_b + variable_block_b_size <= total_size:
        try:
            current_offset = data_stream.tell()
            variable_block_b_data = data_stream.read(variable_block_b_size)
            print(f"Offset 0x{current_offset:04x}: Variable Header Block B (from 0x{start_offset_block_b:04x}, {variable_block_b_size} bytes): {variable_block_b_data.hex()} (Variable Content)")
        except EOFError as e:
             print(f"Error reading Variable Header Block B: {e}")
             return
    else:
        print(f"Offset 0x{start_offset_block_b:04x}: Not enough data for Variable Header Block B ({variable_block_b_size} bytes needed).")
        # Cannot reliably parse structured list or raw data based on this structure if Block B is truncated
        return


    # --- Variable Header Block C (End of Block B to Start of Structured List) ---
    # Find the start of the structured list by searching for the pattern marker
    print("\n--- Variable Header Block C (End of Block B to Start of Structured List) ---")
    pattern_signature = b'\x16\x00' # Little-endian 0x0016 (a common Value seen at list start)
    # Start search from the position *after* reading Block B
    search_start_offset_for_pattern = data_stream.tell()
    structured_data_start_offset = total_size # Default to end of file if not found
    max_pattern_search_distance = 4096 # Search within the next 4KB, heuristic

    print(f"Starting search for list pattern (b'\\x16\\x00') from offset 0x{search_start_offset_for_pattern:04x}...")

    search_buffer_size = min(total_size - search_start_offset_for_pattern, max_pattern_search_distance)

    if search_buffer_size > 0:
        # Read a buffer to search within
        original_pos = data_stream.tell()
        search_buffer = data_stream.read(search_buffer_size)
        data_stream.seek(original_pos) # Restore position

        pattern_offset_in_buffer = search_buffer.find(pattern_signature)

        if pattern_offset_in_buffer != -1:
            structured_data_start_offset = search_start_offset_for_pattern + pattern_offset_in_buffer
            print(f"Found structured data list pattern (b'\\x16\\x00') start at offset 0x{structured_data_start_offset:04x}")

            variable_block_c_size = structured_data_start_offset - search_start_offset_for_pattern
            if variable_block_c_size < 0: # Should not happen, but defensive
                 print(f"Error: Calculated Block C size is negative ({variable_block_c_size}). Resetting to 0.")
                 variable_block_c_size = 0
            if variable_block_c_size > 0:
                current_offset = data_stream.tell() # Should be search_start_offset_for_pattern
                if current_offset != search_start_offset_for_pattern:
                     print(f"Warning: Stream not at expected offset 0x{search_start_offset_for_pattern:04x} before reading Block C. Seeking.")
                     data_stream.seek(search_start_offset_for_pattern)
                     current_offset = data_stream.tell() # Update after seek
                try:
                    variable_block_c_data = data_stream.read(variable_block_c_size)
                    print(f"Offset 0x{current_offset:04x}: Variable Header Block C (0x{search_start_offset_for_pattern:04x}-0x{structured_data_start_offset-1:04x}, {variable_block_c_size} bytes): {variable_block_c_data.hex()[:min(variable_block_c_size*2, 128)]}...") # Print first 64 hex chars
                except EOFError as e:
                     print(f"Error reading Variable Header Block C: {e}")
                     return

            # Stream is now at structured_data_start_offset

        else:
            print(f"Structured data list pattern (b'\\x16\\x00') not found within {search_buffer_size} bytes after 0x{search_start_offset_for_pattern:04x}.")
            print("Assuming remaining data is Raw Data or part of Variable Block C.")
            # If pattern not found, Block C effectively extends to EOF, and there's no structured list as defined.
            structured_data_start_offset = total_size # Set to end of file so no list parsing happens
            # The stream position is still at search_start_offset_for_pattern

    else:
        print(f"No data available to search for structured list pattern after offset 0x{search_start_offset_for_pattern:04x}.")
        structured_data_start_offset = total_size # No data left, so no list


    # --- Structured Data List ---
    print("\n--- Structured Data List ---")
    # Set stream position to the start of the structured list (found dynamically or set to total_size)
    data_stream.seek(structured_data_start_offset)
    current_offset = data_stream.tell()
    list_struct_count = 0 # Count for the summary

    if current_offset < total_size:
        print(f"Parsing structured data list starting at offset 0x{current_offset:04x} (guessing repeating uint16 Value, uint16 Type):")
        print("(Note: The exact number of entries or end marker is unknown. Reading up to max_structs_to_read or EOF)")

        struct_size = 4 # Each structure is 4 bytes (uint16 Value, uint16 Type)
        max_structs_to_read = 2000 # Limit parsing to avoid infinite loops on bad data

        try:
            while data_stream.tell() + struct_size <= total_size and list_struct_count < max_structs_to_read:
                struct_offset = data_stream.tell()
                value = read_uint16_le(data_stream) # Likely a value/offset/length
                type_val = read_uint16_le(data_stream) # Likely a type/marker

                print(f"Offset 0x{struct_offset:04x}: Struct {list_struct_count+1}: Value={value} (0x{value:x}), Type={type_val} (0x{type_val:x})")

                list_struct_count += 1

            if list_struct_count == max_structs_to_read:
                print(f"(Max structures ({max_structs_to_read}) reached, stopping parsing of structured list)")
            elif data_stream.tell() < total_size:
                 print(f"(Reached end of file data or insufficient data for a full structure while reading structured list)")


        except EOFError as e:
             print(f"Could not read full structure at offset 0x{data_stream.tell():04x}. Data ended prematurely while reading structures? {e}")

    else:
        print(f"Offset 0x{current_offset:04x}: No data remaining for Structured Data List (pattern not found or file ended).")


    # --- Raw Data (Pixel/Palette/etc.) ---
    print("\n--- Raw Data (Pixel/Palette/etc.) ---")
    remaining_data_offset = data_stream.tell()
    remaining_data_size = total_size - remaining_data_offset

    print(f"Likely start of Raw Data at offset 0x{remaining_data_offset:04x}")
    print(f"Remaining Raw Data size: {remaining_data_size} bytes")

    # Optional: Dump a small part of the remaining data
    dump_size = min(remaining_data_size, 256) # Dump first 256 bytes
    if dump_size > 0:
        data_stream.seek(remaining_data_offset)
        try:
            remaining_bytes = data_stream.read(dump_size)
            print(f"First {dump_size} bytes of Raw Data: {remaining_bytes.hex()}")
            if remaining_data_size > dump_size:
                print("...")
        except EOFError:
            print("Could not read Raw Data.")


    print("-" * 30)
    print("Analysis complete.")
    print("\nSummary:")
    print(f"- Fixed Header Part 1 (0x0-0x7F)")
    # Assuming Field 2, 3, 4 were successfully read
    if field2 is not None: # Check if these were read successfully
        print(f"- Field 2 (0x80): Total Data Size after 0x80 ({field2})")
        print(f"- Field 3 & 4 (0x84, 0x88): Variable Dimensions/Counts ({field3}, {field4})")
        print(f"- Variable Header Block A (0x8C-0xAF, {variable_block_a_size} bytes)")

    if asur_found_offset != -1:
        unknown_block_size = asur_found_offset - search_start_offset_for_asur
        if unknown_block_size > 0:
             print(f"- Unknown Variable Block (0x{search_start_offset_for_asur:04x}-0x{asur_found_offset-1:04x}, {unknown_block_size} bytes) - BEFORE ASUR")
        print(f"- ASUR Marker found at 0x{asur_found_offset:04x}")

        if variable_block_b_data: # Check if Block B was successfully read
            print(f"- Variable Header Block B (from 0x{start_offset_block_b:04x}, {variable_block_b_size} bytes) - AFTER ASUR")

            if structured_data_start_offset != total_size: # Pattern was found
                variable_block_c_size = structured_data_start_offset - data_stream.tell() # Stream is at end of Block C if pattern found
                print(f"- Variable Header Block C (from 0x{start_offset_block_b + variable_block_b_size:04x} to 0x{structured_data_start_offset-1:04x}, {variable_block_c_size} bytes) - BEFORE Structured List")
                print(f"- Structured Data List (starts 0x{structured_data_start_offset:04x}, {list_struct_count} entries parsed)")
            else: # Pattern not found
                 variable_block_c_size_effective = total_size - data_stream.tell() # Stream is at end of Block B if pattern not found
                 print(f"- Variable Header Block C / Unknown Data (from 0x{search_start_offset_for_pattern:04x}, {variable_block_c_size_effective} bytes) - Pattern not found")

    else: # ASUR not found
         print(f"- ASUR marker not found after 0x{search_start_offset_for_asur:04x}. Structure after this point is unknown.")


    print(f"- Raw Data (starts 0x{remaining_data_offset:04x}, {remaining_data_size} bytes)")

    print("\nNext Steps for Reverse Engineering:")
    if asur_found_offset != -1 and structured_data_start_offset != total_size:
        print("1. Analyze the Value/Type pairs in the structured list:")
        print("   - Look for patterns where 'Value' might correspond to offsets or lengths within the 'Raw Data'.")
        print("   - Look for patterns where 'Type' might indicate pixel format (e.g., 4bpp, 8bpp, 16bpp, 32bpp), compression, or dimensions for individual image/palette chunks.")
        print("   - Pay attention to common Types (like 0x0, 0x16, 0x6666, 0x13, 0x26, 0x66).") # Added types seen in hex dumps
        print("2. Examine the 'Raw Data' based on the parsed structured list entries.")
        print("3. Try decoding small chunks of the Raw Data based on common PS2 image formats and palettes.")
    elif asur_found_offset != -1:
        print("1. The structure after Variable Block B is unclear as the expected list pattern was not found.")
        print("2. Examine the data starting from the end of Variable Block B (0x{search_start_offset_for_pattern:04x}) for other patterns.")
    else:
         print(f"1. The location of the ASUR marker and subsequent data structure is unknown.")
         print(f"2. Examine the data starting from 0x{search_start_offset_for_asur:04x} for other potential markers or structural clues.")


# --- Main Execution Block ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        analyze_nonstandard_tim2(file_path)
    else:
        print("Usage: python your_script_name.py <path_to_your_file>")
        print("Example: python analyze_tim2.py A:\\path\\to\\your\\file.tga")