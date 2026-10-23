"""Render exported models with approximate shared camera poses and neutral shading."""
from pathlib import Path
import sys,json,importlib.util,gc,math
from types import SimpleNamespace
import numpy as np
import torch
import open3d as o3d
from PIL import Image,ImageDraw
from pytorch3d.io import load_objs_as_meshes
from pytorch3d.structures import Meshes
from pytorch3d.renderer import (TexturesVertex,MeshRenderer,MeshRasterizer,RasterizationSettings,
    SoftPhongShader,AmbientLights,DirectionalLights,BlendParams)
from pytorch3d.utils import cameras_from_opencv_projection
torch.set_grad_enabled(False);torch.set_num_threads(4)
p=Path('/data/projects/benchmelb-20261018');out=p/'kiri-comparison';out.mkdir(exist_ok=True)
j=json.loads((out/'alignment-floor.json').read_text());T=np.array(j['kiri_mesh_to_ours'])
spec=importlib.util.spec_from_file_location('colmap_loader','/data/apps/SuGaR/gaussian_splatting/scene/colmap_loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
ims=loader.read_extrinsics_binary(str(p/'sparse/0/images.bin'))
intr=loader.read_intrinsics_binary(str(p/'sparse/0/cameras.bin'))
held=sorted(ims.values(),key=lambda i:i.name)[::8];indices=[0,7,14,20,27,34]
cams=[]
for idx in indices:
    im=held[idx];c=intr[im.camera_id];fx,fy,cx,cy=c.params
    K=torch.tensor([[[fx,0,cx],[0,fy,cy],[0,0,1]]],device='cuda',dtype=torch.float32)
    cams.append(cameras_from_opencv_projection(R=torch.tensor(loader.qvec2rotmat(im.qvec)[None],device='cuda',dtype=torch.float32),
        tvec=torch.tensor(im.tvec[None],device='cuda',dtype=torch.float32),camera_matrix=K,
        image_size=torch.tensor([[c.height,c.width]],device='cuda',dtype=torch.float32)))
models=[('kiri-default',p/'kiri-input/mesh/3DModel.obj'),
        ('kiri-custom',p/'kiri-input/mesh/AdvancedExport/3DModel_Custom.obj'),
        ('ours-preview',p/'delivery/mesh/benchmelb-mesh-preview.ply'),
        ('ours-full',p/'models/2dgs/train/ours_30000/fuse_post.ply')]
for name,path in models:
    if all((out/f'{name}-{mode}-{idx:02d}.jpg').exists() for mode in ['color','gray'] for idx in indices):
        print('Using completed renders',name,flush=True);continue
    print('Loading',name,flush=True)
    if path.suffix=='.obj':
        mesh=load_objs_as_meshes([str(path)],device='cuda')
        v=mesh.verts_packed();M=torch.tensor(T[:3,:3],device='cuda',dtype=torch.float32);b=torch.tensor(T[:3,3],device='cuda',dtype=torch.float32)
        mesh.offset_verts_(v@M.T+b-v)
    else:
        m=o3d.io.read_triangle_mesh(str(path));v=torch.tensor(np.asarray(m.vertices).copy(),device='cuda',dtype=torch.float32)
        f=torch.tensor(np.asarray(m.triangles).copy(),device='cuda',dtype=torch.int64)
        rgb=torch.tensor(np.asarray(m.vertex_colors).copy(),device='cuda',dtype=torch.float32)
        mesh=Meshes(verts=[v],faces=[f],textures=TexturesVertex(verts_features=[rgb]));del m,v,f,rgb
    gray=Meshes(verts=mesh.verts_list(),faces=mesh.faces_list(),textures=TexturesVertex(verts_features=[torch.full_like(mesh.verts_packed(),.65)]))
    print(name,'faces',len(mesh.faces_packed()),flush=True)
    for row,(idx,cam) in enumerate(zip(indices,cams)):
        renderer=MeshRenderer(rasterizer=MeshRasterizer(cameras=cam,raster_settings=RasterizationSettings(
            image_size=(448,800),faces_per_pixel=1,blur_radius=0,bin_size=64,max_faces_per_bin=4000000,cull_backfaces=False)),
            shader=SoftPhongShader(device='cuda',cameras=cam,lights=AmbientLights(device='cuda'),blend_params=BlendParams(background_color=(0,0,0))))
        rgb=renderer(mesh)[0,...,:3].clamp(0,1).cpu().numpy()
        Image.fromarray((rgb*255).astype(np.uint8)).save(out/f'{name}-color-{idx:02d}.jpg',quality=96)
        rgb=renderer(gray,lights=DirectionalLights(device='cuda',direction=((.3,-.7,-1.),),ambient_color=((.6,.6,.6),),diffuse_color=((.4,.4,.4),),specular_color=((0,0,0),)))[0,...,:3].clamp(0,1).cpu().numpy()
        Image.fromarray((rgb*255).astype(np.uint8)).save(out/f'{name}-gray-{idx:02d}.jpg',quality=96)
        print('Rendered',name,idx,flush=True)
    del mesh,gray,renderer;gc.collect();torch.cuda.empty_cache()

# KIRI's splat coordinates use the opposite Y/Z directions to its OBJ export.
sys.path.insert(0,'/data/apps/SuGaR/gaussian_splatting')
from scene import GaussianModel
from scene.cameras import Camera
from gaussian_renderer import render
g=GaussianModel(3);g.load_ply(str(p/'kiri-input/kiribench.ply'));g.active_sh_degree=3
S=T@np.diag([1,-1,-1,1]);scale=np.cbrt(np.linalg.det(S[:3,:3]));rot=S[:3,:3]/scale
for idx in indices:
    im=held[idx];c=intr[im.camera_id];Ro=loader.qvec2rotmat(im.qvec);Co=-Ro.T@im.tvec
    Ck=rot.T@(Co-S[:3,3])/scale;Rk=Ro@rot;tk=-Rk@Ck
    fx,fy,_,_=c.params
    cam=Camera(colmap_id=idx,R=Rk.T,T=tk,FoVx=2*math.atan(c.width/(2*fx)),FoVy=2*math.atan(c.height/(2*fy)),
        image=torch.zeros(3,448,800),gt_alpha_mask=None,image_name=im.name,uid=idx,data_device='cpu')
    rgb=render(cam,g,SimpleNamespace(convert_SHs_python=False,compute_cov3D_python=False,debug=False),torch.zeros(3,device='cuda'))['render'].clamp(0,1).permute(1,2,0).cpu().numpy()
    Image.fromarray((rgb*255).astype(np.uint8)).save(out/f'kiri-gaussian-{idx:02d}.jpg',quality=96)
    print('Rendered KIRI GS',idx,flush=True)

for mode in ['color','gray']:
    sheet=Image.new('RGB',(2000,1500),'white');d=ImageDraw.Draw(sheet)
    for row,idx in enumerate(indices):
        cols=[('Input',p/'images'/held[idx].name)]+[(name,out/f'{name}-{mode}-{idx:02d}.jpg') for name,_ in models]
        for col,(name,path) in enumerate(cols):
            im=Image.open(path).convert('RGB');im.thumbnail((400,224));sheet.paste(im,(col*400,row*250+24));d.text((col*400+5,row*250+5),f'{name} | frame {held[idx].name}',fill='black')
    sheet.save(out/f'mesh-comparison-{mode}.jpg',quality=96)
sheet=Image.new('RGB',(1200,1500),'white');d=ImageDraw.Draw(sheet)
for row,idx in enumerate(indices):
    for col,(name,path) in enumerate([('Input',p/'images'/held[idx].name),('Our 3DGS',p/'models/3dgs/test/ours_30000/renders'/f'{idx:05d}.png'),('KIRI GS (approx aligned)',out/f'kiri-gaussian-{idx:02d}.jpg')]):
        im=Image.open(path).convert('RGB');im.thumbnail((400,224));sheet.paste(im,(col*400,row*250+24));d.text((col*400+5,row*250+5),name,fill='black')
sheet.save(out/'gaussian-comparison.jpg',quality=96)
print('COMPLETE',flush=True)
