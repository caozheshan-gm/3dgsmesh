# 从视频/高斯得到 Mesh：技术路线与本轮选择

2026-10-18，依据官方项目与 KIRI 公开说明。

## KIRI 公开到什么程度

KIRI 官方称与 Chongjie Ye 团队合作，链接 GauStudio 开源库，并提到反射处理、法线预测及将几何目标结合到高斯优化中。商业版当前完整网络、训练配置、清理与纹理流程没有在这些页面完整披露。因此不能把 GauStudio 默认脚本叫作“KIRI 3.0 源码”，也不能承诺复现同等效果。

- https://www.kiriengine.app/blog/what-is-3dgs-to-mesh
- https://www.kiriengine.app/features/mesh-inclusive-3dgs
- https://github.com/GAP-LAB-CUHK-SZ/gaustudio

## 路线

| 路线 | 原理 | 已有普通 3DGS PLY 是否足够 | 主要限制 |
|---|---|---|---|
| GauStudio 网格提取 | 高斯渲染中位深度，不透明度筛选，VDB/TSDF 融合；另做纹理 | 还需要相机；可复用标准高斯 | 普通高斯深度仍可能漂浮，开源默认不等于商业流程 |
| SuGaR | 优化高斯贴近表面，提取/精炼 Mesh | 需原模型、图像和相机，并继续优化 | 结果依赖初始化、几何正则和后处理 |
| 2DGS | 扁平圆盘高斯、深度/法线正则，深度融合 | 需用照片和相机重训 | 错误深度和遮挡会污染融合；上一轮已测 |
| PGSR | 平面高斯、单/多视图几何一致性，深度过滤后融合 | 需照片与相机重训 | 薄结构、遮挡、邻帧设置仍需验证 |
| GOF | 几何正则的高斯不透明度场，Marching Tetrahedra 等值面 | 官方流程需专门训练 | 需额外四面体构建，计算/内存开销须实测 |
| GS2Mesh | 从高斯渲染立体视图，预训练立体匹配模型估深度，再融合 | 需模型与相机及立体网络 | 额外模型权重与兼容性；不保证任意薄杆恢复 |
| GSDF 等高斯 + SDF | 联合优化高斯与有符号距离场，提取等值面 | 通常要专门训练 | 配置与资源更复杂，效果依赖数据 |
| 摄影测量 MVS（独立基线） | 直接照片多视图深度与网格、投影纹理 | 不需要高斯 | 无纹理/反光/遮挡依然困难；并非所有 Mesh 都要经高斯 |

技术来源：
- https://github.com/Anttwo/SuGaR
- https://github.com/hbb1/2d-gaussian-splatting
- https://github.com/zju3dv/PGSR
- https://github.com/autonomousvision/gaussian-opacity-fields
- https://github.com/yanivw12/gs2mesh
- https://github.com/city-super/GSDF

## 本轮实验

先试 GauStudio：复用 BenchMelb 同输入已训练标准 3DGS 与相机，不把现有 2DGS 网格再平滑后冒充另一种重建算法。开源脚本使用中位深度、opacity>=0.5、每三帧一次、voxel=0.01、trunc=0.04、min_weight=5。先核对输出，再决定有依据的调整。对照包含原 2DGS 与 KIRI，采用统一灰模、相同视角，重点检查灯杆伪面、椅板空隙、地面完整度与覆盖范围。

环境 /data/envs/gaustudio 与既有环境隔离安装包，复用系统 torch/CUDA，不改旧结果。下载源码归档的 SHA256 用于追溯版本。实际运行参数、结果与任何代码修补另记。

### GauStudio 安装追溯

源码 master codeload 归档 SHA256：`b8775138dca2f8d0fcbb245c29b600bf16e3d372aa1787dc809557730ae75bea`。torch2.0.1+cu118 / Python3.9 / gcc11 / sm70。扩展名 gaustudio_diff_gaussian_rasterization，不覆盖旧 rasterizer。新增包 vdbfusion0.1.6、trimesh4.3.2、omegaconf2.3.0、einops0.8.1、pyexr0.5.0、OpenEXR3.5.2、cv2-headless4.8.1.78、skimage0.22.0。默认提取保持开源源码未修改；显式传入 cameras.json 修正 README 模型目录歧义。第一帧渲染已核对，图像正常。

### 多视角过滤对照参数

在默认网格后另建 gaustudio-filtered，保留相同93个相机、全分辨率、voxel0.01、trunc0.04、min_weight5，仅新增更严格的不透明度阈值0.8和多视角深度一致性。每个候选表面点从6个邻近/较宽基线视角投影比较深度，至少2票通过；阈值0.005 + 0.01×邻视角深度（均为场景单位）。这是本项目的实验过滤器，不声称为GauStudio官方或KIRI的算法。没有使用KIRI Mesh监督、手动删错面或平滑几何。滤除也可能带来孔洞/薄结构损失，要检查全部六视角。

默认GauStudio渲染的高阶SH读取存在通道排列疑点（颜色偏绿紫）；灰模及深度不受此影响。本次过滤仅渲染SH0深度，正式颜色展示另以原始照片和可见性测试投影，不用该偏色图作贴图效果排名。
