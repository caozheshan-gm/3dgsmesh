#!/usr/bin/env bash
set -euo pipefail
source /data/apps/activate-sugar.sh
p=/data/projects/myroom-sfm-v2/pinhole-baseline
mkdir -p "$p/sparse" "$p/logs"
exec > >(tee "$p/logs/mapper.log") 2>&1
python - <<'PY'
from pathlib import Path
import sqlite3, numpy as np
p=Path('/data/projects/myroom-sfm-v2/pinhole-baseline')
src=sqlite3.connect('/data/projects/myroom-20261017/distorted/database.db')
dst=sqlite3.connect(p/'database.db');src.backup(dst)
for cid,raw in dst.execute('select camera_id,params from cameras').fetchall():
    # Initial OPENCV distortion was zero. Retain identical initial pinhole intrinsics.
    params=np.frombuffer(raw,dtype=np.float64)[:4].copy()
    dst.execute('update cameras set model=1, params=? where camera_id=?',(params.tobytes(),cid))
dst.commit();dst.close();src.close()
(p/'input').symlink_to('/data/projects/myroom-20261017/input',target_is_directory=True)
PY
colmap mapper --database_path "$p/database.db" --image_path "$p/input" --output_path "$p/sparse" --Mapper.num_threads 8 --Mapper.ba_global_function_tolerance 0.000001
for m in "$p"/sparse/*; do
  test -d "$m" && colmap model_analyzer --path "$m" > "$p/logs/model-$(basename "$m").txt" 2>&1
done
touch "$p/logs/COMPLETE"
