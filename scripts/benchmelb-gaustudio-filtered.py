"""Controlled depth-consistency variant of GauStudio extraction for BenchMelb.

Same 93 cameras / voxel / TSDF truncation / fusion weight as the stock run.
Adds opacity>=.8, six nearby views and at least two consistent depth votes.
No manual geometry edits, smoothing, learned prior, or KIRI geometry supervision.
"""
from pathlib import Path
import json,time
import numpy as np
import torch
import torch.nn.functional as F
import vdbfusion,trimesh
from gaustudio import models,renderers
from gaustudio.utils.cameras_utils import JSON_to_camera

torch.set_grad_enabled(False);torch.set_num_threads(4)
p=Path('/data/projects/benchmelb-20261018');out=p/'gaustudio-filtered';out.mkdir(exist_ok=True)
t0=time.time();cameras=[JSON_to_camera(j).to('cuda') for j in json.loads((p/'models/3dgs/cameras.json').read_text())[::3]]
config={'name':'vanilla_pcd','sh_degree':3}
g=models.make(config);g.load(str(p/'models/3dgs/point_cloud/iteration_30000/point_cloud.ply'));g.to('cuda');g.active_sh_degree=0
renderer=renderers.make({'name':'vanilla_renderer'});renderer.bg_color=renderer.bg_color.cuda()
# Depth geometry is independent of spherical harmonics; color will come from
# visibility-tested original photographs, not this SH0 diagnostic render.
depths=[];alphas=[]
for i,c in enumerate(cameras):
    path=out/f'depth-{i:03d}.npz'
    if path.exists():
        a=np.load(path);depth=torch.tensor(a['depth'],device='cuda');alpha=torch.tensor(a['alpha'],device='cuda')
    else:
        pkg=renderer.render(c,g);depth=pkg['rendered_median_depth'][0];alpha=pkg['rendered_final_opacity'][0]
        np.savez_compressed(path,depth=depth.cpu().numpy(),alpha=alpha.cpu().numpy())
    depths.append(depth);alphas.append(alpha)
    if i%10==0:print('Depth',i+1,'/',len(cameras),flush=True)
del g,renderer;torch.cuda.empty_cache()
centers=torch.stack([c.camera_center for c in cameras]);centersnp=centers.cpu().numpy()
volume=vdbfusion.VDBVolume(voxel_size=.01,sdf_trunc=.04,space_carving=False);stats=[]
for i,c in enumerate(cameras):
    depth=depths[i];h,w=depth.shape
    y,x=torch.meshgrid(torch.arange(h,device='cuda'),torch.arange(w,device='cuda'),indexing='ij')
    xyz=c.depth2point(depth,coordinate='world');valid=(alphas[i]>=.8)&torch.isfinite(depth)&(depth>0)
    ids=torch.where(valid.flatten())[0];pts=xyz.reshape(-1,3)[ids]
    dist=np.linalg.norm(centersnp-centersnp[i],axis=1);order=np.argsort(dist);order=order[dist[order]>.08]
    # Sample both close and wider baselines to avoid relying on near-identical views.
    neighbors=[int(order[min(k,len(order)-1)]) for k in [0,2,4,7,10,14]]
    neighbors=list(dict.fromkeys(neighbors));votes=torch.zeros(len(pts),device='cuda',dtype=torch.int16)
    for j in neighbors:
        other=cameras[j];P=other.extrinsics;K=other.intrinsics.to('cuda');camxyz=pts@P[:3,:3].T+P[:3,3]
        z=camxyz[:,2];uv=camxyz@K.T;uv=uv[:,:2]/z.clamp_min(1e-8)[:,None]
        grid=uv.clone();grid[:,0]=grid[:,0]/(w-1)*2-1;grid[:,1]=grid[:,1]/(h-1)*2-1
        zobs=F.grid_sample(depths[j][None,None],grid[None,:,None],mode='nearest',align_corners=True)[0,0,:,0]
        aobs=F.grid_sample(alphas[j][None,None],grid[None,:,None],mode='nearest',align_corners=True)[0,0,:,0]
        inside=(grid.abs()<=1).all(dim=1)&(z>0)&(aobs>=.8)&(zobs>0)
        votes+=(inside&((z-zobs).abs()<(.005+.01*zobs))).to(torch.int16)
    keep=votes>=2;points=pts[keep].double().cpu().numpy()
    volume.integrate(points,extrinsic=centersnp[i].astype(np.float64))
    stats.append({'view':i,'candidate_points':len(pts),'kept_points':len(points),'neighbors':neighbors})
    if i%10==0:print('Fusion',i+1,'/',len(cameras),'keep',len(points),'/',len(pts),flush=True)
vertices,faces=volume.extract_triangle_mesh(min_weight=5)
trimesh.Trimesh(vertices,faces,process=False).export(out/'fused_mesh.ply')
(out/'run.json').write_text(json.dumps({'voxel_size':.01,'sdf_trunc':.04,'min_weight':5,'opacity_threshold':.8,'required_votes':2,'relative_depth_error':.01,'absolute_depth_error':.005,'camera_count':len(cameras),'vertices':len(vertices),'triangles':len(faces),'elapsed_seconds':time.time()-t0,'views':stats},indent=2))
print('COMPLETE',len(vertices),len(faces),'seconds',time.time()-t0,flush=True)
