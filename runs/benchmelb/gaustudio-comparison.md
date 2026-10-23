# BenchMelb 换方法试验：GauStudio 与多视角深度过滤

2026-10-18。目标：同一段视频，检验替换网格重建方法能否改善此前 2DGS → TSDF 的问题，与 KIRI 同输入结果比较。

## 结论

**局部改善，但本轮没有达到 KIRI Mesh 的整体质量。** GauStudio 默认提取及本项目多视角过滤版均消除了原 2DGS 在灯杆旁的大片伪面；然而地面仍粗糙、部分椅板缝被填住，椅背/背景仍有噪声。六视角灰模显示，KIRI 的表面整体更干净。过滤降低了网格量，但不能把面数下降解释为精度提升，更没有测得双方真实几何误差。

这说明换提取器有用，也提示普通展示型高斯的深度质量限制了后处理。下一轮有依据的方向是 PGSR 等带多视图几何约束的专门训练，或 GS2Mesh 的立体匹配深度路线；这是依据本次图像表现的实验建议，不是“这些方法必然优于 KIRI”的保证。

## 输入与对照条件

- 同一视频 BenchMelb-KIRI.mp4，55.35 秒，无新拍摄。
- 复用此前 277 张照片、COLMAP 相机和已训练的标准 3DGS；不重新求相机或训练高斯。
- GauStudio 使用 `models/3dgs/cameras.json` 中每三帧选一，共 93 个相机；分辨率 1416×792。
- 新版 Mesh 与原模型保留在相同 COLMAP 坐标系，无额外几何配准；KIRI 使用上一轮已经目视检查的近似相似变换。
- 六个相同相机输出灰模，统一材质和灯光，不启用贴图、PBR 法线图。KIRI 的抽帧/训练细节仍未知，不属于严格单变量端到端算法评测。
- 没有使用 KIRI 的几何来训练或监督自建网格，没有手动删伪面、裁剪、平滑后冒充重建改善。

## 实跑方法

| 版本 | 方法 | 顶点 | 三角面 |
|---|---|---:|---:|
| 旧方案 | 专门训练 2DGS，深度 TSDF 融合 | 10,312,986 | 19,752,211 |
| GauStudio 默认 | 已有标准 3DGS 中位深度，不透明度过滤，VDB 融合 | 7,442,194 | 12,106,525 |
| GauStudio + 本项目过滤 | 同样深度，新增多视角一致性，再 VDB 融合 | 4,715,765 | 7,730,654 |
| KIRI 默认 | 商业流程，公开细节不完整 | 993,921 | 1,985,972 |

默认参数：opacity>=0.5，voxel_size=0.01，sdf_trunc=0.04，space_carving=False，min_weight=5，未启用 --clean。保留完整原始网格。

过滤版保留相同 93 相机、分辨率、voxel/trunc/min_weight，新增 opacity>=0.8；每个候选点在六个附近/较宽基线视角中至少得到两票深度支持。误差阈值 0.005 + 0.01×邻视角深度，单位是未标定尺度的场景单位。过滤版约 153 秒完成，包括缓存深度与融合，不含首次环境安装、预览减面和颜色。该过滤器为本项目实验代码，不是声称复现官方 GauStudio 或 KIRI 的额外处理。

过滤可能制造孔洞或损失细结构；不能把所有被移除区域都称为错误。它不是完整消除背景噪声的解决方案。

## 颜色与便携导出

完整网格的结论以灰模为准。默认 GauStudio 高阶 SH 读入排列存在颜色问题，因此不使用其彩色渲染来评价材质。另为查看创建独立 200 万面以内预览，以均匀选取的25个原始训练视角、800像素宽照片做可见性检查和颜色投影，输出顶点色 GLB；未使用 KIRI 贴图。约77.4%预览顶点得到直接可见照片颜色，其余以最近已着色顶点补色，不能视为未拍到表面的真实恢复。该颜色流程没有等价于 KIRI 的 4K UV/PBR，细节差异应分开判断。

预览减面只用于打开/展示，完整灰模对照均使用减面前几何。未裁剪、未平滑。近似对齐不用于双方 PSNR 或实测尺寸精度排名。

## 图像与模型

- [默认提取六视角灰模](../../artifacts/benchmelb-mesh-methods/gaustudio-default-comparison-gray.jpg)
- [过滤版六视角灰模](../../artifacts/benchmelb-mesh-methods/gaustudio-filtered-comparison-gray.jpg)
- [关键视角灰模对比](../../artifacts/benchmelb-mesh-methods/mesh-method-key-gray.jpg)

- [完整过滤网格 PLY（无贴图）](../../artifacts/benchmelb-mesh-methods/delivery/benchmelb-gaustudio-filtered-full.ply)
- [照片着色预览 GLB（约200万面，45.5MB）](../../artifacts/benchmelb-mesh-methods/delivery/benchmelb-gaustudio-filtered-preview.glb)
- [预览版彩色对照](../../artifacts/benchmelb-mesh-methods/gaustudio-filtered-preview-comparison-color.jpg)
- [预览版灰模对照](../../artifacts/benchmelb-mesh-methods/gaustudio-filtered-preview-comparison-gray.jpg)

完整 PLY SHA256：d2c14811afffedffa6e9a0e7b0b7c3accfac521197d5ff231236f52988edf298。
预览 GLB SHA256：72d54499f4286e7b55da8240ca331adf4ad0b45b116c9be76c0f815c84c766a4。
GLB 已检查文件头、COLOR_0 和位置数量、重新载入面数与顶点有限值；1345289顶点、1999999面、45525884bytes。

## 复现与环境

- `/data/apps/gaustudio-src`，`/data/envs/gaustudio`；V100 sm70，Python3.9，torch2.0.1+cu118，gcc11。
- 官方源码归档 SHA256：b8775138dca2f8d0fcbb245c29b600bf16e3d372aa1787dc809557730ae75bea。
- 包版本见 gaustudio-env-freeze.txt；实际统计见 gaustudio-default-stats.json、gaustudio-filtered-stats.json、gaustudio-filtered-run.json。
- 脚本见 `scripts/benchmelb-gaustudio-run.sh`、`scripts/benchmelb-gaustudio-filtered.py`、`scripts/benchmelb-render-mesh-method.py`、`scripts/benchmelb-mesh-preview.py`。
- 服务器输出目录：`/data/projects/benchmelb-20261018/gaustudio-default/`、`gaustudio-filtered/`、`mesh-method-comparison/`。
- 各方法技术与来源见 [mesh-methods.md](mesh-methods.md)。
