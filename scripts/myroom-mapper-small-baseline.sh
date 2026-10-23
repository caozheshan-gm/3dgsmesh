#!/bin/bash
set -euo pipefail
source /data/apps/activate-sugar.sh
p=/data/projects/myroom-20261017
mkdir -p "$p/distorted/sparse-small-baseline"
colmap mapper --database_path "$p/distorted/database.db" --image_path "$p/input" --output_path "$p/distorted/sparse-small-baseline" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001 --Mapper.init_min_tri_angle 4 > "$p/logs/small-baseline-sfm.log" 2>&1
for m in "$p"/distorted/sparse-small-baseline/*; do
 test -d "$m" && colmap model_analyzer --path "$m" > "$p/logs/small-baseline-model-$(basename "$m").txt" 2>&1
done
touch "$p/logs/SMALL_BASELINE_SFM_COMPLETE"
