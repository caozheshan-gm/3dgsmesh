"""Experimental learned correspondence front-end; COLMAP still verifies geometry."""
import sys, time, json, sqlite3
from pathlib import Path
import numpy as np
import torch
from PIL import Image
sys.path.insert(0,'/data/apps/myroom-v2-LightGlue')
from lightglue import SuperPoint, LightGlue
from lightglue.utils import load_image

torch.set_num_threads(2)
torch.set_grad_enabled(False)
project=Path('/data/projects/benchmelb-20261018')
p=project/'lightglue'
images=project/'input'
for d in ['features','matches','logs','sparse']: (p/d).mkdir(parents=True,exist_ok=True)
files=sorted(images.glob('*.jpg'))
assert len(files)==277
extractor=SuperPoint(max_num_keypoints=2048).eval().cuda()
features=[]
start=time.time()
for i,f in enumerate(files):
    cache=p/'features'/f'{i:05d}.pt'
    if cache.exists(): feat=torch.load(cache,map_location='cpu')
    else:
        feat=extractor.extract(load_image(f).cuda(),resize=1280)
        feat={k:v.cpu() for k,v in feat.items()}
        torch.save(feat,cache)
    features.append(feat)
    if i%50==0: print('Extract',i,len(files),'keypoints',feat['keypoints'].shape[1],flush=True)
del extractor
torch.cuda.empty_cache()
if "--extract-only" in sys.argv:
    print("FEATURES_COMPLETE",len(features),flush=True)
    sys.exit(0)
global_desc=np.stack([f['descriptors'][0].mean(0).numpy() if f['descriptors'].shape[1] else np.zeros(256) for f in features])
global_desc/=np.maximum(np.linalg.norm(global_desc,axis=1,keepdims=True),1e-8)
similarity=global_desc@global_desc.T
pairs=set()
offsets=list(range(1,13))+[16,24,32,48,64,96,128,192,256]
for i in range(len(files)):
    for offset in offsets:
        if i+offset<len(files):pairs.add((i,i+offset))
    retrieved=0
    for j in np.argsort(similarity[i])[::-1]:
        if abs(int(j)-i)<32:continue
        pairs.add(tuple(sorted((i,int(j)))))
        retrieved+=1
        if retrieved==12:break
pairs=sorted(pairs)
(p/'pairs.json').write_text(json.dumps(pairs))
print('Matching',len(pairs),'pairs',flush=True)
features=[{k:v.cuda() for k,v in f.items()} for f in features]
matcher=LightGlue(features='superpoint',flash=False).eval().cuda()
kept=0
for n,(i,j) in enumerate(pairs):
    cache=p/'matches'/f'{i:05d}_{j:05d}.npy'
    if cache.exists(): matches=np.load(cache)
    elif min(features[i]['keypoints'].shape[1],features[j]['keypoints'].shape[1])<4:
        matches=np.empty((0,2),dtype=np.uint32);np.save(cache,matches)
    else:
        pred=matcher({'image0':features[i],'image1':features[j]})
        matches=pred['matches'][0].cpu().numpy().astype(np.uint32)
        np.save(cache,matches)
    kept+=len(matches)>=16
    if n%100==0:print('Match',n,len(pairs),'pairs>=16',kept,'elapsed',round(time.time()-start,1),flush=True)

db=p/'database.db'
if not db.exists():
    source=sqlite3.connect(str(project/'distorted/database.db'))
    c=sqlite3.connect(db);source.backup(c);source.close()
    for table in ['two_view_geometries','matches','descriptors','keypoints','images','cameras']:c.execute(f'DELETE FROM {table}')
    w,h=Image.open(files[0]).size
    params=np.array([1.2*w,w/2,h/2,0.],dtype=np.float64)
    c.execute('INSERT INTO cameras(camera_id,model,width,height,params,prior_focal_length) VALUES(1,2,?,?,?,0)',(w,h,params.tobytes()))
    for i,f in enumerate(files):
        c.execute('INSERT INTO images(image_id,name,camera_id) VALUES(?,?,1)',(i+1,f.name))
        points=features[i]['keypoints'][0].cpu().numpy().astype(np.float32)+.5
        c.execute('INSERT INTO keypoints(image_id,rows,cols,data) VALUES(?,?,2,?)',(i+1,len(points),points.tobytes()))
    c.commit();c.close()
with (p/'raw-matches.txt').open('w') as out:
    for i,j in pairs:
        matches=np.load(p/'matches'/f'{i:05d}_{j:05d}.npy')
        if len(matches)<16:continue
        out.write(f'{files[i].name} {files[j].name}\n')
        np.savetxt(out,matches,fmt='%d')
        out.write('\n')
(p/'logs/MATCHES_COMPLETE').touch()
print('Completed learned matches',kept,'of',len(pairs),flush=True)
