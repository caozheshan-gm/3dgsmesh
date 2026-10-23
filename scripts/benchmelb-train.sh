#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
p=/data/projects/benchmelb-20261018
test -s "$p/APPROVED_FOR_TRAINING"
mkdir -p "$p/models" "$p/logs"
exec > >(tee "$p/logs/training-stages.log") 2>&1
trap 'echo "FAILED line=$LINENO" > "$p/logs/TRAIN_FAILED"' ERR
model=$(cat "$p/APPROVED_FOR_TRAINING")
colmap image_undistorter --image_path "$p/input" --input_path "$model" --output_path "$p" --output_type COLMAP --max_image_size 1600 > "$p/logs/undistort.log" 2>&1
mkdir -p "$p/sparse/0"
for f in cameras.bin images.bin points3D.bin; do mv "$p/sparse/$f" "$p/sparse/0/$f"; done
python gaussian_splatting/train.py -s "$p" -m "$p/models/3dgs" --iterations 30000 --save_iterations 7000 30000 --checkpoint_iterations 30000 --test_iterations 7000 30000 --eval --data_device cpu > "$p/logs/3dgs-train.log" 2>&1
touch "$p/logs/3DGS_COMPLETE"
python gaussian_splatting/render.py -m "$p/models/3dgs" --iteration 30000 --skip_train > "$p/logs/3dgs-render.log" 2>&1
export PATH=/data/envs/2dgs/bin:$PATH
cd /data/apps/2d-gaussian-splatting
python train.py -s "$p" -m "$p/models/2dgs" --iterations 30000 --save_iterations 7000 30000 --checkpoint_iterations 30000 --test_iterations 7000 30000 --eval --data_device cpu --lambda_dist 100 --lambda_normal 0.05 --depth_ratio 1 > "$p/logs/2dgs-train.log" 2>&1
touch "$p/logs/2DGS_COMPLETE"
python render.py -s "$p" -m "$p/models/2dgs" --iteration 30000 --skip_train --mesh_res 1024 --num_cluster 50 > "$p/logs/2dgs-mesh.log" 2>&1
touch "$p/logs/MESH_COMPLETE"
