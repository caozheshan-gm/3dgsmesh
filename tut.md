# BenchMelb：第一次自己运行 3DGS

目标：用 Windows 桌面上的 `BenchMelb-KIRI.mp4`，从视频抽帧、用 COLMAP 求解相机，再训练出一个 3DGS 高斯模型。**这套命令目前只生成高斯，不生成 Mesh。**

视频来自 [AWS 的 Gaussian Splats 示例素材](https://github.com/aws-solutions-library-samples/guidance-for-open-source-3d-reconstruction-toolbox-for-gaussian-splats-on-aws/blob/main/assets/input/BenchMelb.mov)，约 55 秒。当前文件位于 `C:\Users\Admin\Desktop\BenchMelb-KIRI.mp4`。

## 1. 打开终端并进入工作区

打开 Windows PowerShell 或 Anaconda PowerShell Prompt，逐行运行：

```powershell
cd C:\Users\Admin\Desktop\gitproject\3dgsmesh
conda activate gs-main
```

看到提示符前面出现 `(gs-main)`，再继续。当前电脑已经配置好这个环境；换电脑时参照 [README](README.md) 安装依赖。

已经理解各步骤、只想一次运行时，可打开 `script/windows/Eall_in_one.py`，修改文件开头的 `VIDEO_PATH`，然后在 VS Code 用 `gs-main` 解释器运行。它按下面的第 2～4 步依次调用 A、B、C 脚本；旧数据存在时先运行 `Dinit_workspace.py` 归档。

## 2. 视频抽帧

以后可打开 `script/windows/Aextract_frames.py`，在文件开头修改视频路径、每秒抽帧数和 JPG 质量，再点 VS Code 的“Run Python File”。脚本会在 `data/input` 已有照片时停止，以免混用两个实验。下面保留等价的 FFmpeg 命令，便于学习每个参数：

```powershell
ffmpeg -i "$env:USERPROFILE\Desktop\BenchMelb-KIRI.mp4" -vf fps=3 -q:v 2 "data\input\frame_%04d.jpg"
```

输入是一段视频；输出是 `data\input\frame_0001.jpg` 等 JPG 图片。每秒取 3 帧，约得到 166 张。终端会显示 `frame=`、`time=` 等进度；结束后确认 `data\input` 里有图片。如果 FFmpeg 询问是否覆盖同名文件，先停下来检查旧数据，不要直接混用两次实验的图片。

## 3. 求解相机并整理训练数据

如果 PowerShell 报 `COLMAP not found`，说明当前终端没有读到已经设置的用户环境变量。在**这个终端**先运行一次下面的命令，再执行转换脚本：

```powershell
$env:COLMAP_BIN = 'D:\3dgs\apps\colmap-4.2.1\COLMAP.bat'
```

```powershell
python script\windows\Bconvert.py
```

这个脚本会调用仓库内的官方 `gaussian-splatting\convert.py`，再由它调用 COLMAP。主要产物：

| 位置 | 内容 |
| --- | --- |
| `data\distorted` | COLMAP 中间结果，包括特征数据库和初步相机解算 |
| `data\images` | 去畸变后的训练图片 |
| `data\sparse\0\cameras.bin` | 相机内参，例如焦距、成像尺寸 |
| `data\sparse\0\images.bin` | 每张图片对应的相机位置和朝向 |
| `data\sparse\0\points3D.bin` | 稀疏三维点 |

训练首次读取数据时，官方代码会把 `data\sparse\0\points3D.bin` 转为 `data\sparse\0\points3D.ply`，并复制到 `output\input.ply`。这两个 PLY 都是**稀疏点云，不是训练后的高斯模型**。

终端会输出 COLMAP 各阶段日志，但没有统一的总进度百分比。看到脚本最后报告 `Converted data/images and data/sparse/0`，并确认上述三个 `.bin` 文件都存在，再开始训练。如果相机只恢复了少数图片，先检查拍摄或抽帧，不要急着训练。

## 4. 训练高斯

```powershell
python script\windows\Ctrain.py --iterations 7000 --resolution 2
```

这里运行的是仓库内官方 `gaussian-splatting\train.py`；`7000` 是训练迭代数，`2` 表示训练分辨率为原图的一半。终端会显示训练进度与误差。完成后主要查看：

```text
output\point_cloud\iteration_7000\point_cloud.ply
```

这个 `.ply` 才是训练出的 **3DGS 高斯模型**。`output` 还会有训练参数、相机和评估结果。不要用普通 Mesh 查看器判断这个 PLY 的效果；它需要支持 Gaussian Splatting 的查看器。

## 遇到问题时

- 每条命令成功后再运行下一条；报错时保留 PowerShell 末尾的报错文本。
- `Bconvert.py` 提示 `Conversion output already exists`：`data\distorted`、`data\images` 或 `data\sparse` 有上次的结果。运行 `script/windows/Dinit_workspace.py` 归档旧实验并准备空目录，再开始新实验。
- `Ctrain.py` 提示 `Output folder is not empty`：`output` 中已有训练结果。运行 `script/windows/Dinit_workspace.py` 归档旧结果，再开始新实验。
- 训练出的高斯和 Mesh 是两类不同结果；Mesh 转换是后续单独的实验步骤。



## 预览
- https://superspl.at/editor
