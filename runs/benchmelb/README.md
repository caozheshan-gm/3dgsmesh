# BenchMelb 公共样本

来源：[AWS重建工具文档](https://aws-solutions-library-samples.github.io/compute/open-source-3d-reconstruction-toolbox-for-gaussian-splats-on-aws.html)；仓库assets/input/BenchMelb.mov。

2026-10-18下载到Mac桌面。原文件93091034字节，H.264，1434×802，55.349257秒，约59.784fps。已查看每10秒采样画面，为真实长椅环绕拍摄。只验证输入可用，尚未验证完整相机求解或Mesh质量。

原文件：/Users/czss/Desktop/BenchMelb.mov
上传文件：/Users/czss/Desktop/BenchMelb-KIRI.mp4

用FFmpeg视频流复制转MP4容器，没有缩放/加速/重新编码；完整解码检查通过。两边应统一使用此MP4，KIRI开启3DGS to Mesh，并记录是否启用自动遮罩。

MP4 SHA256：d271b4547a1c7d84a2dd57bc42c7955c17b6c8f0034bf9c068e80e371e659f5a
尚未上传KIRI或启动服务器训练。

## 服务器重建运行

2026-10-18用户授权服务器重建。服务器目录`/data/projects/benchmelb-20261018`。上传SHA256与桌面MP4一致。

- 10fps候选帧，每两帧选择拉普拉斯方差更高的一张，277张，无遮罩。
- COLMAP3.7 CPU SIFT，SIMPLE_RADIAL共享相机，顺序20邻帧+跨间隔对应。
- 相机检查通过后，3DGS和2DGS分别30000步，共用相机/照片，eval每8张保留一张。
- 2DGS官方源码提交`f3e3b9fa67bbd1c75e05167ff37391d8dab2a678`；surfel子模块`e0ed0207b3e0669960cfad70852200a4a5847f61`。服务器GitHub直连慢，改Mac下载源码压缩包后上传；GLM复用已有3DGS头文件，simple-knn复用已有编译模块。
- 环境`/data/envs/2dgs`通过venv复用原sugar环境依赖，但新增包单独安装；surfel CUDA算子sm70编译。
- 2DGS表面参数lambda_dist=100、lambda_normal=.05、depth_ratio=1；有界TSDF mesh_res1024，保留原始与连通块过滤版本。
- PLY/GLB Mesh计划使用顶点颜色；不应把它称为带UV贴图的网格。

运行脚本见`scripts/benchmelb-prepare.sh`、`scripts/benchmelb-train.sh`、`scripts/benchmelb-deliver.py`。

SIFT特征提取已完成；CPU顺序匹配首位置约37.4秒，因预计耗时较长主动停止该实验，保留distorted数据库。改用已验证的SuperPoint2048+LightGlue GPU前端、COLMAP几何验证和增量求解；新数据库位于lightglue/，不覆盖SIFT缓存。

## 相机检查通过

277/277注册，44330点、466293观测，平均重投影误差1.329792px。最终SIMPLE_RADIAL焦距1061.872829px，主点717/401，径向k=.0193632；不是实测标定。轨迹三轴投影呈连续两圈不同高度的环绕，没有原房间实验的大幅跳变。相邻速度按轨迹稳健跨度归一化，q50=.1097、q99=.1735、max=.2004每秒，未出现孤立尖峰。只是通过当前视觉/一致性检查，不是测绘精度认证。

已创建服务器APPROVED_FOR_TRAINING，启动3DGS→2DGS→Mesh顺序任务。

审查脚本泛化时变量project与投影函数同名导致接触表输出TypeError；已改为project_root并重新运行成功，数值报告/点云不受影响。

3DGS7000步中间检查：测试PSNR25.093669dB、训练25.410795dB。35个测试视角渲染完成，6视角接触表显示长椅正/背/侧面连接合理，周边地面及远处仍有模糊；继续30000步训练。此指标无KIRI对应评估，不能直接排名。

3DGS30000步已完成，训练进度计时33分21秒（另有评估/保存/渲染开销），测试PSNR27.9173165dB。PLY SHA256：daac5000b618aac59d7cd90400185ad8e2a5464d2f6f332e36ac5a7e1b15adc1。开始2DGS实际训练，文件下载与训练并行。

2DGS7000步测试24.60012dB。用该快照做512分辨率有界TSDF中间验证：原网格1980779顶点，清理后1771406顶点；实际导出、GLB与PyTorch3D同相机渲染全部成功。预览显示长椅主体成形，灯杆近处存在伪面、地面边缘破碎，远处背景因有界深度范围缺失；这些不是已解决的问题。最终仍用30000步与1024分辨率，后续需重新检查，不把早期结果当最终成果。中间结果单独存intermediate-7000。

最终3DGS：2166760高斯，512.5MiB，已下载并SHA256核对一致。

最终2DGS30000步：1017811个表面高斯，训练进度计时35:23，测试PSNR26.649112dB。最终1024 TSDF生成原始12491976顶点、清理后10312986顶点。GLB检查遇到Trimesh将带材质顶点色网格读为TextureVisuals，不能用visual.vertex_colors；已核对GLB原始POSITION/COLOR_0 accessor计数与文件长度并修复检查逻辑，重启交付阶段。模型训练和TSDF无需重做。

## 最终交付（已完成）

- 高斯：gaussian/benchmelb-3dgs-30000.ply，标准3DGS，2166760个高斯，约512.5MiB；可导入支持3DGS的查看器或插件。
- 网格轻量版：mesh/benchmelb-mesh-preview.glb，513835顶点、999999三角面，约19.3MiB，适合先在网页查看或Blender导入。
- 完整网格：mesh/benchmelb-mesh.glb，10312986顶点、19752211三角面，约383.4MiB，保留完整细节，查看和编辑负担较大。
- 对照图：preview/input-3dgs-mesh.jpg，左原照片、中3DGS、右轻量网格；六个相同的测试相机，网格预览用了减面版。
- preview/mesh-gray-*.png：灰模几何检查；mesh-*.png为顶点色预览。

## 实际效果与限制

长椅主体较完整；Mesh灯杆近处仍有大片伪面，地面边缘破碎。有界TSDF没有恢复远处全部街景，图中的黑色代表没有提取网格的区域。高斯换视角仍可能存在模糊/漂浮物。没有测绘真值，不据此宣称尺寸准确。

网格由独立2DGS分支提取，和3DGS共用照片/相机，不是把展示用3DGS PLY直接转换。Mesh采用顶点颜色，没有UV纹理/PBR材质分解；GLB采用unlit材质保留扫描光照。

3DGS与2DGS均30000步，测试PSNR分别27.9173dB、26.6491dB，只能作为本次分支内部指标，不能与没有对应相机/测试集的KIRI直接排名。训练进度计时分别33分21秒、35分23秒，不包括SfM、安装、评估、导出、减面和传输。

原始及连通块清理后的PLY保留在服务器 /data/projects/benchmelb-20261018/models/2dgs/train/ours_30000/。这里只下载标准高斯、完整GLB与轻量GLB，三文件SHA256已逐个核对。

2026-10-18发现下载目录kiribench.ply：720413个高斯，约170.4MiB；没有发现这次KIRI网格ZIP。点数/大小不能证明质量优劣，双方效果对比尚未完成。

完整参数、版本、异常与复现脚本记录见仓库 runs/benchmelb/README.md。

交付完整性错误修正后，真实完整GLB重读、面数、坐标有限性、颜色accessor与文件长度验证通过。轻量化约100万面，最终同视角渲染与灰模预览完成；本地三主要文件SHA256与服务器一致，见delivered-files.json。

## KIRI 同输入比较已完成

见 [详细对照报告](kiri-comparison.md)。KIRI 默认和高级 OBJ、PBR、点数已检查；六视角彩色/灰模及高斯对照已保存。当前 KIRI Mesh 明显更干净，自建完整 Mesh 的伪面与地面噪声不能归因于预览减面。

## GauStudio 换方法试验完成

见 [实际结果与文件](gaustudio-comparison.md) 和 [技术路线与官方来源](mesh-methods.md)。默认提取与多视角过滤均已运行，灯杆伪面改善，但整体仍不及KIRI；完整灰模和着色GLB分别保存。
