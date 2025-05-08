import re
import struct
import math
import matplotlib.pyplot as plt
import os # Needed for os.path

# --- Configuration ---
# Set the input file path here
file_path = "lodmodel1.rws.PS3.preinstanced"
# Set to True to print detailed parsing steps for each mesh chunk
DEBUG_PARSING = False

# --- Helper Function for Logging ---
def log_debug(message):
    if DEBUG_PARSING:
        print(message)

# --- Load the File ---
try:
    with open(file_path, "rb") as f:
        data = f.read()
    file_size = len(data)
    print(f"Successfully loaded file: {file_path} ({file_size:,} bytes)")
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

# --- Step 1: Find Potential Model Sections ---
# This regex pattern is taken directly from the SimpGameImport script
# It identifies a potential header or marker preceding mesh data.
msh_pattern = re.compile(b"\x33\xEA\x00\x00....\x2D\x00\x02\x1C", re.DOTALL)
matches = list(msh_pattern.finditer(data))
model_header_offsets = [m.start() for m in matches] # Store the start of the pattern match

print(f"Found {len(model_header_offsets)} potential model header patterns.")

# --- Data Structure Offsets Storage ---
# These lists will store the *calculated* starting offsets of various data blocks
# based on the importer's logic.
mesh_chunk_start_offsets = [] # Where parsing *actually* begins (after header pattern)
vertex_buffer_start_offsets = [] # Calculated start of vertex data
face_buffer_start_offsets = []   # Calculated start of face index data
string_offsets = []              # Offsets of generic ASCII strings
special_string_offsets = []        # Offsets of specific keywords

# --- Step 2: Parse Mesh Chunks (Following Importer Logic) ---

def process_mesh_chunk(start_offset: int, chunk_index: int) -> None:
    """
    Parses a mesh chunk starting at the given offset within the global 'data',
    replicating the logic found in the SimpGameImport Blender addon.

    Reads mesh header information, identifies submeshes, calculates buffer offsets,
    and populates global lists for analysis. Handles potential errors during parsing.

    Args:
        start_offset: The starting byte offset for parsing this chunk
                      (typically m.end() + 4 from the regex match).
        chunk_index: An identifier for logging purposes.
    """
    log_debug(f"\n--- Processing Mesh Chunk {chunk_index} at offset {start_offset} (0x{start_offset:X}) ---")
    current_pos = start_offset
    mesh_chunk_start_offsets.append(start_offset) # Record where we start parsing

    try:
        # 1. Read FaceDataOff and MeshDataSize (Little Endian)
        if current_pos + 8 > file_size:
            print(f"[Chunk {chunk_index} Error] Offset {current_pos} too close to EOF to read FaceDataOff/MeshDataSize.")
            return
        FaceDataOff = struct.unpack('<I', data[current_pos : current_pos+4])[0]
        MeshDataSize = struct.unpack('<I', data[current_pos+4 : current_pos+8])[0]
        current_pos += 8
        MeshChunkStart = current_pos # This is the reference point used by importer's relative offsets
        log_debug(f"[Chunk {chunk_index}] FaceDataOff: {FaceDataOff}, MeshDataSize: {MeshDataSize}, MeshChunkStart: {MeshChunkStart} (0x{MeshChunkStart:X})")

        # 2. Skip 0x14 bytes
        if MeshChunkStart + 0x14 > file_size:
             print(f"[Chunk {chunk_index} Error] Offset {MeshChunkStart} too close to EOF for 0x14 skip.")
             return
        current_pos = MeshChunkStart + 0x14
        log_debug(f"[Chunk {chunk_index}] Skipped 0x14 bytes, current_pos: {current_pos} (0x{current_pos:X})")

        # 3. Read Counts (Big Endian)
        if current_pos + 8 > file_size:
            print(f"[Chunk {chunk_index} Error] Offset {current_pos} too close to EOF to read mDataTableCount/mDataSubCount.")
            return
        mDataTableCount = struct.unpack('>I', data[current_pos : current_pos+4])[0]
        mDataSubCount = struct.unpack('>I', data[current_pos+4 : current_pos+8])[0]
        current_pos += 8
        log_debug(f"[Chunk {chunk_index}] mDataTableCount: {mDataTableCount}, mDataSubCount: {mDataSubCount}")

        # 4. Skip Data Table (Importer reads and discards 4 bytes after seeking 4)
        table_skip_bytes = mDataTableCount * 8
        if current_pos + table_skip_bytes > file_size:
             print(f"[Chunk {chunk_index} Error] Offset {current_pos} too close to EOF for data table skip ({table_skip_bytes} bytes).")
             return
        current_pos += table_skip_bytes
        mDataSubStart = current_pos # Start of sub-mesh offset pointers
        log_debug(f"[Chunk {chunk_index}] Skipped data table ({table_skip_bytes} bytes), mDataSubStart: {mDataSubStart} (0x{mDataSubStart:X})")

        # 5. Process Sub-Meshes
        for i in range(mDataSubCount):
            log_debug(f"--- Sub-Mesh {i} ---")
            # 5a. Read Sub-Mesh Offset Pointer (Big Endian)
            # Importer seeks to mDataSubStart + i * 0xC + 8 before reading
            submesh_entry_pos = mDataSubStart + i * 0xC + 8
            if submesh_entry_pos + 4 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {submesh_entry_pos} too close to EOF to read submesh offset.")
                continue # Skip this submesh

            submesh_offset_rel = struct.unpack('>I', data[submesh_entry_pos : submesh_entry_pos+4])[0]
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Read relative offset {submesh_offset_rel} from {submesh_entry_pos} (0x{submesh_entry_pos:X})")

            # 5b. Seek to Sub-Mesh Detail Start
            # Importer seeks to offset + MeshChunkStart + 0xC
            submesh_detail_pos = submesh_offset_rel + MeshChunkStart + 0xC
            if submesh_detail_pos + 4 > file_size: # Need at least 4 bytes for VertCountDataOff_rel
                 print(f"[Chunk {chunk_index}, Sub {i} Error] Calculated submesh detail offset {submesh_detail_pos} (0x{submesh_detail_pos:X}) out of bounds.")
                 continue

            current_pos = submesh_detail_pos # Update current position for reading detail data
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Submesh detail starts at: {current_pos} (0x{current_pos:X})")

            # 5c. Read Vertex Count Data Offset (Big Endian)
            # Importer reads 4 bytes, adds MeshChunkStart, then seeks there
            VertCountDataOff_rel = struct.unpack('>I', data[current_pos : current_pos+4])[0]
            current_pos += 4 # Advance past this read

            # Calculate absolute position for vertex count info
            vert_count_info_pos = VertCountDataOff_rel + MeshChunkStart
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Read VertCountDataOff_rel: {VertCountDataOff_rel}, calculated info pos: {vert_count_info_pos} (0x{vert_count_info_pos:X})")

            # 5d. Read Vertex Size Info (Big Endian) from calculated position
            if vert_count_info_pos + 8 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {vert_count_info_pos} too close to EOF to read vertex sizes.")
                continue
            VertChunkTotalSize = struct.unpack('>I', data[vert_count_info_pos : vert_count_info_pos+4])[0]
            VertChunkSize = struct.unpack('>I', data[vert_count_info_pos+4 : vert_count_info_pos+8])[0]

            # 5e. Calculate Vertex Count
            VertCount = 0
            if VertChunkSize != 0 and not math.isnan(VertChunkSize):
                try:
                    VertCount = int(VertChunkTotalSize / VertChunkSize)
                    if math.isnan(VertCount): VertCount = 0 # Handle potential NaN result
                except ZeroDivisionError:
                    print(f"[Chunk {chunk_index}, Sub {i} Warning] Division by zero calculating VertCount.")
                    VertCount = 0
            else:
                 print(f"[Chunk {chunk_index}, Sub {i} Warning] Invalid VertChunkSize ({VertChunkSize}). Cannot calculate VertCount.")

            log_debug(f"[Chunk {chunk_index}, Sub {i}] VertChunkTotalSize: {VertChunkTotalSize}, VertChunkSize: {VertChunkSize}, Calculated VertCount: {VertCount}")

            # --- Calculate and Store Buffer Start Offsets ---
            # Importer now calculates VertexStart and FaceStart from the submesh_detail_pos onwards

            current_pos = vert_count_info_pos + 8 # Position after reading vertex sizes

            # 5f. Skip 8 bytes (Importer does seek(8, 1))
            if current_pos + 8 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF for 8 byte skip.")
                continue
            current_pos += 8

            # 5g. Read VertexStart Offset (Big Endian) and Calculate Absolute VertexStart
            if current_pos + 4 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF to read VertexStart_offset.")
                continue
            VertexStart_offset = struct.unpack('>I', data[current_pos : current_pos+4])[0]
            current_pos += 4
            # Absolute Vertex Buffer Start = offset + FaceDataOff + MeshChunkStart
            VertexStart = VertexStart_offset + FaceDataOff + MeshChunkStart
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Read VertexStart_offset: {VertexStart_offset}, Calculated VertexStart: {VertexStart} (0x{VertexStart:X})")
            if VertexStart < file_size and VertCount > 0: # Only store if valid offset and vertices exist
                 vertex_buffer_start_offsets.append(VertexStart)
            elif VertCount > 0:
                 print(f"[Chunk {chunk_index}, Sub {i} Warning] Calculated VertexStart {VertexStart} is out of bounds for file size {file_size}.")

            # 5h. Skip 0x14 bytes (Importer does seek(0x14, 1))
            if current_pos + 0x14 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF for 0x14 skip.")
                continue
            current_pos += 0x14

            # 5i. Read Face Indices Count (Big Endian)
            if current_pos + 4 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF to read FaceIndicesCount.")
                continue
            FaceIndicesCount = struct.unpack('>I', data[current_pos : current_pos+4])[0]
            current_pos += 4
            # Calculate FaceCount (Importer divides by 2, potentially due to strip representation or short indices)
            FaceCount = int(FaceIndicesCount / 2)
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Read FaceIndicesCount: {FaceIndicesCount}, Calculated FaceCount: {FaceCount}")

            # 5j. Skip 4 bytes (Importer does seek(4, 1))
            if current_pos + 4 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF for 4 byte skip.")
                continue
            current_pos += 4

            # 5k. Read FaceStart Offset (Big Endian) and Calculate Absolute FaceStart
            if current_pos + 4 > file_size:
                print(f"[Chunk {chunk_index}, Sub {i} Error] Offset {current_pos} too close to EOF to read FaceStart_offset.")
                continue
            FaceStart_offset = struct.unpack('>I', data[current_pos : current_pos+4])[0]
            current_pos += 4
            # Absolute Face Index Buffer Start = offset + FaceDataOff + MeshChunkStart
            FaceStart = FaceStart_offset + FaceDataOff + MeshChunkStart
            log_debug(f"[Chunk {chunk_index}, Sub {i}] Read FaceStart_offset: {FaceStart_offset}, Calculated FaceStart: {FaceStart} (0x{FaceStart:X})")
            if FaceStart < file_size and FaceCount > 0: # Only store if valid offset and faces exist
                face_buffer_start_offsets.append(FaceStart)
            elif FaceCount > 0:
                print(f"[Chunk {chunk_index}, Sub {i} Warning] Calculated FaceStart {FaceStart} is out of bounds for file size {file_size}.")
            # End of sub-mesh loop

    except struct.error as e:
        print(f"[Chunk {chunk_index} Struct Error] Error processing mesh chunk at offset {start_offset}, current_pos ~{current_pos}: {e}")
    except Exception as e:
        print(f"[Chunk {chunk_index} General Error] Error processing mesh chunk at offset {start_offset}, current_pos ~{current_pos}: {e}")

# --- Process all found model header patterns ---
print("\nStarting mesh chunk processing...")
for i, match in enumerate(matches):
    # The importer starts reading *after* the pattern + 4 bytes
    parsing_start_offset = match.end() + 4
    if parsing_start_offset >= file_size:
        print(f"Skipping potential chunk {i} starting at {match.start()}: Parsing start offset {parsing_start_offset} exceeds file size.")
        continue
    process_mesh_chunk(parsing_start_offset, i)
print("Mesh chunk processing complete.")

# --- Step 3: Find Strings ---
print("\nSearching for strings...")
# Searching for ASCII strings (adjust length threshold as needed)
ascii_pattern = re.compile(rb"[a-zA-Z0-9_/\.\-]{4,}") # Allow path chars, min length 4
keywords = [b"palette", b"simpsons", b"texture", b".tga", b".dds", b".png"] # Keywords of interest

for match in ascii_pattern.finditer(data):
    offset = match.start()
    text = match.group()

    # Check if it contains any keywords (case-insensitive)
    is_special = False
    lowered_text = text.lower()
    for keyword in keywords:
        if keyword in lowered_text:
            special_string_offsets.append(offset)
            is_special = True
            break # Found a keyword, no need to check others

    if not is_special:
        string_offsets.append(offset)
print(f"Found {len(string_offsets)} generic strings and {len(special_string_offsets)} special strings.")

# --- Step 4: Analysis Summary ---
print("\n==== Analysis Summary ====")
print(f"File: {os.path.basename(file_path)}")
print(f"File Size: {file_size:,} bytes")
print("-" * 20)
print(f"Model Header Patterns Found: {len(model_header_offsets)}")
print(f"Mesh Chunks Parsed (Started): {len(mesh_chunk_start_offsets)}")
print(f"Vertex Buffer Starts Identified: {len(vertex_buffer_start_offsets)}")
print(f"Face Buffer Starts Identified: {len(face_buffer_start_offsets)}")
print(f"Generic Strings Found: {len(string_offsets)}")
print(f"Special Strings (Keywords) Found: {len(special_string_offsets)}")
print("-" * 20)

# Optional: Print first few offsets of each type
if model_header_offsets: print(f"First few Model Header Offsets: {[hex(o) for o in model_header_offsets[:5]]}")
if mesh_chunk_start_offsets: print(f"First few Mesh Chunk Start Offsets: {[hex(o) for o in mesh_chunk_start_offsets[:5]]}")
if vertex_buffer_start_offsets: print(f"First few Vertex Buffer Start Offsets: {[hex(o) for o in vertex_buffer_start_offsets[:5]]}")
if face_buffer_start_offsets: print(f"First few Face Buffer Start Offsets: {[hex(o) for o in face_buffer_start_offsets[:5]]}")
if string_offsets: print(f"First few Generic String Offsets: {[hex(o) for o in string_offsets[:5]]}")
if special_string_offsets: print(f"First few Special String Offsets: {[hex(o) for o in special_string_offsets[:5]]}")

print("===========================")

# --- Step 5: Visualize Results ---
print("\nGenerating plot...")
plt.figure(figsize=(18, 8)) # Wider figure

# Define plot categories and colors
plot_data = [
    (face_buffer_start_offsets, "Face Buffer Start", "purple", 0),
    (vertex_buffer_start_offsets, "Vertex Buffer Start", "red", 1),
    (mesh_chunk_start_offsets, "Mesh Chunk Start", "green", 2), # Effective start of parsing
    (model_header_offsets, "Model Header Pattern", "blue", 3),  # Start of the regex pattern
    (string_offsets, "Generic String", "gray", 4),
    (special_string_offsets, "Special String", "orange", 5)
]

# Create scatter plots for each data type
y_ticks_labels = {}
for offsets, label, color, y_val in plot_data:
    if offsets: # Only plot if data exists
        plt.scatter(offsets, [y_val] * len(offsets), label=f"{label} ({len(offsets)})", s=15, color=color, alpha=0.7)
        y_ticks_labels[y_val] = label
    else:
        # Add placeholder for legend even if no data
        plt.scatter([], [], label=f"{label} (0)", color=color)
        y_ticks_labels[y_val] = label


# Sort labels based on y_val for consistent tick order
sorted_y_vals = sorted(y_ticks_labels.keys())
sorted_labels = [y_ticks_labels[y] for y in sorted_y_vals]

# Customizing the plot
plt.yticks(sorted_y_vals, sorted_labels)
plt.xlabel("File Offset (bytes)")
plt.ylabel("Data Type")
plt.title(f"Binary Asset File Structure Analysis: {os.path.basename(file_path)}")
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5)) # Place legend outside plot
plt.grid(True, axis='x', linestyle=':', alpha=0.6) # Grid only on x-axis
plt.xlim(0, file_size) # Ensure x-axis covers the whole file
plt.ylim(-0.5, max(sorted_y_vals) + 0.5) # Adjust y-limits slightly
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend

# Save the plot
plot_filename = f"{os.path.splitext(file_path)[0]}_structure_analysis.png"
try:
    plt.savefig(plot_filename)
    print(f"Plot saved as: {plot_filename}")
except Exception as e:
    print(f"Error saving plot: {e}")

# Show the plot
plt.show()

print("\nAnalysis finished.")