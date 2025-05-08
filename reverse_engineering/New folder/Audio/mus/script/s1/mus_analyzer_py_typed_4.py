import os
import collections
from pathlib import Path
import statistics
import struct # For potential integer parsing

# --- Configuration ---
HEADER_SIZE = 16  # Bytes to read as the header
HEADER_TYPE1_SUFFIX = bytes.fromhex("78013200")
HEADER_TYPE2_SUFFIX = bytes.fromhex("02030203")
MIN_ZERO_BLOCK_SIZE = 4 # Minimum length for a sequence of zeros to be considered a block
SEQUENCE_TO_FIND = bytes.fromhex("0C000000") # The specific sequence to look for in zero blocks
# --- End Configuration ---

def analyze_byte_frequency(data):
  """Calculates the frequency of each byte in the data."""
  if not data:
    return collections.Counter()
  return collections.Counter(data)

def analyze_block_structure(data, min_zero_size, sequence_to_find):
  """
  Analyzes data for blocks: 'data', 'pure_zero', 'mixed_zero_seq'.
  'mixed_zero_seq' specifically means a zero block containing SEQUENCE_TO_FIND.

  Returns:
      A dictionary containing lists of lengths and counts for each block type,
      and analysis of the specific sequence within mixed_zero blocks.
  """
  analysis = {
      'data_lengths': [],
      'pure_zero_lengths': [],
      'mixed_zero_seq_lengths': [],
      'mixed_zero_seq_occurrences': 0, # Count how many mixed blocks had the sequence
      'data_pure_zero_pairs': [],
      'data_mixed_zero_seq_pairs': []
  }
  if not data: return analysis # Handle empty data

  current_pos = 0
  while current_pos < len(data):
    start_pos = current_pos
    byte = data[current_pos]

    if byte != 0:
      # --- Data Block ---
      while current_pos < len(data) and data[current_pos] != 0:
        current_pos += 1
      block_len = current_pos - start_pos
      analysis['data_lengths'].append(block_len)
      # Check previous block for pair analysis later if needed (more complex)

    else:
      # --- Zero Block ---
      while current_pos < len(data) and data[current_pos] == 0:
        current_pos += 1
      block_len = current_pos - start_pos

      if block_len >= min_zero_size:
        zero_block_data = data[start_pos:current_pos]
        # Check if the specific sequence exists within this zero block
        if sequence_to_find in zero_block_data:
           analysis['mixed_zero_seq_lengths'].append(block_len)
           # Count occurrences *within* the block if needed, here just counting blocks
           analysis['mixed_zero_seq_occurrences'] += 1 # Count blocks containing the sequence
        else:
           analysis['pure_zero_lengths'].append(block_len)
      # else: Ignore short zero blocks < min_zero_size

  # --- Post-process for pairs (Simplified: assumes alternating structure) ---
  # This simple pair logic might be inaccurate if blocks don't strictly alternate
  # A more robust state machine would be needed for perfect pairing.
  # For now, let's focus on block types and lengths.
  # We can add pair analysis back if the block types are correctly identified.

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
        fields['field2_int'] = struct.unpack('<I', fields['field2_bytes'])[0]
    except struct.error: fields['field2_int'] = None
    try:
        fields['field3_int'] = struct.unpack('<I', fields['field3_bytes'])[0]
    except struct.error: fields['field3_int'] = None

    return fields


def process_mus_file(filepath):
  """
  Reads a .mus file, parses header fields, determines type,
  and returns relevant data for combined analysis.
  """
  print(f"\n--- Processing: {filepath.name} ---")
  file_type = "Unknown"
  header_fields = None
  try:
    with open(filepath, 'rb') as f:
      header_bytes = f.read(HEADER_SIZE)
      if not header_bytes or len(header_bytes) < HEADER_SIZE:
        print(f"Warning: File too small or empty ({len(header_bytes or b'')} bytes).")
        # Attempt to read whatever data exists
        f.seek(0)
        file_data = f.read()
        # Try partial parse if possible
        header_fields = parse_header_fields(header_bytes + b'\x00' * (HEADER_SIZE - len(header_bytes or b''))) if header_bytes else None
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

      if header_fields['suffix_bytes'] == HEADER_TYPE1_SUFFIX: file_type = "Type 1"
      elif header_fields['suffix_bytes'] == HEADER_TYPE2_SUFFIX: file_type = "Type 2"
      print(f"Detected Type: {file_type}")

      f.seek(0)
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

    # Header Field Values
    print("\nHeader Field Values Observed:")
    print("  Field 2 (Bytes 4-7):")
    for val_bytes, count in type_data['field2_values'].most_common(5):
        val_int = 'N/A'
        try:
            val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        except:
            pass
        print(f"    {val_bytes.hex(' ').upper():<12} (Int: {val_int}): {count} times")
    print("  Field 3 (Bytes 8-11):")
    for val_bytes, count in type_data['field3_values'].most_common(5):
        val_int = 'N/A'
        try:
            val_int = struct.unpack('<I', val_bytes)[0] if len(val_bytes) == 4 else 'N/A'
        except:
            pass
        print(f"    {val_bytes.hex(' ').upper():<12} (Int: {val_int}): {count} times")

    # Byte Frequency
    print("\nByte Frequency (Top 5):")
    if type_data['byte_counts']:
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
    else: print("  No byte data processed.")

    # --- Block Structure ---
    print(f"\nBlock Structure Analysis (Min Zero Length: {MIN_ZERO_BLOCK_SIZE}):")

    # Data Blocks
    total_data_blocks = len(type_data['data_lengths'])
    if total_data_blocks > 0:
        avg_data_len = statistics.mean(type_data['data_lengths'])
        print(f"\n  Data Blocks: {total_data_blocks:,} found")
        print(f"    Min/Max/Avg length: {min(type_data['data_lengths'])} / {max(type_data['data_lengths'])} / {avg_data_len:.2f}")
    else: print("\n  Data Blocks: None found.")

    # Pure Zero Blocks
    total_pure_zero_blocks = len(type_data['pure_zero_lengths'])
    if total_pure_zero_blocks > 0:
        avg_pure_zero_len = statistics.mean(type_data['pure_zero_lengths'])
        print(f"\n  Pure Zero Blocks (Only 0x00): {total_pure_zero_blocks:,} found")
        print(f"    Min/Max/Avg length: {min(type_data['pure_zero_lengths'])} / {max(type_data['pure_zero_lengths'])} / {avg_pure_zero_len:.2f}")
    else: print("\n  Pure Zero Blocks: None found.")

    # Mixed Zero Blocks (Containing Sequence)
    total_mixed_zero_blocks = len(type_data['mixed_zero_seq_lengths'])
    if total_mixed_zero_blocks > 0:
        avg_mixed_zero_len = statistics.mean(type_data['mixed_zero_lengths']) # Corrected key
        print(f"\n  'Mixed' Zero Blocks (Containing {SEQUENCE_TO_FIND.hex(' ').upper()}): {type_data['mixed_zero_seq_occurrences']:,} found")
        print(f"    Min/Max/Avg length of these blocks: {min(type_data['mixed_zero_seq_lengths'])} / {max(type_data['mixed_zero_seq_lengths'])} / {avg_mixed_zero_len:.2f}")
    else:
        print(f"\n  'Mixed' Zero Blocks (Containing {SEQUENCE_TO_FIND.hex(' ').upper()}): None found.")

    # Pair analysis could be added here if needed, but focus is on block types now


if __name__ == "__main__":
  script_dir = Path(__file__).parent
  print(f"Looking for .mus files in: {script_dir}")

  mus_files = sorted(list(script_dir.glob('*.mus')))

  if not mus_files:
    print("No .mus files found in this directory.")
  else:
    print(f"Found {len(mus_files)} .mus files.")

    analysis_by_type = {
        "Type 1": collections.defaultdict(lambda: 0),
        "Type 2": collections.defaultdict(lambda: 0),
        "Unknown": collections.defaultdict(lambda: 0)
    }
    for ftype in analysis_by_type:
        analysis_by_type[ftype]['byte_counts'] = collections.Counter()
        analysis_by_type[ftype]['field2_values'] = collections.Counter()
        analysis_by_type[ftype]['field3_values'] = collections.Counter()
        analysis_by_type[ftype]['data_lengths'] = []
        analysis_by_type[ftype]['pure_zero_lengths'] = []
        analysis_by_type[ftype]['mixed_zero_seq_lengths'] = [] # Renamed key
        # Removed mixed_zero_content as we only check for specific sequence now
        # Removed pair lists for simplicity for now

    total_bytes_processed_all = 0
    all_signatures = collections.Counter()

    for mus_file in mus_files:
      header_fields, file_data, file_type = process_mus_file(mus_file)

      if header_fields and file_data and file_type:
          data_len = len(file_data)
          total_bytes_processed_all += data_len
          all_signatures[header_fields['signature_id']] += 1
          current_type_data = analysis_by_type[file_type]

          current_type_data['count'] += 1
          current_type_data['total_bytes'] += data_len
          current_type_data['field2_values'][header_fields['field2_bytes']] += 1
          current_type_data['field3_values'][header_fields['field3_bytes']] += 1
          current_type_data['byte_counts'].update(analyze_byte_frequency(file_data))

          # Aggregate new block structure
          block_analysis = analyze_block_structure(file_data, MIN_ZERO_BLOCK_SIZE, SEQUENCE_TO_FIND)
          current_type_data['data_lengths'].extend(block_analysis['data_lengths'])
          current_type_data['pure_zero_lengths'].extend(block_analysis['pure_zero_lengths'])
          current_type_data['mixed_zero_seq_lengths'].extend(block_analysis['mixed_zero_seq_lengths'])
          current_type_data['mixed_zero_seq_occurrences'] += block_analysis['mixed_zero_seq_occurrences']
          # Aggregate pairs if re-enabled

    # --- Print Reports ---
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
    # Simplified signature printing
    print(f"  {len(all_signatures)} unique signatures found.")


    for ftype, data in analysis_by_type.items():
        if data['count'] > 0:
            generate_type_report(ftype, data)

    print("\n--- Analysis Complete ---")
