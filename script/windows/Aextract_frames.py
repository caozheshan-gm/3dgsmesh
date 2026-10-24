"""Extract video frames into data/input for COLMAP and 3DGS training."""

from pathlib import Path
import shutil
import subprocess


# Edit these settings before starting a new video experiment.
VIDEO_PATH = Path.home() / "Desktop" / "BenchMelb-KIRI.mp4"
FPS = 3  # Frames extracted per second; 3 means one frame about every 0.33 s.
JPEG_QUALITY = 2  # For FFmpeg's JPEG encoder, smaller is better (1-31).
FFMPEG = "ffmpeg"  # Or set this to the full path of ffmpeg.exe.


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    output_dir = repo / "data" / "input"
    video = Path(VIDEO_PATH).expanduser()

    if not video.is_file():
        raise SystemExit(f"Video not found: {video}\nEdit VIDEO_PATH at the top of this script.")
    if FPS <= 0:
        raise SystemExit("FPS must be greater than 0.")
    if not 1 <= JPEG_QUALITY <= 31:
        raise SystemExit("JPEG_QUALITY must be between 1 and 31.")
    ffmpeg = shutil.which(FFMPEG)
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
               "-vf", f"fps={FPS}", "-q:v", str(JPEG_QUALITY), str(pattern)]
    print(f"Video: {video}", flush=True)
    print(f"Output: {output_dir}", flush=True)
    print(f"Extracting {FPS} frames/s at JPEG quality {JPEG_QUALITY}...", flush=True)
    subprocess.run(command, check=True)

    count = sum(1 for path in output_dir.glob("frame_*.jpg") if path.is_file())
    if not count:
        raise SystemExit("FFmpeg finished but produced no JPG frames. Check the video and FFmpeg output.")
    print(f"Extracted {count} frames. Next: python script\\windows\\convert.py", flush=True)


if __name__ == "__main__":
    main()
