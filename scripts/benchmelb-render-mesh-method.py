"""Render a new reconstruction at the six previously compared cameras.

No alignment is fitted: a model trained using the existing COLMAP must remain
in those world coordinates. Optional projected colors use visible source photos.
"""
from pathlib import Path
import argparse, importlib.util, json
import numpy as np
import torch
import open3d as o3d
from PIL import Image, ImageDraw
from pytorch3d.structures import Meshes
from pytorch3d.renderer import (TexturesVertex, MeshRenderer, MeshRasterizer,
    RasterizationSettings, SoftPhongShader, AmbientLights, DirectionalLights, BlendParams)
from pytorch3d.utils import cameras_from_opencv_projection

ap=argparse.ArgumentParser();ap.add_argument('--mesh',required=True);ap.add_argument('--name',required=True)
ap.add_argument('--project-colors',action='store_true');args=ap.parse_args()
torch.set_grad_enabled(False);torch.set_num_threads(4)
p=Path('/data/projects/benchmelb-20261018');out=p/'mesh-method-comparison';out.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('colmap_loader','/data/apps/SuGaR/gaussian_splatting/scene/colmap_loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
ims=sorted(loader.read_extrinsics_binary(str(p/'sparse/0/images.bin')).values(),key=lambda x:x.name)
intr=loader.read_intrinsics_binary(str(p/'sparse/0/cameras.bin'));held=ims[::8];indices=[0,7,14,20,27,34]
mesh=o3d.io.read_triangle_mesh(args.mesh);verts=np.asarray(mesh.vertices).copy();faces=np.asarray(mesh.triangles).copy()
assert len(faces)>0 and np.isfinite(verts).all()
v=torch.tensor(verts,device='cuda',dtype=torch.float32);f=torch.tensor(faces,device='cuda',dtype=torch.int64)
def camera(im):
    c=intr[im.camera_id];fx,fy,cx,cy=c.params
    return cameras_from_opencv_projection(R=torch.tensor(loader.qvec2rotmat(im.qvec)[None],device='cuda',dtype=torch.float32),
        tvec=torch.tensor(im.tvec[None],device='cuda',dtype=torch.float32),
        camera_matrix=torch.tensor([[[fx,0,cx],[0,fy,cy],[0,0,1]]],device='cuda',dtype=torch.float32),
        image_size=torch.tensor([[c.height,c.width]],device='cuda',dtype=torch.float32))
settings=RasterizationSettings(image_size=(448,800),faces_per_pixel=1,blur_radius=0,bin_size=64,max_faces_per_bin=4000000,cull_backfaces=False)
gray=Meshes(verts=[v],faces=[f],textures=TexturesVertex(verts_features=[torch.full_like(v,.65)]))
if args.project_colors:
    mesh.compute_vertex_normals();normals=torch.tensor(np.asarray(mesh.vertex_normals).copy(),device='cuda',dtype=torch.float32)
    sums=torch.zeros_like(v);weights=torch.zeros(len(v),device='cuda')
    # Uniform temporal sampling from original training images; exclude held-out views.
    train_all=[im for i,im in enumerate(ims) if i%8!=0]
    train=[train_all[i] for i in np.linspace(0,len(train_all)-1,min(25,len(train_all))).round().astype(int)]
    raster=MeshRasterizer(raster_settings=settings)
    for i,im in enumerate(train):
        c=intr[im.camera_id];cam=camera(im)
        cw=800;ch=round(c.height*cw/c.width)
        native_settings=RasterizationSettings(image_size=(ch,cw),faces_per_pixel=1,blur_radius=0,bin_size=64,max_faces_per_bin=2000000,cull_backfaces=False)
        frag=raster(gray,cameras=cam,raster_settings=native_settings)
        # Mesh zbuffer uses view-space depth in this PyTorch3D version.
        screen=cam.transform_points_screen(v,image_size=((ch,cw),))
        uv=screen[:,:2];xy=uv.round().long();z=cam.get_world_to_view_transform().transform_points(v)[:,2]
        valid=(xy[:,0]>=0)&(xy[:,0]<cw)&(xy[:,1]>=0)&(xy[:,1]<ch)&(z>0)
        ids=torch.where(valid)[0];qx=xy[ids,0];qy=xy[ids,1]
        zbuf=frag.zbuf[0,qy,qx,0];validz=(zbuf>0)&((z[ids]-zbuf).abs()<(.01+.005*z[ids]))
        ids=ids[validz]
        tocam=cam.get_camera_center()[0]-v[ids];tocam=tocam/tocam.norm(dim=1,keepdim=True).clamp_min(1e-8)
        w=(normals[ids]*tocam).sum(dim=1).abs().clamp_min(0)**2
        photo_image=Image.open(p/'images'/im.name).convert('RGB');assert photo_image.size==(c.width,c.height)
        arr=np.asarray(photo_image.resize((cw,ch),Image.Resampling.LANCZOS)).copy()
        photo=torch.tensor(arr,device='cuda',dtype=torch.float32).permute(2,0,1)[None]/255
        grid=uv[ids].clone();grid[:,0]=grid[:,0]/(cw-1)*2-1;grid[:,1]=grid[:,1]/(ch-1)*2-1
        rgb=torch.nn.functional.grid_sample(photo,grid[None,:,None],mode='bilinear',align_corners=True)[0,:,:,0].T
        sums[ids]+=rgb*w[:,None];weights[ids]+=w
        if i%10==0:print('Projected',i+1,'/',len(train),flush=True)
    rgb=sums/weights.clamp_min(1e-8)[:,None];missing=weights<1e-8
    if missing.any() and (~missing).any():
        from scipy.spatial import cKDTree
        mask=missing.cpu().numpy();_,nearest=cKDTree(verts[~mask]).query(verts[mask],workers=4)
        rgb[missing]=rgb[~missing][torch.tensor(nearest,device='cuda')]
    mesh.vertex_colors=o3d.utility.Vector3dVector(rgb.cpu().numpy().clip(0,1))
    o3d.io.write_triangle_mesh(str(out/f'{args.name}-colored.ply'),mesh)
    print('Color coverage',float((~missing).float().mean()),flush=True)
else:
    rgb=torch.tensor(np.asarray(mesh.vertex_colors).copy(),device='cuda',dtype=torch.float32) if mesh.has_vertex_colors() else torch.full_like(v,.65)
colored=Meshes(verts=[v],faces=[f],textures=TexturesVertex(verts_features=[rgb]))
for idx in indices:
    cam=camera(held[idx]);renderer=MeshRenderer(rasterizer=MeshRasterizer(cameras=cam,raster_settings=settings),
        shader=SoftPhongShader(device='cuda',cameras=cam,lights=AmbientLights(device='cuda'),blend_params=BlendParams(background_color=(0,0,0))))
    for mode,m in [('gray',gray),('color',colored)]:
        kw={} if mode=='color' else dict(lights=DirectionalLights(device='cuda',direction=((.3,-.7,-1.),),ambient_color=((.6,.6,.6),),diffuse_color=((.4,.4,.4),),specular_color=((0,0,0),)))
        pixels=renderer(m,**kw)[0,...,:3].clamp(0,1).cpu().numpy()
        Image.fromarray((pixels*255).astype(np.uint8)).save(out/f'{args.name}-{mode}-{idx:02d}.jpg',quality=96)
    print('Rendered',idx,flush=True)
for mode in ['color','gray']:
    sheet=Image.new('RGB',(1600,1500),'white');d=ImageDraw.Draw(sheet)
    for row,idx in enumerate(indices):
        cols=[('Input',p/'images'/held[idx].name),('KIRI default',p/'kiri-comparison'/f'kiri-default-{mode}-{idx:02d}.jpg'),
            ('Original 2DGS full',p/'kiri-comparison'/f'ours-full-{mode}-{idx:02d}.jpg'),(args.name,out/f'{args.name}-{mode}-{idx:02d}.jpg')]
        for col,(label,path) in enumerate(cols):
            im=Image.open(path).convert('RGB');im.thumbnail((400,224));sheet.paste(im,(col*400,row*250+24));d.text((col*400+5,row*250+5),label,fill='black')
    sheet.save(out/f'{args.name}-comparison-{mode}.jpg',quality=96)
(out/f'{args.name}-stats.json').write_text(json.dumps({'vertices':len(verts),'triangles':len(faces),'bounds':[verts.min(0).tolist(),verts.max(0).tolist()]},indent=2))
print('COMPLETE',flush=True)
