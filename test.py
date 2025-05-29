import struct
import argparse
import os

def parse_htxt_block(data, block_start_offset):
    """
    Parses a single HTXT block from the given data starting at block_start_offset.
    Yields decoded strings.
    """
    # Signature: "Asura   HTXT" (12 bytes)
    # Header Field 1 (4 bytes)
    # Header Field 2 (4 bytes)
    # Reserved (4 bytes)
    # String Count (4 bytes)
    # Unknown Meta 1 (4 bytes)
    # Unknown Meta 2 (4 bytes)
    # Total header size from start of "Asura   " = 12 + 4 + 4 + 4 + 4 + 4 + 4 = 36 bytes

    header_fmt = '<12sI I I I I I' # 12s for signature, then 6 uint32_t fields
                                  # sig, val1, val2, reserved, str_count, unk1, unk2

    # The block_start_offset is where "Asura   HTXT" begins.
    # String count is at offset 24 from the start of the signature.
    string_count_offset = block_start_offset + 24
    if string_count_offset + 4 > len(data):
        print(f"Warning: Not enough data for string count at offset {string_count_offset}.")
        return

    try:
        string_count = struct.unpack_from('<I', data, string_count_offset)[0]
    except struct.error:
        print(f"Warning: Could not unpack string count at offset {string_count_offset}.")
        return

    print(f"Found HTXT block at 0x{block_start_offset:X}, String count: {string_count}")

    # Current offset points to the start of the first string's 4-byte marker
    current_offset = block_start_offset + 36

    for i in range(string_count):
        if current_offset + 8 > len(data): # Need at least 8 bytes for marker + length
            print(f"Warning: Unexpected EOF when trying to read string entry {i+1}/{string_count} header.")
            break

        try:
            # 1. Read 4-byte String Marker (we'll just read and advance past it for now)
            # string_marker = data[current_offset : current_offset + 4]
            current_offset += 4

            # 2. Read 4-byte String Length (Little Endian)
            str_len_utf16_chars = struct.unpack_from('<I', data, current_offset)[0]
            current_offset += 4

            if str_len_utf16_chars == 0: # Empty string or padding entry
                # print(f"  String {i+1}: Empty entry (length 0).")
                continue

            # 3. Read String Data (UTF-16LE)
            str_data_len_bytes = str_len_utf16_chars * 2
            if current_offset + str_data_len_bytes > len(data):
                print(f"Warning: String data for entry {i+1} exceeds file bounds.")
                print(f"  Marker: (skipped), Declared UTF-16 Chars: {str_len_utf16_chars}, Bytes: {str_data_len_bytes}")
                print(f"  Current Offset: 0x{current_offset:X}, Remaining data: {len(data) - current_offset} bytes.")
                break

            raw_string_bytes = data[current_offset : current_offset + str_data_len_bytes]
            current_offset += str_data_len_bytes

            # Decode UTF-16LE. The last char is usually a null terminator.
            try:
                # The last two bytes should be 00 00 (UTF-16 NULL)
                decoded_string = raw_string_bytes[:-2].decode('utf-16-le')
                # Remove CR (U+000D) and LF (U+000A) characters from the string content
                decoded_string = decoded_string.replace('\x00', '')
                yield decoded_string
            except UnicodeDecodeError as e:
                print(f"Warning: UnicodeDecodeError for string {i+1} at offset 0x{current_offset - str_data_len_bytes:X}: {e}")
                yield f"[DECODE_ERROR: {raw_string_bytes.hex()}]"

        except struct.error as e:
            print(f"Warning: Struct unpack error for string entry {i+1}: {e}")
            break
        except IndexError as e:
            print(f"Warning: IndexError for string entry {i+1} (likely EOF): {e}")
            break


def main():
    parser = argparse.ArgumentParser(description='Extracts text strings from Simpsons Game ASR/HTXT files.')
    parser.add_argument('input_file', help='Path to the input ASR archive or HTXT file.')
    parser.add_argument('output_file', help='Path to the output TXT file for extracted strings.')
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        return

    try:
        with open(args.input_file, 'rb') as f_in, open(args.output_file, 'w', encoding='utf-8') as f_out:
            file_content = f_in.read()

            htxt_signature = b'HTXT'
            search_offset = 0
            blocks_found = 0

            while True:
                block_start = file_content.find(htxt_signature, search_offset)
                if block_start == -1:
                    break

                blocks_found += 1
                f_out.write(f"--- HTXT Block found at offset 0x{block_start:X} ---\n")

                for extracted_string in parse_htxt_block(file_content, block_start):
                    f_out.write(extracted_string.replace('\r\n', '\n').replace('\r', '\n') + '\n')

                f_out.write("\n--- End of HTXT Block ---\n\n")
                search_offset = block_start + len(htxt_signature) # Continue search after this found signature

            if blocks_found == 0:
                print(f"No '{htxt_signature.decode()}' blocks found in '{args.input_file}'.")
            else:
                print(f"Successfully processed {blocks_found} HTXT block(s).")
                print(f"Extracted strings written to '{args.output_file}'.")

    except IOError as e:
        print(f"File I/O Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()