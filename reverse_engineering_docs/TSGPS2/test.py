import struct
import io
import sys

def read_uint32_le(data_stream):
    """Reads a little-endian unsigned 32-bit integer."""
    # Ensure we have enough bytes before reading
    if data_stream.tell() + 4 > data_stream.getbuffer().nbytes:
        raise EOFError("Not enough data to read uint32_le")
    return struct.unpack('<I', data_stream.read(4))[0]

def read_uint16_le(data_stream):
    """Reads a little-endian unsigned 16-bit integer."""
    if data_stream.tell() + 2 > data_stream.getbuffer().nbytes:
        raise EOFError("Not enough data to read uint16_le")
    return struct.unpack('<H', data_stream.read(2))[0]

def read_uint8(data_stream):
    """Reads an unsigned 8-bit integer (byte)."""
    if data_stream.tell() + 1 > data_stream.getbuffer().nbytes:
         raise EOFError("Not enough data to read uint8")
    return struct.unpack('<B', data_stream.read(1))[0]

def analyze_nonstandard_tim2_from_bytes(byte_data):
    """
    Attempts to analyze the nonstandard TIM2 byte data.

    Args:
        byte_data: A bytes object containing the file's data.
    """
    data_stream = io.BytesIO(byte_data)
    total_size = len(byte_data)

    print(f"Analyzing data stream of size: {total_size} bytes")
    print("-" * 30)

    # --- Check Signature ---
    current_offset = data_stream.tell()
    try:
        signature = data_stream.read(4)
        print(f"Offset 0x{current_offset:x}: Signature: {signature.hex()} ({signature.decode('ascii', errors='ignore')})")

        if signature != b'TIM2':
            print("Warning: Signature is not standard TIM2 ('TIM2'). Analysis might be inaccurate.")
            # Continue anyway, as it's nonstandard
            # return # Uncomment to stop if not TIM2

    except EOFError:
        print(f"Offset 0x{current_offset:x}: Not enough data for signature.")
        return


    # --- Attempt to Parse Initial Header Fields ---
    # Based on typical TIM2 structure and observation
    print("\nAttempting to parse initial header fields:")

    try:
        # Field 1: Likely version/flags (4 bytes after signature)
        current_offset = data_stream.tell()
        field1 = data_stream.read(4)
        print(f"Offset 0x{current_offset:x}: Field 1 (Version/Flags?): {field1.hex()} (Raw bytes)")

        # Skip a large block of zeros / reserved space based on offset 0x80
        expected_next_offset = 0x80
        if data_stream.tell() < expected_next_offset:
             skip_bytes = expected_next_offset - data_stream.tell()
             if data_stream.tell() + skip_bytes <= total_size:
                skipped_data = data_stream.read(skip_bytes)
                # print(f"Offset 0x{current_offset+4:x}: Skipped {skip_bytes} bytes (mostly zeros: {skipped_data.hex()[:min(skipped_bytes, 16)]}...)") # Optional debug print
                current_offset = data_stream.tell()
             else:
                print(f"Offset 0x{data_stream.tell():x}: Not enough data to skip to 0x{expected_next_offset:x}. Skipping header fields.")
                return
        elif data_stream.tell() > expected_next_offset:
              print(f"Warning: Current offset {data_stream.tell():x} is past expected header offset {expected_next_offset:x}. Might have missed header fields.")
              data_stream.seek(expected_next_offset) # Attempt to recover
              current_offset = data_stream.tell()


        # Field 2: Likely Total Data Size (observed = total_size - 0x80)
        field2 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:x}: Field 2 (Data Size after 0x80?): {field2} (0x{field2:x}) (Matches total_size - 0x80)")
        current_offset = data_stream.tell()

        # Field 3: Potential Dimension 1 (e.g., Width) - observed variable
        field3 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:x}: Field 3 (Dim1?): {field3} (0x{field3:x}) (Variable)")
        current_offset = data_stream.tell()

        # Field 4: Potential Dimension 2 (e.g., Height) - observed variable
        field4 = read_uint32_le(data_stream)
        print(f"Offset 0x{current_offset:x}: Field 4 (Dim2?): {field4} (0x{field4:x}) (Variable)")
        current_offset = data_stream.tell()


        # Read remaining bytes up to expected ASUR start (0xb0)
        expected_asur_start = 0xb0
        if data_stream.tell() < expected_asur_start:
             remaining_header_bytes = expected_asur_start - data_stream.tell()
             if remaining_header_bytes > 0:
                 if data_stream.tell() + remaining_header_bytes <= total_size:
                     header_remainder = data_stream.read(remaining_header_bytes)
                     print(f"Offset 0x{current_offset:x}: Bytes before ASUR ({remaining_header_bytes} bytes): {header_remainder.hex()} (Raw bytes) (Variable)")
                     current_offset = data_stream.tell()
                 else:
                     print(f"Offset 0x{data_stream.tell():x}: Not enough data for bytes before ASUR.")
                     return

        elif data_stream.tell() > expected_asur_start:
              print(f"Warning: Current offset {data_stream.tell():x} is past expected ASUR offset {expected_asur_start:x}. Might have missed bytes.")
              data_stream.seek(expected_asur_start) # Attempt to recover
              current_offset = data_stream.tell()


    except EOFError as e:
        print(f"Error reading initial header fields: {e}")
        return


    # --- Search for "ASUR" Marker ---
    print("\nSearching for 'ASUR' marker...")
    asur_signature = b'ASUR'
    asur_offset = -1
    # Search from current position up to a reasonable limit
    search_start = data_stream.tell()
    search_limit = min(search_start + 128, total_size) # Search a reasonable range forward

    original_pos = data_stream.tell()
    if search_start < search_limit:
        data_stream.seek(search_start)
        search_data = data_stream.read(search_limit - search_start)
        data_stream.seek(original_pos) # Restore position

        asur_offset_in_search = search_data.find(asur_signature)

        if asur_offset_in_search != -1:
            asur_offset = search_start + asur_offset_in_search
            print(f"Found 'ASUR' marker at offset 0x{asur_offset:x}")
            data_stream.seek(asur_offset + len(asur_signature)) # Move past ASUR
            current_offset = data_stream.tell()

            # Read a few bytes immediately after ASUR, as they seem variable
            bytes_after_asur_count = 4 # Read 4 bytes for inspection
            if data_stream.tell() + bytes_after_asur_count <= total_size:
                 after_asur_bytes = data_stream.read(bytes_after_asur_count)
                 print(f"Offset 0x{current_offset:x}: Bytes immediately after ASUR ({bytes_after_asur_count} bytes): {after_asur_bytes.hex()} (Variable)")
                 current_offset = data_stream.tell()
            else:
                 print(f"Offset 0x{current_offset:x}: Not enough data immediately after ASUR.")

        else:
            print(" 'ASUR' marker not found within the expected range.")
            return # Stop if ASUR is critical for the format structure
    else:
         print("Search range for ASUR is invalid or too small.")
         return


    # --- Search for and Analyze Structured Data Pattern (uint16 Value, uint16 Type) ---
    # The start of the repeating (Value, Type) pattern varies. Search for b'\x16\x00'.
    print("\nSearching for the start of the structured data list (b'\\x16\\x00')...")

    pattern_search_start = data_stream.tell()
    pattern_signature = b'\x16\x00' # Little-endian 0x0016 (a common Value seen at list start)

    # Search from current position to end of file
    original_pos = data_stream.tell()
    structured_data_start_offset = -1

    if original_pos < total_size:
        data_stream.seek(original_pos)
        remaining_data_for_search = data_stream.read()
        data_stream.seek(original_pos) # Restore position

        pattern_offset_in_remaining = remaining_data_for_search.find(pattern_signature)

        if pattern_offset_in_remaining != -1:
            structured_data_start_offset = pattern_search_start + pattern_offset_in_remaining
            print(f"Found structured data list pattern (b'\\x16\\x00') start at offset 0x{structured_data_start_offset:x}")

            # Now parse the structured section from this dynamically found offset
            data_stream.seek(structured_data_start_offset)
            current_offset = data_stream.tell()

            print(f"\nParsing structured data list starting at offset 0x{structured_data_start_offset:x} (guessing repeating uint16 Value, uint16 Type):")
            print("(Note: The exact number of entries or end marker is unknown. Reading up to max_structs_to_read or EOF)")

            struct_size = 4 # Each structure is 4 bytes (uint16, uint16)
            max_structs_to_read = 1000 # Increase limit to read more if needed

            struct_count = 0
            try:
                while data_stream.tell() + struct_size <= total_size and struct_count < max_structs_to_read:
                    struct_offset = data_stream.tell()
                    value = read_uint16_le(data_stream) # Likely a value/offset/length
                    type_val = read_uint16_le(data_stream) # Likely a type/marker

                    print(f"Offset 0x{struct_offset:x}: Struct {struct_count+1}: Value={value} (0x{value:x}), Type={type_val} (0x{type_val:x})")

                    struct_count += 1

                if struct_count == max_structs_to_read:
                    print(f"(Max structures ({max_structs_to_read}) reached, stopping parsing of structured list)")


            except EOFError:
                 print(f"Could not read full structure at offset 0x{data_stream.tell():x}. Data ended prematurely while reading structures?")

        else:
            print("Structured data list pattern (b'\\x16\\x00') not found after ASUR. Cannot parse structured list.")

    else:
         print("Search range for structured data list pattern is invalid or too small.")


    # --- Indicate Remaining Data ---
    remaining_data_offset = data_stream.tell()
    remaining_data_size = total_size - remaining_data_offset
    print("-" * 30)
    print(f"\nLikely start of pixel/palette data (remaining data) at offset 0x{remaining_data_offset:x}")
    print(f"Remaining data size: {remaining_data_size} bytes")

    # Optional: Dump a small part of the remaining data
    dump_size = min(remaining_data_size, 128) # Dump first 128 bytes
    if dump_size > 0:
        data_stream.seek(remaining_data_offset)
        try:
            remaining_bytes = data_stream.read(dump_size)
            print(f"First {dump_size} bytes of remaining data: {remaining_bytes.hex()}")
            if remaining_data_size > dump_size:
                print("...")
        except EOFError:
             print("Could not read remaining data.")


    print("-" * 30)
    print("Analysis complete (based on observed patterns and guesses).")
    print("\nNext Steps for Reverse Engineering:")
    print("1. Analyze the Value/Type pairs in the structured list:")
    print("   - Look for patterns where 'Value' might correspond to offsets or lengths within the 'Remaining data'.")
    print("   - Look for patterns where 'Type' might indicate pixel format (e.g., 4bpp, 8bpp, 16bpp, 32bpp), compression, or dimensions for individual image/palette chunks.")
    print("2. Examine the 'Remaining data' based on the parsed structured list entries.")
    print("3. Try decoding small chunks of the remaining data based on common TIM2 pixel formats (even if the wrapper is nonstandard).")


# --- Main Execution Block ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            analyze_nonstandard_tim2_from_bytes(file_data)
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
        except Exception as e:
            print(f"An error occurred while reading or processing the file: {e}")
    else:
        print("Usage: python your_script_name.py <path_to_your_file>")
        print("Example: python analyze_tim2.py A:\\path\\to\\your\\file.tga")

