# Windows：图片到高斯模型

## 文件夹与运行顺序

1. 在仓库 `data/input/` 放入相互重叠的 JPG/PNG 照片。建议初次测试用几十张到一百多张清晰照片，有真实的相机位移，避免大量重复帧、运动模糊和 HEIC 原片。
2. 打开已经配置好的 3DGS Conda 环境，在仓库根目录执行 `python script\windows\Bconvert.py`。这一步调用仓库内 `gaussian-splatting/convert.py` 和 COLMAP，输出 `data/images/`、`data/sparse/0/`。
3. 检查已注册图片数、相机轨迹和稀疏点云。相机求解不好时先处理照片，不要急着训练。
4. 执行 `python script\windows\Ctrain.py --iterations 7000 --resolution 2`。它调用仓库内 `gaussian-splatting/train.py`，输出 `output/point_cloud/iteration_7000/point_cloud.ply`。

`--resolution 2` 是先用半分辨率适配 16GB 显存；若显存不足可试 `--resolution 4`。确认流程和照片质量后，再另起一次实验尝试更多迭代。脚本会拒绝覆盖已有转换或训练结果；更换素材前运行 `script/windows/Dinit_workspace.py`，将本轮 `data/` 与 `output/` 归档并创建空目录。

## 换电脑时

源码与三个扩展源码都随本仓库保存，因此不需要把官方仓库再克隆到项目里；**仍需在新电脑安装**兼容的 NVIDIA 驱动、CUDA、PyTorch、编译器和 COLMAP，并在 Conda 环境中编译扩展。版本、已验证的 Windows 配置和安装路径见 [Windows 原生环境记录](Windows原生3DGS环境.md)。

脚本通过当前 `python` 运行官方源码，不写死 Conda 安装路径。COLMAP 可在 `PATH` 中，也可设环境变量 `COLMAP_BIN` 指向 `COLMAP.bat` 或 `colmap.exe`。当前 Windows 电脑已设置用户级 `COLMAP_BIN`；在新电脑上需重新配置该变量。固定版本的官方 `convert.py` 构造 COLMAP 命令时没有给数据路径加引号，因此仓库路径请避免空格。

源码版本以 `gaussian-splatting/source-manifest.json` 及环境记录为准。为兼容当前 COLMAP 4.2.1，仓库内 `gaussian-splatting/convert.py` 将 `--SiftExtraction.use_gpu`、`--SiftMatching.use_gpu` 分别改为 `--FeatureExtraction.use_gpu`、`--FeatureMatching.use_gpu`。其余训练逻辑没有改动。源码保留原许可；本流程当前用于学习和实验。

## 已验证

2026-10-23，用旧房间素材的 48 张图通过新目录中的两个脚本进行了短测试：COLMAP 注册 48/48 张，随后训练 50 步，生成 `output/point_cloud/iteration_50/point_cloud.ply`。这只验证路径和执行流程；50 步结果不能评价重建质量，也没有生成 Mesh。

仓库清理前的 `runs/` 历史报告已归档到本机 `D:\3dgs\archive\legacy-runs-20261023\`；本次目录结构烟测的 PLY 已归档到 `D:\3dgs\archive\repo-layout-smoke-20261023\point_cloud.ply`。工作区内的 `data/input/` 与 `output/` 已清空，供下一段真实素材使用。
