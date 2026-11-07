# Redmi AX6 刷机 + 机场（HomeProxy）配置完整流程

> 适用设备：Redmi AX6（`board_name=redmi,ax6-stock`，双分区布局）
> 固件：ImmortalWrt 23.05.4（内核 5.15.167，架构 `aarch64_cortex-a53`）
> 目标：改管理 IP、配置 WAN 上网、开启 5G/2.4G 无线、安装可用机场插件
> 插件版本：sing-box **1.12.24** + HomeProxy（**已升级支持 anytls**）

---

## 一、环境信息速查

| 项目 | 值 |
|------|-----|
| 管理 IP | `192.168.123.1` |
| SSH 凭据 | 用户名 `root`，密码 `password` |
| SSH 登录 | `ssh -o StrictHostKeyChecking=no root@192.168.123.1` |
| WAN | DHCP，光猫已拨号（光猫网关 `192.168.1.1`） |
| 5G WiFi | `OpenWrt_5G` / 密码 `cccc1025`（psk2） |
| 2.4G WiFi | `OpenWrt_2.4G` / 密码 `cccc1025`（psk2） |
| 架构 | `aarch64_cortex-a53`，目标 `ipq807x/generic` |
| 内核 | 5.15.167 |

---

## 二、MTD 分区布局（重要，勿乱动）

```
mtd12: 023c0000 "rootfs"      -> 运行中的固件分区（flag_boot_rootfs=0）
mtd13: 023c0000 "rootfs_1"    -> 备用分区，已重新格式化（存 sing-box 二进制）
mtd14: 01ec0000 "overlay"     -> 小米原数据，已删除
```

**⚠️ 注意：mtd13 已无旧固件备份，不能再回滚！运行中的是 mtd12。**

### UBI 卷映射（重启后需手动挂载）

| UBI 设备 | 对应 MTD | 卷名 | 挂载点 | 用途 |
|----------|----------|------|--------|------|
| `ubi2` | `mtd13` (rootfs_1) | data | `/mnt/ext` | 存放 sing-box 二进制 |
| `ubi1` | `mtd14` (overlay) | data | `/mnt/ovl` | 备用 |
| `ubi0` | 内核自动挂载 | - | `/overlay` 等 | 系统可写层 |

---

## 三、刷机/基础配置流程

### 1. 改管理 IP 为 192.168.123.1
```sh
uci set network.lan.ipaddr='192.168.123.1'
uci commit network
/etc/init.d/network restart
```

### 2. 配置 WAN 上网（DHCP）
```sh
uci set network.wan.proto='dhcp'
uci commit network
/etc/init.d/network restart
# 验证：ip addr show wan 应拿到 192.168.1.2/24
```

### 3. 开启无线 5G/2.4G
```sh
# 5G
uci set wireless.radio0.disabled='0'
uci set wireless.default_radio0.ssid='OpenWrt_5G'
uci set wireless.default_radio0.encryption='psk2'
uci set wireless.default_radio0.key='cccc1025'

# 2.4G
uci set wireless.radio1.disabled='0'
uci set wireless.default_radio1.ssid='OpenWrt_2.4G'
uci set wireless.default_radio1.encryption='psk2'
uci set wireless.default_radio1.key='cccc1025'

uci commit wireless
wifi reload
```

---

## 四、安装机场插件（HomeProxy + sing-box）

> **核心难点**：sing-box 二进制 30.6MB，而 overlay 只有 12.2MB，装不下。
> **解决方案**：把 sing-box 放到 mtd13（`/mnt/ext`），软链到 `/usr/bin/sing-box`，再用"伪造 opkg 状态"方式只装 LuCI 界面（594KB）。

### 1. 配置 opkg 软件源（ImmortalWrt 官方源）

编辑 `/etc/opkg/distfeeds.conf`（备份：`/etc/opkg/distfeeds.conf.bak`）：

```
src/gz immortalwrt_core https://downloads.immortalwrt.org/releases/23.05.4/targets/ipq807x/generic/packages
src/gz immortalwrt_base https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/base
src/gz immortalwrt_luci https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/luci
src/gz immortalwrt_packages https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/packages
src/gz immortalwrt_routing https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/routing
src/gz immortalwrt_telephony https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/telephony
```

**⚠️ 注意点：**
- sing-box / homeproxy 是 ImmortalWrt 专属包，**不在** OpenWrt 官方镜像（如 `vsean.net/openwrt`），必须用 ImmortalWrt 源。
- 改完执行 `opkg update`（6 源签名校验通过才算成功）。

### 2. 释放空间 + 重新格式化 mtd13

```sh
# 删除小米原系统数据（mtd14）
# 删除旧 ImmortalWrt（mtd13），重新格式化得到 /mnt/ext（27.6MB）
ubiformat /dev/mtd13 -y
ubiattach -m 13 -d 2
ubimkvol /dev/ubi2 -N data -m
mount -t ubifs /dev/ubi2_0 /mnt/ext
```

### 3. 部署 sing-box 到 /mnt/ext（不占 overlay）

```sh
mkdir -p /mnt/ext/usr/bin
# 解压 sing-box ipk（/tmp/sing-box_1.11.15-1_aarch64_cortex-a53.ipk）
# 把二进制放到 /mnt/ext/usr/bin/sing-box（30,603,576 字节）
ln -sf /mnt/ext/usr/bin/sing-box /usr/bin/sing-box
/usr/bin/sing-box version   # 验证 v1.11.15
```

### 4. 创建 sing-box 用户（uid/gid 5566）

```sh
# 添加到 /etc/passwd
echo 'sing-box:x:5566:5566:sing-box:/var/run/sing-box:/bin/false' >> /etc/passwd
# 添加到 /etc/group
echo 'sing-box:x:5566:' >> /etc/group
```

### 5. 伪造 opkg 状态（让 opkg 认为 sing-box 已装）

**⚠️ 极度危险操作！切勿用 `>` 覆盖 status 文件！**

```sh
# 1. 备份
cp /usr/lib/opkg/status /usr/lib/opkg/status.bak

# 2. 用 >> 追加（不是 > ！）
# 追加 5 个 kmod 记录 + sing-box 记录，均标记 Status: install user installed
# kmod-inet-diag / kmod-netlink-diag / kmod-nf-tproxy / kmod-nft-tproxy / kmod-tun

# 3. 创建 sing-box 的 info 元数据文件（缺一不可）
#   /usr/lib/opkg/info/sing-box.control
#   /usr/lib/opkg/info/sing-box.list
#   /usr/lib/opkg/info/sing-box.conffiles
#   /usr/lib/opkg/info/sing-box.postinst
#   /usr/lib/opkg/info/sing-box.prerm
```

**⚠️ 注意点：**
- 原始固件完整包列表备份在 `/rom/usr/lib/opkg/status`（223 包基线），可作恢复参考。
- opkg 判断"已安装"需要 **status 记录 + info/*.list 文件同时存在**。
- 曾经误用 `>` 覆盖 status 丢失 223 条记录，务必先备份、用 `>>` 追加。

### 6. 安装 LuCI 界面（此时不重复下载 sing-box）

```sh
opkg install luci-app-homeproxy luci-i18n-homeproxy-zh-cn
# 验证
opkg list-installed | grep homeproxy
# 应显示：luci-app-homeproxy / luci-i18n-homeproxy-zh-cn
```

---

## 五、配置开机自动挂载（关键！否则重启后 sing-box 失效）

> **问题**：重启后 UBI 卷（ubi1_0 / ubi2_0）不会自动 attach，sing-box 软链会失效。

创建 `/etc/init.d/mount-ext`（START=10，早于 HomeProxy 的 START=99）：

```sh
cat > /etc/init.d/mount-ext <<'EOF'
#!/bin/sh /etc/rc.common

START=10
STOP=90

start() {
    # 挂载 mtd13 (rootfs_1) -> /mnt/ext，存放 sing-box 二进制
    [ -e /dev/ubi2_0 ] || ubiattach -m 13 -d 2
    [ -d /mnt/ext ] || mkdir -p /mnt/ext
    mountpoint -q /mnt/ext || mount -t ubifs /dev/ubi2_0 /mnt/ext

    # 挂载 mtd14 (overlay 分区) -> /mnt/ovl
    [ -e /dev/ubi1_0 ] || ubiattach -m 14 -d 1
    [ -d /mnt/ovl ] || mkdir -p /mnt/ovl
    mountpoint -q /mnt/ovl || mount -t ubifs /dev/ubi1_0 /mnt/ovl
}

stop() {
    umount /mnt/ext 2>/dev/null
    umount /mnt/ovl 2>/dev/null
}
EOF
chmod +x /etc/init.d/mount-ext
/etc/init.d/mount-ext enable
```

**⚠️ 注意点：**
- HomeProxy 自己用 procd 启动 sing-box（`PROG=/usr/bin/sing-box`），**不依赖** `/etc/init.d/sing-box`，所以 sing-box 的 init 脚本无需单独启用。
- 挂载脚本必须 `START=10`，早于 `S99homeproxy`，确保 sing-box 软链在启动时已可用。

---

## 六、更新机场订阅（关键！UA 设置 + anytls 支持）

> **最大坑**：机场服务端检测到 User-Agent 会返回**不同内容**，选错 UA 会导致只导入假节点或"无有效节点"。
- **关键坑**：机场根据订阅请求的 `User-Agent` 返回不同格式：
  - `User-Agent: v2rayN` / `Wget` → 返回**假节点**（"版本太旧"占位符）
  - `User-Agent: Clash` / `clash-verge/v2.5.8` → 返回 **Clash YAML**（HomeProxy 无法解析，报 "No valid node found"）
  - `User-Agent: Quantumult/1.0.30` 或 `hysteria2` → 返回 **base64 节点列表**（11800 字节，44 个真实节点，含 anytls）✅ **正确选择**
  - 空 UA → 返回 base64 节点列表，但 HomeProxy 的 `wGET()` 空 UA 会自动回退为 `Wget/1.21 (HomeProxy, like v2rayN)`，触发假节点返回

> **⚠️ 前置条件：anytls 支持升级**。机场 44 个节点中 31 个是 `anytls` 协议，**官方源里的旧版 HomeProxy（sing-box 1.11.x）不支持 anytls**，会因"无有效节点"只导入 13 个。必须先完成：
> 1. **升级 sing-box 到 1.12.x**（anytls 是 1.12 新增协议）—— 见下文「第八节」
> 2. **升级 HomeProxy 文件 + 安装 digest 模块** —— 见下文「第八节」

### 订阅 URL
```
https://sub-1.smjcdh.top/smjc/api/v1/client/subscribe?token=e56e11f8b1eb6e62685d42fc7abaa41f
```

### 配置步骤

```sh
# 1. 添加订阅 URL（注意用单引号包裹，避免 & 被 shell 解释）
uci add_list homeproxy.subscription.subscription_url='https://sub-1.smjcdh.top/smjc/api/v1/client/subscribe?token=e56e11f8b1eb6e62685d42fc7abaa41f'

# 2. 设置 User-Agent（必须是 'Quantumult/1.0.30'，返回 base64 节点列表）
uci set homeproxy.subscription.user_agent='Quantumult/1.0.30'

uci commit homeproxy

# 3. 导入节点
ucode -S /etc/homeproxy/scripts/update_subscriptions.uc

# 4. 查看日志确认
tail -20 /var/run/homeproxy/homeproxy.log
# 应显示 "Successfully fetched 41 nodes of total 44" 及 "28 nodes added"
```

### 设置主节点 + 启动

```sh
# 查看节点列表（label + type）
for n in $(uci show homeproxy | grep "=node" | cut -d= -f1); do
  echo "$n: $(uci get $n.label 2>/dev/null) [$(uci get $n.type 2>/dev/null)]"
done

# 设置主节点（用上面查到的节点 section 名）
uci set homeproxy.config.main_node='<节点section名>'
uci commit homeproxy

# 启动
/etc/init.d/homeproxy start
```

### 验证代理生效

```sh
# 访问谷歌应返回 HTML（说明代理通了）
wget -qO- --timeout=12 http://www.google.com | head -c 80

# 查看 sing-box 进程（ujail 沙箱中运行）
ps w | grep -i sing-box | grep -v grep
```

---

## 七、机场节点列表（导入后共 41 个）

| 类型 | 数量 | 节点示例 |
|------|------|----------|
| anytls | 28 | 美国凤凰城、2x专线-日本/香港/新加坡、美国洛杉矶-1/2/3、香港原生IP、台湾1/2 等 |
| hysteria2 | 7 | 加拿大/英国/法国/德国/卢森堡 等 |
| vless | 3 | 日本cdn1、日本cdn2、韩国+cdn（电信高速 2倍率） |
| trojan | 3 | 2x专线-日本-4、2x专线-香港-4、2x专线-新加坡-4（均 IPv6） |

> 44 个总节点中 3 个被黑名单过滤（「剩余流量」「距离下次重置」「套餐到期」占位节点）。
> 当前主节点：`8659b4d1a77ff195c0cb2b1f45267c1d`（vless，ws 传输）。

---

## 八、升级 sing-box + HomeProxy 以支持 anytls

> **背景**：机场主力节点已全面切换为 `anytls` 协议（44 节点中 31 个），而 ImmortalWrt 23.05.4 官方源的 sing-box 1.11.15 与 HomeProxy 均不支持 anytls，导致订阅只能导入 13 个非 anytls 节点。

### 1. 升级 sing-box 到 1.12.24

```sh
# 备份旧版
cp /mnt/ext/usr/bin/sing-box /mnt/ovl/sing-box.bak.1.11.15

# 下载 sing-box 1.12.24 通用 arm64 包（Windows 走代理下载，再通过本地 HTTP 传给路由器）
# https://github.com/SagerNet/sing-box/releases/download/v1.12.24/sing-box-1.12.24-linux-arm64.tar.gz

# 替换二进制
cp /tmp/sing-box-1.12.24 /mnt/ext/usr/bin/sing-box
chmod 755 /mnt/ext/usr/bin/sing-box
/usr/bin/sing-box version   # 验证 1.12.24
```

### 2. 安装 digest 模块（HomeProxy 上游新依赖）

```sh
opkg update
opkg install ucode-mod-digest
# 验证
ucode -e "import { md5 } from 'digest'; print(md5('abc'));"
# 输出 900150983cd24fb0d6963f7d28e17f72 即正常
```

### 3. 替换 HomeProxy 文件（后端 + 前端）

> 从 `https://github.com/immortalwrt/homeproxy` master 分支下载最新文件（已含 anytls 支持），通过本地 HTTP 服务器 + 路由器 wget 替换。**必须先备份**：

```sh
mkdir -p /mnt/ovl/homeproxy.bak
cp -a /etc/homeproxy/scripts/*.uc /mnt/ovl/homeproxy.bak/
cp -a /www/luci-static/resources/homeproxy.js /mnt/ovl/homeproxy.bak/
cp -a /www/luci-static/resources/view/homeproxy/*.js /mnt/ovl/homeproxy.bak/
```

需替换的文件清单（后端 5 个 + 前端 5 个）：

| 类别 | 文件 | 远端路径 | 说明 |
|------|------|----------|------|
| 后端 | update_subscriptions.uc | /etc/homeproxy/scripts/ | 新增 anytls case（3 处） |
| 后端 | homeproxy.uc | /etc/homeproxy/scripts/ | 删除 calcStringMD5，改用 digest |
| 后端 | generate_client.uc | /etc/homeproxy/scripts/ | 新增 anytls 出站（3 处） |
| 后端 | generate_server.uc | /etc/homeproxy/scripts/ | 新增 anytls 入站（3 处） |
| 后端 | migrate_config.uc | /etc/homeproxy/scripts/ | 新增 dns_server 迁移 |
| 前端 | node.js | /www/luci-static/resources/view/homeproxy/ | 新增 anytls UI 选项（15 处） |
| 前端 | client.js | /www/luci-static/resources/view/homeproxy/ | 配套更新 |
| 前端 | server.js | /www/luci-static/resources/view/homeproxy/ | 配套更新 |
| 前端 | status.js | /www/luci-static/resources/view/homeproxy/ | 配套更新 |
| 前端 | homeproxy.js | /www/luci-static/resources/ | 前端辅助函数更新 |

> **⚠️ 注意点：**
> - `firewall_pre.uc` 与上游完全一致，**无需替换**。
> - 前端 JS 是压缩单行代码，需整体替换（不可手工 patch）。
> - 后端 `.uc` 需 `chmod 755`，前端 `.js` 保持 `644`。
> - 上游整套文件是配套关系，**不能只换单个文件**（如只换 update_subscriptions.uc 而不换 homeproxy.uc，会因 `import { md5 } from 'digest'` 与旧 calcStringMD5 冲突）。

### 4. 验证 anytls 生效

```sh
# 检查后端脚本 anytls 引用数
grep -c anytls /etc/homeproxy/scripts/update_subscriptions.uc   # 3
grep -c anytls /etc/homeproxy/scripts/generate_client.uc        # 3
grep -c anytls /www/luci-static/resources/view/homeproxy/node.js # 15

# 重新订阅（UA 设为 Quantumult 后）
ucode -S /etc/homeproxy/scripts/update_subscriptions.uc

# 检查节点类型分布
uci show homeproxy | grep '.type=' | cut -d= -f2 | sort | uniq -c | sort -rn
# 应显示 28 'anytls' / 7 'hysteria2' / 3 'vless' / 3 'trojan'

# 检查 anytls 节点字段是否完整（address/port/password/tls_sni/tls_insecure）
uci show homeproxy.<任意anytls节点section>
```

---

## 九、常用命令速查

```sh
# 重启路由器
reboot

# 检查挂载（重启后应看到 /mnt/ext 和 /mnt/ovl）
mount | grep mnt

# 检查 sing-box 是否可用
/usr/bin/sing-box version

# 重启 HomeProxy
/etc/init.d/homeproxy restart

# 查看 HomeProxy 日志
tail -30 /var/run/homeproxy/homeproxy.log

# 查看 opkg 已装包数
opkg list-installed | wc -l

# 检查 overlay 剩余空间
df -h /overlay

# 查看节点类型分布（验证 anytls 已导入）
uci show homeproxy | grep '.type=' | cut -d= -f2 | sort | uniq -c | sort -rn

# 手动更新订阅
ucode -S /etc/homeproxy/scripts/update_subscriptions.uc

# 手动生成客户端配置
ucode -S /etc/homeproxy/scripts/generate_client.uc
```

---

## 十、⚠️ 注意事项汇总

1. **切勿用 `>` 覆盖 `/usr/lib/opkg/status`** —— 会丢失全部包记录，必须用 `>>` 追加且先备份。
2. **opkg 判断"已安装"需 status 记录 + info/*.list 文件同时存在**，缺一不可。
3. **订阅 UA 必须是 `Quantumult/1.0.30`**（返回 base64 节点列表）。含 `v2rayN`/`Wget` 返回假节点，含 `Clash`/`clash-verge` 返回 Clash YAML（HomeProxy 无法解析）。
4. **订阅 URL 含 `&`**，在 shell 里必须用单引号包裹，否则被解释为后台符号。
5. **mtd13 已无旧固件备份，不能再回滚**，运行中的是 mtd12。
6. **重启后 UBI 卷不自动挂载**，依赖 `/etc/init.d/mount-ext`（START=10）在 HomeProxy（S99）之前挂载。
7. **sing-box 在 ujail 沙箱中运行**，软链 `/usr/bin/sing-box → /mnt/ext/usr/bin/sing-box` 在沙箱内正常解析（已实测通过，无需额外挂载）。
8. **Go 静态二进制（sing-box）压缩率低**，30.6MB 文件在 ubifs 实际占用约 21.4MB，放 overlay（12.2MB）必失败。
9. **anytls 支持需同时升级 sing-box（1.12.x）+ HomeProxy + 安装 ucode-mod-digest**，三者缺一不可；替换 HomeProxy 文件须整套替换（后端+前端），不可只换单个。

---

*文档生成时间：2026-11-07*
*最后更新：2026-11-08（sing-box 升级 1.12.24 + HomeProxy 支持 anytls，节点 13 → 41）*
*下次刷机/更新订阅，按第五节（开机挂载）、第六节（订阅更新）、第八节（anytls 升级）操作即可。*


