# Windows 原生 3DGS 环境记录

截至 2026-10-23，在用户的 DESKTOP-QC218N8 上安装，不使用 WSL2。系统实际查询为 Windows 11 Home 10.0.26300，i9-13980HX、64 GB RAM、RTX 4090 Laptop GPU 16 GB VRAM、驱动 617.42。通过 Mac SSH 别名 `win4090` 管理；密钥不保存在仓库。

## 安装位置与版本

- `D:\3dgs\BuildTools`：Visual Studio 2022 Build Tools，MSVC 14.38.33130、Windows SDK 22621。还有 14.44，但构建 CUDA 扩展时固定使用 14.38。
- `D:\3dgs\envs\gs-main`：独立 Conda 环境，Python 3.10.19。已有 `kitting`、`meeting` 等环境保留。
- CUDA 12.4.1 包：NVIDIA 官方 Conda 标签 `cuda-12.4.1` 的 win-64 包，下载时逐个用官方 repodata 的 SHA256 验证。CUDA 编译器为 `D:\3dgs\envs\gs-main\bin\nvcc.exe`，头文件在环境根目录 `include`，库在 `Lib\x64`。
- PyTorch 2.5.1+cu124、torchvision 0.20.1+cu124、NumPy 1.26.4 等：官方轮子经 OpenClaw 跳板服务器中转后离线安装。
- `D:\3dgs\apps\colmap-4.2.1`：官方 Windows CUDA 包；完整包 SHA256 `e9c5cbd84c2ea986d2e970a2473fc2d2e6b34a2cdcf5d3df2765c319a63af881`。`colmap -h` 已运行。
- `D:\3dgs\apps\gaussian-src`：官方 3DGS 根提交 `54c035f7834b564019656c3e3fcc3646292f727d`；rasterizer `9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0`；fused-ssim `1272e21a282342e89537159e4bad508b19b34157`；simple-knn `86710c2d4b46680c02301765dd79e465819c8f19`（同提交镜像）；GLM `5c46b9c07008ae65cb81ab79cd677ecc1934b903`。大图片 assets 与 SIBR viewer 未下载，不影响训练脚本。
- 启动脚本 `D:\3dgs\scripts\activate-gs.cmd`，编译脚本 `D:\3dgs\scripts\build-extensions.cmd`。日志在 `D:\3dgs\logs`。这些是当时安装环境所用的脚本，保留在本机 `D:\3dgs\scripts`；仓库日常入口现为 `script/windows/convert.py` 和 `script/windows/train.py`。

## 中转下载

OpenClaw 服务器仅作文件中转；文件在其 `/home/ubuntu/3dgs-downloads`，不调用其 GPU。完整 COLMAP 下载约 34 秒、平均约 11.5 MiB/s；Mac/Windows 同源直接下载约 15–31 KiB/s。PyTorch Windows wheel 约 2.5 GB，服务器已缓存并下载。Windows 传输最初用 Mac SSH 流式转发，在约 650 MiB 时连接重置；随后改成 27 段、每段 96 MiB，逐段核对 SHA256，再核对完整包及 24 个轮子文件的 SHA256。Mac 不长期保存 3 GB 完整 wheel。用户可打开 Mac 桌面 `Windows-3DGS-progress.command` 查看安装日志；传输已完成，显示的分段进度停在最终数量。

## 验证

- COLMAP 4.2.1 CLI 已执行；其 GPU SIFT 提取 2 张小样图片成功。
- 旧 `myroom.mov` 求解结果的 48 张照片经 COLMAP 去畸变，`model_analyzer` 显示 48/48 图像、2030 稀疏点、平均重投影误差 0.768 px。这只验证工具链输入，不证明整房间结构已经正确。
- CUDA 12.4 编译器 `nvcc --version` 已执行。
- PyTorch 2.5.1+cu124 报告 CUDA 可用、GPU 为 RTX 4090 Laptop；512×512 CUDA 矩阵运算与梯度回传成功（`GPU_GRAD_OK`）。`pip check` 无依赖冲突。
- `diff_gaussian_rasterization`、`simple_knn`、`fused_ssim` 三个 Windows 扩展均以 MSVC 14.38/CUDA 12.4 编译、安装、导入成功。
- 48 张旧房间求解图做 50 步环境烟测，训练退出码 0，`D:\3dgs\runs\smoke-room-50\point_cloud\iteration_50\point_cloud.ply` 存在，504969 字节、2030 个 Gaussian。第 25 步训练视角 PSNR 6.02 dB、第 50 步 8.78 dB；仅为工具链验证，不用于评价重建质量。

## 使用方式

这是安装时的历史记录。现在项目内已保存官方源码快照；在已激活的 Conda 环境中，从仓库根目录运行 `python script\windows\convert.py` 和 `python script\windows\train.py`。输入为 `data\input`，输出为 `output`。测试不会替代对视频质量、相机求解和真实尺寸的审查。

Windows 桌面已创建 `3DGS Environment.cmd`，双击后打开并保持已激活环境的命令提示符。Mac 桌面 `Windows-3DGS-progress.command` 已改为显示完成摘要。

官方 3DGS 及其扩展含研究/评估用途许可；若将来厂房展示用于商业交付，需要逐项核对源码与模型工具许可。本次仅作本地学习和实验。
