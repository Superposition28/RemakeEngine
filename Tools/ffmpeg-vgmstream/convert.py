"""
Unified CLI tool for converting media using FFmpeg or vgmstream-cli.
"""
import argparse
import subprocess
from pathlib import Path

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Utils')))
from printer import print, colours, print_error, print_verbose, print_debug, printc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert media files using FFmpeg or vgmstream-cli."
    )
    parser.add_argument(
        "--mode", "-m",
        required=True,
        choices=["ffmpeg", "vgmstream"],
        help="Conversion mode: 'ffmpeg' for video, 'vgmstream' for audio."
    )
    # Common args
    parser.add_argument("--source", "-s", required=True, help="Path to the source directory.")
    parser.add_argument("--target", "-t", required=True, help="Path to the target directory.")
    parser.add_argument("--input-ext", "-i", required=True, help="Input file extension (with dot).")
    parser.add_argument("--output-ext", "-o", required=True, help="Output file extension (with dot).")

    # FFmpeg-specific
    parser.add_argument("--ffmpeg-path", "-f", help="Path to the FFmpeg executable.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--video-codec", default="libtheora", help="FFmpeg video codec.")
    parser.add_argument("--video-quality", default="10", help="FFmpeg video quality.")
    parser.add_argument("--audio-codec", default="libvorbis", help="FFmpeg audio codec.")
    parser.add_argument("--audio-quality", default="10", help="FFmpeg audio quality.")

    # vgmstream-specific
    parser.add_argument("--vgmstream-cli", help="Path or name of the vgmstream-cli tool.")

    # Logging
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output.")
    parser.add_argument("--debug", "-d", action="store_true", help="Debug output.")

    return parser.parse_args()

# -------------------- FFmpeg logic -------------------- #
def convert_with_ffmpeg(args):
    if not args.ffmpeg_path:
        print_error("FFmpeg path is required for ffmpeg mode.")
        sys.exit(1)

    source_dir = Path(args.source).resolve()
    target_dir = Path(args.target).resolve()
    ffmpeg_executable = args.ffmpeg_path

    if not source_dir.is_dir():
        print_error(f"Source directory not found: {source_dir}")
        sys.exit(1)

    files = list(source_dir.rglob(f"*{args.input_ext}"))
    if not files:
        print(colours.YELLOW, f"No '{args.input_ext}' files found in {source_dir}.")
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
        subprocess.run(cmd)

    print(colours.GREEN, "FFmpeg conversion finished.")

# -------------------- vgmstream logic -------------------- #
def convert_with_vgmstream(args):
    if not args.vgmstream_cli:
        print_error("vgmstream-cli path is required for vgmstream mode.")
        sys.exit(1)

    vgmstream_cli = Path(args.vgmstream_cli)
    if vgmstream_cli.is_file():
        vgmstream_cli = vgmstream_cli.resolve()
    else:
        vgmstream_cli = args.vgmstream_cli  # Allow PATH resolution

    source_dir = Path(args.source).resolve()
    target_dir = Path(args.target).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    files = list(source_dir.rglob(f"*{args.input_ext}"))
    if not files:
        print(colours.CYAN, f"No {args.input_ext} files found in: {source_dir}")
        return

    print(colours.CYAN, f"Found {len(files)} {args.input_ext} files.")
    skip_count = 0
    success_count = 0
    error_count = 0

    for src in files:
        rel = src.relative_to(source_dir)
        dest_file = (target_dir / rel).with_suffix(args.output_ext)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        if dest_file.exists():
            skip_count += 1
            continue

        print(colours.CYAN, f"Converting {rel} -> {dest_file.relative_to(target_dir)}")
        cmd = [str(vgmstream_cli), "-o", str(dest_file), str(src)]
        try:
            subprocess.run(cmd, check=True, text=True, capture_output=False)
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(colours.CYAN, f"Error converting {rel}: {e.stderr}", file=sys.stderr)
            if dest_file.exists():
                try:
                    dest_file.unlink()
                except Exception:
                    pass
            error_count += 1

    print(colours.CYAN, "vgmstream conversion finished.")
    print(colours.CYAN, f"Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}")

# -------------------- Main Entry Point -------------------- #
def main():
    args = parse_args()

    # Enable optional logging
    if args.debug:
        print_debug.enable()
    if args.verbose or args.debug:
        print_verbose.enable()

    print(colours.CYAN, f"--- Starting {args.mode.upper()} Conversion ---")

    if args.mode == "ffmpeg":
        convert_with_ffmpeg(args)
    elif args.mode == "vgmstream":
        convert_with_vgmstream(args)

    print(colours.CYAN, "--- Conversion Completed ---")

"""

FFmpeg mode:
python Tools/ffmpeg-vgmstream/convert.py -m ffmpeg -s ./videos -t ./output_videos -f ffmpeg.exe -i .vp6 -o .ogv --overwrite

vgmstream mode:
python Tools/ffmpeg-vgmstream/convert.py -m vgmstream -s ./audio -t ./output_audio --vgmstream-cli vgmstream-cli.exe -i .snu -o .wav


"""

if __name__ == "__main__":
    main()
