# Contributing to Remake Engine

First off, thank you for considering contributing to Remake Engine! This project thrives on community contributions, especially in adding support for new games and their unique workflows. Your efforts help make this tool more versatile and useful for everyone.

This document provides guidelines for contributing. Please read it carefully.

## Getting Started for Contributors

1.  **Fork the Repository:**
    Start by forking the [main Remake Engine repository](https://github.com/Superposition28/RemakeEngine) to your own GitHub account.

2.  **Clone Your Fork:**
    Clone your forked repository to your local machine:
    ```pwsh
    git clone [https://github.com/YOUR_USERNAME/RemakeEngine.git](https://github.com/YOUR_USERNAME/RemakeEngine.git)
    cd RemakeEngine
    ```

3.  **Set Up Your Environment:**
    * Ensure you have Python installed (preferably version 3.8+). The project is developed with Python 3.13.2.
    * Install required Python packages:
      ```pwsh
      pip install questionary
      # Add any other dependencies listed in requirements.txt or noted in the main README
      ```
    * **Configure `project.json`:**
        * If it doesn't exist, create a `project.json` file in the root of your cloned repository. You can often copy `project.json.example` if available.
        * Modify `project.json` with your local absolute paths for game sources or other global settings. This file is typically user-specific and should often be listed in your global or repository `.gitignore` file.

4.  **Create a New Branch:**
    Create a new branch for your contribution (e.g., adding a new game):
    ```pwsh
    git checkout -b add-game-myawesometown
    ```

## How to Add Support for a New Game

This is the primary way to contribute. Follow these steps:

### Step 1: Create the Game Directory

* Navigate to the `RemakeRegistry/Games/` directory.
* Create a new directory for the game. The naming convention should be descriptive, often including the game name and platform/variant.
    * Example: `RemakeRegistry/Games/TheSimpsonsGame PS3/`

### Step 2: Create `operations.json`

* Inside your new game directory (e.g., `RemakeRegistry/Games/TheSimpsonsGame PS3/`), create a file named `operations.json`.
* This JSON file is the heart of your game's integration. It defines the game's display name and the list of operations (workflow steps) available for it.
* The basic structure is:

    ```json
    {
      "Your Game Display Name (Platform)": [
        // List of operation objects will go here
      ]
    }
    ```
    Replace `"Your Game Display Name (Platform)"` with the actual name you want to appear in the Remake Engine menu.

### Step 3: Define Operations (The `operations.json` Schema)

Each item in the list above is an "operation object". Here are the common keys you can define for each operation:

* `Name`: (String)
    * **Required** for operations you want to appear in the interactive menu.
    * The display name of the operation.
    * Example: `"Extract Game Archives"`

* `init`: (Boolean)
    * Optional, defaults to `false`.
    * If set to `true`, this operation will attempt to run automatically when the game is selected from the main menu.
    * If `init` is `true` AND `Name` is *not* provided, the operation will be hidden from the manual selection menu.
    * Example: ` "init": true`

* `Type`: (String)
    * Optional. If omitted, the operation is assumed to be of type `"script"`.
    * Currently supported explicit types:
        * `"script"`: Executes an external Python script.
        * `"download"`: Downloads a file from a URL and can optionally unpack it.
    * Example: `"Type": "download"`

* `Instructions`: (String)
    * Optional.
    * A description of what the operation does or any prerequisites. This information can be displayed to the user before execution (if the main engine script implements this display).
    * Example: `"Instructions": "This will extract all .STR archives from the game's source directory."`

* `python_executable`: (String)
    * Optional, defaults to `"python"`.
    * Specifies the Python interpreter to use for `"script"` type operations.
    * Example: `"python_executable": "python3.9"`

#### Fields for `Type: "script"` (or when `Type` is omitted):

* `script`: (String)
    * **Required** for script operations.
    * The path to the Python script to execute. This path should typically be relative to the **project root directory**.
    * Example: `"script": "Tools/QuickBMS/bms_extract.py"`
    * Example: `"script": "RemakeRegistry/Games/MyGame/Scripts/my_game_specific_script.py"`

* `args`: (List of Strings)
    * Optional.
    * A list of command-line arguments to pass to the script.
    * Arguments can be static strings or include placeholders.
    * Example: ` "args": ["--input", "{{Game.RootPath}}/assets", "--output", "Extracted/Assets"]`

#### Fields for `Type: "download"`:

* `url`: (String)
    * **Required**. The URL of the file to download. Can use placeholders.
* `destination`: (String)
    * Optional, defaults to `.` (the game's root directory: `{{Game.RootPath}}`).
    * The directory (relative to `Game.RootPath`) where the file will be saved. Can use placeholders.
    * Example: `"destination": "tools_downloaded/my_tool/"`
* `filename`: (String)
    * Optional. If omitted, the filename is derived from the URL.
    * The explicit name for the downloaded file. Can use placeholders.
* `unpack`: (Boolean)
    * Optional, defaults to `false`.
    * If `true`, attempts to unpack the downloaded file (supports `.zip`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.xz`).
* `unpack_destination`: (String)
    * Optional, defaults to `.` (the game's root directory: `{{Game.RootPath}}`). Only used if `unpack` is `true`.
    * The directory (relative to `Game.RootPath`) where the archive will be unpacked. Can use placeholders.
* `cleanup_archive`: (Boolean)
    * Optional, defaults to `false`. Only used if `unpack` is `true`.
    * If `true`, the downloaded archive file will be deleted after successful unpacking.

#### `prompts`: (List of Objects)

* Optional.
* Defines a list of interactive questions to ask the user before executing the operation. Answers can be used in placeholders or to construct command-line arguments.
* Each prompt object has the following keys:
    * `Name`: (String) **Required**. An internal name for this prompt. The user's answer will be stored under this name and can be accessed by later prompts or operations using `{{PromptName}}`.
    * `message`: (String) **Required**. The question displayed to the user.
    * `type`: (String) **Required**. The type of prompt. Supported types:
        * `"confirm"`: A Yes/No question.
            * `default`: (Boolean, Optional) `true` or `false`.
            * `cli_arg`: (String, Optional) If the user answers "Yes" (true), this string is added as a single command-line argument to the script's `args`. Useful for flags like `--verbose`.
        * `"text"`: Free-form text input.
            * `default`: (String, Optional) Default text value.
            * `cli_arg_template`: (String, Optional) A template where `{value}` is replaced by the user's text input (e.g., `"--filename={value}"`). The result is added as a single argument.
            * `cli_arg_prefix`: (String, Optional) If the user provides input, this prefix string is added as an argument, followed by the user's input as a *separate* argument.
            * `cli_arg`: (String, Optional) If the user provides input, this string is added as an argument, followed by the user's input as a *separate* argument. (Use this or `cli_arg_prefix`).
        * `"checkbox"`: Allows the user to select multiple options from a list.
            * `choices`: (List of Strings, Required) The list of options to display.
            * `cli_prefix`: (String, Optional) If the user selects items, this prefix string is added as an argument, followed by *each selected choice* as a separate argument.
    * `condition`: (String, Optional) The `Name` of a *previous prompt in the same operation* that was of type `"confirm"`. This current prompt will only be shown if the answer to the conditional prompt was "Yes" (true).
    * `validation`: (Object, Optional) For `"text"` and `"checkbox"` prompts.
        * `required`: (Boolean, Optional) If `true`, the user must provide an answer / make a selection.
        * `message`: (String, Optional) Custom message to display if validation fails.

### Step 4: Add Scripts and Other Files

* **Game-Specific Scripts:** Place Python scripts unique to this game inside a subfolder within your game's directory (e.g., `RemakeRegistry/Games/MyGame/Scripts/`).
* **Reusable Tools/Scripts:** If a script or tool is generic and could be used by other games, consider placing it in the global `Tools/` directory (you might want to discuss this with project maintainers).
* **Data Files:** Game-specific data files (like `.bms` scripts, database files for mapping, etc.) should also go into your game's directory.
* **Paths in `operations.json`:** Remember that paths to scripts (`"script": "..."`) and paths within arguments should generally be relative to the **project root**. Use placeholders for dynamic path parts.

### Step 5: Utilize Placeholders

Remake Engine's placeholder system makes your configurations dynamic and portable.

* **Syntax:** `{{Placeholder.Path.Or.Name}}`
* **Available Standard Placeholders:**
    * `{{Game.RootPath}}`: The absolute path to the current game's directory (e.g., `C:/Projects/RemakeEngine/RemakeRegistry/Games/MyGame PS3/`).
    * `{{Game.Name}}`: The display name of the currently selected game (the top-level key from `operations.json`).
* **Global Configuration Placeholders (from `project.json`):**
    * You can access any value from your `project.json` file.
    * Example: If `project.json` has `{"RemakeEngine": {"Directories": {"SourcePath": "A:\\Path\\To\\Source"}}}` then `{{RemakeEngine.Directories.SourcePath}}` will resolve to `"A:\Path\To\Source"`.
* **Prompt Answer Placeholders:**
    * Within an operation, after a prompt has been answered, you can use its `Name` as a placeholder.
    * Example: If a prompt has `"Name": "outputDir"`, you can use `{{outputDir}}` in subsequent `args` or prompt messages for the same operation.

### Step 6: Add a `readme.md` (Recommended)

* Inside your game's directory (e.g., `RemakeRegistry/Games/MyGame/`), consider adding a simple `readme.md` file.
* This file can explain:
    * Any specific setup required *for that game's operations* (e.g., "Ensure you have GameSourceXYZ mounted at the path specified in your `project.json`").
    * Brief descriptions of what each operation does, if not fully covered by `Instructions`.
    * Dependencies for the custom scripts used (e.g., "The `convert_textures.py` script requires `Pillow`").

### Step 7: `PrimaryIndex.db` (Optional Data File)

* As seen in some examples, a `PrimaryIndex.db` (or similar) might be used by your scripts to track file statuses, checksums, or metadata throughout a complex workflow. If you implement such a system, ensure it's documented in your game's `readme.md`.

## Coding Style and Best Practices (for Scripts)

* **Modularity:** Write small, focused functions/scripts.
* **Clarity:** Use descriptive variable and function names. Add comments where necessary.
* **Error Handling:** Scripts should handle potential errors gracefully and provide informative error messages to `stderr`.
* **Exit Codes:**
    * `sys.exit(0)` on successful completion.
    * `sys.exit(non-zero_value)` (e.g., `sys.exit(1)`) on failure. The Remake Engine uses this to determine if an operation succeeded.
* **Argument Parsing:** For scripts that take multiple or complex arguments, use Python's `argparse` module.
* **Output:** Print normal progress or success messages to `stdout`. Print errors or verbose debugging to `stderr`.

## Submitting Contributions

1.  **Commit Your Changes:**
    Make clear, concise commit messages. Example: `feat(games): Add support for My Awesome Game (PS3)`
    ```pwsh
    git add .
    git commit -m "feat(games): Add The Simpsons Game (PS3) operations"
    ```

2.  **Push to Your Fork:**
    ```pwsh
    git push origin add-game-myawesometown
    ```

3.  **Open a Pull Request (PR):**
    * Go to the original Remake Engine repository on GitHub.
    * You should see a prompt to create a Pull Request from your new branch.
    * Provide a clear title and description for your PR, outlining the changes you've made and why.
    * Reference any relevant issues if applicable.

4.  **Contributor License Agreement (CLA):**
    By contributing to this project, you agree to the terms outlined in [CLA.md](./CLA.md).
    Pull requests that do not comply with the Contributor License Agreement or the project's legal and license constraints will be rejected.
    *(Ensure you have a `CLA.md` file in your repository if you require contributors to agree to one. If you don't have a formal CLA, you might adjust this section or remove it, but it's good practice for larger projects.)*

5.  **Code Review:**
    * Project maintainers will review your PR. Be prepared to answer questions and make adjustments based on feedback.

## Code of Conduct

Please note that this project may have a Code of Conduct. Participants are expected to follow it in all their interactions with the project. (Link to `CODE_OF_CONDUCT.md` if it exists).

## Questions?

If you have questions or need clarification on any of these guidelines, please feel free to open an issue on the GitHub repository.

---

Thank you for contributing to Remake Engine!
