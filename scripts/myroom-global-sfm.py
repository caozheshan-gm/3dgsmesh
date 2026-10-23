"""Global SfM comparison using the same learned features and raw matches."""
from pathlib import Path
import sqlite3,json,time
import numpy as np
import pycolmap

p=Path('/data/projects/myroom-sfm-v2/global-lightglue');p.mkdir(exist_ok=True)
db=p/'database.db'
assert not db.exists(), 'Preserve prior experiments; use a new output folder for reruns.'
source=sqlite3.connect('/data/projects/myroom-sfm-v2/lightglue/database.db')
dest=sqlite3.connect(db);source.backup(dest);source.close()
# Estimated calibration from the incremental model; not a measured calibration.
params=np.array([1645.361480821543,1690.051465812578,562.,1000.],dtype=np.float64)
dest.execute('UPDATE cameras SET params=?, prior_focal_length=1 WHERE camera_id=1',(params.tobytes(),))
dest.commit();dest.close()
calib=pycolmap.ViewGraphCalibrationOptions()
calib.cross_validate_prior_focal_lengths=False
print('Calibrate view graph / reestimate relative poses',flush=True)
result=pycolmap.calibrate_view_graph(db,calib)
print('Calibration result',result,flush=True)
opts=pycolmap.GlobalPipelineOptions()
opts.num_threads=8;opts.random_seed=42;opts.min_num_matches=30
opts.mapper.num_threads=8
opts.mapper.global_positioning.use_gpu=False
opts.mapper.bundle_adjustment.ceres.use_gpu=False
opts.mapper.bundle_adjustment.ceres.solver_options.num_threads=8
(p/'options.txt').write_text(opts.summary())
models=pycolmap.global_mapping(db,Path('/data/projects/myroom-sfm-v2/sharp-pinhole/input'),p/'sparse',opts)
report={str(k):{'images':r.num_reg_images(),'points':r.num_points3D(),'mean_reprojection_error':r.compute_mean_reprojection_error()} for k,r in models.items()}
(p/'result.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
(p/'SFM_COMPLETE').touch()
