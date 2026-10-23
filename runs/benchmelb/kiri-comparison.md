# BenchMelb：KIRI 与自建流程对照

日期：2026-10-18。两方使用同一段 BenchMelb-KIRI.mp4。KIRI 的内部抽帧、相机求解和训练配置未知。本报告依据下载文件检查和实际渲染，不推断其私有算法。

## 结论

这次 KIRI 的 Mesh 明显优于当前自建 2DGS → TSDF 流程：灯杆、长椅和地面更完整，漂浮伪面更少。关闭贴图、使用相同灰色材质后差异仍然存在，所以不能仅归因于 4K 贴图或 PBR。我们的完整 1975 万面网格也存在灯杆大片伪面，不能归因于预览减面。

默认 KIRI Mesh 与高级导出在本次六个视角中没有显著的观感差距；这不代表两者在所有用途上等价。高斯结果都能较好表现长椅，KIRI 部分背景更清晰，且点数与文件大小约为我们的三分之一；不能据此给出普遍的画质排名。

## 用户截图中的导出设置

- Generate Quad Mesh：开启；Target Quad Count 50%；Target Curve Ratio 50%。
- Include PBR Materials：开启。
- 格式 OBJ，纹理 4K。
- Generate Rig：开启。

仅记录相关技术设置，不保存截图中的收件信息。

## 实际文件

| 结果 | 顶点 | 面 | 颜色方式 |
|---|---:|---:|---|
| KIRI 默认 3DModel.obj | 993,921 | 1,985,972 三角面 | UV + 4096×4096 JPG |
| KIRI AdvancedExport/3DModel_Custom.obj | 845,669 | 1,681,485 三角面 | UV + 4096×4096 JPG；另附 PBR 图 |
| 自建完整 Mesh | 10,312,986 | 19,752,211 三角面 | 顶点 RGB，无 UV 贴图 |
| 自建预览 Mesh | 513,835 | 999,999 三角面 | 顶点 RGB，无 UV 贴图 |

两个 OBJ 中均未发现四边面；可能在导出阶段三角化，不能据此认定内部没有做重拓扑或开关失效。高级导出的三角面数约为默认的 84.7%，截图的 50% 不应直接理解为最终三角面数减半。

包内共有六张 4096×4096 JPG：默认颜色、高级颜色及 Basecolor、Normal、Roughness、Metallic。两个 MTL 仅通过 map_Kd 引用主颜色图，没有连接额外 PBR 图。因此在软件中仅打开 OBJ 并不等于完整启用所有 PBR 材质。附带 Rig FBX 的绑定与动画未测试，不参与静态网格对比。

| 高斯文件 | 点数 | 文件大小 |
|---|---:|---:|
| KIRI kiribench.ply | 720,413 | 178,663,955 bytes |
| 自建 benchmelb-3dgs-30000.ply | 2,166,760 | 537,358,012 bytes |

两者都是 SH3 高斯 PLY，62 个 float32 属性。KIRI 包含约 50,000 个外层球形分布点；点数不代表所有点对当前画面有相同贡献。

## 比较方法与限制

KIRI OBJ 与自建场景先对齐地面，再估计偏航、平移与统一缩放。采用六个自建 COLMAP 相机视角，输出彩色与灰模。灰模统一材质和灯光，不使用 PBR 法线图。完整网格以足够的 raster bin 容量重渲，最终无溢出警告。

KIRI 高斯的 Y/Z 方向与其 OBJ 相反；渲染时据此变换相机，避免直接旋转 SH 系数。配准为近似对齐，并非 KIRI 原始相机位姿；不做双方 PSNR 或实测尺寸精度排名。拟合残差是任意场景单位，不能当作厘米。

自建展示高斯与 Mesh 训练分支共用图像和相机；Mesh 来自独立 2DGS 训练与 TSDF 融合，不是把展示用 3DGS PLY 直接转换成网格。本次结果说明当前表面重建流程仍需改进，不证明 2DGS 的效果上限，也不能反推出 KIRI 使用的具体方法。

## 对照图

- [关键视角：上排颜色、下排灰模，左 KIRI、右自建完整 Mesh](../../artifacts/benchmelb-kiri/comparison/mesh-key-comparison.jpg)
- [六视角彩色：输入 / KIRI 默认 / KIRI 高级 / 自建预览 / 自建完整](../../artifacts/benchmelb-kiri/comparison/mesh-comparison-color.jpg)
- [六视角灰模，同上列顺序](../../artifacts/benchmelb-kiri/comparison/mesh-comparison-gray.jpg)
- [六视角高斯：输入 / 自建 / KIRI](../../artifacts/benchmelb-kiri/comparison/gaussian-comparison.jpg)

详细计数见 kiri-mesh-statistics.json，设置见 kiri-export-settings.json。输入提取保存在 artifacts/benchmelb-kiri/，服务器 /data/projects/benchmelb-20261018/kiri-input/。

## 输入校验 SHA256

- KIRI kiribench.ply：8cd115e7c9bff4328d587febe35491aaafd9902ce49342a6307d8028c7dc8f5e
- KIRI ZIP：4de506f385da70c02a6778052baa603c76cca518f87e986211438f95959f8fb4
