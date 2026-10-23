#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
sfm=/data/projects/myroom-sfm-v2
p=/data/projects/myroom-v2-full
model=/data/apps/SuGaR/output/vanilla_gs/myroom-v2-full
test -f "$sfm/APPROVED_FOR_TRAINING"

mkdir -p "$p/logs"
exec > >(tee "$p/logs/stages.log") 2>&1
trap 'status=$?; echo "FAILED $status line=$LINENO" >> "$p/logs/FAILED"; exit "$status"' ERR
selected_model=$(cat "$sfm/APPROVED_FOR_TRAINING")
test -s "$selected_model/images.bin"
test -s "$selected_model/cameras.bin"
colmap image_undistorter --image_path /data/projects/myroom-sfm-v2/sharp-pinhole/input --input_path "$selected_model" --output_path "$p" --output_type COLMAP --max_image_size 1600
mkdir -p "$p/sparse/0"
for f in cameras.bin images.bin points3D.bin; do mv "$p/sparse/$f" "$p/sparse/0/$f"; done
touch "$p/logs/UNDISTORT_COMPLETE"
python gaussian_splatting/train.py -s "$p" -m "$model" --iterations 7000 --save_iterations 7000 --checkpoint_iterations 7000 --test_iterations 7000 --eval --data_device cpu > "$p/logs/vanilla-train.log" 2>&1
test -s "$model/point_cloud/iteration_7000/point_cloud.ply"
touch "$p/logs/VANILLA_COMPLETE"
python gaussian_splatting/render.py -m "$model" --iteration 7000 --skip_train > "$p/logs/vanilla-render.log" 2>&1
touch "$p/logs/RENDER_COMPLETE"
# Mesh is intentionally a separate step after inspection of the trained scene.
