#!/usr/bin/env bash
# Existing /data/envs/gaustudio must already contain the compiled sm70 extension.
set -euo pipefail
source /data/apps/activate-sugar.sh
export PATH=/data/envs/gaustudio/bin:$PATH
export OMP_NUM_THREADS=4 PYTHONUNBUFFERED=1
p=/data/projects/benchmelb-20261018
cd /data/apps/gaustudio-src
python -m gaustudio.scripts.extract_mesh -m "$p/models/3dgs" \
  -s "$p/models/3dgs/cameras.json" -o "$p/gaustudio-default" --resolution 1 --sh 3
python /data/apps/benchmelb-gaustudio-filtered.py
python /data/apps/benchmelb-render-mesh-method.py --mesh "$p/gaustudio-default/fused_mesh.ply" --name gaustudio-default
python /data/apps/benchmelb-render-mesh-method.py --mesh "$p/gaustudio-filtered/fused_mesh.ply" --name gaustudio-filtered
