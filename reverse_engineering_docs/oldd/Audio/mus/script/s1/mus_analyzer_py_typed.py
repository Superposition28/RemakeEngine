import os
import collections
from pathlib import Path
import statistics
import struct # For potential integer parsing

# --- Configuration ---
HEADER_SIZE = 16  # Bytes to read as the header
HEADER_TYPE1_SUFFIX = bytes.fromhex("78013200")
HEADER_TYPE2_SUFFIX = bytes.fromhex("02030203")
MIN_ZERO_BLOCK_SIZE = 8 # Minimum number of consecutive zeros to consider a 'gap'
# --- End Configuration ---

def analyze_byte_frequency(data):
  """Calculates the frequency of each byte in the data."""
  if not data:
    return collections.Counter()
  return collections.Counter(data)

def analyze_block_structure(data, min_zero_size):
  """
  Analyzes data for non-zero blocks followed by zero blocks.

  Returns:
      A dictionary containing lists of data block lengths, zero block lengths,
      and data-zero pair lengths.
  """
  blocks = []
  current_pos = 0
  if not data: # Handle empty data
      return {
          'data_block_lengths': [],
          'zero_block_lengths': [],
          'data_zero_pairs_combined_lengths': []
      }

  in_zero_block = data[0] == 0
  block_start = 0

  while current_pos < len(data):
    byte = data[current_pos]
    is_zero = (byte == 0)

    if is_zero != in_zero_block:
      # State changed (data -> zero or zero -> data)
      block_len = current_pos - block_start
      if block_len > 0: # Only record non-empty blocks
          if in_zero_block:
            # Just finished a zero block
            if block_len >= min_zero_size:
              blocks.append({'type': 'zero', 'start': block_start, 'length': block_len})
            # else: Ignore short zero sequences for now
          else:
            # Just finished a data block
            blocks.append({'type': 'data', 'start': block_start, 'length': block_len})

      block_start = current_pos
      in_zero_block = is_zero

    current_pos += 1

  # Add the last block
  block_len = len(data) - block_start
  if block_len > 0:
      if in_zero_block:
          if block_len >= min_zero_size:
              blocks.append({'type': 'zero', 'start': block_start, 'length': block_len})
      else:
          blocks.append({'type': 'data', 'start': block_start, 'length': block_len})

  # --- Analyze the detected blocks ---
  analysis = {
      'data_block_lengths': [],
      'zero_block_lengths': [],
      'data_zero_pairs_combined_lengths': [] # Store combined lengths directly
  }
  for i in range(len(blocks)):
      block = blocks[i]
      if block['type'] == 'data':
          analysis['data_block_lengths'].append(block['length'])
          # Check if the next block is a zero block
          if i + 1 < len(blocks) and blocks[i+1]['type'] == 'zero':
              combined_len = block['length'] + blocks[i+1]['length']
              analysis['data_zero_pairs_combined_lengths'].append(combined_len)
      elif block['type'] == 'zero':
          analysis['zero_block_lengths'].append(block['length'])

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


def generate_type_report(file_type_name, type_data, total_bytes_all_files):
    """Generates the analysis report section for a specific file type."""
    print(f"\n--- Analysis for {file_type_name} ({type_data['count']} files, {type_data['total_bytes']:,} bytes) ---")

    # Type-Specific Header Field Values
    print("\nHeader Field Values Observed:")
    print("  Field 2 (Bytes 4-7):")
    for val_bytes, count in type_data['field2_values'].most_common(5):
        val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        print(f"    {val_bytes.hex(' ').upper()} (Int: {val_int}): {count} times")
    print("  Field 3 (Bytes 8-11):")
    for val_bytes, count in type_data['field3_values'].most_common(5):
        val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        print(f"    {val_bytes.hex(' ').upper()} (Int: {val_int}): {count} times")


    # Type-Specific Byte Frequency
    print("\nByte Frequency (Top 5):")
    if type_data['byte_counts']:
        # Ensure 0x00 is shown if present
        top_5 = type_data['byte_counts'].most_common(5)
        zero_present = any(byte_val == 0 for byte_val, count in top_5)

        for byte_val, count in top_5:
          percentage = (count / type_data['total_bytes']) * 100 if type_data['total_bytes'] else 0
          print(f"  Byte 0x{byte_val:02X}: {count:,} times ({percentage:.2f}%)")

        if 0 in type_data['byte_counts'] and not zero_present:
             count = type_data['byte_counts'][0]
             percentage = (count / type_data['total_bytes']) * 100 if type_data['total_bytes'] else 0
             print(f"  Byte 0x00: {count:,} times ({percentage:.2f}%)")
    else:
        print("  No byte data processed for this type.")

    # Type-Specific Block Structure
    print(f"\nBlock Structure (Zero Gaps >= {MIN_ZERO_BLOCK_SIZE} bytes):")
    total_data_blocks = len(type_data['data_lengths'])
    total_zero_blocks = len(type_data['zero_lengths'])
    total_pairs = len(type_data['pair_lengths'])

    if total_data_blocks > 0:
        avg_data_len = statistics.mean(type_data['data_lengths'])
        print(f"  Found {total_data_blocks:,} data blocks.")
        print(f"    Min/Max/Avg length: {min(type_data['data_lengths'])} / {max(type_data['data_lengths'])} / {avg_data_len:.2f}")
    else:
        print("  No significant data blocks found.")

    if total_zero_blocks > 0:
        avg_zero_len = statistics.mean(type_data['zero_lengths'])
        print(f"  Found {total_zero_blocks:,} zero blocks (gaps).")
        print(f"    Min/Max/Avg length: {min(type_data['zero_lengths'])} / {max(type_data['zero_lengths'])} / {avg_zero_len:.2f}")
    else:
         print("  No significant zero blocks (gaps) found.")

    if total_pairs > 0:
        print(f"  Found {total_pairs:,} data-followed-by-zero pairs.")
        pair_lengths_counter = collections.Counter(type_data['pair_lengths'])
        print(f"  Common combined (data+zero) lengths for pairs (Top 5):")
        for length, count in pair_lengths_counter.most_common(5):
             percentage_of_pairs = (count/total_pairs) * 100
             print(f"    Length {length}: {count:,} times ({percentage_of_pairs:.2f}% of pairs)")
    else:
        print("  No data-followed-by-zero pairs found.")


if __name__ == "__main__":
  script_dir = Path(__file__).parent
  print(f"Looking for .mus files in: {script_dir}")

  mus_files = sorted(list(script_dir.glob('*.mus'))) # Sort for consistent order

  if not mus_files:
    print("No .mus files found in this directory.")
  else:
    print(f"Found {len(mus_files)} .mus files.")

    # Initialize combined analysis structures PER TYPE
    analysis_by_type = {
        "Type 1": collections.defaultdict(lambda: collections.Counter() if isinstance(collections.Counter(), collections.Counter) else list()),
        "Type 2": collections.defaultdict(lambda: collections.Counter() if isinstance(collections.Counter(), collections.Counter) else list()),
        "Unknown": collections.defaultdict(lambda: collections.Counter() if isinstance(collections.Counter(), collections.Counter) else list())
    }
    # Initialize counters and totals within each type's dictionary
    for ftype in analysis_by_type:
        analysis_by_type[ftype]['count'] = 0
        analysis_by_type[ftype]['total_bytes'] = 0
        analysis_by_type[ftype]['byte_counts'] = collections.Counter()
        analysis_by_type[ftype]['field2_values'] = collections.Counter()
        analysis_by_type[ftype]['field3_values'] = collections.Counter()
        analysis_by_type[ftype]['data_lengths'] = []
        analysis_by_type[ftype]['zero_lengths'] = []
        analysis_by_type[ftype]['pair_lengths'] = []


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
          current_type_data['zero_lengths'].extend(block_analysis['zero_block_lengths'])
          current_type_data['pair_lengths'].extend(block_analysis['data_zero_pairs_combined_lengths'])

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
            generate_type_report(ftype, data, total_bytes_processed_all)


    print("\n--- Analysis Complete ---")

