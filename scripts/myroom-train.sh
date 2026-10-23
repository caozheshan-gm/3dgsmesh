#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=8
project=/data/projects/myroom-20261017
model=/data/apps/SuGaR/output/vanilla_gs/myroom-20261017
exec > >(tee "$project/logs/train-stages.log") 2>&1
trap 'status=$?; echo "FAILED exit=$status line=$LINENO" >> "$project/logs/TRAIN_FAILED"; exit "$status"' ERR
colmap image_undistorter --image_path "$project/input" --input_path "$project/distorted/sparse-global/0" --output_path "$project" --output_type COLMAP
mkdir -p "$project/sparse/0"
for file in cameras.bin images.bin points3D.bin; do
  mv "$project/sparse/$file" "$project/sparse/0/$file"
done
touch "$project/logs/UNDISTORT_COMPLETE"
python gaussian_splatting/train.py -s "$project" -m "$model" --iterations 7000 --save_iterations 7000 --test_iterations 7000 --eval --data_device cpu > "$project/logs/vanilla-train.log" 2>&1
test -s "$model/point_cloud/iteration_7000/point_cloud.ply"
touch "$project/logs/VANILLA_COMPLETE"
python gaussian_splatting/render.py -m "$model" --iteration 7000 --skip_train > "$project/logs/vanilla-render.log" 2>&1
python train.py -s "$project" -c "$model/" -i 7000 -r dn_consistency --low_poly True --refinement_time short --export_uv_textured_mesh True --export_ply True --eval True > "$project/logs/sugar-train.log" 2>&1
touch "$project/logs/TRAIN_SCRIPT_COMPLETE"
