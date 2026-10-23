"""Validate exported OBJ and render test views using the existing server runtime."""
import json
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from plyfile import PlyData
from pytorch3d.io import load_objs_as_meshes
from pytorch3d.renderer import (
    MeshRasterizer, MeshRenderer, RasterizationSettings, SoftPhongShader,
    AmbientLights, BlendParams,
)
from sugar_scene.cameras import load_gs_cameras, convert_camera_from_gs_to_pytorch3d

project = Path('/data/projects/myroom-20261017')
root = Path('/data/apps/SuGaR/output')
obj = next((root / 'refined_mesh/myroom-20261017').glob('*.obj'))
preview = project / 'preview'
preview.mkdir(exist_ok=True)
mesh = load_objs_as_meshes([str(obj)], device='cuda')
assert torch.isfinite(mesh.verts_packed()).all()
assert mesh.faces_packed().numel() > 0
assert mesh.textures is not None
report = {
    'obj': str(obj),
    'vertices': int(mesh.verts_packed().shape[0]),
    'triangles': int(mesh.faces_packed().shape[0]),
    'uv_vertices': int(mesh.textures.verts_uvs_padded().shape[1]),
    'texture_shape': list(mesh.textures.maps_padded().shape),
    'bounds_min': mesh.verts_packed().min(0).values.tolist(),
    'bounds_max': mesh.verts_packed().max(0).values.tolist(),
    'gaussians': {},
}
for kind, path in [
    ('vanilla', root / 'vanilla_gs/myroom-20261017/point_cloud/iteration_7000/point_cloud.ply'),
    ('refined', next((root / 'refined_ply/myroom-20261017').glob('*.ply'))),
]:
    ply = PlyData.read(str(path))
    names = ply['vertex'].data.dtype.names
    assert all(k in names for k in ['x', 'y', 'z', 'opacity', 'scale_0', 'rot_0'])
    report['gaussians'][kind] = {'count': ply['vertex'].count, 'bytes': path.stat().st_size}
cams = load_gs_cameras(str(project), str(root / 'vanilla_gs/myroom-20261017') + '/', load_gt_images=False)
for idx in [0, 24]:
    cam = cams[idx]
    cameras = convert_camera_from_gs_to_pytorch3d([cam])
    height = 800
    width = round(cam.image_width / cam.image_height * height)
    renderer = MeshRenderer(
        rasterizer=MeshRasterizer(cameras=cameras, raster_settings=RasterizationSettings(
            image_size=(height, width), blur_radius=0., faces_per_pixel=1, max_faces_per_bin=100000,
        )),
        shader=SoftPhongShader(device='cuda', cameras=cameras,
            lights=AmbientLights(device='cuda'), blend_params=BlendParams(background_color=(1.,1.,1.))),
    )
    with torch.no_grad():
        rgb = renderer(mesh)[0, ..., :3].clamp(0, 1).cpu().numpy()
    Image.fromarray((rgb * 255).astype(np.uint8)).save(preview / f'mesh-view-{idx:02d}.png')
(project / 'logs/artifact-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
