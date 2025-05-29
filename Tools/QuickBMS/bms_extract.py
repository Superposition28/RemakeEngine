import os
import subprocess
import argparse

def extract_str_file(file_path: str) -> None:
    """
    Extracts a file using QuickBMS if it matches the specified file extension.

    Args:
        file_path (str): The path to the file to extract.
    """
    global QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR, FILE_EXTENSIONS

    print(f"Extracting {file_path}...")

    #if not file_path.lower().endswith(FILE_EXTENSIONS.lower()):
    #    print(f"Skipping non-{FILE_EXTENSIONS} file: {file_path}")
    #    return
    #else:
    #    print(f"Processing {file_path}... with extension {FILE_EXTENSIONS}")

    # Create output directory for this str file
    relative_path = os.path.relpath(file_path, start=STR_INPUT_DIR)
    # if in path A:\\Dev\\Games\\TheSimpsonsGame\\PAL\\test\\in\\loc\loc_global.txd and out path is A:\Dev\Games\TheSimpsonsGame\PAL\test\out then outpath is A:\Dev\Games\TheSimpsonsGame\PAL\test\out\loc\loc_global_txd
    output_dir = os.path.join(OUTPUT_BASE_DIR, os.path.dirname(relative_path))
    output_dir = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0]+ "_" + FILE_EXTENSIONS[1:])
    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting {file_path} to {output_dir}...")

    try:
        subprocess.run(
            [QUICKBMS_EXE, "-o", BMS_SCRIPT, file_path, output_dir],
            check=True
        )
        print(f"Done: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Extraction failed for {file_path}: {e}")

def main():
    global QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR, FILE_EXTENSIONS
    parser = argparse.ArgumentParser(description="Extract files via QuickBMS")
    parser.add_argument("-e", "--quickbms", help="Path to quickbms.exe")
    parser.add_argument("-s", "--script", help="Path to .bms script")
    parser.add_argument("-i", "--input", help="Input directory or file")
    parser.add_argument("-o", "--output", help="Base output directory")
    parser.add_argument("-ext", "--extension", help="File extension to process")
    parser.add_argument("paths", nargs="*", help="Files or directories to process")
    args = parser.parse_args()

    if not args.quickbms or not args.script or not args.input or not args.output or not args.extension:
        print("Usage: bms_extract.py -e <quickbms_path> -s <script_path> -i <input_dir> -o <output_dir> [-ext <file_extension>] [<files_or_dirs>] -ext <.file_extension>")
        return
    else:
        print("Arguments:")
        print(f"  quickbms: {args.quickbms}")
        print(f"  script: {args.script}")
        print(f"  input: {args.input}")
        print(f"  output: {args.output}")
        print(f"  extension: {args.extension}")
        print(f"  paths: {args.paths}")

    QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR, FILE_EXTENSIONS = (
        args.quickbms, args.script, args.input, args.output, args.extension
    )

    targets = args.paths or [STR_INPUT_DIR]
    if not targets:
        print("No files or directories specified. Exiting.")
        return
    print(f"Targets: {targets}")
    for path in targets:
        if os.path.isdir(path):
            print(f"Processing directory: {path}")
            for root, _, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(FILE_EXTENSIONS.lower()):
                        extract_str_file(os.path.join(root, f))
                    elif FILE_EXTENSIONS == "*":
                        extract_str_file(os.path.join(root, f))
                    #else:
                    #    print(f"Skipping non-{FILE_EXTENSIONS} file: {f}")
        else:
            print(f"Processing file: {path}")
            extract_str_file(path)

if __name__ == "__main__":
    main()
