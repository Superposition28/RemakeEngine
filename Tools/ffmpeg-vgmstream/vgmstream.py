import subprocess
import sys
from pathlib import Path
import argparse # For parsing command-line arguments
from printer import print, print_error, print_verbose, print_debug, colours


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

"""
This script handles the core audio processing task. It takes command-line
arguments for source and target directories, vgmstream-cli path/command,
and file extensions. It finds audio files with a source extension in the 
source directory, converts them to a target extension using the 
vgmstream-cli tool, and saves them to the target directory while 
preserving the relative folder structure.
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def run(
    audio_source_dir: Path,
    audio_target_dir: Path,
    vgmstream_cli_ref: str, # Can be name or path
    source_ext: str,
    target_ext: str
) -> None:
    """Contains the main logic for finding and processing audio files using pathlib."""

    vgmstream_cli_full_path_str = vgmstream_cli_ref

    def prepare_directories(source_dir: Path, target_dir: Path) -> tuple[Path, Path]:
        """Prepare and validate source and target directories."""
        audio_source_dir_full = source_dir.resolve()
        if not audio_source_dir_full.is_dir():
            print(f"Error: Audio source directory does not exist: {audio_source_dir_full}", file=sys.stderr)
            sys.exit(1)
        audio_target_dir_full = target_dir.resolve()
        audio_target_dir_full.mkdir(parents=True, exist_ok=True)
        return audio_source_dir_full, audio_target_dir_full

    audio_source_dir_full, audio_target_dir_full = prepare_directories(audio_source_dir, audio_target_dir)

    def process_audio_files(
            source_dir_full: Path,
            target_dir_full: Path,
            cli_full_path_str: str,
            src_ext: str,
            tgt_ext: str
        ) -> None:
        """Process audio files by converting them from source_ext to target_ext."""
        source_files = list(source_dir_full.rglob(f'*{src_ext}'))
        if not source_files:
            print(f"No {src_ext} files found in the source directory: {source_dir_full}")
            return
        print(f"Found {len(source_files)} {src_ext} files.")

        pre_existing_target_count = 0
        for source_file_path_check in source_files:
            relative_path_check = source_file_path_check.relative_to(source_dir_full)
            audio_target_path_check = target_dir_full / relative_path_check
            target_file_check = audio_target_path_check.with_suffix(tgt_ext)
            if target_file_check.exists():
                pre_existing_target_count += 1
        
        print(f"Found {pre_existing_target_count} corresponding {tgt_ext} files in the target directory.")

        if pre_existing_target_count == len(source_files) and len(source_files) > 0:
            print("All files appear to be already converted. No action needed.")
            return
        elif pre_existing_target_count > 0:
             print(f"{pre_existing_target_count} files appear to be already converted and will be skipped.")

        skip_count = 0
        success_count = 0
        error_count = 0
        for source_file_path in source_files:
            relative_path = source_file_path.relative_to(source_dir_full)
            audio_target_path = target_dir_full / relative_path
            audio_target_directory = audio_target_path.parent
            audio_target_directory.mkdir(parents=True, exist_ok=True)
            target_file = audio_target_path.with_suffix(tgt_ext)

            if target_file.exists():
                skip_count += 1
                continue

            print(f"Converting '{relative_path}' to '{target_file.relative_to(target_dir_full)}'")
            command = [
                cli_full_path_str,
                "-o", str(target_file),
                str(source_file_path)
            ]
            try:
                result = subprocess.run(command, check=True, text=True, capture_output=True)
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"Error converting {relative_path}: vgmstream-cli failed.", file=sys.stderr)
                print(f"  Command: {' '.join(e.cmd)}", file=sys.stderr)
                print(f"  Return code: {e.returncode}", file=sys.stderr)
                if e.stdout: print(f"  Stdout: {e.stdout.strip()}", file=sys.stderr)
                if e.stderr: print(f"  Stderr: {e.stderr.strip()}", file=sys.stderr)
                
                if target_file.exists():
                    try:
                        target_file.unlink()
                        print(f"  Removed potentially incomplete file: {target_file}", file=sys.stderr)
                    except OSError as unlink_err:
                        print(f"  Warning: Could not remove potentially incomplete file {target_file}: {unlink_err}", file=sys.stderr)
                error_count += 1
            except FileNotFoundError:
                print(f"Error: Command not found '{cli_full_path_str}'. Ensure vgmstream-cli is installed and accessible.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Unexpected error during conversion of {relative_path}: {e}", file=sys.stderr)
                error_count += 1

        print("Processing complete.")
        print(f"Summary: Success={success_count}, Skipped={skip_count}, Errors={error_count}, Total Source Files Found={len(source_files)}")
        if error_count > 0:
            print("Please check the error messages above for details on failed conversions.")

    process_audio_files(
        audio_source_dir_full,
        audio_target_dir_full,
        vgmstream_cli_full_path_str,
        source_ext,
        target_ext
    )

def main() -> None:
    """
    Entry point of the script. Parses command-line arguments
    and initiates audio processing.
    """
    parser = argparse.ArgumentParser(description="Convert audio files using vgmstream-cli.")
    parser.add_argument(
        "audio_source_dir",
        type=Path,
        help="Source directory for audio files."
    )
    parser.add_argument(
        "audio_target_dir",
        type=Path,
        help="Target directory for converted audio files."
    )
    parser.add_argument(
        "vgmstream_cli_ref",
        type=str,
        help="Path or name of the vgmstream-cli executable."
    )
    parser.add_argument(
        "source_ext",
        type=str,
        help="Source audio file extension (e.g. .snu)."
    )
    parser.add_argument(
        "target_ext",
        type=str,
        help="Target audio file extension (e.g. .wav)."
    )

    args = parser.parse_args()

    resolved_audio_source_dir = args.audio_source_dir.resolve()
    resolved_audio_target_dir = args.audio_target_dir.resolve()

    vgmstream_cli_to_use = args.vgmstream_cli_ref
    vgmstream_cli_path_obj = Path(args.vgmstream_cli_ref)
    if vgmstream_cli_path_obj.is_file():
        vgmstream_cli_to_use = str(vgmstream_cli_path_obj.resolve())

    source_ext = args.source_ext if args.source_ext.startswith('.') else '.' + args.source_ext
    target_ext = args.target_ext if args.target_ext.startswith('.') else '.' + args.target_ext

    print(f"Using Audio Source Dir: {resolved_audio_source_dir}")
    print(f"Using Audio Target Dir: {resolved_audio_target_dir}")
    print(f"Using vgmstream-cli reference: {vgmstream_cli_to_use}")
    print(f"Using Source Ext: {source_ext}")
    print(f"Using Target Ext: {target_ext}")

    run(resolved_audio_source_dir, resolved_audio_target_dir, vgmstream_cli_to_use, source_ext, target_ext)
    print("Audio processing task finished.")

if __name__ == "__main__":
    main()
