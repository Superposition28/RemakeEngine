File Format Documentation: Dialogue Data (.dat) Files

Source Context and Cross-Platform Correlation:

These .dat files are individual data entries extracted from larger archive files from the PS2 version of "The Simpsons Game". Specifically, they are found after processing language-specific container files, such as ENVS\01_LOC.EN (for English dialogue), using a BMS script designed for the Asura engine.

The path component like DLLN_chunk\ (e.g., ENVS\01_LOC_en\DLLN_chunk\.298.dat) indicates that these files originate from a parent chunk within the PS2 archive that had a 4-character identifier (e.g., "DLLN"). This parent chunk, in turn, contained a series of these individual dialogue entries.

Each .dat file represents a single line of dialogue or subtitle text and its associated metadata for the PS2 version. A crucial piece of information within each .dat file is the AssetID. This AssetID (e.g., lisa_xxx_0005a65 from the example file .298.dat) directly corresponds to an audio asset in the PS3 version of the game.

For instance, the AssetID lisa_xxx_0005a65 found in a PS2 .dat file corresponds to the PS3 audio file located at a path similar to:
USRDIR\audiostreams\EN\sa_xxx_0\d_lisa_xxx_0005a65.exa.snu

This original PS3 file (.snu extension, which is a known audio format used in some EA games, sometimes "Sony NUSound") is typically converted to a more standard format like .wav (e.g., d_lisa_xxx_0005a65.exa.wav) for playback and analysis. Note the common pattern in the PS3 filename: a prefix like d_ and a suffix like .exa.snu (or .exa.wav after conversion) are often appended to the core AssetID.

This direct correlation allows for linking the PS2's text/subtitle data with the higher quality audio assets often found in the PS3 version.

File Naming Convention (Extractor Output):
The files are typically named .[index].dat (e.g., .12.dat, .298.dat) by the BMS script, where [index] is a zero-based counter for chunks of that type. The parent directory name like DLLN_chunk reflects the 4-character ID of the chunk type within the main game archive from which these entries were extracted.

Overall Structure:
Each .dat file contains a fixed-size header followed by variable-length text data. The byte order for multi-byte numerical fields (integers, floats) is Little-Endian.

Field Breakdown:
Offset (Bytes)	Size (Bytes)	Data Type	Field Name	Description	Example Value (from .298.dat)
0	16	ASCII String	AssetID	A 16-character null-padded ASCII string. This appears to be a unique identifier for the dialogue line, correlating with audio file names (e.g., lisa_xxx_0005a65).	lisa_xxx_0005a65
16	4	Unsigned Integer (32-bit)	Separator / Padding	Typically all zeros (0x00000000). Its exact purpose is unknown, likely padding or a null separator.	00 00 00 00
20	16	Binary Data / Byte Array	UnknownMetadataBlock	A 16-byte block of unknown binary data. This could contain various game-specific metadata such as speaker ID, emotion/animation cues, flags, or a hash. Further analysis is needed to determine its exact function.	8B B0 32 00 41 D6 13 5C 92 A2 00 81 07 78 8A 05
36	4	Float (32-bit)	AudioDuration	A single-precision floating-point number representing the duration of the associated audio for this dialogue line, in seconds.	37 D0 E9 3F (approx. 1.8267 seconds)
40	4	Unsigned Integer (32-bit)	TextLengthInChars	An unsigned integer specifying the length of the subsequent TextContent field, in characters (not bytes).	26 00 00 00 (38 decimal)
44	Variable	UTF-16 LE String	TextContent	The actual dialogue or subtitle text. The length of this field in bytes is TextLengthInChars * 2.	"Wait wait wait, that’s all I ever do."
44 + (L*2)	2	UTF-16 LE Character	NullTerminator	A UTF-16 null terminator (0x0000). This marks the end of the text string.	00 00

(Where L = value of TextLengthInChars)

Example Breakdown (DLLN_chunk\.298.dat):

    Bytes 0-15: 6C 69 73 61 5F 78 78 78 5F 30 30 30 35 61 36 35 (lisa_xxx_0005a65)
    Bytes 16-19: 00 00 00 00 (Separator)
    Bytes 20-35: 8B B0 32 00 41 D6 13 5C 92 A2 00 81 07 78 8A 05 (Unknown Metadata)
    Bytes 36-39: 37 D0 E9 3F (Audio Duration: approx. 1.83s)
    Bytes 40-43: 26 00 00 00 (Text Length: 38 characters)
    Bytes 44 - (44 + 38*2 - 1): 57 00 61 00 ... 2E 00 (UTF-16 LE text: "Wait wait wait, that’s all I ever do.")
    Bytes (44 + 382) - (44 + 382 + 1): 00 00 (Null Terminator for the string)

Total file size: 44 + (TextLengthInChars * 2) + 2 bytes.
For .298.dat: 44 + (38 * 2) + 2 = 44 + 76 + 2 = 122 bytes.

Usage Notes:
When parsing these files, it's crucial to read the TextLengthInChars first to determine how many bytes to read for the TextContent. The UnknownMetadataBlock requires further comparative analysis across multiple files, potentially correlating with in-game events or other asset properties, to decipher its meaning.
