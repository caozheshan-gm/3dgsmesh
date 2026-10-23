#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
p=/data/projects/benchmelb-20261018
mkdir -p "$p/candidates" "$p/input" "$p/distorted/sparse" "$p/logs"
exec > >(tee "$p/logs/prepare-sfm.log") 2>&1
trap 'echo "FAILED line=$LINENO" > "$p/logs/PREPARE_FAILED"' ERR
ffmpeg -hide_banner -loglevel warning -i "$p/BenchMelb-KIRI.mp4" -vf fps=10 -q:v 2 "$p/candidates/candidate_%05d.jpg"
python - <<'PY'
from pathlib import Path
import json, shutil
import numpy as np
from PIL import Image
p=Path('/data/projects/benchmelb-20261018')
files=sorted((p/'candidates').glob('*.jpg'));rows=[]
for i in range(0,len(files),2):
    scores=[]
    for f in files[i:i+2]:
        im=Image.open(f).convert('L');im.thumbnail((800,450));a=np.asarray(im,dtype=np.float32)
        lap=a[:-2,1:-1]+a[2:,1:-1]+a[1:-1,:-2]+a[1:-1,2:]-4*a[1:-1,1:-1]
        scores.append((float(lap.var()),f))
    score,f=max(scores,key=lambda x:x[0]);dst=p/'input'/f'frame_{len(rows)+1:05d}.jpg';shutil.copy2(f,dst)
    rows.append(dict(image=dst.name,candidate=f.name,candidate_time_seconds=(int(f.stem.split('_')[-1])-1)/10,sharpness=score))
(p/'frame-selection.json').write_text(json.dumps(rows,indent=2));print('Selected',len(rows),'from',len(files),flush=True)
PY
colmap feature_extractor --database_path "$p/distorted/database.db" --image_path "$p/input" --ImageReader.single_camera 1 --ImageReader.camera_model SIMPLE_RADIAL --SiftExtraction.use_gpu 0 --SiftExtraction.num_threads 8 --SiftExtraction.max_image_size 1600 --SiftExtraction.max_num_features 8192
colmap sequential_matcher --database_path "$p/distorted/database.db" --SiftMatching.use_gpu 0 --SiftMatching.num_threads 8 --SequentialMatching.overlap 20 --SequentialMatching.quadratic_overlap 1 --SiftMatching.guided_matching 1
colmap mapper --database_path "$p/distorted/database.db" --image_path "$p/input" --output_path "$p/distorted/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001
for m in "$p"/distorted/sparse/*; do
  if test -d "$m"; then colmap model_analyzer --path "$m" > "$p/logs/model-$(basename "$m").txt" 2>&1; fi
done
touch "$p/logs/SFM_COMPLETE"
