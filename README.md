# 3dgsmesh

这是 Windows 上的图片预处理和 3DGS 训练工作区。官方 [3D Gaussian Splatting 源码](https://github.com/graphdeco-inria/gaussian-splatting)及训练所需的三个扩展源码保存在 `gaussian-splatting/`，脚本使用仓库相对路径，不依赖另一份 `D:\3dgs\apps\gaussian-src`。

```text
data/input/                 放 JPG/PNG 照片
output/                     训练结果
script/windows/extract_frames.py  视频抽帧，可在 VS Code 中直接运行
script/windows/convert.py   COLMAP 相机求解与去畸变
script/windows/train.py     3DGS 训练
gaussian-splatting/         固定版本的官方源码快照
docs/                       环境与实验记录
```

## 依赖安装（新 Windows 电脑）

当前这台 Windows 电脑已装好以下依赖，不需要重新安装。本流程使用 NVIDIA GPU 原生 Windows 环境，不使用 WSL2。仓库已包含官方 3DGS 和三个 CUDA 扩展的源码，不需要再次克隆官方仓库。已验证的版本如下；官方仓库附带的旧 `environment.yml` 使用 Python 3.7 / CUDA 11.6，**不要直接用它覆盖本机环境**。

1. 安装 [NVIDIA 显卡驱动](https://www.nvidia.com/en-us/drivers/)；用 `nvidia-smi` 确认能识别显卡。
2. 安装 [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install) 和 [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)（C++ 编译工具、Windows SDK）。这台电脑编译扩展时使用 MSVC 14.38 / Windows SDK 22621。
3. 安装 [COLMAP 4.2.1 的 Windows CUDA 版](https://github.com/colmap/colmap/releases/tag/4.2.1)，并把 `COLMAP.bat` 或 `colmap.exe` 加入 `PATH`，或者设置用户环境变量 `COLMAP_BIN` 指向该文件。当前电脑的 `COLMAP_BIN` 指向 `D:\3dgs\apps\colmap-4.2.1\COLMAP.bat`。
   如果从视频抽帧，还需安装 [FFmpeg](https://ffmpeg.org/download.html) 并将 `ffmpeg.exe` 加入 `PATH`；当前电脑已经安装。
4. 在 Conda 终端创建环境，安装 Python 3.10、CUDA 12.4 编译工具、PyTorch CUDA 12.4 和 Python 包：

```powershell
conda create -n gs-main python=3.10.19 pip=24.3.1 -y
conda activate gs-main
conda install cuda -c nvidia/label/cuda-12.4.1
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
python -m pip install numpy==1.26.4 pillow==12.3.0 plyfile==1.0.3 tqdm==4.70.1 opencv-python-headless==4.10.0.84 joblib==1.6.0 setuptools==70.2.0 ninja==1.11.1.3 cmake==3.31.6
```

5. **在已加载 MSVC 编译环境的命令提示符（CMD）中**，激活同一 Conda 环境，再从仓库根目录编译三个扩展。可先打开 VS 2022 的“x64 Native Tools Command Prompt”；如果安装了多个 MSVC 版本，按 [Windows 环境文档](docs/Windows原生3DGS环境.md)选择 14.38。以下为 CMD 命令，`%CONDA_PREFIX%` 是当前环境路径：

```bat
conda activate gs-main
set "CUDA_HOME=%CONDA_PREFIX%"
set "CUDA_PATH=%CONDA_PREFIX%"
set "PATH=%CONDA_PREFIX%\bin;%PATH%"
set "DISTUTILS_USE_SDK=1"
set "TORCH_CUDA_ARCH_LIST=8.9"
set "MAX_JOBS=4"
python -m pip install --no-build-isolation --no-deps .\gaussian-splatting\submodules\diff-gaussian-rasterization .\gaussian-splatting\submodules\simple-knn .\gaussian-splatting\submodules\fused-ssim
```

`TORCH_CUDA_ARCH_LIST=8.9` 对应当前 RTX 4090 Laptop；换显卡时应按其计算能力调整。先执行 `nvcc --version`、`python -c "import torch; print(torch.cuda.is_available())"` 和 `python -m pip check` 验证环境。本机已验证这些组件能共同运行；上面的新机器安装命令尚未在一台空白电脑上从头重跑。安装位置和构建记录见 [Windows 环境文档](docs/Windows原生3DGS环境.md)。

## 运行

如果输入是视频，先打开 `script/windows/extract_frames.py`，在文件开头修改 `VIDEO_PATH`、`FPS` 和 `JPEG_QUALITY`。在 VS Code 中首次运行前，安装 Python 扩展并用“Python: Select Interpreter”选好 `gs-main` 环境；以后点击右上角“Run Python File”即可抽帧，不必再输入 FFmpeg 命令。脚本会把照片放进 `data/input/`；如果该目录已有旧实验照片，会停止，避免混用。已经准备好 JPG/PNG 照片时，直接放进 `data/input/`。

之后在仓库根目录、已激活环境中运行；当前电脑现在可直接用 `conda activate gs-main`：

```powershell
conda activate gs-main
python script\windows\convert.py
python script\windows\train.py --iterations 7000 --resolution 2
```

转换结果在 `data/images/` 和 `data/sparse/0/`，高斯模型在 `output/point_cloud/iteration_7000/point_cloud.ply`。`data/` 和 `output/` 的内容默认不提交 Git。首次使用及更换电脑时的依赖配置、参数和注意事项见 [Windows 工作流](docs/Windows-image-to-3dgs.md)。

源码快照取自本机此前验证过的官方固定版本，保留原许可与依赖源码；只为兼容 COLMAP 4.2.1 修改了 `gaussian-splatting/convert.py` 中两个已更名的 GPU 参数。原始版本和环境记录见 [Windows 环境文档](docs/Windows原生3DGS环境.md)。本流程只输出 3DGS；Mesh 是之后独立的一步。

## 历史归档

myroom 和 BenchMelb 的旧实验报告、参数与结果统计已移到 Mac 本机 `/Users/czss/Documents/3dgsmesh-archive-2026-10-23/runs/`；高斯、网格和截图在同一归档目录的 `artifacts/`。旧报告中的相对链接需以该归档目录为根打开。迁移到 Windows 时按需复制具体成果。过去的 Linux 单次实验脚本可从 Git 历史恢复。
