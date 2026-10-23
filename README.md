# 3dgsmesh

Windows 原生图片 → COLMAP 相机求解 → 3D Gaussian Splatting 训练工作区。当前电脑的官方 3DGS 源码已单独安装在 `D:\3dgs\apps\gaussian-src`，本仓库只保存调用脚本、说明和项目记录，不复制官方源码。

## 从图片开始

在本仓库根目录打开 PowerShell，第一次执行（`corner` 可换成英文项目名）：

```powershell
.\scripts\windows\run-project.cmd corner
```

脚本会创建 `data\corner\input\`。把 JPG/PNG 照片放进去，然后先做相机求解：

```powershell
.\scripts\windows\run-project.cmd corner -ConvertOnly
```

检查生成的 `data\corner\images\` 和 `data\corner\sparse\0\`，确认照片注册和相机轨迹合理，再训练高斯：

```powershell
.\scripts\windows\run-project.cmd corner -TrainOnly -Iterations 7000 -Resolution 2
```

结果在 `outputs\corner\point_cloud\iteration_7000\point_cloud.ply`。也可省略 `-ConvertOnly`、`-TrainOnly`，一次完成两步。`data/`、`outputs/` 被 Git 忽略，正式训练前请阅读[完整操作和注意事项](docs/Windows-image-to-3dgs.md)。

- [Windows 原生环境与已验证版本](docs/Windows原生3DGS环境.md)
- [Windows SSH 连接记录](docs/Windows-4090-SSH连接记录.md)
- [历史技术和云服务器记录](docs/技术栈与服务器安装记录.md)

`runs/` 是之前的实验记录；`scripts/windows/` 包含环境、转换、训练和烟测脚本。当前流程输出 **3DGS**，Mesh 是后续独立步骤。
