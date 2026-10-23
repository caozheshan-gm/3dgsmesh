#!/bin/bash
set -euo pipefail
source /data/apps/activate-sugar.sh
export OMP_NUM_THREADS=8 PYTHONUNBUFFERED=1
p=/data/projects/myroom-20261017
trap 'status=$?; echo "FAILED exit=$status line=$LINENO" >> "$p/logs/SUGAR_FAILED"; exit "$status"' ERR
python train.py -s "$p" -c /data/apps/SuGaR/output/vanilla_gs/myroom-20261017/ -i 7000 -r dn_consistency --low_poly True --refinement_time short --export_uv_textured_mesh True --export_ply True --eval True > "$p/logs/sugar-train-resume.log" 2>&1
touch "$p/logs/TRAIN_SCRIPT_COMPLETE"
