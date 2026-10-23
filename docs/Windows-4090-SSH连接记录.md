# Windows 本地训练机 SSH 连接记录

2026-10-23 实际连接验证通过。

- 系统：Windows 10（用户提供）。
- 主机：DESKTOP-QC218N8；登录账户：desktop-qc218n8\admin。
- Tailscale IP：100.78.124.120。
- Mac SSH 别名：`win4090`，使用 `ssh win4090`。
- Mac 专用密钥位置：`~/.ssh/id_ed25519_win4090`；私钥不放仓库。
- Windows 公钥授权文件：`C:\ProgramData\ssh\administrators_authorized_keys`，用户已添加公钥并设置 Administrators/SYSTEM ACL。
- 主机 ED25519 指纹：`SHA256:Jk+biIC/zjcOGbpuVLVaeBjKXGKJhKLqAGAeQeC6R/Q`；通过用户本机读取的公钥与远端扫描结果比对，已加入 Mac known_hosts。
- 密钥登录 `whoami`、`hostname`、`nvidia-smi` 和 SSH 别名登录均成功。
- 实际 GPU：**NVIDIA GeForce RTX 4090 Laptop GPU**，16376 MiB（约16GB显存），驱动617.42。不是24GB显存的桌面 RTX4090，后续模型训练需要按16GB显存规划。
- 当前仅配置并验证 SSH，未安装重建环境或启动训练。
- sshd 已设为自动启动（用户执行）。防火墙来源限制按用户要求暂不设置；没有添加路由器公网端口映射。
- 异地访问依赖 Mac/Windows 的 Tailscale 在线和访问策略允许，Windows需开机且不睡眠；Windows无需选择 Mullvad 出口。
