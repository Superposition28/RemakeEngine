# Remake Engine

**An extensible, interactive command-line engine for managing and executing complex workflows for various games, with a focus on community-driven configurations for reverse engineering and modding.**

Remake Engine provides a streamlined interface for developers, modders, and reverse engineers to run predefined tasks—from executing custom scripts to managing asset extraction and conversion—for a collection of games. Its power lies in its configuration-driven approach, allowing new games and their specific workflows to be added easily by defining them in JSON, without modifying the core engine.

## Key Features

* **Highly Extensible:** Add support for new games by simply creating a configuration file and associated scripts/tools.
* **Interactive CLI:** User-friendly menus powered by `questionary` for easy navigation and operation execution.
* **Configuration-Driven:** All games and operations are defined in simple JSON files (`operations.json`).
* **Powerful Placeholder System:** Use placeholders like `{{RemakeEngine.Directories.SourcePath}}` or `{{Game.RootPath}}` in your configurations for dynamic values.
* **Orchestrates Custom Scripts & External Tools:** Natively runs Python scripts and can easily integrate command-line tools (like QuickBMS, FFmpeg).
* **Advanced User Input:** A flexible prompt system gathers necessary inputs before execution, supporting conditional questions and validation.
* **Community Focused:** Designed to be a platform for sharing tools and operational knowledge for various games.
* **Clear Feedback:** Colorized output for status, warnings, and errors.

## How It Works

Remake Engine operates on a simple "engine vs. content" model:

* **Engine:** The core Python scripts that provide the interactive interface, load configurations, resolve placeholders, and execute operations via `subprocess`.
* **Content:**
    * **Game Configurations:** Each game has its directory within `RemakeRegistry/Games/`. Inside, `operations.json` defines the game's name and its list of workflow steps (operations).
    * **Global Configuration:** A `project.json` file in the tool's root directory can store global settings (like base paths), accessible via placeholders.
    * **Scripts & Tools:** A `Tools/` directory (or similar structure) holds reusable scripts and external executables orchestrated by the engine. Game-specific scripts can live within their game's directory.

When run (ideally from the project root), the engine scans for games, lets you select one, and then presents its specific operations.

## Getting Started

### Prerequisites

* Python 3.13.2+
* `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```pwsh
    git clone https://github.com/Superposition28/RemakeEngine
    ```
    ```pwsh
    cd RemakeEngine
    ```

2.  **Install dependencies:**
    ```pwsh
    pip install questionary
    ```
TODO Add other dependencies


3.  **Configure `project.json`:**
    * Create a `project.json` file in the root directory (you might start by copying `project.json.example` if one exists).
    * Edit it to set up *your* specific paths (e.g., game source locations). **Note:** This file often contains user-specific absolute paths and might be excluded from Git via `.gitignore`.

4.  **Acquire External Tools:**
    * Ensure any external tools referenced in `operations.json` (like `quickbms.exe`, `ffmpeg.exe`) are placed in their expected locations (e.g., under `Tools/`).

### Running the Tool

Execute the main script **from the project's root directory**:

```pwsh
python main.py
```
or for tool downloads
```pwsh
python download.py
```


# Directory Structure
```
RemakeEngine/
├── main.py                 # Main engine script
├── download.py             # tool downloads
├── project.json            # global configuration
├── Tools/                  # Reusable scripts and external executables
    +---Blender
    |   |   asset_map.sqlite
    |   |
    |   \---blender-4.0.2-windows-x64
    |          blender.exe
    |
    +---ffmpeg-vgmstream
    |      convert.py
    |
    +---Process
    |   +---Flat
    |   |      flat.py
    |   |
    |   \---Rename
    |          RenameFolders copy.py
    |          RenameFolders.py
    |          __init__.py
    |
    \---QuickBMS
        |   bms_extract.py
        |
        \---exe
            quickbms.exe
|
├── RemakeRegistry/
│   └── Games/
│       └── <GameName Platform/Variant>/
│           ├── readme.md
│           ├── operations.json # defines the main menu options and scripts
│           ├── Scripts/
│           │   ├── init.py
│           │   ├── *.bms
|           |   └── **
│           └── PrimaryIndex.db   # Game file index, listing all files at each stage of extraction, modification etc and meta data
└── Utils/
    └── printer.py            # Utility for colored console output
```

# Usage
1. Run the main script from the project root.
2. Select a game.
3. Select an operation.
4. Answer any prompts.
5. Observe the execution.
6. Return to the menu or change games.

# Contributing (Adding New Game Support)
1. Create a new directory under RemakeRegistry/Games/.
2. Inside it, create your operations.json.
3. Define your operations. Assume operations are of type "script" unless other types are added later. Ensure paths to scripts (script key) and arguments (args key) are relative to the project root or absolute. Use {{Game.RootPath}} (path to this game's folder) and {{RemakeEngine...}} placeholders where needed.
4. Add any game-specific scripts or data files to your game's directory.
5. If you need new reusable tools, add them under the Tools/ directory (discuss with project maintainers if applicable).

### Example operations.json Entry:

```json
{
    "Name": "Extract Archives (.STR)",
    "Instructions": "run quickbms script using RemakeRegistry/Games/TheSimpsonsGame PS3/Scripts/simpsons_str.bms",
    "python_executable": "python",
    "script": "Tools/QuickBMS/bms_extract.py", // Path relative to project root
    "args": [
        "--quickbms", "Tools/QuickBMS/exe/quickbms.exe",
        "--script", "RemakeRegistry/Games/TheSimpsonsGame PS3/Scripts/simpsons_str.bms",
        "--input", "{{RemakeEngine.Directories.SourcePath}}", // Placeholder use
        "--output", "GameFiles/STROUT", // Relative path (will be created in CWD or handle abs path)
        "--extension", ".str"
    ]
}
```

#### (Please refer to CONTRIBUTING.md for detailed guidelines.)

# Configuration Details
`project.json` (Global Configuration)

* Stores global settings, often user-specific paths.
* Values are accessible via {{RemakeEngine.Key.SubKey}} placeholders.

`operations.json` (Game Manifest File)

* Defines the game name and its workflow steps (operations).
* Supports init scripts for automatic execution.
* Defines Name, Instructions, python_executable, script, args, and prompts for each operation.

# License

(Please specify your project's license here, e.g., MIT License.)
