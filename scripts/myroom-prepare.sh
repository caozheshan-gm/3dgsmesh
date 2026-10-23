#!/usr/bin/env bash
set -euo pipefail
project=/data/projects/myroom-20261017
exec > >(tee "$project/logs/prepare.log") 2>&1
# Keep the interrupted pre-tonemap feature database for provenance.
if test -d "$project/distorted"; then
  mv "$project/distorted" "$project/distorted-pre-tonemap"
fi
ffmpeg -hide_banner -loglevel warning -i "$project/myroom.mov" -vf 'fps=2,scale=1600:1600:force_original_aspect_ratio=decrease,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=full,format=yuvj420p' -q:v 2 -y "$project/input/frame_%05d.jpg"
touch "$project/logs/FRAMES_COMPLETE"
bash "$project/run-sfm.sh"
