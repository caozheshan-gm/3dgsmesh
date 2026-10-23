# myroom 首次运行

- 日期：2026-10-17
- 输入：`/Users/czss/Desktop/myroom.mov`
- 本地成果：`artifacts/myroom-20261017/`（Git 忽略）
- 服务器项目：`/data/projects/myroom-20261017/`
- 视频：121.7017秒，4K HEVC，约30fps，HLG HDR，竖屏。
- 抽帧：2fps，长边1600，JPEG q=2，HLG→线性→Mobius色调映射→BT.709 SDR。
- COLMAP：单OPENCV相机、SIFT CPU 8线程、最多8192特征、顺序匹配overlap20及quadratic overlap。
- 状态：服务器训练、网格和贴图导出完成；本地下载校验见下方记录。

执行脚本位于仓库 `scripts/myroom-prepare.sh`、`scripts/myroom-sfm.sh`。

原片保留，本地 input 已同步为服务器实际使用的 SDR 照片。

## 阶段结果

- 顺序匹配：27/243张；全局匹配：48/243张（选用）；小基线4°尝试：48、19、21张三个分离模型。
- 基础3DGS：7000步，约4分30秒，测试PSNR27.529dB。PLY约92MiB，已下载到`artifacts/myroom-20261017/gaussian/myroom-vanilla-7000.ply`。
- 测试视角图片：`artifacts/myroom-20261017/preview/test/renders/`，对应输入图片在`gt/`。
- 有效内容主要为沙发/桌子局部，边缘存在拉伸、模糊；不是完整房间重建。
- SuGaR 的表面优化、网格提取、2000步细化和贴图导出均已完成。
- 修复：SuGaR检查点路径要求末尾`/`，已修正并从该阶段恢复。

## 最终成果

| 成果 | 路径（项目根目录下） | 实际信息 |
| --- | --- | --- |
| 基础高斯 | `artifacts/myroom-20261017/gaussian/myroom-vanilla-7000.ply` | 388313个高斯，96303155字节 |
| 网格绑定高斯 | `artifacts/myroom-20261017/gaussian/refined/` | 2134482个高斯，529353068字节 |
| 带贴图网格 | `artifacts/myroom-20261017/mesh/` | OBJ+MTL+PNG，193439顶点，355747三角面，3376×3376贴图 |
| 高斯测试渲染 | `artifacts/myroom-20261017/preview/test/renders/` | 6张未参与训练视角 |
| 原片/高斯对比 | `artifacts/myroom-20261017/preview/source-vs-gaussian.jpg` | 左：输入照片；右：基础高斯渲染 |
| 网格测试渲染 | `artifacts/myroom-20261017/preview/mesh/` | 2个测试视角 |
| 运行日志 | `artifacts/myroom-20261017/logs/` | 包含中途路径错误与成功恢复记录 |

大文件已由`.gitignore`忽略。原始训练检查点、COLMAP数据库仍保留在服务器，未全部下载。

验证详情在本目录`artifact-validation.json`；服务器成果SHA256清单在`deliverables-sha256.json`。

## 质量结论

第一条真实素材工作流已成功生成高斯和带贴图网格，但仅重建到局部。

- 有效照片仅48/243；单个有效模型覆盖沙发、桌子附近及部分床/墙面。
- 高斯测试渲染有模糊和边缘拉伸；相机视角附近看起来较好，不代表任意位置都完整。
- Mesh渲染可辨识沙发/桌子，但天花板、床沿和沙发局部有破洞、缺面及粗糙表面。
- Poisson阶段出现无效数据警告；最终网格可读取、顶点坐标有限、UV/贴图可加载，仍不代表几何精确。
- 尚未实测比例校准、清理或导入Blender；不能用于尺寸或施工判断。

建议下一次只拍沙发+桌子的一个角落，缓慢移动形成平移视差，减少只拍白墙/天花板的片段，优先解决模糊和覆盖问题，再提升训练质量。

本地下载完成：5个核心成果文件与服务器SHA256逐个一致，见`local-verification.json`。服务器GPU任务已结束，主机未停机，仍可能持续计费。
