"""Choose the sharpest candidate within each 0.25-second video interval."""
from pathlib import Path
import json, shutil
import numpy as np
from PIL import Image

p=Path('/data/projects/myroom-sfm-v2/sharp-pinhole')
out=p/'input';out.mkdir(exist_ok=True)
files=sorted((p/'candidates').glob('*.jpg'))
assert len(files)>1000, f'Incomplete candidates: {len(files)}'
records=[]
for start in range(0,len(files),3):
    batch=[]
    for f in files[start:start+3]:
        im=Image.open(f).convert('L');im.thumbnail((450,800))
        a=np.asarray(im,dtype=np.float32)
        lap=a[:-2,1:-1]+a[2:,1:-1]+a[1:-1,:-2]+a[1:-1,2:]-4*a[1:-1,1:-1]
        score=float(lap.var())
        batch.append((score,f))
    score,f=max(batch,key=lambda x:x[0])
    dst=out/f'frame_{len(records)+1:05d}.jpg'
    shutil.copy2(f,dst)
    records.append({'image':dst.name,'candidate':f.name,'candidate_time_seconds':(int(f.stem.split('_')[-1])-1)/12,
                    'sharpness':score,'candidate_scores':[s for s,_ in batch]})
(p/'frame-selection.json').write_text(json.dumps(records,indent=2))
print('Selected',len(records),'of',len(files),'frames',flush=True)
