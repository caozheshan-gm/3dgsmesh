"""Train the vendored official 3DGS code from data/ into output/."""

import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description="Train 3DGS from the converted data/ folder")
parser.add_argument("--iterations", type=int, default=7000)
parser.add_argument("--resolution", type=int, choices=(1, 2, 4, 8), default=2)
args = parser.parse_args()
if not 1 <= args.iterations <= 30000:
    parser.error("--iterations must be between 1 and 30000")

repo = Path(__file__).resolve().parents[2]
data = repo / "data"
output = repo / "output"
upstream = repo / "gaussian-splatting"
trainer = upstream / "train.py"
for name in ("cameras.bin", "images.bin", "points3D.bin"):
    file = data / "sparse" / "0" / name
    if not file.is_file():
        raise SystemExit(f"Missing {file}; run script/windows/Bconvert.py first.")
if not (data / "images").is_dir():
    raise SystemExit("Missing data/images; run script/windows/Bconvert.py first.")
if not trainer.is_file():
    raise SystemExit(f"Official source missing: {trainer}")
if output.exists() and any(path.name != ".gitkeep" for path in output.iterdir()):
    raise SystemExit(f"Output folder is not empty: {output}. Move it before starting another run.")
output.mkdir(exist_ok=True)

print(f"Training {args.iterations} iterations at resolution 1/{args.resolution}", flush=True)
subprocess.run(
    [sys.executable, str(trainer), "-s", str(data), "-m", str(output),
     "--iterations", str(args.iterations), "--resolution", str(args.resolution),
     "--data_device", "cpu", "--disable_viewer", "--test_iterations", str(args.iterations)],
    cwd=upstream,
    check=True,
)
ply = output / "point_cloud" / f"iteration_{args.iterations}" / "point_cloud.ply"
if not ply.is_file():
    raise SystemExit(f"Training finished but PLY is missing: {ply}")
print(f"3DGS PLY: {ply}", flush=True)
