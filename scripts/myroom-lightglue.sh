#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=8 TORCH_HOME=/data/cache/torch
p=/data/projects/myroom-sfm-v2/lightglue
mkdir -p "$p/logs" "$p/sparse"
exec > >(tee "$p/logs/run.log") 2>&1
/data/envs/sfm-lightglue/bin/python /data/apps/myroom-lightglue.py
export QT_QPA_PLATFORM=offscreen
colmap matches_importer --database_path "$p/database.db" --match_list_path "$p/raw-matches.txt" --match_type raw --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8
colmap mapper --database_path "$p/database.db" --image_path /data/projects/myroom-sfm-v2/sharp-pinhole/input --output_path "$p/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001 --Mapper.init_min_tri_angle 4
for m in "$p"/sparse/*; do
 test -d "$m" && colmap model_analyzer --path "$m" > "$p/logs/model-$(basename "$m").txt" 2>&1
done
touch "$p/logs/SFM_COMPLETE"
