"""Validate outputs and render mesh at the same held-out cameras as 3DGS."""
from pathlib import Path
import importlib.util, json, shutil, sys, struct
import numpy as np
import open3d as o3d
import trimesh
import torch
from PIL import Image, ImageDraw
from plyfile import PlyData
from pytorch3d.structures import Meshes
from pytorch3d.renderer import (TexturesVertex, MeshRenderer, MeshRasterizer,
    RasterizationSettings, SoftPhongShader, AmbientLights, DirectionalLights, BlendParams)
from pytorch3d.utils import cameras_from_opencv_projection

def export_vertex_color_glb(mesh, path):
    # Preserve the captured illumination: no metallic default or extra lighting.
    def material(tree):
        tree['materials']=[{'name':'Captured vertex colors','doubleSided':True,
            'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1},
            'extensions':{'KHR_materials_unlit':{}}}]
        tree.setdefault('extensionsUsed',[]).append('KHR_materials_unlit')
        for node in tree['meshes']:
            for primitive in node['primitives']:primitive['material']=0
    path.write_bytes(trimesh.exchange.gltf.export_glb(trimesh.Scene(mesh),tree_postprocessor=material))

p=Path('/data/projects/benchmelb-20261018')
iteration=int(sys.argv[1]) if len(sys.argv)>1 else 30000
out=p/('delivery' if iteration==30000 else f'intermediate-{iteration}')
for name in ['gaussian','mesh','preview']: (out/name).mkdir(parents=True,exist_ok=True)
src=p/'models/3dgs/point_cloud/iteration_30000/point_cloud.ply'
if iteration==30000:shutil.copy2(src,out/'gaussian/benchmelb-3dgs-30000.ply')
gs_ply=PlyData.read(str(src))
for name in ['x','y','z','opacity','scale_0','scale_1','scale_2','rot_0','rot_1','rot_2','rot_3']:
    assert np.isfinite(gs_ply['vertex'][name]).all(),name
meshroot=p/f'models/2dgs/train/ours_{iteration}'
for name in ['fuse.ply','fuse_post.ply']: shutil.copy2(meshroot/name,out/'mesh'/name)
mesh=o3d.io.read_triangle_mesh(str(meshroot/'fuse_post.ply'))
assert len(mesh.triangles)>0 and mesh.has_vertex_colors()
rawstats={'vertices':len(mesh.vertices),'triangles':len(mesh.triangles)}
export_vertex_color_glb(trimesh.Trimesh(vertices=np.asarray(mesh.vertices),faces=np.asarray(mesh.triangles),vertex_colors=(np.asarray(mesh.vertex_colors)*255).astype(np.uint8),process=False),out/'mesh/benchmelb-mesh.glb')
assert np.isfinite(np.asarray(mesh.vertices)).all()
glb_check=trimesh.load(out/'mesh/benchmelb-mesh.glb',force='mesh',process=False)
assert len(glb_check.faces)==len(mesh.triangles)
assert np.isfinite(glb_check.vertices).all()
# A GLB material makes Trimesh return TextureVisuals even with COLOR_0.
with (out/'mesh/benchmelb-mesh.glb').open('rb') as glb_file:
    magic,version,declared_size=struct.unpack('<III',glb_file.read(12))
    json_size,chunk_type=struct.unpack('<II',glb_file.read(8))
    glb_json=json.loads(glb_file.read(json_size))
assert magic==0x46546c67 and version==2
assert declared_size==(out/'mesh/benchmelb-mesh.glb').stat().st_size
for glb_mesh in glb_json['meshes']:
    for primitive in glb_mesh['primitives']:
        attr=primitive['attributes'];assert 'COLOR_0' in attr
        assert glb_json['accessors'][attr['COLOR_0']]['count']==glb_json['accessors'][attr['POSITION']]['count']
del glb_check
if len(mesh.triangles)>1000000:
    mesh=mesh.simplify_quadric_decimation(1000000)
mesh.compute_vertex_normals()
o3d.io.write_triangle_mesh(str(out/'mesh/benchmelb-mesh-preview.ply'),mesh)
verts=np.asarray(mesh.vertices); faces=np.asarray(mesh.triangles); colors=np.asarray(mesh.vertex_colors)
tmesh=trimesh.Trimesh(vertices=verts,faces=faces,vertex_colors=(colors*255).astype(np.uint8),process=False)
export_vertex_color_glb(tmesh,out/'mesh/benchmelb-mesh-preview.glb')
spec=importlib.util.spec_from_file_location('colmap_loader','/data/apps/SuGaR/gaussian_splatting/scene/colmap_loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
ims=loader.read_extrinsics_binary(str(p/'sparse/0/images.bin'))
intr=loader.read_intrinsics_binary(str(p/'sparse/0/cameras.bin'))
held=sorted(ims.values(),key=lambda i:i.name)[::8]
indices=np.linspace(0,len(held)-1,6).round().astype(int)
v=torch.tensor(verts.copy(),device='cuda',dtype=torch.float32)
f=torch.tensor(faces.copy(),device='cuda',dtype=torch.int64)
tex=torch.tensor(colors.copy(),device='cuda',dtype=torch.float32)
colored=Meshes(verts=[v],faces=[f],textures=TexturesVertex(verts_features=[tex]))
gray=Meshes(verts=[v],faces=[f],textures=TexturesVertex(verts_features=[torch.full_like(tex,.65)]))
sheet=Image.new('RGB',(1200,6*250),'white'); draw=ImageDraw.Draw(sheet)
mapping=[]
for row,idx in enumerate(indices):
    im=held[idx]; c=intr[im.camera_id]
    assert c.model=='PINHOLE',c.model
    fx,fy,cx,cy=c.params
    K=torch.tensor([[[fx,0,cx],[0,fy,cy],[0,0,1]]],device='cuda',dtype=torch.float32)
    cam=cameras_from_opencv_projection(
        R=torch.tensor(loader.qvec2rotmat(im.qvec)[None],device='cuda',dtype=torch.float32),
        tvec=torch.tensor(im.tvec[None],device='cuda',dtype=torch.float32),camera_matrix=K,
        image_size=torch.tensor([[c.height,c.width]],device='cuda',dtype=torch.float32))
    renderer=MeshRenderer(rasterizer=MeshRasterizer(cameras=cam,raster_settings=RasterizationSettings(
        image_size=(448,800),faces_per_pixel=1,blur_radius=0,max_faces_per_bin=200000,cull_backfaces=False)),
        shader=SoftPhongShader(device='cuda',cameras=cam,lights=AmbientLights(device='cuda'),
            blend_params=BlendParams(background_color=(0,0,0))))
    with torch.no_grad(): a=renderer(colored)[0,...,:3].clamp(0,1).cpu().numpy()
    mi=Image.fromarray((a*255).astype(np.uint8));mi.save(out/'preview'/f'mesh-{idx:05d}.png')
    with torch.no_grad():
        shaded=renderer(gray,lights=DirectionalLights(device='cuda',direction=((.3,-.7,-1.),),ambient_color=((.35,.35,.35),),diffuse_color=((.65,.65,.65),),specular_color=((0,0,0),)))
        a=shaded[0,...,:3].clamp(0,1).cpu().numpy()
    Image.fromarray((a*255).astype(np.uint8)).save(out/'preview'/f'mesh-gray-{idx:05d}.png')
    for col,(label,path) in enumerate([
        ('Input',p/'images'/im.name),
        ('3DGS',p/'models/3dgs/test/ours_30000/renders'/f'{idx:05d}.png'),
        (f'2DGS mesh@{iteration} vertex colors',out/'preview'/f'mesh-{idx:05d}.png')]):
        pic=Image.open(path).convert('RGB');pic.thumbnail((400,224));sheet.paste(pic,(col*400,row*250+24))
        draw.text((col*400+4,row*250+5),f'{label} | {im.name}',fill='black')
    mapping.append({'test_index':int(idx),'image':im.name})
sheet.save(out/'preview/input-3dgs-mesh.jpg',quality=95)
report={'mesh_iteration':iteration,'mesh_raw_post':rawstats,'mesh_preview':{'vertices':len(verts),'triangles':len(faces),'color':'vertex RGB; GLB unlit; no UV atlas'},
    'gaussians':gs_ply['vertex'].count,'preview_cameras':mapping}
(out/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
