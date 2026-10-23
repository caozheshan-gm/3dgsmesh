"""Summarize registration coverage and project sparse geometry for inspection."""
import sys,json,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import open3d as o3d

model=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('colmap_loader','/data/apps/SuGaR/gaussian_splatting/scene/colmap_loader.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
images=loader.read_extrinsics_binary(str(model/'images.bin'))
intrinsics=loader.read_intrinsics_binary(str(model/'cameras.bin'))
xyz,rgb,err=loader.read_points3D_binary(str(model/'points3D.bin'))
selection=json.loads(Path('/data/projects/myroom-sfm-v2/sharp-pinhole/frame-selection.json').read_text())
times={v['image']:v['candidate_time_seconds'] for v in selection}
rows=[]
for im in images.values():
    R=loader.qvec2rotmat(im.qvec);c=-R.T@im.tvec
    rows.append({'name':im.name,'time':times[im.name],'center':c.tolist(),'observations':int((im.point3D_ids>=0).sum())})
rows.sort(key=lambda r:r['time']);centers=np.array([r['center'] for r in rows])
bins=np.linspace(0,122,13);hist=np.histogram([r['time'] for r in rows],bins)[0]
allhist=np.histogram(list(times.values()),bins)[0]
report={'registered':len(rows),'selected':len(selection),'fraction':len(rows)/len(selection),
 'points':len(xyz),'point_error_quantiles':np.quantile(err,[.5,.9,.99]).tolist(),
 'time_bins':bins.tolist(),'registered_per_bin':hist.tolist(),'selected_per_bin':allhist.tolist(),
 'model_path':str(model),'intrinsics':{str(k):{'model':c.model,'width':c.width,'height':c.height,'params':c.params.tolist()} for k,c in intrinsics.items()},'cameras':rows}
(out/'audit.json').write_text(json.dumps(report,indent=2))
cloud=o3d.geometry.PointCloud();cloud.points=o3d.utility.Vector3dVector(xyz);cloud.colors=o3d.utility.Vector3dVector(rgb/255.)
o3d.io.write_point_cloud(str(out/'sparse.ply'),cloud)
# Robust PCA plot; axes arbitrary, camera path colored by video time.
lo,hi=np.quantile(xyz,[.01,.99],axis=0);mask=((xyz>=lo)&(xyz<=hi)).all(1)
data=xyz[mask];colors=rgb[mask]
origin=np.median(data,axis=0);_,s,V=np.linalg.svd(data-origin,full_matrices=False)
a=(data-origin)@V.T;b=(centers-origin)@V.T
sheet=Image.new('RGB',(1500,520),'#fafafa');draw=ImageDraw.Draw(sheet)
for j,(u,v) in enumerate([(0,1),(0,2),(1,2)]):
    pts=np.concatenate([a[:,[u,v]],b[:,[u,v]]]);low,high=np.quantile(pts,[.005,.995],axis=0)
    span=max(high-low);scale=440/max(span,1e-6);middle=(low+high)/2
    def project(q):return ((q-middle)*scale+[j*500+250,270]).astype(int)
    pp=project(a[:,[u,v]])
    for xy,c in zip(pp,colors):
        if j*500<=xy[0]<(j+1)*500 and 30<=xy[1]<510:draw.point(tuple(xy),fill=tuple(int(x) for x in c))
    cc=project(b[:,[u,v]])
    for k,xy in enumerate(cc):
        t=rows[k]['time']/122;col=(int(255*t),40,int(255*(1-t)))
        if k:draw.line([tuple(cc[k-1]),tuple(xy)],fill=col,width=1)
        draw.ellipse((xy[0]-2,xy[1]-2,xy[0]+2,xy[1]+2),fill=col)
    draw.text((j*500+10,8),f'PCA axes {u+1}/{v+1}: {len(rows)}/{len(selection)} cameras',fill='black')
sheet.save(out/'geometry-contact.jpg',quality=95)
# Selected registered frames distributed across the video.
contact=Image.new('RGB',(1200,800),'white');d=ImageDraw.Draw(contact)
for j in range(12):
    candidates=[r for r in rows if bins[j]<=r['time']<bins[j+1]]
    if not candidates:
        d.text(((j%6)*200+5,(j//6)*400+5),'NO REGISTERED FRAME',fill='red');continue
    r=min(candidates,key=lambda r:abs(r['time']-(bins[j]+bins[j+1])/2))
    im=Image.open(Path('/data/projects/myroom-sfm-v2/sharp-pinhole/input')/r['name']);im.thumbnail((200,370))
    x=(j%6)*200;y=(j//6)*400;contact.paste(im,(x,y+25));d.text((x+5,y+5),f'{r["time"]:.1f}s ({len(candidates)} frames)',fill='black')
contact.save(out/'registered-contact.jpg',quality=94)
print(json.dumps({k:v for k,v in report.items() if k!='cameras'},indent=2))
