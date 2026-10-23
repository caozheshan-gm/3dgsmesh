"""Render interior diagnostic views; models are not registered to one another."""
from pathlib import Path
import json
import numpy as np
import torch
from PIL import Image, ImageDraw
from pytorch3d.io import load_objs_as_meshes
from pytorch3d.renderer import (
    FoVPerspectiveCameras, look_at_view_transform, MeshRasterizer,
    MeshRenderer, RasterizationSettings, SoftPhongShader, AmbientLights, BlendParams,
)

p = Path('/data/projects/myroom-20261017')
out = p / 'kiri-comparison'
out.mkdir(exist_ok=True)
paths = {
    'kiri-default': p / 'kiri-mesh/3DModel.obj',
    'sugar': next(Path('/data/apps/SuGaR/output/refined_mesh/myroom-20261017').glob('*.obj')),
}
report = {}
directions = [(1,0,0),(-1,0,0),(0,0,1),(0,0,-1),(0,1,0),(0,-1,0)]
for name, path in paths.items():
    print('Loading', name, flush=True)
    mesh = load_objs_as_meshes([str(path)], device='cuda')
    verts = mesh.verts_packed()
    v = verts.cpu().numpy()
    # Match the diagnostic framing rule, not the physical camera pose.
    lo, hi = np.quantile(v, [.05,.95], axis=0)
    center = (lo + hi) / 2
    faces = mesh.faces_packed().cpu().numpy()
    edges = np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    _,counts = np.unique(edges,axis=0,return_counts=True)
    report[name] = {'center':center.tolist(),'vertices':len(v),'triangles':len(faces),
        'boundary_edges_raw':int((counts==1).sum()),'nonmanifold_edges_raw':int((counts>2).sum()),
        'edges_raw':len(counts)}
    del edges, counts
    tiles=[]
    for i,d in enumerate(directions):
        eye = torch.tensor(center,device='cuda',dtype=torch.float32)[None]
        at = eye + torch.tensor(d,device='cuda',dtype=torch.float32)[None]
        up = ((0.,0.,1.),) if abs(d[1])==1 else ((0.,1.,0.),)
        R,T=look_at_view_transform(eye=eye,at=at,up=up,device='cuda')
        cameras=FoVPerspectiveCameras(device='cuda',R=R,T=T,fov=90,znear=.01,zfar=100)
        renderer=MeshRenderer(
            rasterizer=MeshRasterizer(cameras=cameras,raster_settings=RasterizationSettings(
                image_size=600,faces_per_pixel=1,blur_radius=0.,max_faces_per_bin=100000,cull_backfaces=False)),
            shader=SoftPhongShader(device='cuda',cameras=cameras,lights=AmbientLights(device='cuda'),
                blend_params=BlendParams(background_color=(.15,.15,.15))))
        with torch.no_grad():
            image=renderer(mesh)[0,...,:3].clamp(0,1).cpu().numpy()
        im=Image.fromarray((image*255).astype(np.uint8))
        ImageDraw.Draw(im).text((10,10),f'{name} direction {d}',fill='red')
        im.save(out/f'{name}-{i}.jpg',quality=93)
        tiles.append(im.resize((400,400)))
        print('Rendered',name,i,flush=True)
    sheet=Image.new('RGB',(1200,800))
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%3)*400,(i//3)*400))
    sheet.save(out/f'{name}-contact.jpg',quality=94)
    del mesh, verts
    torch.cuda.empty_cache()
(out/'mesh-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
