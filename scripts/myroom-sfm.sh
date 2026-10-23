#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
project=/data/projects/myroom-20261017
mkdir -p "$project/distorted/sparse" "$project/logs"
exec > >(tee -a "$project/logs/sfm.log") 2>&1
date -Is
colmap feature_extractor --database_path "$project/distorted/database.db" --image_path "$project/input" --ImageReader.single_camera 1 --ImageReader.camera_model OPENCV --SiftExtraction.use_gpu 0 --SiftExtraction.num_threads 8 --SiftExtraction.max_image_size 1600 --SiftExtraction.max_num_features 8192
colmap sequential_matcher --database_path "$project/distorted/database.db" --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8 --SequentialMatching.overlap 20 --SequentialMatching.quadratic_overlap 1
colmap mapper --database_path "$project/distorted/database.db" --image_path "$project/input" --output_path "$project/distorted/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001
for model in "$project"/distorted/sparse/*; do
  if test -d "$model"; then
    colmap model_analyzer --path "$model" > "$project/logs/model-$(basename "$model").txt" 2>&1
  fi
done
date -Is
touch "$project/logs/SFM_COMPLETE"
