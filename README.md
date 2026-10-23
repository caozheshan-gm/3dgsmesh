# 3dgsmesh

视频 / 照片 → 相机求解 → 3D Gaussian Splatting → Mesh 的实验工作区。后续训练以 **Windows 原生环境**为主，Mac 用于整理素材、SSH 管理和查看结果。

## 当前环境

- [Windows 原生 3DGS 环境](docs/Windows原生3DGS环境.md)：已安装的版本、路径和 GPU 烟测结果。
- [Windows 4090 SSH 连接](docs/Windows-4090-SSH连接记录.md)：Tailscale 与远程连接记录。
- [Windows 脚本](scripts/windows/)：环境激活、依赖安装、扩展编译与 50 步烟测。正式训练脚本和新实验从这里继续编写。
- [历史技术与云服务器记录](docs/技术栈与服务器安装记录.md)：此前的云端试验；腾讯云 GPU 实例目前关机。

myroom 和 BenchMelb 的历史实验报告、参数与结果统计已移到本机 `/Users/czss/Documents/3dgsmesh-archive-2026-10-23/runs/`。过去的 Linux 单次实验脚本已从当前工作树移除，需要时可从 Git 历史恢复。

历史高斯、网格和截图原本位于 Git 忽略的 `artifacts/`。为让仓库保持精简，这批结果已移到同一归档目录的 `artifacts/`；旧报告中的相对链接需以该归档目录为根打开。迁移到 Windows 时按需复制具体成果，不必同步整份归档。临时安装中转文件及重复压缩副本已经删除。

训练生成的数据、模型和安装包请放在 Git 忽略的 `artifacts/`、`data/`、`outputs/` 或仓库外的项目目录；只把脚本、配置和必要的实验记录提交到 Git。
