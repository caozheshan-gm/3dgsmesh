"""Convert data/input JPG/PNG images into the official 3DGS COLMAP layout."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
data = repo / "data"
photos = data / "input"
upstream = repo / "gaussian-splatting"
converter = upstream / "convert.py"

photos.mkdir(parents=True, exist_ok=True)
images = [p for p in photos.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
if len(images) < 3:
    raise SystemExit(f"Place JPG/PNG photos in {photos} (found {len(images)}; need at least 3).")
if not converter.is_file():
    raise SystemExit(f"Official source missing: {converter}")
if any(part.isspace() for part in str(data)) or " " in str(data):
    raise SystemExit("The current official convert.py needs a repo path without spaces.")
if any((data / name).exists() for name in ("distorted", "images", "sparse")):
    raise SystemExit("Conversion output already exists in data/. Move or remove it before converting a new photo set.")

colmap = os.environ.get("COLMAP_BIN") or shutil.which("colmap")
if not colmap or not Path(colmap).is_file():
    raise SystemExit("COLMAP not found. Put colmap on PATH or set COLMAP_BIN to its COLMAP.bat/colmap.exe path.")

print(f"Converting {len(images)} photos with {colmap}", flush=True)
subprocess.run(
    [sys.executable, str(converter), "-s", str(data), "--colmap_executable", colmap],
    cwd=upstream,
    check=True,
)
for name in ("cameras.bin", "images.bin", "points3D.bin"):
    if not (data / "sparse" / "0" / name).is_file():
        raise SystemExit(f"COLMAP output missing: data/sparse/0/{name}")
print("Converted data/images and data/sparse/0. Check camera coverage before training.", flush=True)
