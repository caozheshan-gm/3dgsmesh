"""Estimate a similarity transform; its result must be checked in rendered views."""
from pathlib import Path
import importlib.util, json
import numpy as np
import open3d as o3d
from PIL import Image, ImageDraw

o3d.utility.random.seed(42)
p=Path('/data/projects/benchmelb-20261018');out=p/'kiri-comparison';out.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('colmap_loader','/data/apps/SuGaR/gaussian_splatting/scene/colmap_loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
ims=loader.read_extrinsics_binary(str(p/'sparse/0/images.bin'))
centers=[];directions=[];ups=[]
for im in ims.values():
    R=loader.qvec2rotmat(im.qvec);centers.append(-R.T@im.tvec);directions.append(R.T[:,2]);ups.append(-R.T[:,1])
centers=np.array(centers);directions=np.array(directions)
A=np.eye(3)[None]-directions[:,:,None]*directions[:,None,:]
focus=np.linalg.solve(A.sum(0),np.einsum('nij,nj->ni',A,centers).sum(0))
up=np.mean(ups,axis=0);up/=np.linalg.norm(up)
radius=np.median(np.linalg.norm(centers-focus,axis=1))
print('focus',focus,'up',up,'radius',radius,flush=True)

def cloud(path):
    mesh=o3d.io.read_triangle_mesh(str(path));pc=o3d.geometry.PointCloud();pc.points=mesh.vertices
    return pc
src=cloud(p/'kiri-input/mesh/3DModel.obj')
dst=cloud(p/'delivery/mesh/benchmelb-mesh-preview.ply')

def crop(pc,center,radius,up):
    pc=pc.voxel_down_sample(radius*.008)
    plane,ids=pc.segment_plane(distance_threshold=radius*.012,ransac_n=3,num_iterations=1000)
    plane=np.array(plane)
    if plane[:3]@up<0:plane=-plane
    v=np.asarray(pc.points);h=v@plane[:3]+plane[3]
    anchor=center-plane[:3]*(center@plane[:3]+plane[3])
    horizontal=v-anchor-h[:,None]*plane[:3]
    keep=(np.linalg.norm(horizontal,axis=1)<radius)&(h>radius*.07)&(h<radius*.75)
    part=pc.select_by_index(np.where(keep)[0])
    print('crop',len(part.points),'plane',plane.tolist(),'height bounds',np.quantile(h[keep],[.05,.5,.95]).tolist(),flush=True)
    return part,plane
src,source_plane=crop(src,np.array([0.,-1.,0.]),2.6,np.array([0.,1.,0.]))
dst,target_plane=crop(dst,focus,radius,up)
o3d.io.write_point_cloud(str(out/'source-crop.ply'),src)
o3d.io.write_point_cloud(str(out/'target-crop.ply'),dst)

def normalize(pc):
    v=np.asarray(pc.points);c=np.median(v,axis=0);r=np.linalg.norm(np.quantile(v,.95,axis=0)-np.quantile(v,.05,axis=0))
    M=np.eye(4);M[:3,:3]/=r;M[:3,3]=-c/r
    pc.transform(M);pc=pc.voxel_down_sample(.012)
    pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=.05,max_nn=40))
    f=o3d.pipelines.registration.compute_fpfh_feature(pc,o3d.geometry.KDTreeSearchParamHybrid(radius=.1,max_nn=100))
    return pc,f,M
src,fs,Ms=normalize(src);dst,ft,Mt=normalize(dst)
reg=o3d.pipelines.registration
result=reg.registration_ransac_based_on_feature_matching(src,dst,fs,ft,True,.065,
    reg.TransformationEstimationPointToPoint(True),4,
    [reg.CorrespondenceCheckerBasedOnEdgeLength(.8),reg.CorrespondenceCheckerBasedOnDistance(.065)],reg.RANSACConvergenceCriteria(1000000,.999))
print('RANSAC',result,flush=True)
scale=float(np.cbrt(np.linalg.det(result.transformation[:3,:3])))
assert .7<scale<1.4,('Degenerate normalized scale',scale)
result=reg.registration_icp(src,dst,.045,result.transformation,reg.TransformationEstimationPointToPoint(False),reg.ICPConvergenceCriteria(max_iteration=100))
T=np.linalg.inv(Mt)@result.transformation@Ms
report={'kiri_mesh_to_ours':T.tolist(),'fitness':result.fitness,'normalized_inlier_rmse':result.inlier_rmse,
    'focus':focus.tolist(),'up':up.tolist(),'camera_radius':float(radius),'source_floor':source_plane.tolist(),'target_floor':target_plane.tolist(),
    'note':'Similarity fit to cropped geometry, not measured ground truth; verify silhouettes before comparison.'}
(out/'alignment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
src.transform(result.transformation)
both=np.concatenate([np.asarray(src.points),np.asarray(dst.points)])
low,high=np.quantile(both,[.005,.995],axis=0)
sheet=Image.new('RGB',(1500,500),'white');draw=ImageDraw.Draw(sheet)
for col,(u,v) in enumerate([(0,1),(0,2),(1,2)]):
    scale=440/max(high[u]-low[u],high[v]-low[v]);mid=(low+high)/2
    for pc,color in [(dst,(40,100,240)),(src,(240,90,40))]:
        a=(np.asarray(pc.points)[:,[u,v]]-mid[[u,v]])*scale+[col*500+250,250]
        for x,y in a:draw.ellipse((int(x)-1,int(y)-1,int(x)+1,int(y)+1),fill=color)
    draw.text((col*500+8,8),'KIRI orange / ours blue (cropped fit)',fill='black')
sheet.save(out/'alignment-contact.jpg',quality=95)
