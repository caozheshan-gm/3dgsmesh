#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export OMP_NUM_THREADS=8
p=/data/projects/myroom-sfm-v2/sharp-pinhole
mkdir -p "$p/candidates" "$p/input" "$p/sparse" "$p/logs"
exec > >(tee "$p/logs/run.log") 2>&1
trap 'status=$?; echo "FAILED $status line=$LINENO" >> "$p/logs/FAILED"; exit "$status"' ERR
ffmpeg -hide_banner -loglevel warning -threads 6 -i /data/projects/myroom-20261017/myroom.mov -vf 'fps=12,scale=2000:2000:force_original_aspect_ratio=decrease:force_divisible_by=2,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=full,format=yuvj420p' -q:v 2 -y "$p/candidates/candidate_%05d.jpg"
python /data/apps/myroom-v2-select-frames.py
touch "$p/logs/FRAMES_COMPLETE"
colmap feature_extractor --database_path "$p/database.db" --image_path "$p/input" --ImageReader.single_camera 1 --ImageReader.camera_model PINHOLE --ImageReader.default_focal_length_factor 0.8 --SiftExtraction.use_gpu 0 --SiftExtraction.num_threads 8 --SiftExtraction.max_image_size 2000 --SiftExtraction.max_num_features 16384
colmap sequential_matcher --database_path "$p/database.db" --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8 --SiftMatching.guided_matching 1 --SequentialMatching.overlap 30 --SequentialMatching.quadratic_overlap 1
colmap mapper --database_path "$p/database.db" --image_path "$p/input" --output_path "$p/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001 --Mapper.init_min_tri_angle 4
for m in "$p"/sparse/*; do
 test -d "$m" && colmap model_analyzer --path "$m" > "$p/logs/model-$(basename "$m").txt" 2>&1
done
touch "$p/logs/SFM_COMPLETE"
