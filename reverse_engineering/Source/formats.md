# File Formats in STR output


### .vfb
- **Files:** 8,770
- **Percent:** 0.390%
- **Assumed Purpose:** Unknown RenderWare format (Framebuffer? Vertex Buffer?); RenderWare Visual Effects
- **Known Purpose:** —
- **Summary:** Use RenderWare SDK, Reverse Engineering Tools. Examine headers, consult RenderWare/PS3 communities.
- **Bytes:** `6C 69 73 61 5F 73 70 69 6E 00 00 00 00 00 00 00 00 00 00 06 00 00 00 31`

### .preinstanced
- **Files:** 5,533
- **Percent:** 40.562%
- **Assumed Purpose:** RenderWare Geometry Instancing Data; Compressed 3D Assets
- **Known Purpose:** 3D Assets
- **Summary:** Use RenderWare SDK, Blender (with plugin?), R.E. Tools. Investigate RenderWare compression methods.

#### .rws.ps3.preinstanced
- **Files:** 3,499
- **Assumed Purpose:** RenderWare Stream with Instancing Data (PS3 Platform); Compressed 3D Assets
- **Known Purpose:** 3D Assets
- **Summary:** Use RenderWare SDK, R.E. Tools. RenderWare Scene, static assets ie: world chunks or props.
- **Bytes:** `10 00 00 00 65 82 00 00 2D 00 02 1C 01 00 00 00 0C 00 00 00 2D 00 02 1C`

#### .dff.ps3.preinstanced
- **Files:** 2,034
- **Assumed Purpose:** RenderWare Model with Instancing Data (PS3 Platform); Compressed 3D Assets
- **Known Purpose:** 3D Assets
- **Summary:** Use RenderWare SDK, R.E. Tools. Dynamic Fragment Format, dynamic assets ie: Character models or complex props.
- **Bytes:** `10 00 00 00 77 30 08 00 2D 00 02 1C 01 00 00 00 0C 00 00 00 2D 00 02 1C`

### .ps3
- **Files:** 4,962
- **Percent:** 12.351%
- **Assumed Purpose:** Platform Suffix (PS3); Can be FMOD FSB; Base format varies; Unknown (Asset/Metadata)
- **Known Purpose:** Platform Identifier
- **Summary:** Use Platform Identifier / FMOD Tools / Specific Tool. Examine headers, compare content.

#### .rcb.ps3
- **Files:** 1,226
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `00 00 53 A8 00 00 00 17 FC 59 46 DA 00 00 00 00 00 00 00 00 00 00 00 00`

#### .bnk.ps3
- **Files:** 1,213
- **Assumed Purpose:** Sound Bank (EA?, FMOD?, Sony Proprietary?) (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Use VGMStream (if EA/FMOD), Custom/Sony Tools?
- **Bytes:** `00 02 4A E0 00 00 00 09 37 15 84 51 FC 59 46 DA 00 00 00 00 00 00 00 00`

#### .hko.ps3
- **Files:** 1,021
- **Assumed Purpose:** Havok Collision/Physics Object Data (PS3 Platform)
- **Known Purpose:** Havok Physics file
- **Summary:** Use Havok SDK, R.E. Tools.
- **Bytes:** `48 6B 78 10 09 00 00 00 00 00 00 00 00 00 00 00 57 E0 E0 57 10 C0 C0 10`

#### .hkt.ps3
- **Files:** 878
- **Assumed Purpose:** Havok Tagfile (Serialized Physics/Animation Data) (PS3 Platform)
- **Known Purpose:** Havok Physics file
- **Summary:** Use Havok SDK, R.E. Tools.
- **Bytes:** `48 6B 78 10 09 00 00 00 00 00 00 00 00 00 00 00 57 E0 E0 57 10 C0 C0 10`

#### .acs.ps3
- **Files:** 267
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `01 09 00 00 00 00 00 50 DC BB A7 F2 F8 E3 10 95 00 06 43 00 00 73 00 00`

#### .xml.ps3
- **Files:** 153
- **Assumed Purpose:** XML Data/Configuration (PS3 Platform)
- **Known Purpose:** XML Data
- **Summary:** Use Text Editors, XML Editors, Game/Engine Tools.
- **Bytes:** `73 65 71 6D 00 00 08 88 00 00 00 01 00 00 00 10 00 00 04 10 BB BB BB BB`

#### .bbn.ps3
- **Files:** 110
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 B1 83 33 23 00 00 00 02`

#### .tox.ps3
- **Files:** 77
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `31 42 4F 54 00 00 00 90 00 00 00 00 00 00 00 08 19 59 2C 63 00 00 04 10`

#### .shk.ps3
- **Files:** 16
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `2A F8 4D D8 00 01 00 04 2C AF 61 00 00 00 01 FF 00 32 01 00 00 64 01 FF`

#### .cec.ps3
- **Files:** 1
- **Assumed Purpose:** Unknown format (PS3 Platform)
- **Known Purpose:** —
- **Summary:** Unknown tools.
- **Bytes:** `01 00 00 47 39 FC E8 8F 00 62 61 73 69 63 70 6C 61 79 65 72 00 00 00 00`

### .xml
- **Files:** 1 + 2,616 = 2,617
- **Percent:** 0.092% (for .xml only)
- **Assumed Purpose:** Configuration Data
- **Known Purpose:** XML Data/Configuration
- **Summary:** Use Text Editors, XML Editors, Game/Engine Tools. Inspect content for recognizable structures.

#### .xml
- **Files:** 1
- **Assumed Purpose:** Configuration Data
- **Known Purpose:** XML Data/Configuration
- **Summary:** Use Text Editors, XML Editors, Game/Engine Tools.

#### .meta.xml
- **Files:** 2,616
- **Assumed Purpose:** XML Metadata File
- **Known Purpose:** XML Metadata
- **Summary:** Use Text Editors, XML Editors, Game/Engine Tools.
- **Bytes:** `4D 4D 64 6C 00 00 00 0A 00 00 04 70 00 00 00 00 0B 50 45 30 B9 E4 A9 11`

### .txd
- **Files:** 858
- **Percent:** 26.034%
- **Assumed Purpose:** Texture Dictionaries
- **Known Purpose:** RenderWare Texture Dictionary (Archive); Texture Dictionaries
- **Summary:** Use RenderWare SDK, Magic.TXD, RW Analyze, Noesis; Use Noesis with Python plugin.
- **Bytes:** `16 00 00 00 04 FA 0F 00 2D 00 02 1C 01 00 00 00 04 00 00 00 2D 00 02 1C`

### .lh2
- **Files:** 554 + (5 * 20) = 654
- **Percent:** 0.242% (for .lh2 only)
- **Assumed Purpose:** Game Text Strings
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools (e.g., 7-Zip, lhasa); Try LHA decompression tools.
- **Bytes:** `32 48 43 4C 00 00 27 F3 00 00 00 01 00 00 00 00 00 00 00 2A 00 00 00 05`

#### .lh2
- **Files:** 554
- **Assumed Purpose:** Game Text Strings
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.
- **Bytes:** `32 48 43 4C 00 00 27 F3 00 00 00 01 00 00 00 00 00 00 00 2A 00 00 00 05`

#### .en.lh2
- **Files:** 20
- **Assumed Purpose:** LHA Compressed Archive (English Localization)
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.
- **Bytes:** `32 48 43 4C 00 02 32 6D 00 00 00 01 00 00 00 00 00 00 0D 18 00 00 00 01`

#### .ss.lh2
- **Files:** 20
- **Assumed Purpose:** LHA Compressed Archive (Spanish? Localization)
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.
- **Bytes:** `32 48 43 4C 00 01 65 D8 00 00 00 01 00 00 00 00 00 00 0D 18 00 00 00 01`

#### .fr.lh2
- **Files:** 20
- **Assumed Purpose:** LHA Compressed Archive (French Localization)
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.

#### .es.lh2
- **Files:** 20
- **Assumed Purpose:** LHA Compressed Archive (Spanish Localization)
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.

#### .it.lh2
- **Files:** 20
- **Assumed Purpose:** LHA Compressed Archive (Italian Localization)
- **Known Purpose:** LHA Compressed Archive
- **Summary:** Use LHA Decompression Tools.

### .alb
- **Files:** 529
- **Percent:** 0.031%
- **Assumed Purpose:** Unknown in game context; Likely Photo/Media Album;
- **Known Purpose:** —
- **Summary:** Use Unknown (Possibly Photo Album Software). Broaden search for PS3 audio formats.
- **Bytes:** `00 06 00 0D 00 00 00 08 04 64 84 62 2C 04 E1 25 27 8B 42 62 27 8B 42 62`

### .ctb
- **Files:** 528
- **Percent:** 0.042%
- **Assumed Purpose:** Highly Ambiguous; Unlikely standard RenderWare
- **Known Purpose:** —
- **Summary:** Use Ambiguous (AutoCAD?, Atari?, CheatEngine?, etc.). Consider RenderWare plugins or custom data.
- **Bytes:** `00 06 00 00 00 00 00 00 00 00 00 00 40 A0 00 00 00 11 3B 03 00 00 00 18`

### .dat
- **Files:** 867
- **Percent:** 0.240%
- **Assumed Purpose:** Generic Data File (Content Varies); Unknown
- **Known Purpose:** —
- **Summary:** Use Hex Editors, Game/Engine Specific Tools. Examine headers, try generic archive tools.
- **Bytes:** `00 00 00 00 53 69 6D 47 00 00 00 01 9D 47 54 3E 00 00 00 01 00 00 00 B0`

### .graph
- **Files:** 425
- **Percent:** 0.577%
- **Assumed Purpose:** Unknown RenderWare format (Scene Graph?)
- **Known Purpose:** —
- **Summary:** Use RenderWare SDK, RW Analyze, R.E. Tools. Explore RenderWare scene graph documentation.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 10 01 18 02 F7 2C 04 E1 25 41 07 E4 3C`

### .rcm_b
- **Files:** 346
- **Percent:** 0.000%
- **Assumed Purpose:** Unknown format
- **Known Purpose:** —
- **Summary:** Unknown tools. Continue searching PS3 file format databases.
- **Bytes:** `00 01 00 05 00 00 00 10 EF BE 00 00 00 00 00 74 07 42 68 BB 2C 04 E1 25`

### .sbk
- **Files:** 157
- **Percent:** 15.300%
- **Assumed Purpose:** Sound Bank (The Simpsons Game PS3, "knbs" header); Unknown
- **Known Purpose:** Sound Bank
- **Summary:** Use Custom Tools, R.E. Tools. Research sound data formats in PS3 games.
- **Bytes:** `6B 6E 62 73 00 00 00 CB 00 00 EB FC 00 34 B8 D8 00 00 EC 40 00 34 B8 D8`

### .bsp
- **Files:** 113
- **Percent:** 0.080%
- **Assumed Purpose:** RenderWare Binary Space Partitioning (Level Geometry); Unknown
- **Known Purpose:** —
- **Summary:** Use RenderWare SDK, RW Analyze, R.E. Tools. Investigate RenderWare support for .bsp or similar formats.
- **Bytes:** `00 00 00 0B 00 00 00 00 00 00 00 06 00 00 00 70 00 00 00 00 01 73 00 64`

### .smb
- **Files:** 99
- **Percent:** 0.057%
- **Assumed Purpose:** Ambiguous: Audio Pointer (Simpsons), Model (4x4 Evo); Unknown
- **Known Purpose:** —
- **Summary:** Use Context-Dependent (Audio Pointer?, Model?) tools. Research game model formats on PS3.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 0C 00 00 00 0D 00 00 00 CA 00 00 00 18`

### .mib
- **Files:** 89
- **Percent:** 0.013%
- **Assumed Purpose:** Sony MultiStream Audio (Requires .mih header); Unknown
- **Known Purpose:** Sony MultiStream Audio
- **Summary:** Use VGMStream (Player Plugins, VGSC). Research audio formats recognized by VGMStream.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 18 00 00 00 00 00 00 00 00 00 00 00 00`

### .amb
- **Files:** 58
- **Percent:** 3.551%
- **Assumed Purpose:** Ambiguous: Game Audio Container (VGMStream?), Ambisonics?; Unknown
- **Known Purpose:** —
- **Summary:** Use VGMStream?, Ambisonics Tools?, R.E. Tools. Research ambient sound formats.
- **Bytes:** `00 00 00 09 00 09 4C 4C 00 00 00 D8 00 09 4C 4C 00 00 00 00 2C 82 F4 EE`

### .uix
- **Files:** 54
- **Percent:** 0.360%
- **Assumed Purpose:** Unknown format (Potentially UI related); Unknown
- **Known Purpose:** —
- **Summary:** Use Unknown (UI Middleware?). Investigate UI middleware used in PS3 games.
- **Bytes:** `75 69 78 66 00 04 23 60 74 69 74 6C 00 00 00 11 62 75 73 5F 73 74 6F 70`

### (No Extension)
- **Files:** 46
- **Percent:** 0.001%
- **Assumed Purpose:** Files requiring content-based identification; Unknown
- **Known Purpose:** —
- **Summary:** Use File ID Utilities, Hex Editors, VGMStream?. Examine headers, use file identification tools.
- **Bytes (LightTOC example):** `40 F2 00 01 00 00 00 10 00 00 00 00 00 01 00 00 EE B2 C9 98 45 0E 50 CA`
- **Bytes (StreamSetConfig example):** `00 00 00 03 00 00 00 1A 00 00 02 65 07 7D 77 B5 00 00 00 01 00 00 00 00`

### .imb
- **Files:** 44
- **Percent:** 0.026%
- **Assumed Purpose:** Unknown format;
- **Known Purpose:** —
- **Summary:** Unknown tools. Broaden search for PS3 game asset formats.
- **Bytes:** `5B A0 8C AA 00 02 00 10 00 33 00 06 00 00 00 1C 00 00 06 80 00 00 07 40`

### .toc
- **Files:** 20 + 5 = 25
- **Percent:** 0.003% (for .toc only)
- **Assumed Purpose:** Table of Contents / Index File (Format specific to archive); Unknown
- **Known Purpose:** Table of Contents
- **Summary:** Use Archive Specific Tools, Hex Editors. Analyze content for file offsets or names.
- **Bytes:** `9C BA 7B 28 00 00 00 09 00 00 09 D1 00 00 03 DC 00 28 00 27 00 00 00 04`

#### .toc
- **Files:** 20
- **Assumed Purpose:** Table of Contents / Index File
- **Known Purpose:** Table of Contents
- **Summary:** Use Archive Specific Tools, Hex Editors.
- **Bytes:** `9C BA 7B 28 00 00 00 09 00 00 09 D1 00 00 03 DC 00 28 00 27 00 00 00 04`

#### .str.occ.toc
- **Files:** 5
- **Assumed Purpose:** Table of Contents for Streamed Occlusion Data
- **Known Purpose:** Table of Contents
- **Summary:** Use Game/Engine Specific Tools, R.E. Tools.
- **Bytes:** `6F 63 74 63 00 00 00 03 00 00 00 2E 00 00 00 10 3A 2B 38 F4 00 00 02 40`

### .msb
- **Files:** 19
- **Percent:** 0.007%
- **Assumed Purpose:** EA Audio Container (Likely); Unknown
- **Known Purpose:** —
- **Summary:** Use VGMStream (Player Plugins, VGSC), EA Tools?. Confirm association with EA Redwood Shores' audio format.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00`

### .inf
- **Files:** 12
- **Percent:** 0.003%
- **Assumed Purpose:** Ambiguous: Font Metrics?, Game Manifest?, Windows Setup Info?; Unknown (Information)
- **Known Purpose:** —
- **Summary:** Use Context-Dependent (Font Tool?, Manifest Tool?, Driver Tool?). Examine content for metadata or setup instructions.
- **Bytes:** `46 4F 4E 54 00 00 1A 20 00 06 00 BF 00 00 04 34 00 00 00 00 00 00 00 14`

### .aub
- **Files:** 2
- **Percent:** 0.001%
- **Assumed Purpose:** Unknown format; Unknown
- **Known Purpose:** —
- **Summary:** Unknown tools. Broaden search for PS3 game asset formats.
- **Bytes:** `00 00 00 00 00 00 00 00 00 00 00 0C 00 00 00 0A 00 00 00 37 00 00 00 05`

### .bin
- **Files:** 2 + 2 = 4
- **Percent:** 0.038% (for .bin only)
- **Assumed Purpose:** Generic Binary Data (Content Varies); Unknown
- **Known Purpose:** —
- **Summary:** Use Hex Editors, Game/Engine Specific Tools. Explore generic binary format tools.
- **Bytes:** <!-- No specific example found in files.txt for base .bin -->

#### .bin
- **Files:** 2
- **Assumed Purpose:** Generic Binary Data (Content Varies)
- **Known Purpose:** —
- **Summary:** Use Hex Editors, Game/Engine Specific Tools.
- **Bytes:** <!-- No specific example found in files.txt for base .bin -->

#### .hud.bin
- **Files:** 2
- **Assumed Purpose:** Generic Binary Data (Likely for Heads-Up Display)
- **Known Purpose:** —
- **Summary:** Use Hex Editors, Game/Engine Specific Tools.
- **Bytes:** `01 20 00 3F 00 00 00 03 00 00 00 03 00 00 02 80 00 00 01 40 00 00 01 40`

### .txt
- **Files:** 2
- **Percent:** 0.000%
- **Assumed Purpose:** Plain Text File
- **Known Purpose:** Plain Text
- **Summary:** Use Text Editors. Likely placeholder or leftover debug text.
- **Bytes:** `32 0A 65 6E 0A 66 72 6F 6E 74 65 6E 64 5C 74 65 78 74 5C 38 31 44 45 31`
