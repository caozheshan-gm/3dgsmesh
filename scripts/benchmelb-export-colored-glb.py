"""Export the separately reduced, photo-colored mesh with unlit vertex colors."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
import open3d as o3d
import trimesh
p=Path('/data/projects/benchmelb-20261018');out=p/'gaustudio-delivery';out.mkdir(exist_ok=True)
src=p/'mesh-method-comparison/gaustudio-filtered-preview-colored.ply'
m=o3d.io.read_triangle_mesh(str(src));v=np.asarray(m.vertices);f=np.asarray(m.triangles);c=np.asarray(m.vertex_colors)
assert len(f)>0 and c.shape==v.shape and np.isfinite(v).all() and np.isfinite(c).all()
def material(tree):
    tree['materials']=[{'name':'Captured photo colors','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}}]
    tree.setdefault('extensionsUsed',[]).append('KHR_materials_unlit')
    for mesh in tree['meshes']:
        for prim in mesh['primitives']:prim['material']=0
path=out/'benchmelb-gaustudio-filtered-preview.glb'
mesh=trimesh.Trimesh(vertices=v,faces=f,vertex_colors=(c*255).round().astype(np.uint8),process=False)
path.write_bytes(trimesh.exchange.gltf.export_glb(trimesh.Scene(mesh),tree_postprocessor=material))
with path.open('rb') as stream:
    magic,version,total=struct.unpack('<III',stream.read(12));size,kind=struct.unpack('<II',stream.read(8));tree=json.loads(stream.read(size))
assert magic==0x46546c67 and version==2 and total==path.stat().st_size
for model in tree['meshes']:
    for prim in model['primitives']:
        a=prim['attributes'];assert 'COLOR_0' in a
        assert tree['accessors'][a['COLOR_0']]['count']==tree['accessors'][a['POSITION']]['count']
check=trimesh.load(path,force='mesh',process=False);assert len(check.faces)==len(f) and np.isfinite(check.vertices).all()
stats={'vertices':len(v),'triangles':len(f),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'has_vertex_color':True,'uv_texture':False,'material':'KHR_materials_unlit','validation':'GLB header, colors/accessor counts, reload face count and finite vertices checked'}
(out/'validation.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
