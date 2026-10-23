"""Create a separately named 2M-face preview, without smoothing or cropping."""
from pathlib import Path
import argparse,json
import open3d as o3d
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');args=ap.parse_args()
m=o3d.io.read_triangle_mesh(args.source);before={'vertices':len(m.vertices),'triangles':len(m.triangles)}
assert len(m.triangles)>0 and np.isfinite(np.asarray(m.vertices)).all()
if len(m.triangles)>2000000:m=m.simplify_quadric_decimation(2000000)
m.compute_vertex_normals();o3d.io.write_triangle_mesh(args.output,m)
Path(args.output+'.json').write_text(json.dumps({'source':args.source,'before':before,'after':{'vertices':len(m.vertices),'triangles':len(m.triangles)},'operations':['quadric decimation to at most 2M triangles','compute vertex normals'],'cropped':False,'smoothed':False},indent=2))
print('COMPLETE',before,len(m.vertices),len(m.triangles),flush=True)
