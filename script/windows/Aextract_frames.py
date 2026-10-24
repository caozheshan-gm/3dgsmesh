"""Extract video frames into data/input for COLMAP and 3DGS training."""

import argparse
from pathlib import Path
import shutil
import subprocess


# Edit these settings before starting a new video experiment.
VIDEO_PATH = Path.home() / "Desktop" / "BenchMelb-KIRI.mp4"
FPS = 3  # Frames extracted per second; 3 means one frame about every 0.33 s.
JPEG_QUALITY = 2  # For FFmpeg's JPEG encoder, smaller is better (1-31).
FFMPEG = "ffmpeg"  # Or set this to the full path of ffmpeg.exe.


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract JPG frames from a video into data/input")
    parser.add_argument("--video", type=Path, default=VIDEO_PATH)
    parser.add_argument("--fps", type=float, default=FPS)
    parser.add_argument("--jpeg-quality", type=int, default=JPEG_QUALITY)
    parser.add_argument("--ffmpeg", default=FFMPEG)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    output_dir = repo / "data" / "input"
    video = args.video.expanduser()

    if not video.is_file():
        raise SystemExit(f"Video not found: {video}\nEdit VIDEO_PATH or pass --video.")
    if args.fps <= 0:
        raise SystemExit("FPS must be greater than 0.")
    if not 1 <= args.jpeg_quality <= 31:
        raise SystemExit("JPEG_QUALITY must be between 1 and 31.")
    ffmpeg = shutil.which(args.ffmpeg)
    if not ffmpeg:
        raise SystemExit("FFmpeg not found. Put ffmpeg on PATH or set FFMPEG to ffmpeg.exe's full path.")

    output_dir.mkdir(parents=True, exist_ok=True)
    old_images = [
        path for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if old_images:
        raise SystemExit(
            f"{output_dir} already contains {len(old_images)} images. "
            "Move the previous experiment's images out before extracting a new video."
        )

    pattern = output_dir / "frame_%04d.jpg"
    command = [ffmpeg, "-hide_banner", "-n", "-i", str(video),
               "-vf", f"fps={args.fps}", "-q:v", str(args.jpeg_quality), str(pattern)]
    print(f"Video: {video}", flush=True)
    print(f"Output: {output_dir}", flush=True)
    print(f"Extracting {args.fps} frames/s at JPEG quality {args.jpeg_quality}...", flush=True)
    subprocess.run(command, check=True)

    count = sum(1 for path in output_dir.glob("frame_*.jpg") if path.is_file())
    if not count:
        raise SystemExit("FFmpeg finished but produced no JPG frames. Check the video and FFmpeg output.")
    print(f"Extracted {count} frames. Next: python script\\windows\\Bconvert.py", flush=True)


if __name__ == "__main__":
    main()
