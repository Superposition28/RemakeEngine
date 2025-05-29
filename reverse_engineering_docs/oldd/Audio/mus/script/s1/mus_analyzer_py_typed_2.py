import os
import collections
from pathlib import Path
import statistics
import struct # For potential integer parsing

# --- Configuration ---
HEADER_SIZE = 16  # Bytes to read as the header
HEADER_TYPE1_SUFFIX = bytes.fromhex("78013200")
HEADER_TYPE2_SUFFIX = bytes.fromhex("02030203")
MIN_ZERO_BLOCK_SIZE = 4 # Lowered threshold slightly to catch smaller blocks potentially containing 0C 00 00 00
NON_ZERO_THRESHOLD = 0.1 # Example: If more than 10% of bytes in a 'zero-ish' block are non-zero, maybe treat it differently? (Not used in current logic, but placeholder)
# --- End Configuration ---

def analyze_byte_frequency(data):
  """Calculates the frequency of each byte in the data."""
  if not data:
    return collections.Counter()
  return collections.Counter(data)

def analyze_block_structure(data, min_zero_size):
  """
  Analyzes data for blocks: 'data', 'pure_zero', 'mixed_zero'.

  Returns:
      A dictionary containing lists of lengths and counts for each block type,
      and analysis of non-zero bytes within mixed_zero blocks.
  """
  blocks = []
  current_pos = 0
  if not data: # Handle empty data
      return {
          'data_block_lengths': [],
          'pure_zero_block_lengths': [],
          'mixed_zero_block_lengths': [],
          'mixed_zero_block_content': collections.Counter(), # Counts non-zero bytes found in mixed blocks
          'data_pure_zero_pairs_combined_lengths': [],
          'data_mixed_zero_pairs_combined_lengths': []
      }

  # Determine initial state carefully
  in_zeroish_block = data[0] == 0 # Start assuming zero if first byte is 0
  block_start = 0

  while current_pos < len(data):
    byte = data[current_pos]
    is_zero = (byte == 0)

    # --- State Change Detection ---
    # We are primarily interested in transitions *out* of a block type.
    # A block ends when the characteristic of the bytes changes.
    # For simplicity, let's define 'data' blocks as any sequence not starting with 0,
    # and 'zeroish' blocks as any sequence starting with 0.
    # We'll classify zeroish blocks later.

    current_block_is_zeroish = data[block_start] == 0

    # Detect end of a block: either byte zero-ness changes OR we hit the end
    end_of_block = False
    if current_pos > block_start: # Need at least one byte in the block
        # If current byte's zero-ness differs from the START byte's zero-ness,
        # it *might* be the end, but VBR data blocks can contain zeros.
        # A more robust (but complex) approach is needed for perfect VBR parsing.
        # Let's stick to a simpler definition for this analysis:
        # Data block = sequence of non-zero bytes.
        # Zero block = sequence of zero bytes.

        # Revised logic: Define blocks by contiguous identical zero-ness
        if is_zero != (data[current_pos-1] == 0):
             end_of_block = True


    # Process the completed block if we ended one OR hit the end of data
    if end_of_block or current_pos == len(data) -1 :
        # Adjust end position if we are at the very end of the data
        block_end_pos = current_pos if end_of_block else len(data)
        block_len = block_end_pos - block_start
        block_data = data[block_start:block_end_pos]

        if block_len > 0:
            # Was the completed block zero or non-zero? Check the byte *before* the current one
            # (or the start byte if it's the first block)
            block_was_zero = (data[block_end_pos-1] == 0)

            if block_was_zero:
                # It was a block of zeros, check length and purity
                if block_len >= min_zero_size:
                    is_pure = True
                    non_zeros_in_block = collections.Counter()
                    for b in block_data:
                        if b != 0:
                            is_pure = False
                            non_zeros_in_block[b] += 1

                    if is_pure:
                        blocks.append({'type': 'pure_zero', 'start': block_start, 'length': block_len})
                    else:
                        blocks.append({'type': 'mixed_zero', 'start': block_start, 'length': block_len, 'content': non_zeros_in_block})
                # else: Ignore short zero blocks
            else:
                # It was a block of non-zeros (data block)
                blocks.append({'type': 'data', 'start': block_start, 'length': block_len})

        # Start the next block
        block_start = block_end_pos

    current_pos += 1


  # --- Analyze the detected blocks ---
  analysis = {
      'data_block_lengths': [],
      'pure_zero_block_lengths': [],
      'mixed_zero_block_lengths': [],
      'mixed_zero_block_content': collections.Counter(), # Counts non-zero bytes found in mixed blocks
      'data_pure_zero_pairs_combined_lengths': [],
      'data_mixed_zero_pairs_combined_lengths': []
  }

  last_block_type = None
  last_block_len = 0

  for i in range(len(blocks)):
      block = blocks[i]
      block_type = block['type']
      block_len = block['length']

      if block_type == 'data':
          analysis['data_block_lengths'].append(block_len)
      elif block_type == 'pure_zero':
          analysis['pure_zero_block_lengths'].append(block_len)
          if last_block_type == 'data':
              analysis['data_pure_zero_pairs_combined_lengths'].append(last_block_len + block_len)
      elif block_type == 'mixed_zero':
          analysis['mixed_zero_block_lengths'].append(block_len)
          analysis['mixed_zero_block_content'].update(block['content'])
          if last_block_type == 'data':
               analysis['data_mixed_zero_pairs_combined_lengths'].append(last_block_len + block_len)

      last_block_type = block_type
      last_block_len = block_len

  return analysis


def parse_header_fields(header):
    """Parses known/suspected fields from the 16-byte header."""
    if len(header) < HEADER_SIZE:
        return None # Not enough data

    fields = {
        'signature_id': header[0:4],
        'field2_bytes': header[4:8],    # Bytes 4-7
        'field3_bytes': header[8:12],   # Bytes 8-11
        'suffix_bytes': header[12:16]   # Bytes 12-15
    }

    # Attempt to interpret fields as little-endian integers
    try:
        # '<I' is format code for little-endian unsigned int (4 bytes)
        fields['field2_int'] = struct.unpack('<I', fields['field2_bytes'])[0]
    except struct.error:
        fields['field2_int'] = None # Parsing failed

    try:
        fields['field3_int'] = struct.unpack('<I', fields['field3_bytes'])[0]
    except struct.error:
        fields['field3_int'] = None # Parsing failed

    return fields


def process_mus_file(filepath):
  """
  Reads a .mus file, parses header fields, determines type,
  and returns relevant data for combined analysis.

  Returns:
      A tuple: (header_fields_dict, file_data_bytes, file_type_str) or (None, None, None) on error.
  """
  print(f"\n--- Processing: {filepath.name} ---")
  file_type = "Unknown" # Default type
  header_fields = None
  try:
    with open(filepath, 'rb') as f:
      # Read header
      header_bytes = f.read(HEADER_SIZE)
      if not header_bytes:
        print("File is empty.")
        return None, None, None
      if len(header_bytes) < HEADER_SIZE:
          print(f"Warning: File is smaller than header size ({len(header_bytes)} bytes).")
          f.seek(0)
          file_data = f.read()
          print(f"Header ({len(header_bytes)} bytes): {header_bytes.hex(' ').upper()}")
          # Try partial parse if possible, otherwise return unknown
          header_fields = parse_header_fields(header_bytes + b'\x00' * (HEADER_SIZE - len(header_bytes))) # Pad for parsing attempt
          return header_fields, file_data, file_type

      print(f"Header ({HEADER_SIZE} bytes): {header_bytes.hex(' ').upper()}")
      header_fields = parse_header_fields(header_bytes)

      if not header_fields:
           print("Error parsing header fields.")
           return None, None, None

      print(f"  Signature/ID: {header_fields['signature_id'].hex(' ').upper()}")
      print(f"  Field 2 (Bytes 4-7): {header_fields['field2_bytes'].hex(' ').upper()} (Int: {header_fields['field2_int']})")
      print(f"  Field 3 (Bytes 8-11): {header_fields['field3_bytes'].hex(' ').upper()} (Int: {header_fields['field3_int']})")
      print(f"  Suffix (Bytes 12-15): {header_fields['suffix_bytes'].hex(' ').upper()}")

      # Determine file type based on header suffix
      if header_fields['suffix_bytes'] == HEADER_TYPE1_SUFFIX:
          file_type = "Type 1"
      elif header_fields['suffix_bytes'] == HEADER_TYPE2_SUFFIX:
          file_type = "Type 2"

      print(f"Detected Type: {file_type}")

      # Read the rest of the file for further analysis
      f.seek(0) # Reset file pointer
      file_data = f.read()
      return header_fields, file_data, file_type

  except FileNotFoundError:
    print(f"Error: File not found.")
    return None, None, None
  except Exception as e:
    print(f"An error occurred processing {filepath.name}: {e}")
    return None, None, None


def generate_type_report(file_type_name, type_data):
    """Generates the analysis report section for a specific file type."""
    print(f"\n--- Analysis for {file_type_name} ({type_data['count']} files, {type_data['total_bytes']:,} bytes) ---")

    # Type-Specific Header Field Values
    print("\nHeader Field Values Observed:")
    print("  Field 2 (Bytes 4-7):")
    for val_bytes, count in type_data['field2_values'].most_common(5):
        val_int = 'N/A'
        try:
             val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        except struct.error: pass
        print(f"    {val_bytes.hex(' ').upper():<12} (Int: {val_int}): {count} times")
    print("  Field 3 (Bytes 8-11):")
    for val_bytes, count in type_data['field3_values'].most_common(5):
        val_int = 'N/A'
        try:
            val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        except struct.error: pass
        print(f"    {val_bytes.hex(' ').upper():<12} (Int: {val_int}): {count} times")


    # Type-Specific Byte Frequency
    print("\nByte Frequency (Top 5):")
    if type_data['byte_counts']:
        # Ensure 0x00 is shown if present
        top_5 = type_data['byte_counts'].most_common(5)
        zero_present = any(byte_val == 0 for byte_val, count in top_5)
        total_type_bytes = type_data['total_bytes']

        for byte_val, count in top_5:
          percentage = (count / total_type_bytes) * 100 if total_type_bytes else 0
          print(f"  Byte 0x{byte_val:02X}: {count:,} times ({percentage:.2f}%)")

        if 0 in type_data['byte_counts'] and not zero_present:
             count = type_data['byte_counts'][0]
             percentage = (count / total_type_bytes) * 100 if total_type_bytes else 0
             print(f"  Byte 0x00: {count:,} times ({percentage:.2f}%)")
    else:
        print("  No byte data processed for this type.")

    # --- Type-Specific Block Structure ---
    print(f"\nBlock Structure Analysis (Min Zero Length: {MIN_ZERO_BLOCK_SIZE}):")

    # Data Blocks
    total_data_blocks = len(type_data['data_lengths'])
    if total_data_blocks > 0:
        avg_data_len = statistics.mean(type_data['data_lengths'])
        print(f"\n  Data Blocks: {total_data_blocks:,} found")
        print(f"    Min/Max/Avg length: {min(type_data['data_lengths'])} / {max(type_data['data_lengths'])} / {avg_data_len:.2f}")
    else:
        print("\n  Data Blocks: None found.")

    # Pure Zero Blocks
    total_pure_zero_blocks = len(type_data['pure_zero_lengths'])
    if total_pure_zero_blocks > 0:
        avg_pure_zero_len = statistics.mean(type_data['pure_zero_lengths'])
        print(f"\n  Pure Zero Blocks (Only 0x00): {total_pure_zero_blocks:,} found")
        print(f"    Min/Max/Avg length: {min(type_data['pure_zero_lengths'])} / {max(type_data['pure_zero_lengths'])} / {avg_pure_zero_len:.2f}")
    else:
        print("\n  Pure Zero Blocks: None found.")

    # Mixed Zero Blocks
    total_mixed_zero_blocks = len(type_data['mixed_zero_lengths'])
    if total_mixed_zero_blocks > 0:
        avg_mixed_zero_len = statistics.mean(type_data['mixed_zero_lengths'])
        print(f"\n  Mixed Zero Blocks (Mostly 0x00, with others): {total_mixed_zero_blocks:,} found")
        print(f"    Min/Max/Avg length: {min(type_data['mixed_zero_lengths'])} / {max(type_data['mixed_zero_lengths'])} / {avg_mixed_zero_len:.2f}")
        print(f"    Common non-zero bytes found within these blocks (Top 5):")
        for byte_val, count in type_data['mixed_zero_content'].most_common(5):
             print(f"      Byte 0x{byte_val:02X}: {count:,} occurrences")
    else:
        print("\n  Mixed Zero Blocks: None found.")

    # --- Combined Pair Analysis ---
    print("\nCombined Lengths for Data -> Zero Pairs:")

    # Data -> Pure Zero Pairs
    total_data_pure_pairs = len(type_data['data_pure_zero_pairs'])
    if total_data_pure_pairs > 0:
        print(f"\n  Data -> Pure Zero Pairs: {total_data_pure_pairs:,} found")
        pair_lengths_counter = collections.Counter(type_data['data_pure_zero_pairs'])
        print(f"    Common combined lengths (Top 5):")
        for length, count in pair_lengths_counter.most_common(5):
             percentage_of_pairs = (count/total_data_pure_pairs) * 100
             print(f"      Length {length}: {count:,} times ({percentage_of_pairs:.2f}% of these pairs)")
    else:
        print("\n  Data -> Pure Zero Pairs: None found.")

    # Data -> Mixed Zero Pairs
    total_data_mixed_pairs = len(type_data['data_mixed_zero_pairs'])
    if total_data_mixed_pairs > 0:
        print(f"\n  Data -> Mixed Zero Pairs: {total_data_mixed_pairs:,} found")
        pair_lengths_counter = collections.Counter(type_data['data_mixed_zero_pairs'])
        print(f"    Common combined lengths (Top 5):")
        for length, count in pair_lengths_counter.most_common(5):
             percentage_of_pairs = (count/total_data_mixed_pairs) * 100
             print(f"      Length {length}: {count:,} times ({percentage_of_pairs:.2f}% of these pairs)")
    else:
        print("\n  Data -> Mixed Zero Pairs: None found.")


if __name__ == "__main__":
  script_dir = Path(__file__).parent
  print(f"Looking for .mus files in: {script_dir}")

  mus_files = sorted(list(script_dir.glob('*.mus'))) # Sort for consistent order

  if not mus_files:
    print("No .mus files found in this directory.")
  else:
    print(f"Found {len(mus_files)} .mus files.")

    # Initialize combined analysis structures PER TYPE
    # Using defaultdict for simpler aggregation
    analysis_by_type = {
        "Type 1": collections.defaultdict(lambda: 0), # Use 0 for counts, init others below
        "Type 2": collections.defaultdict(lambda: 0),
        "Unknown": collections.defaultdict(lambda: 0)
    }
    # Initialize specific keys needed
    for ftype in analysis_by_type:
        analysis_by_type[ftype]['byte_counts'] = collections.Counter()
        analysis_by_type[ftype]['field2_values'] = collections.Counter()
        analysis_by_type[ftype]['field3_values'] = collections.Counter()
        analysis_by_type[ftype]['data_lengths'] = []
        analysis_by_type[ftype]['pure_zero_lengths'] = []
        analysis_by_type[ftype]['mixed_zero_lengths'] = []
        analysis_by_type[ftype]['mixed_zero_content'] = collections.Counter()
        analysis_by_type[ftype]['data_pure_zero_pairs'] = []
        analysis_by_type[ftype]['data_mixed_zero_pairs'] = []


    total_bytes_processed_all = 0
    all_signatures = collections.Counter()

    # Process each file and aggregate data into the correct type
    for mus_file in mus_files:
      header_fields, file_data, file_type = process_mus_file(mus_file)

      if header_fields and file_data and file_type:
          data_len = len(file_data)
          total_bytes_processed_all += data_len
          all_signatures[header_fields['signature_id']] += 1

          # Get the dictionary for the current file type
          current_type_data = analysis_by_type[file_type]

          # Aggregate general info
          current_type_data['count'] += 1
          current_type_data['total_bytes'] += data_len

          # Aggregate header fields
          current_type_data['field2_values'][header_fields['field2_bytes']] += 1
          current_type_data['field3_values'][header_fields['field3_bytes']] += 1

          # Aggregate byte frequency
          current_type_data['byte_counts'].update(analyze_byte_frequency(file_data))

          # Aggregate block structure
          block_analysis = analyze_block_structure(file_data, MIN_ZERO_BLOCK_SIZE)
          current_type_data['data_lengths'].extend(block_analysis['data_block_lengths'])
          current_type_data['pure_zero_lengths'].extend(block_analysis['pure_zero_block_lengths'])
          current_type_data['mixed_zero_lengths'].extend(block_analysis['mixed_zero_block_lengths'])
          current_type_data['mixed_zero_content'].update(block_analysis['mixed_zero_block_content'])
          current_type_data['data_pure_zero_pairs'].extend(block_analysis['data_pure_zero_pairs_combined_lengths'])
          current_type_data['data_mixed_zero_pairs'].extend(block_analysis['data_mixed_zero_pairs_combined_lengths'])


    # --- Print Combined Analysis Report ---
    print("\n\n--- Overall Summary ---")
    print(f"Analyzed {len(mus_files)} files, {total_bytes_processed_all:,} total bytes.")
    print("\nFile Type Counts:")
    for ftype, data in analysis_by_type.items():
        if data['count'] > 0:
             suffix = ""
             if ftype == "Type 1": suffix = f"(ends with {HEADER_TYPE1_SUFFIX.hex(' ').upper()})"
             elif ftype == "Type 2": suffix = f"(ends with {HEADER_TYPE2_SUFFIX.hex(' ').upper()})"
             print(f"  {ftype}: {data['count']} file(s) {suffix}")

    print("\nUnique File Signatures/IDs Found (First 4 Bytes):")
    if len(all_signatures) > 10:
         print(f"  {len(all_signatures)} unique signatures found (showing first 10):")
         for i, (sig, count) in enumerate(all_signatures.most_common()):
             if i >= 10: break
             print(f"    Signature {sig.hex(' ').upper()}: {count} file(s)")
    else:
         for sig, count in all_signatures.items():
            print(f"  Signature {sig.hex(' ').upper()}: {count} file(s)")


    # --- Print Detailed Reports Per Type ---
    for ftype, data in analysis_by_type.items():
        if data['count'] > 0: # Only print report if files of this type were found
            generate_type_report(ftype, data)


    print("\n--- Analysis Complete ---")
