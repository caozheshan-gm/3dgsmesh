# Windows：图片 → COLMAP → 3DGS

这个仓库负责实验输入、调用脚本和结果记录。官方 3DGS 源码已经单独安装在 `D:\3dgs\apps\gaussian-src`；**不要把官方仓库再次复制进本项目**。`convert.py` 和 `train.py` 都来自那份官方源码，本仓库的 `scripts/windows/run-project.cmd` 只是调用入口。

## 第一次使用

在本仓库根目录打开 PowerShell，先执行：

```powershell
.\scripts\windows\run-project.cmd corner
```

它会创建 `data\corner\input\` 并提示放入照片。复制相互重叠的 JPG/PNG 照片到该目录。路径应使用英文字母、数字、`_` 或 `-` 作为项目名；仓库所在目录不要含空格，因为当前固定版本的官方 `convert.py` 内部没有给 COLMAP 数据路径加引号。视频需先抽帧；HEIC 照片先转成 JPG/PNG。首次小样建议几十到一百多张清晰、有视差、有重叠的图片，并避免大量相同机位的重复帧。

## 运行

推荐分两步，先检查相机求解再投入训练时间：

```powershell
.\scripts\windows\run-project.cmd corner -ConvertOnly
.\scripts\windows\run-project.cmd corner -TrainOnly -Iterations 7000 -Resolution 2
```

第一步通过仓库的 `convert-colmap42.py` 运行官方 `convert.py`。已安装的 COLMAP 4.2.1 将两个旧 GPU 参数更名；适配器仅在内存中替换参数名，不修改官方源码。它调用 COLMAP 特征提取、**穷举匹配**、相机求解和去畸变。结果位于 `data\corner\images\` 与 `data\corner\sparse\0\`。检查 COLMAP 注册图片数量、相机轨迹和稀疏点云后，再运行第二步。超过几百张图时穷举匹配会很慢，应先筛选抽帧或改用适合长序列的匹配流程。

也可以在确认照片质量后一次运行：

```powershell
.\scripts\windows\run-project.cmd corner -Iterations 7000 -Resolution 2
```

第二步调用官方 `train.py`，训练数据放在 `data\corner\`，输出在 `outputs\corner\`。成功后高斯模型位于：

```text
outputs\corner\point_cloud\iteration_7000\point_cloud.ply
```

`7000` 步适合先看覆盖情况；满意后可另建项目或移走旧输出，再用 `-Iterations 30000` 训练。`-Resolution 2` 按 1/2 原图尺寸训练，适合先试 16GB 显存；若显存不足改用 `-Resolution 4`。参数只影响本项目训练，不更改官方源码。

数据和模型由 `.gitignore` 忽略，不会自动提交到 Git。此流程**只生成 3DGS**，不会生成 Mesh；Mesh 需要单独的表面重建与贴图步骤。若转换或训练中断，脚本会拒绝覆盖已有结果；检查问题后将旧结果移走，或使用新项目名重新运行。

## 已验证的小测试

2026-10-23 用旧房间素材的 48 张图片在这份 Windows 仓库运行了上述两阶段入口：COLMAP 注册 48/48 张、1939 个稀疏点、平均重投影误差 0.809 px；接着 `-TrainOnly -Iterations 50 -Resolution 2` 成功生成 `outputs\workflow-smoke\point_cloud\iteration_50\point_cloud.ply`。这是入口与环境烟测，50 步高斯模型不能用于评价视觉质量，也不能证明整房间几何正确。
