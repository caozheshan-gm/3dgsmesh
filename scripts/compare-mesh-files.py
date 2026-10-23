from pathlib import Path
import numpy as np,json,subprocess
files={'kiri_default':Path('artifacts/kiri-mesh/3DModel.obj'),'kiri_custom':Path('artifacts/kiri-mesh/AdvancedExport/3DModel_Custom.obj'),'sugar':next(Path('artifacts/myroom-20261017/mesh').glob('*.obj'))}
report={}
for name,p in files.items():
 count={k:0 for k in ['v','vt','vn','f','triangles','non_triangular_faces']};lo=np.full(3,np.inf);hi=-lo;materials=[]
 with p.open() as f:
  for line in f:
   if line.startswith('v '):
    xyz=np.array([float(x) for x in line.split()[1:4]]);lo=np.minimum(lo,xyz);hi=np.maximum(hi,xyz);count['v']+=1
   elif line.startswith('vt '):count['vt']+=1
   elif line.startswith('vn '):count['vn']+=1
   elif line.startswith('f '):
    n=len(line.split())-1;count['f']+=1;count['triangles']+=n-2;count['non_triangular_faces']+=n!=3
   elif line.startswith('mtllib '):materials.append(line.strip()[7:])
 r={'path':str(p.resolve()),'bytes':p.stat().st_size,**count,'bounds_min':lo.tolist(),'bounds_max':hi.tolist(),'material_files':materials}
 report[name]=r
Path('runs/kiri-comparison/mesh-statistics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
