import questionary
from pathlib import Path
from printer import print, colours
import init
import os

# --- Define your custom style (as per your example) ---
custom_style_fancy = questionary.Style([
    ('question', 'white'),
    ('answer', '#4688f1'),
    ('pointer', 'green'),
    ('highlighted', 'blue'),
    ('selected', '#cc241d'),
    ('separator', 'white'),
    ('instruction', ''),
    ('text', 'darkmagenta'),
    ('disabled', '#858585 italic')
])

status, path_value = init.main()

print(colours.CYAN, "Tool initialization complete press any key to continue...")
input()


# Check if essential Module directories exist
module_paths_exist = (
    Path('Modules').exists() and
    Path('Modules\\Extract').exists() and
    Path('Modules\\Model').exists() and
    Path('Modules\\Texture').exists() and
    Path('Modules\\Video').exists() and
    Path('Modules\\Audio').exists() and
    Path('Modules\\Godot').exists()
)

if module_paths_exist:
    while True: # Start of the main loop
        # clear all console output for a fresh menu display
        os.system('cls' if os.name == 'nt' else 'clear')

        # Define the choices for the questionary select prompt
        choices = [
            "Extract Archives (.STR)",
            "Convert Models (.preinstanced -> .blend)",
            "Extract Textures (.txd -> .png)",
            "Convert Videos (.vp6 -> .ogv)",
            "Convert Audio (.snu -> .wav)",
            #"init Godot",
            questionary.Separator(),
            "Run all Steps (1-5)",
            "Exit"
        ]

        # Display the interactive menu and get the user's choice
        choice = questionary.select(
            "Select operation(s) to perform:",
            choices=choices,
            use_shortcuts=True,
            style=custom_style_fancy
        ).ask()

        # --- Handle the user's choice ---
        if choice is None or choice == "Exit":
            print(colours.CYAN, "Exiting...")
            break # Exit the while loop

        elif choice == "Extract Archives (.STR)":
            print(colours.GREEN, f"Running: {choice}")
            import Modules.Extract.run as run_qbms
            run_qbms.main()

        elif choice == "Convert Models (.preinstanced -> .blend)":
            print(colours.GREEN, f"Running: {choice}")
            import Modules.Model.run as run_model
            verbose_input = questionary.confirm("Model Conversion: Enable verbose output?", default=False, style=custom_style_fancy).ask()
            debug_sleep_input = questionary.confirm("Model Conversion: Enable debug sleep?", default=False, style=custom_style_fancy).ask()
            export_input = questionary.confirm(
                "Model Conversion: Export additional formats (FBX/GLTF)?",
                default=False,
                style=custom_style_fancy
            ).ask()

            export = set()

            if export_input:
                export_formats = questionary.checkbox(
                    "Select export formats:",
                    choices=["fbx", "glb"],
                    style=custom_style_fancy,
                    validate=lambda x: True if len(x) > 0 else "You must select at least one format."
                ).ask()

                if export_formats:
                    export.update(export_formats)
                    print(colours.CYAN, f"Exporting to: {export}")
                else:
                    print(colours.RED, "No export formats selected. Skipping export.")

            if verbose_input is None or debug_sleep_input is None or export_input is None:
                print(colours.RED, "Model conversion configuration err. Skipping.")
            else:
                run_model.main(verbose=verbose_input, debug_sleep=debug_sleep_input, export=export)

        elif choice == "Extract Textures (.txd -> .png)":
            print(colours.GREEN, f"Running: {choice}")
            import Modules.Texture.run as run_texture
            run_texture.main()

        elif choice == "Convert Videos (.vp6 -> .ogv)":
            print(colours.GREEN, f"Running: {choice}")
            import Modules.Video.run as run_video
            run_video.main()

        elif choice == "Convert Audio (.snu -> .wav)":
            print(colours.GREEN, f"Running: {choice}")
            import Modules.Audio.run as run_audio
            run_audio.main()

        # elif choice == "Prepare for Godot":
        #     print(colours.GREEN, f"Running: {choice}")
        #     import Modules.Godot.run as run_godot
        #     run_godot.main()

        elif choice == "Run all Steps (1-5)":
            print(colours.GREEN, f"Running: {choice}")
            # --- Logic for running steps 1-5 sequentially ---

            print(colours.YELLOW, "\n--- Starting Step: Extract Archives ---")
            if Path('Modules\\Extract').exists():
                import Modules.Extract.run as run_qbms
                output_dir_extract = Path('Modules\\Extract\\GameFiles\\quickbms_out')
                if not output_dir_extract.exists() or not any(output_dir_extract.iterdir()):
                    print(colours.CYAN, "Running Archive Extraction (run_qbms)...")
                    run_qbms.main()
                else:
                    print(colours.CYAN, f"Extraction output directory '{output_dir_extract}' already exists and is not empty. Skipping extraction.")
            else:
                print(colours.RED, "Extract module not found. Skipping.")


            print(colours.YELLOW, "\n--- Starting Step: Convert Models ---")
            if Path('Modules\\Model').exists():
                import Modules.Model.run as run_model
                output_dir_model = Path('Modules\\Model\\GameFiles\\blend_out')
                if not output_dir_model.exists() or not any(output_dir_model.iterdir()):
                    print(colours.CYAN, "Running Model Conversion (run_model)...")
                    verbose_input = questionary.confirm("Model Conversion: Enable verbose output?", default=False, style=custom_style_fancy).ask()
                    debug_sleep_input = questionary.confirm("Model Conversion: Enable debug sleep?", default=False, style=custom_style_fancy).ask()
                    export_input = questionary.confirm("Model Conversion: Export additional formats (FBX/GLTF)?", default=True, style=custom_style_fancy).ask()

                    if verbose_input is None or debug_sleep_input is None or export_input is None:
                        print(colours.RED, "Model conversion configuration cancelled. Skipping.")
                    else:
                        run_model.main(verbose=verbose_input, debug_sleep=debug_sleep_input, export=export_input)
                else:
                    print(colours.CYAN, f"Model output directory '{output_dir_model}' already exists and is not empty. Skipping model conversion.")
            else:
                print(colours.RED, "Model module not found. Skipping.")

            print(colours.YELLOW, "\n--- Starting Step: Extract Textures ---")
            if Path('Modules\\Texture').exists():
                import Modules.Texture.run as run_texture
                output_dir_texture = Path('Modules\\Texture\\GameFiles\\Textures_out')
                if not output_dir_texture.exists() or not any(output_dir_texture.iterdir()):
                    print(colours.CYAN, "Running Texture Extraction (run_texture)...")
                    run_texture.main()
                else:
                    print(colours.CYAN, f"Texture output directory '{output_dir_texture}' already exists and is not empty. Skipping texture extraction.")
            else:
                print(colours.RED, "Texture module not found. Skipping.")

            print(colours.YELLOW, "\n--- Starting Step: Convert Videos ---")
            if Path('Modules\\Video').exists():
                import Modules.Video.run as run_video
                output_dir_video_check = Path('Modules\\Video\\GameFiles\\Assets_1_Video_Movies')
                if not output_dir_video_check.exists() or not any(f for f in output_dir_video_check.glob('*.ogv') if f.is_file()):
                    print(colours.CYAN, "Running Video Conversion (run_video)...")
                    run_video.main()
                else:
                    print(colours.CYAN, f"Video output directory '{output_dir_video_check}' appears to contain '.ogv' files. Skipping video conversion.")
            else:
                print(colours.RED, "Video module not found. Skipping.")

            print(colours.YELLOW, "\n--- Starting Step: Convert Audio ---")
            if Path('Modules\\Audio').exists():
                import Modules.Audio.run as run_audio
                output_dir_audio_check = Path('Modules\\Audio\\GameFiles\\Assets_1_Audio_Streams')
                if not output_dir_audio_check.exists() or not any(f for f in output_dir_audio_check.glob('*.wav') if f.is_file()):
                    print(colours.CYAN, "Running Audio Conversion (run_audio)...")
                    run_audio.main(project_path=path_value)
                else:
                    print(colours.CYAN, f"Audio output directory '{output_dir_audio_check}' appears to contain '.wav' files. Skipping audio conversion.")
            else:
                print(colours.RED, "Audio module not found. Skipping.")

            print(colours.GREEN, "\n--- ALL Essential Steps Completed ---")

        else: # Should not be reached if choices are handled correctly
            print(colours.RED, f"Invalid selection: {choice}")

        # After an operation (or "Run all Steps") is done, pause before re-displaying menu
        if choice != "Exit" and choice is not None:
            print(colours.MAGENTA, "\nOperation finished. Press any key to return to the menu.")
            input()
            # The loop will then clear the screen and show the menu again

else:
    print(colours.RED, "Error: One or more essential 'Modules' subdirectories are missing.")
    print(colours.YELLOW, "Please ensure Modules, Modules\\Extract, Modules\\Model, etc., exist.")
    # This exit() is fine as it's for a fatal startup error

# This part is reached only after breaking from the loop (i.e., user selected Exit)
print(colours.MAGENTA, "\nAll operations exited. Press any key to close the tool.")
input()