"""Fit scale, floor-plane translation and yaw without arbitrary 3-D rotations."""
from pathlib import Path
import json
import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw
p=Path('/data/projects/benchmelb-20261018/kiri-comparison')
old=json.loads((p/'alignment.json').read_text())
def frame(plane,hint):
    n=np.array(plane[:3]);x=np.array([1.,0,0]);x-=n*(x@n);x/=np.linalg.norm(x)
    B=np.stack([x,n,np.cross(x,n)],axis=1);h=np.array(hint);anchor=h-n*(h@n+plane[3])
    return B,anchor
Bs,As=frame(old['source_floor'],[0,-1,0]);Bt,At=frame(old['target_floor'],old['focus'])
def points(name,B,A):
    pc=o3d.io.read_point_cloud(str(p/name));pc=pc.voxel_down_sample(.035)
    v=(np.asarray(pc.points)-A)@B
    if len(v)>9000:v=v[np.linspace(0,len(v)-1,9000).astype(int)]
    return v
src=points('source-crop.ply',Bs,As);dst=points('target-crop.ply',Bt,At)
tree=cKDTree(dst);rng=np.random.default_rng(42)
def rotation(angle):
    c,s=np.cos(angle),np.sin(angle);return np.array([[c,0,-s],[0,1,0],[s,0,c]])
def solve(v,w):
    a=v[:,[0,2]];b=w[:,[0,2]];ac=a.mean(0);bc=b.mean(0)
    U,_,Vt=np.linalg.svd((a-ac).T@(b-bc));D=np.eye(2);D[-1,-1]=np.linalg.det(Vt.T@U.T)
    R2=Vt.T@D@U.T
    scale=(np.sum(((a-ac)@R2.T)*(b-bc))+np.sum(v[:,1]*w[:,1]))/(np.sum((a-ac)**2)+np.sum(v[:,1]**2))
    scale=np.clip(scale,.65,1.6);t=np.zeros(3);t[[0,2]]=bc-scale*(R2@ac)
    R=np.eye(3);R[np.ix_([0,2],[0,2])]=R2
    return scale,R,t
answers=[]
for angle in np.linspace(0,2*np.pi,36,endpoint=False):
    for initial_scale in [.9,1.2]:
        s=initial_scale;R=rotation(angle);t=np.zeros(3)
        for it in range(45):
            q=s*src@R.T+t;dist,ids=tree.query(q,workers=1)
            keep=dist<=np.quantile(dist,.8)
            ns,nR,nt=solve(src[keep],dst[ids[keep]])
            change=abs(ns-s)+np.linalg.norm(nR-R)+np.linalg.norm(nt-t)
            s,R,t=ns,nR,nt
            if change<1e-6:break
        q=s*src@R.T+t;d1=tree.query(q,workers=1)[0];d2=cKDTree(q).query(dst,workers=1)[0]
        score=np.sqrt(np.mean(np.sort(d1)[:int(len(d1)*.75)]**2)+np.mean(np.sort(d2)[:int(len(d2)*.75)]**2))
        answers.append((score,s,R,t))
answers.sort(key=lambda x:x[0]);score,s,R,t=answers[0]
T=np.eye(4);T[:3,:3]=s*Bt@R@Bs.T;T[:3,3]=At+Bt@t-T[:3,:3]@As
report={**old,'kiri_mesh_to_ours':T.tolist(),'method':'floor-constrained multi-start yaw/scale/translation ICP',
        'fitness':None,'normalized_inlier_rmse':None,'trimmed_bidirectional_rmse_scene_units':float(score),
        'scale':float(s),'top_scores':[float(x[0]) for x in answers[:8]],
        'note':'Approximate geometry alignment, not calibrated camera ground truth; inspect silhouettes.'}
(p/'alignment-floor.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
q=s*src@R.T+t;both=np.concatenate([q,dst]);lo,hi=np.quantile(both,[.005,.995],axis=0)
sheet=Image.new('RGB',(1500,500),'white');d=ImageDraw.Draw(sheet)
for col,(u,v) in enumerate([(0,1),(0,2),(1,2)]):
    k=440/max(hi[u]-lo[u],hi[v]-lo[v]);mid=(lo+hi)/2
    for a,color in [(dst,(40,100,240)),(q,(240,90,40))]:
        xy=(a[:,[u,v]]-mid[[u,v]])*k+[col*500+250,250]
        for x,y in xy:d.point((int(x),int(y)),fill=color)
    d.text((col*500+8,8),'Floor-constrained: KIRI orange / ours blue',fill='black')
sheet.save(p/'alignment-floor.jpg',quality=95)
