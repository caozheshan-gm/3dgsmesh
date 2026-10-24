"""Run video -> frames -> COLMAP -> 3DGS using the existing A/B/C scripts."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


# Edit these settings, then run this file in VS Code with the gs-main interpreter.
VIDEO_PATH = Path.home() / "Desktop" / "BenchMelb-KIRI.mp4"
FPS = 3
JPEG_QUALITY = 2  # FFmpeg range: 1 (best) to 31 (worst).
ITERATIONS = 7000
RESOLUTION = 2  # 2 means half of the original image width and height.
FFMPEG = "ffmpeg"


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    scripts = Path(__file__).resolve().parent
    video = Path(VIDEO_PATH).expanduser().resolve()
    data = repo / "data"
    output = repo / "output"

    if not video.is_file():
        raise SystemExit(f"Video not found: {video}. Edit VIDEO_PATH at the top of this file.")
    if FPS <= 0 or not 1 <= JPEG_QUALITY <= 31:
        raise SystemExit("Set FPS > 0 and JPEG_QUALITY between 1 and 31.")
    if not 1 <= ITERATIONS <= 30000 or RESOLUTION not in (1, 2, 4, 8):
        raise SystemExit("Set ITERATIONS to 1–30000 and RESOLUTION to 1, 2, 4, or 8.")
    if not shutil.which(FFMPEG):
        raise SystemExit("FFmpeg not found. Install it or set FFMPEG to ffmpeg.exe's full path.")
    colmap = os.environ.get("COLMAP_BIN") or shutil.which("colmap")
    if not colmap or not Path(colmap).is_file():
        raise SystemExit("COLMAP not found. Set COLMAP_BIN or put colmap on PATH.")
    if not (repo / "gaussian-splatting" / "train.py").is_file():
        raise SystemExit("Official gaussian-splatting/train.py is missing.")
    for name in ("Aextract_frames.py", "Bconvert.py", "Ctrain.py"):
        if not (scripts / name).is_file():
            raise SystemExit(f"Missing script: {scripts / name}")

    input_dir = data / "input"
    if input_dir.exists() and any(p.name != ".gitkeep" for p in input_dir.iterdir()):
        raise SystemExit(f"data/input already contains files: {input_dir}. Run Dinit_workspace.py first.")
    if any((data / name).exists() for name in ("distorted", "images", "sparse", "stereo")):
        raise SystemExit("Previous COLMAP output exists in data/. Run Dinit_workspace.py first.")
    if output.exists() and any(p.name != ".gitkeep" for p in output.iterdir()):
        raise SystemExit(f"output already contains files: {output}. Run Dinit_workspace.py first.")

    stages = (
        ("1/3 Extract video frames", [sys.executable, str(scripts / "Aextract_frames.py"),
                                      "--video", str(video), "--fps", str(FPS),
                                      "--jpeg-quality", str(JPEG_QUALITY), "--ffmpeg", FFMPEG]),
        ("2/3 Solve cameras with COLMAP", [sys.executable, str(scripts / "Bconvert.py")]),
        ("3/3 Train 3DGS", [sys.executable, str(scripts / "Ctrain.py"),
                            "--iterations", str(ITERATIONS), "--resolution", str(RESOLUTION)]),
    )
    print(f"Video: {video}", flush=True)
    print(f"Python: {sys.executable}", flush=True)
    for label, command in stages:
        print(f"\n=== {label} ===", flush=True)
        subprocess.run(command, cwd=repo, check=True)

    ply = output / "point_cloud" / f"iteration_{ITERATIONS}" / "point_cloud.ply"
    print(f"\nFinished. 3DGS model: {ply}", flush=True)


if __name__ == "__main__":
    main()
