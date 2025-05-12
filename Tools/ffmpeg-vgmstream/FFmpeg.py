#!/usr/bin/env python3
"""
CLI tool for converting videos using FFmpeg.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from printer import print, print_error, print_verbose, print_debug, colours

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively convert video files from one format to another using FFmpeg."
    )
    parser.add_argument(
        "--source", "-s",
        required=True,
        help="Path to the source directory containing input videos."
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Path to the target directory where converted videos will be saved."
    )
    parser.add_argument(
        "--ffmpeg-path", "-f",
        required=True,
        help="Path to the FFmpeg executable."
    )
    parser.add_argument(
        "--input-ext", "-i",
        default=".vp6",
        help="Input file extension (including dot), e.g. .vp6"
    )
    parser.add_argument(
        "--output-ext", "-o",
        default=".ogv",
        help="Output file extension (including dot), e.g. .ogv"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite existing files without prompting."
    )
    parser.add_argument(
        "--video-codec",
        default="libtheora",
        help="Video codec to use for conversion."
    )
    parser.add_argument(
        "--video-quality",
        default="10",
        help="Video quality setting (codec-specific), e.g. 0-10 for Theora."
    )
    parser.add_argument(
        "--audio-codec",        
        default="libvorbis",
        help="Audio codec to use for conversion."
    )
    parser.add_argument(
        "--audio-quality",
        default="10",
        help="Audio quality setting (codec-specific), e.g. 0-10 for Vorbis."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    # Configure logging
    if args.debug:
        print_debug.enable()
    if args.verbose or args.debug:
        print_verbose.enable()

    print(colours.CYAN, "--- Starting Video Conversion Process ---")

    source_dir = Path(args.source).resolve()
    target_dir = Path(args.target).resolve()
    ffmpeg_executable = args.ffmpeg_path

    print_verbose(f"Source directory: {source_dir}")
    print_verbose(f"Target directory: {target_dir}")

    if not source_dir.is_dir():
        print_error(f"Source directory not found: {source_dir}")
        sys.exit(1)

    # Find files recursively
    input_pattern = f"*{args.input_ext}"
    files = list(source_dir.rglob(input_pattern))
    if not files:
        print(colours.YELLOW, f"No '{args.input_ext}' files found in {source_dir}.")
        print(colours.CYAN, "--- Conversion Finished (No files) ---")
        return

    print(colours.CYAN, f"Found {len(files)} '{args.input_ext}' files.")
    errors = 0

    for src in files:
        rel = src.relative_to(source_dir)
        dest_base = target_dir / rel.parent / src.stem
        dest_file = dest_base.with_suffix(args.output_ext)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        if dest_file.exists() and not args.overwrite:
            print(colours.YELLOW, f"Skipping existing: {dest_file}")
            continue

        print(colours.CYAN, f"Converting {src.name} -> {dest_file.name}")
        cmd = [
            ffmpeg_executable,
            *( ["-y"] if args.overwrite else [] ),
            "-i", str(src),
            "-c:v", args.video_codec,
            "-q:v", args.video_quality,
            "-c:a", args.audio_codec,
            "-q:a", args.audio_quality,
            str(dest_file)
        ]
        print_debug(f"Command: {' '.join(cmd)}")

        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(colours.GREEN, f"Success: {dest_file.name}")
        else:
            errors += 1
            print_error(f"Error converting {src.name}: return code {result.returncode}")

    print(colours.CYAN, "--- Video Conversion Process Finished ---")
    if errors:
        print(colours.RED, f"{errors} error(s) occurred.")
        sys.exit(1)
    else:
        print(colours.GREEN, "All conversions completed successfully.")

if __name__ == "__main__":
    main()
