"""Test fixed estimated intrinsics and a strong initial baseline in COLMAP 4.2.1."""
from pathlib import Path
import sqlite3,json
import numpy as np
import pycolmap

p=Path('/data/projects/myroom-sfm-v2/modern-fixed');p.mkdir(exist_ok=True)
db=p/'database.db';assert not db.exists()
src=sqlite3.connect('/data/projects/myroom-sfm-v2/global-lightglue/database.db')
dst=sqlite3.connect(db);src.backup(dst);src.close()
f=(1636.9355218820435+1636.2367460451808)/2
params=np.array([f,f,562.,1000.],dtype=np.float64)
dst.execute('UPDATE cameras SET params=?, prior_focal_length=1 WHERE camera_id=1',(params.tobytes(),))
dst.commit();dst.close()
calib=pycolmap.ViewGraphCalibrationOptions();calib.cross_validate_prior_focal_lengths=False
print('Recalibrating pair geometry',flush=True)
print(pycolmap.calibrate_view_graph(db,calib),flush=True)
opts=pycolmap.IncrementalPipelineOptions()
opts.num_threads=8;opts.random_seed=42;opts.min_num_matches=30
opts.ba_use_gpu=False
opts.ba_refine_focal_length=False;opts.ba_refine_extra_params=False
opts.mapper.num_threads=8
opts.mapper.abs_pose_refine_focal_length=False;opts.mapper.abs_pose_refine_extra_params=False
# Leave initialization at the official 16-degree default, rather than relaxing to 4 degrees.
(p/'options.txt').write_text(opts.summary())
models=pycolmap.incremental_mapping(db,Path('/data/projects/myroom-sfm-v2/sharp-pinhole/input'),p/'sparse',opts)
report={str(k):{'images':r.num_reg_images(),'points':r.num_points3D(),'mean_reprojection_error':r.compute_mean_reprojection_error()} for k,r in models.items()}
(p/'result.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
(p/'SFM_COMPLETE').touch()
