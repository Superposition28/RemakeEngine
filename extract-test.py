"""
This script processes game files for The Simpsons Game by performing various tasks such as:
- Extracting assets from STR archives
- Converting 3D models to .blend files
- Extracting textures from .txd archives
- Converting video files from .vp6 to .ogv
- Converting audio files from .snu to .wav
"""

from pathlib import Path
import time

if Path('Modules').exists():
    # step A.2
    if Path('Modules\\Extract').exists():
        import Modules.Extract.run as run_extract

        if not Path('Modules\\Extract\\GameFiles\\quickbms_out').exists():
            print("Running extract .run")
            run_extract.main()
            time.sleep(1)
            print("completed run_extract")
        else:
            print("QuickBMS output already exists. Skipping init and run.")
