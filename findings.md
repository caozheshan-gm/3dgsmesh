# myroom 发现记录

- 原视频 121.7017 秒，HEVC，3840×2160，约 30fps，旋转元数据 -90°，约 370MiB。
- 2026-10-17 连接 gs-train 成功，V100 空闲，/data 可用 173GiB。
- 保留原视频；抽帧自动按旋转元数据处理。
- 接触表显示整间房覆盖，包含较长低纹理白墙/天花板片段，存在相机求解失败或模型断裂风险；先测试，不预判成功。
- 首轮抽帧：2fps，长边1600，JPEG q=2。
- 顺序匹配模型仅注册27/243张，1537点，平均重投影误差0.741742px；不能作为整房结果。
- 进行第二轮全局exhaustive匹配，输出sparse-global，保留第一轮结果。
- 全局匹配：48/243张注册，2030点，重投影误差0.768148px。
- 检查默认初始化最小三角化角为16°；另试4°以诊断小位移拍摄，保留原结果。
- 已查看基础3DGS测试渲染：沙发、笔记本、桌子可辨识，存在边缘拉伸和模糊；为局部有效结果，不能称完整房间。

## KIRI 同素材对比
- 用户确认下载/3DGS.ply来自同一段myroom.mov。
- KIRI: 300402高斯，74501227字节，62个float属性，SH3；其中50000个点精确位于半径50球面，疑似背景层，不能当房间表面。
- 自建基础:388313高斯，96303155字节；SuGaR refined:2134482高斯，529353068字节。
- SuperSplat实际查看KIRI：沙发/桌子外，还可见门和柜子方向；存在明显模糊与拉伸。不能从文件推断KIRI实际相机注册率、算法、训练次数。
- 同素材KIRI覆盖更广，先前把缺失主要归因素材的判断不充分，流程差异需进一步定位。

## 相机求解优化第二轮
- 固定原243照片与匹配，OPENCV→PINHOLE，最大模型仍48张（2021点，平均误差0.825473px）。单独简化相机模型未改善覆盖。
- 新实验：12fps候选长边2000，按0.25秒窗口选最清晰候选，约487张；PINHOLE、最多16384 SIFT特征、guided sequential匹配、4°初始化。
- 目标：相机覆盖与结构通过才启动训练，当前未启动高斯/Mesh。
- 学习式增量模型：471/487，61162点，平均误差1.380677px；焦距约1645/1690。覆盖高，但相邻近似画面出现位置跳变，未放行训练。
- pycolmap4.2.1全局SfM：484/487，28541点，平均误差2.169690px；焦距约1636.94/1636.24。相机轨迹异常比增量更大，亦未放行。
- 当前对照：现代增量求解，固定由全局估计得到的方形像素焦距约1636.59（不是实测标定），重新校准照片对、使用默认16°强基线初始化。
- 相机求解用独立系统Python3.10环境/data/envs/colmap-modern（numpy2.2.6、pycolmap4.2.1），与训练Python3.9环境分开。

## BenchMelb 重建准备

- 原MP4 SHA256已在Mac/服务器核对一致，277张清晰选帧保留全段。
- 旧COLMAP3.7 CPU SIFT匹配耗时大，保留缓存后改已安装的SuperPoint/LightGlue；7130候选对，6562对至少16个对应。
- COLMAP几何验证完成，耗时7.317分钟；增量相机求解运行中，当前约98张注册。
- 2DGS官方实现已在独立venv安装，CUDA扩展sm70编译通过；复用torch2.0.1+cu118/open3d0.17。计划Mesh为顶点颜色PLY/GLB，与KIRI的UV纹理表现需分别评价。

## BenchMelb KIRI 比较结论（2026-10-18）

KIRI 约199万/168万三角面 OBJ 的几何明显优于自建1975万面完整2DGS/TSDF网格，灰模确认并非贴图带来的全部优势。两个OBJ没有四边面；PBR图齐全但MTL仅连颜色图；Rig未验证。KIRI GS72万点、自建217万点，长椅均可辨，禁止用近似对齐视角做精确PSNR排名。详见 runs/benchmelb/kiri-comparison.md。

## 新 Mesh 方法调查（2026-10-18）

KIRI 官方 https://www.kiriengine.app/blog/what-is-3dgs-to-mesh 确认与 Chongjie Ye 团队合作，明确链接 GAP-LAB-CUHK-SZ/gaustudio；描述反射处理、法线预测和训练中结合几何。不能把 GauStudio 默认开源脚本等同于商业 3.0 完整流程。GOF 官方采用几何正则与 Marching Tetrahedra；PGSR 官方采用平面高斯和多视图几何，并支持提取时深度过滤。后续据代码与兼容性选实跑方法。

GauStudio 默认网格六视角灰模已生成，12106525三角面。目视 pole 视角14：原2DGS灯杆大片伪面不再存在；地面仍噪，部分椅板缝被填平。说明不同提取方法确有改进，但不是复现KIRI。下一项有依据实验：保留默认输出，另渲染缓存中位深度，对附近视角做深度一致性验证，再用相同体素尺度融合，核对噪声与细结构损失。

过滤版最终灰模六视角检查：地面仍粗糙、椅背有浮动/波纹、缝隙不完整，未达到KIRI整体质量；主要改进仍是原灯杆大片伪面消失。默认/过滤均保留完整几何。完整过滤PLY取回Mac，SHA256本地/服务器一致：d2c14811afffedffa6e9a0e7b0b7c3accfac521197d5ff231236f52988edf298。不要以减少面数或贴色来宣称提高精度；下一轮真正改变训练可选PGSR，或GS2Mesh立体深度路线。

## 2026-10-18 再核对用户提供的视频

已完整读取桌面《I Was Wrong About Gaussian Splats — They Just Became Playable》字幕。视频为生态/可交互展示综述：扫描入口提 Scaniverse/KIRI/Polycam/Postshot/gsplat，KIRI 展示高质量Mesh但不教授私有训练/提取配置；ImageBlaster/World Labs 段是付费API生成世界，与真实现状扫描不同。PlayCanvas FPS 核心是高斯负责外观、碰撞Mesh负责物理，非把高斯替换成同画质纹理Mesh。官方原教程第一步直接下载已有优质扫描，并未提供从原始视频训练出最佳高斯的完整参数：https://blog.playcanvas.com/turning-a-gaussian-splat-into-a-videogame/ 。

重要更正：当前官方 splat-transform 的 --collision-mesh 确能生成 .collision.glb；不能再笼统说它“没有生成mesh功能”。其碰撞Mesh用于运行时碰撞，不能等同KIRI纹理展示Mesh。官方指南 https://developer.playcanvas.com/user-manual/splat-transform/collision/ 。对用户真实展示/加柜子/漫游，需把高斯视觉+代理几何路线与高质量独立Mesh路线清楚区分，避免默认必须先解出完美Mesh才能展示。

## 2026-10-18 B站18份3DGS教程字幕评估

目录 /Users/czss/Downloads/b站3dgs教学字幕，共18份（XR_1605，01—18）。重点阅读05采集、07空三、10/11工具对照、13碰撞、14/16LichtFeld、15室内、18LOD；旧环境/租服务器/UE章节作定向检索。重点价值是采集覆盖/视差/过渡图、先看相机再训练、多工具同数据对照、高斯外观+手工代理几何、后续LOD发布。13明确演示CloudCompare Poisson粗网格后在Blender重画地面墙体，不是精细自动Mesh算法。作者把COLMAP匹配失败全归因空三、单component视为保证成功等说法过强；EXIF焦距不自动恢复绝对尺度；轴/单位参数与插件有关。不能把30%重叠当建议采集目标，也不能直接将f11—16/f32照搬iPhone。10/11为作者主观默认参数评测，且点数/压缩/相机流程有差异，不能排绝对排名；14/16也说明旧版本结论已变化。

已查当前官方：LichtFeld README要求NVIDIA CC>=7.5、驱动570+、CUDA12.8+，Windows/Linux；现V100 CC7.0不在支持范围，不能直接装最新版本到现有服务器或Mac原生CUDA训练；4090是合适试验设备，尚未安装。源码免费、预编译Windows包付费；不沿用视频固定价格。Postshot官方现Free无PLY/SPZ导出，Indie含导出，不能把旧免费beta教程当当前条件。RealityScan官方免费有年收入门槛，且已列Linux支持，不复读“只Windows/完全免费”。Aholo官方确认chunk LOD及 @manycore/aholo-splat-transform，与 @playcanvas/splat-transform 名称近似但不是相同包；不保证字幕里的低配帧率或“比Spark快五倍”。
