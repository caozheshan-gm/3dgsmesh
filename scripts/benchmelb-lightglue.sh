#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export PATH=/data/envs/sfm-lightglue/bin:$PATH TORCH_HOME=/data/cache/torch OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
p=/data/projects/benchmelb-20261018/lightglue
mkdir -p "$p/logs" "$p/sparse"
exec > >(tee "$p/logs/stages.log") 2>&1
trap 'echo "FAILED line=$LINENO" > "$p/logs/FAILED"' ERR
python /data/apps/benchmelb-lightglue.py
colmap matches_importer --database_path "$p/database.db" --match_list_path "$p/raw-matches.txt" --match_type raw --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8 > "$p/logs/verify.log" 2>&1
colmap mapper --database_path "$p/database.db" --image_path /data/projects/benchmelb-20261018/input --output_path "$p/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001 > "$p/logs/mapper.log" 2>&1
for m in "$p"/sparse/*; do
 if test -d "$m"; then colmap model_analyzer --path "$m" > "$p/logs/model-$(basename "$m").txt" 2>&1; fi
done
touch "$p/logs/SFM_COMPLETE"
