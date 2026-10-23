# 3dgsmesh

这是 Windows 上的图片预处理和 3DGS 训练工作区。官方 [3D Gaussian Splatting 源码](https://github.com/graphdeco-inria/gaussian-splatting)及训练所需的三个扩展源码保存在 `gaussian-splatting/`，脚本使用仓库相对路径，不依赖另一份 `D:\3dgs\apps\gaussian-src`。

```text
data/input/                 放 JPG/PNG 照片
output/                     训练结果
script/windows/convert.py   COLMAP 相机求解与去畸变
script/windows/train.py     3DGS 训练
gaussian-splatting/         固定版本的官方源码快照
docs/                       环境与实验记录
```

在仓库根目录、已经激活的 3DGS Conda 环境中运行：

```powershell
python script\windows\convert.py
python script\windows\train.py --iterations 7000 --resolution 2
```

转换结果在 `data/images/` 和 `data/sparse/0/`，高斯模型在 `output/point_cloud/iteration_7000/point_cloud.ply`。`data/` 和 `output/` 的内容默认不提交 Git。首次使用及更换电脑时的依赖配置、参数和注意事项见 [Windows 工作流](docs/Windows-image-to-3dgs.md)。

源码快照取自本机此前验证过的官方固定版本，保留原许可与依赖源码；只为兼容 COLMAP 4.2.1 修改了 `gaussian-splatting/convert.py` 中两个已更名的 GPU 参数。原始版本和环境记录见 [Windows 环境文档](docs/Windows原生3DGS环境.md)。本流程只输出 3DGS；Mesh 是之后独立的一步。
