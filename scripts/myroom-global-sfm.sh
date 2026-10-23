#!/bin/bash
set -euo pipefail
source /data/apps/activate-sugar.sh
p=/data/projects/myroom-20261017
exec > >(tee "$p/logs/global-sfm.log") 2>&1
mkdir -p "$p/distorted/sparse-global"
colmap exhaustive_matcher --database_path "$p/distorted/database.db" --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8
colmap mapper --database_path "$p/distorted/database.db" --image_path "$p/input" --output_path "$p/distorted/sparse-global" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001
for m in "$p"/distorted/sparse-global/*; do
  test -d "$m" && colmap model_analyzer --path "$m" > "$p/logs/global-model-$(basename "$m").txt" 2>&1
done
touch "$p/logs/GLOBAL_SFM_COMPLETE"
