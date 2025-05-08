# Main File Formats in USRDIR

This directory contains information about the primary file formats found in the `PS3_GAME\USRDIR` directory of The Simpsons Game (PAL PS3 version).

## Main Formats

*   **.snu** (`29,430` files)
    *   Main audio files, likely containing sound effects and dialogue. Encapsulates EA SNR/SNS or SPS streams, often using EA-XAS ADPCM. See `snu/readme.md`.
*   **.mus** (`17` files)
    *   Audio stream format, likely used for background music. Proprietary EA format with two subtypes, using fixed 64-byte chunks and VBR. See `mus/readme.md`.
*   **.str** (`550` files)
    *   Archive format (`SToc` signature) containing various game assets (models, textures, scripts, etc.). Often uses dk2 compression. See `str/readme.md`.
*   **.vp6** (`172` files)
    *   Video format used for pre-rendered cutscenes ("Movies"). Likely uses the VP6 codec. See `vp6/readme.md`.

## Other Formats

*   **.lua** (`3` files)
    *   Lua source code files, likely used for game scripting. See `other/lua/readme.md`.
*   **.bin** (`1` file)
    *   Generic binary data file. Purpose requires further analysis. See `other/bin/readme.md`.
*   **.txt** (`1` file)
    *   Plain text file. Likely placeholder or leftover debug text. See `other/txt/readme.md`.

USRDIR
.bin
.lua

USRDIR\text
.txt

USRDIR\Assets_1_Audio_Streams
.snu
.mus

USRDIR\Assets_1_Video_Movies
.vp6

USRDIR\Assets_2_Characters_Simpsons
USRDIR\Assets_2_Frontend
USRDIR\Map_3-00_GameHub
USRDIR\Map_3-00_SprHub
USRDIR\Map_3-01_LandOfChocolate
USRDIR\Map_3-02_BartmanBegins
USRDIR\Map_3-03_HungryHungryHomer
USRDIR\Map_3-04_TreeHugger
USRDIR\Map_3-05_MobRules
USRDIR\Map_3-06_EnterTheCheatrix
USRDIR\Map_3-07_DayOfTheDolphin
USRDIR\Map_3-08_TheColossalDonut
USRDIR\Map_3-09_Invasion
USRDIR\Map_3-10_BargainBin
USRDIR\Map_3-11_NeverQuest
USRDIR\Map_3-12_GrandTheftScratchy
USRDIR\Map_3-13_MedalOfHomer
USRDIR\Map_3-14_BigSuperHappy
USRDIR\Map_3-15_Rhymes
USRDIR\Map_3-16_MeetThyPlayer
.str


