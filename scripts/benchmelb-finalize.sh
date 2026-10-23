#!/usr/bin/env bash
set -euo pipefail
p=/data/projects/benchmelb-20261018
while ! test -f "$p/logs/MESH_COMPLETE"; do
  if test -f "$p/logs/TRAIN_FAILED"; then exit 1; fi
  sleep 5
done
source /data/apps/activate-sugar.sh
export PATH=/data/envs/2dgs/bin:$PATH OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
trap 'echo "FAILED line=$LINENO" > "$p/logs/DELIVERY_FAILED"' ERR
python /data/apps/benchmelb-deliver.py > "$p/logs/delivery-validation.log" 2>&1
touch "$p/logs/DELIVERY_COMPLETE"
