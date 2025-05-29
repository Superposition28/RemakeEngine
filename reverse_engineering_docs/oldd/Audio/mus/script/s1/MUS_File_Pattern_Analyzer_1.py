import os
import collections
from pathlib import Path
import statistics # For calculating averages and potentially median/mode later

# --- Configuration ---
HEADER_SIZE = 16    # Bytes to read as the header
EXPECTED_SIGNATURE = bytes.fromhex("D241C20D") # First 4 bytes expected for some files
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


def process_mus_file(filepath):
    """
    Reads a .mus file and returns its header and raw data for combined analysis.
    Prints individual header info.

    Returns:
            A tuple: (header_bytes, file_data_bytes) or (None, None) on error.
    """
    print(f"\n--- Processing: {filepath.name} ---")
    try:
        with open(filepath, 'rb') as f:
            # Read header
            header = f.read(HEADER_SIZE)
            if not header:
                print("File is empty.")
                return None, None

            print(f"Header ({HEADER_SIZE} bytes): {header.hex(' ').upper()}")
            signature = header[:len(EXPECTED_SIGNATURE)]
            print(f"Signature: {signature.hex(' ').upper()}", end="")
            if signature == EXPECTED_SIGNATURE:
                print(f" (MATCHES expected {EXPECTED_SIGNATURE.hex(' ').upper()})")
            else:
                # Check for other known signatures if necessary
                # Example: if signature == bytes.fromhex("E59258AC"): print(" (Known signature type 2)")
                print(f" (DOES NOT MATCH expected {EXPECTED_SIGNATURE.hex(' ').upper()})")


            # Read the rest of the file for further analysis
            f.seek(0) # Reset file pointer
            file_data = f.read()
            return header, file_data

    except FileNotFoundError:
        print(f"Error: File not found.")
        return None, None
    except Exception as e:
        print(f"An error occurred processing {filepath.name}: {e}")
        return None, None


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    print(f"Looking for .mus files in: {script_dir}")

    mus_files = sorted(list(script_dir.glob('*.mus'))) # Sort for consistent order

    if not mus_files:
        print("No .mus files found in this directory.")
    else:
        print(f"Found {len(mus_files)} .mus files.")

        # Initialize combined analysis structures
        combined_byte_counts = collections.Counter()
        combined_data_lengths = []
        combined_zero_lengths = []
        combined_pair_lengths = []
        total_bytes_processed = 0
        file_signatures = collections.Counter()

        # Process each file and aggregate data
        for mus_file in mus_files:
            header, file_data = process_mus_file(mus_file)
            if header and file_data:
                    total_bytes_processed += len(file_data)
                    file_signatures[header[:len(EXPECTED_SIGNATURE)]] += 1 # Count signatures

                    # Aggregate byte frequency
                    combined_byte_counts.update(analyze_byte_frequency(file_data))

                    # Aggregate block structure
                    block_analysis = analyze_block_structure(file_data, MIN_ZERO_BLOCK_SIZE)
                    combined_data_lengths.extend(block_analysis['data_block_lengths'])
                    combined_zero_lengths.extend(block_analysis['zero_block_lengths'])
                    combined_pair_lengths.extend(block_analysis['data_zero_pairs_combined_lengths'])

        # --- Print Combined Analysis Report ---
        print("\n\n--- Combined Analysis Report ---")
        print(f"Analyzed {len(mus_files)} files, {total_bytes_processed:,} total bytes.")

        # Signatures Found
        print("\nFile Signatures Found:")
        for sig, count in file_signatures.items():
                print(f"    Signature {sig.hex(' ').upper()}: {count} file(s)")


        # Combined Byte Frequency
        print("\nCombined Byte Frequency (Top 10):")
        if combined_byte_counts:
                # Ensure 0x00 is shown if present, even if not top 10
                top_10 = combined_byte_counts.most_common(10)
                zero_present_in_top_10 = any(byte_val == 0 for byte_val, count in top_10)

                for byte_val, count in top_10:
                    percentage = (count / total_bytes_processed) * 100 if total_bytes_processed else 0
                    print(f"    Byte 0x{byte_val:02X}: {count:,} times ({percentage:.2f}%)")

                if 0 in combined_byte_counts and not zero_present_in_top_10:
                        count = combined_byte_counts[0]
                         percentage = (count / total_bytes_processed) * 100 if total_bytes_processed else 0
                        print(f"    Byte 0x00: {count:,} times ({percentage:.2f}%)") # Specifically show zero count
        else:
                print("    No byte data processed.")

        # Combined Block Structure
        print(f"\nCombined Block Structure (Zero Gaps >= {MIN_ZERO_BLOCK_SIZE} bytes):")
        total_data_blocks = len(combined_data_lengths)
        total_zero_blocks = len(combined_zero_lengths)
        total_pairs = len(combined_pair_lengths)

        if total_data_blocks > 0:
                avg_data_len = statistics.mean(combined_data_lengths)
                print(f"    Found {total_data_blocks:,} data blocks across all files.")
                print(f"        Min/Max/Avg length: {min(combined_data_lengths)} / {max(combined_data_lengths)} / {avg_data_len:.2f}")
        else:
                print("    No significant data blocks found.")

        if total_zero_blocks > 0:
                avg_zero_len = statistics.mean(combined_zero_lengths)
                print(f"    Found {total_zero_blocks:,} zero blocks (gaps) across all files.")
                print(f"        Min/Max/Avg length: {min(combined_zero_lengths)} / {max(combined_zero_lengths)} / {avg_zero_len:.2f}")
        else:
                print("    No significant zero blocks (gaps) found.")

        if total_pairs > 0:
                print(f"    Found {total_pairs:,} data-followed-by-zero pairs across all files.")
                pair_lengths_counter = collections.Counter(combined_pair_lengths)
                print(f"    Common combined (data+zero) lengths for pairs (Top 5):")
                for length, count in pair_lengths_counter.most_common(5):
                         percentage_of_pairs = (count/total_pairs) * 100
                        print(f"        Length {length}: {count:,} times ({percentage_of_pairs:.2f}% of pairs)")
        else:
                print("    No data-followed-by-zero pairs found.")


    print("\n--- Analysis Complete ---")
