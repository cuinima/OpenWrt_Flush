# OpenWrt_flash

两台家用 OpenWrt 路由器的刷机、机场（代理）配置与运维脚本仓库。

> ⚠️ 本仓库**不含**任何固件二进制、sing-box 二进制、订阅解码结果等大文件/敏感文件，
> 均已通过 `.gitignore` 排除。脚本中出现的订阅 token、密码仅为个人环境的示例值。

## 设备概览

| 目录 | 设备 | 系统 | 用途 |
|------|------|------|------|
| [`openclash/`](openclash/) | NOKIA EA0326GMP | ImmortalWrt 21.02（MT7981） | 主路由，跑 OpenClash（mihomo 内核）代理 |
| [`ax6/`](ax6/) | Redmi AX6 | ImmortalWrt 23.05.4（IPQ807x） | 跑 HomeProxy（sing-box 内核）代理 |

---

## 📁 目录结构

```
OpenWrt_flash/
├── openclash/            # OpenClash 路由器（NOKIA EA0326GMP）相关
│   ├── OpenClash更新与修复步骤.md   # 完整运维/修复文档（含订阅、OOM 修复等）
│   ├── ssh_helper_oc.py             # SSH 助手（192.168.100.1）
│   ├── diag_oc_mem*.py              # 内存诊断脚本（OOM 排查用）
│   ├── fix_oc_mem*.py               # OOM 修复脚本（禁用服务/保护进程）
│   ├── probe_oc_*.py                # 启动机制探查脚本
│   ├── verify_oc_fix.py             # 修复验证脚本
│   ├── openclash_watchdog.sh        # 修改后的 watchdog（含 oom 保护）
│   └── sub_clash.yaml               # Clash 订阅样例
│
├── ax6/                   # Redmi AX6（HomeProxy + sing-box）相关
│   ├── Redmi-AX6-刷机与机场配置.md   # 刷机 + HomeProxy 配置完整流程
│   ├── ssh_helper.py                 # SSH 助手（192.168.123.1）
│   ├── deploy_homeproxy.py           # 部署 HomeProxy 上游文件
│   ├── download_upstream.py          # 下载 HomeProxy 上游源码
│   ├── sftp_upload.py                # 上传 sing-box 二进制
│   ├── check_anytls_node.py          # anytls 节点检查
│   ├── test_anytls_generate.py       # anytls 出站生成验证
│   ├── test_digest.py                # ucode digest 函数测试
│   ├── hp_deploy/                    # HomeProxy 部署文件（scripts/ + view/）
│   ├── hp_makefile.txt               # HomeProxy 包 Makefile
│   ├── profiles.json                 # 设备 profile 信息
│   ├── upstream_*.{uc,js}            # HomeProxy 上游源文件
│   └── sub_*.{json,yaml,txt}         # 订阅解析样例（敏感 b64 已忽略）
│
├── .gitignore
└── README.md
```

---

## 🚀 快速开始

### OpenClash 路由器（NOKIA EA0326GMP，`192.168.100.1`）

```bash
# 通过 SSH 执行任意命令
python openclash/ssh_helper_oc.py "free -m"

# 修复 OOM 崩溃（详见文档第八节）
python openclash/fix_oc_mem1.py   # 禁用 netdata/haproxy 释放内存
python openclash/fix_oc_mem3.py   # 给 clash 进程设 oom_score_adj 保护

# 验证修复
python openclash/verify_oc_fix.py
```

### Redmi AX6（`192.168.123.1`）

```bash
# 通过 SSH 执行任意命令
python ax6/ssh_helper.py "uci show homeproxy | head"

# 部署 HomeProxy（需本地已准备 sing-box 二进制）
python ax6/deploy_homeproxy.py

# 上传 sing-box 二进制
python ax6/sftp_upload.py
```

> 依赖：Python 3 + `paramiko`（`pip install paramiko`）。

---

## 📖 详细文档

- **OpenClash**：见 [`openclash/OpenClash更新与修复步骤.md`](openclash/OpenClash更新与修复步骤.md)，涵盖：
  1. 环境信息、机场订阅（User-Agent 坑）
  2. 完整操作步骤、常见坑
  3. 系统清理瘦身
  4. 自动选择组限定港新节点
  5. **OOM 崩溃重启修复**（第八节）
- **Redmi AX6**：见 [`ax6/Redmi-AX6-刷机与机场配置.md`](ax6/Redmi-AX6-刷机与机场配置.md)，涵盖：
  1. 刷机、改管理 IP、WAN/无线配置
  2. HomeProxy + sing-box 安装
  3. 机场订阅（UA 设置 + anytls 支持升级）

---

## ⚠️ 安全提示

- 脚本中的 `token`、`password` 均为**个人环境示例值**，若需对外公开请替换。
- `sub_*.b64`、`sub_real.txt` 等订阅解码结果已被 `.gitignore` 排除，避免泄露节点信息。
- 大固件（`.ubi`/`.bin`）、sing-box 二进制、`*.tar.gz` 均不纳入版本库，按文档从官方渠道重新下载即可。
