# OpenClash 更新 / 修复完整步骤与注意点

> 适用设备：NOKIA EA0326GMP（ImmortalWrt 21.02-SNAPSHOT）
> 整理日期：2026-11-07
> 用途：下次 OpenClash 出问题或升级后，按本文档一步步恢复。

---

## 一、环境信息

| 项目 | 值 |
|------|-----|
| 路由器 | NOKIA EA0326GMP |
| 系统 | ImmortalWrt 21.02-SNAPSHOT r20568-3fa9687ca7 |
| 内核 | Linux 5.4.255，aarch64（mediatek/mt7981） |
| 管理 IP | `192.168.100.1` |
| SSH 凭据 | 用户名 `root`，密码 `password` |
| OpenClash 内核目录 | `/etc/openclash/core/` |
| Meta 内核路径 | `/etc/openclash/core/clash_meta` |
| 内核软链接 | `/etc/openclash/clash` → `clash_meta` |
| 运行配置 | `/etc/openclash/config/smjc.yaml` |
| 机场 | 三毛机场（按 User-Agent 返回不同内容，见下文） |

---

## 二、机场订阅信息

- **订阅地址**：
  ```
  https://sub-1.smjcdh.top/smjc/api/v1/client/subscribe?token=e56e11f8b1eb6e62685d42fc7abaa41f
  ```
- **关键坑**：机场会根据订阅请求的 `User-Agent` 返回**不同内容**：
  - `User-Agent: Clash` → 返回**假节点**（7841 字节，节点 server 全是 `127.0.0.1:999`，节点名「客户端不支持或版本太旧」）
  - `User-Agent: clash-verge/v2.5.8` → 返回**真节点**（约 19888 字节，48 个真实节点）
  - `User-Agent: ClashMetaForAndroid/2.11.27.Alpha` → 返回**真节点**（约 19888 字节，48 个真实节点）
- 节点协议：`anytls`、`trojan`、`hysteria2`
- 节点密码（示例，以实际订阅为准）：`6cad50c5-c981-400d-96ac-bcb71f8a1ec8`

---

## 三、完整操作步骤

### 1. SSH 连接路由器

```bash
ssh root@192.168.100.1
# 密码：password
```

---

### 2. 检查当前内核是否损坏 / 过旧

```bash
/etc/openclash/core/clash_meta -v
```

- **正常输出**应为类似：`Mihomo Meta alpha-gbc76c13 linux arm64 with go1.26.9`
- **异常情况**：旧版 `clash v1.15.1` 不支持 `RULE-SET`，或文件损坏无法执行（报 `Segmentation fault` / `Exec format error`），则需要替换内核。

---

### 3. 下载新版 mihomo 内核到 /tmp（不要直接下载到 overlay！）

> ⚠️ 必须先下载到 `/tmp`（tmpfs），因为 overlay 分区只有 46.3M 且几乎满了。

```bash
cd /tmp
curl -sSL -o clash.tar.gz \
  https://cdn.jsdelivr.net/gh/vernesong/OpenClash@core/master/meta/clash-linux-arm64.tar.gz
tar -xzf clash.tar.gz
ls -lh /tmp/clash   # 解压后是单文件，约 12.8M，未 UPX 压缩
```

- 备用下载源（若 jsdelivr 被墙/超时）：
  - `https://fastly.jsdelivr.net/gh/vernesong/OpenClash@core/master/meta/clash-linux-arm64.tar.gz`
  - `https://testingcf.jsdelivr.net/gh/vernesong/OpenClash@core/master/meta/clash-linux-arm64.tar.gz`

---

### 4. 替换内核文件

```bash
cp /tmp/clash /etc/openclash/core/clash_meta
chmod 4755 /etc/openclash/core/clash_meta
/etc/openclash/core/clash_meta -v   # 验证能运行
```

---

### 5. 建立/修正内核软链接

```bash
ln -sf /etc/openclash/core/clash_meta /etc/openclash/clash
ls -l /etc/openclash/clash
```

---

### 6. 修复新版 mihomo 的 external-ui 路径校验（SAFE_PATHS）

新版 mihomo 有 **SAFE_PATHS 路径校验**，只允许 `/etc/openclash` 及 home 目录，
而 OpenClash 默认把 `external-ui` 指向 `/usr/share/openclash/ui`，会被拒绝启动。

两种办法（都做更保险）：

**方法 A：创建软链接（推荐）**
```bash
ln -sf /usr/share/openclash/ui /etc/openclash/ui
```

**方法 B：修改 `yml_change.sh` 里硬编码的路径**
```bash
sed -i "s#Value\['external-ui'\]='/usr/share/openclash/ui';#Value['external-ui']='/etc/openclash/ui';#" \
  /usr/share/openclash/yml_change.sh
grep -n "external-ui" /usr/share/openclash/yml_change.sh   # 确认改为 /etc/openclash/ui
```

---

### 7. 修改订阅下载的 User-Agent（解决假节点问题）★ 最关键

OpenClash 的订阅下载脚本 `/usr/share/openclash/openclash.sh` 里硬编码了
`User-Agent: Clash`，机场识别后返回假节点。

```bash
sed -i "s#User-Agent: Clash#User-Agent: clash-verge/v2.5.8#g" /usr/share/openclash/openclash.sh
grep -n "User-Agent:" /usr/share/openclash/openclash.sh   # 确认 4 处全部改好
```

> 共 4 处（第 92 / 94 / 96 / 100 行附近），都要改成 `clash-verge/v2.5.8`。

---

### 8. 确认 UCI 配置

```bash
uci show openclash | grep -E 'config_path|enable_meta_core|enable=|dashboard'
```

关键项应为：
- `openclash.config.config_path='/etc/openclash/config/smjc.yaml'`
- `openclash.config.enable_meta_core='1'`
- `openclash.config.enable='1'`
- 订阅 `openclash.@config_subscribe[0].sub_convert='0'`（直接下载，不转换）

---

### 9. 重新触发订阅更新

```bash
# 清理残留锁，确认没有 clash 进程在跑
rm -f /tmp/lock/openclash_subs.lock
ps w | grep -iE 'clash|mihomo' | grep -v grep

# 只更新 smjc 这一个配置（会下载→校验→注入设置→写回→自动重启 OpenClash）
/usr/share/openclash/openclash.sh /etc/openclash/config/smjc.yaml
```

更新成功后：
```bash
# 确认节点已是真实 IP（不再有 127.0.0.1:999）
grep -nE 'server:|127.0.0.1|999|客户端不支持' /etc/openclash/config/smjc.yaml | head -20
wc -c /etc/openclash/config/smjc.yaml   # 应约 19861 字节
```

---

### 10. 验证运行与连通性

```bash
# 进程与 watchdog
ps w | grep -iE 'clash|mihomo' | grep -v grep

# 日志应出现真实节点，而非 127.0.0.1:999 connection refused
tail -20 /tmp/openclash.log

# 端到端测试（Google / YouTube 应返回 200）
curl -sS -m 20 -o /dev/null -w 'google  http_code=%{http_code} time=%{time_total}s\n' https://www.google.com
curl -sS -m 20 -o /dev/null -w 'youtube http_code=%{http_code} time=%{time_total}s\n' https://www.youtube.com
```

---

## 四、注意点 / 常见坑

### 1. 机场按 User-Agent 返回假节点 ★★★
- 症状：订阅更新「成功」，但所有节点 server 是 `127.0.0.1:999`，节点名「客户端不支持或版本太旧」，日志疯狂报 `dial tcp 127.0.0.1:999: connect: connection refused`。
- 根因：OpenClash 硬编码 `User-Agent: Clash`，被机场识别为不支持的客户端。
- 解决：改成 `clash-verge/v2.5.8`（见步骤 7）。
- **排查技巧**：先用 curl 直接带不同 UA 测订阅，对比返回大小判断真假：
  ```bash
  curl -sSL -H 'User-Agent: Clash' '订阅地址' -o /tmp/sub_fake.yaml
  curl -sSL -H 'User-Agent: clash-verge/v2.5.8' '订阅地址' -o /tmp/sub_real.yaml
  wc -c /tmp/sub_fake.yaml /tmp/sub_real.yaml   # 真节点明显更大（~19KB vs ~7KB）
  ```

### 2. overlay 分区空间不足
- overlay（`/dev/ubi0_2`）只有 **46.3M**，平时 95% 满。
- 内核文件（12.8M~28M）**必须先下载到 `/tmp`**（tmpfs 有 112.5M），替换时再 `cp` 过去。
- 及时清理 `/tmp` 下的大文件释放空间/内存。

### 3. 内存紧张（OOM 风险）
- 总内存 230MB + swap 114MB，clash 运行时可用内存常只有 10~80MB。
- 长时间运行或频繁更新可能导致 OOM 杀掉 clash。
- **停止 OpenClash 的正确姿势**（`/etc/init.d/openclash stop` 经常停不干净）：
  ```bash
  kill -9 $(pgrep -f '/etc/openclash/clash')
  pkill -9 -f 'openclash_watchdog'
  ```

### 4. 新版 mihomo 的 SAFE_PATHS 校验
- 只允许访问 `/etc/openclash` 及 home 目录。
- 默认 `external-ui=/usr/share/openclash/ui` 会被拒绝，导致启动失败。
- 解决：软链接 `/etc/openclash/ui` → `/usr/share/openclash/ui`，并改 `yml_change.sh`（见步骤 6）。

### 5. 只读 squashfs + overlay 写时复制（重要！）
- `/usr/share/openclash/*.sh` 在只读 squashfs 上，我们的 `sed` 修改是通过 **overlay 写时复制**实现的。
- **升级 OpenClash 版本、重装插件、或恢复出厂设置后，这些修改会丢失**，需要重新执行：
  - 步骤 6（external-ui 路径）
  - 步骤 7（User-Agent）
  - 步骤 5（内核软链接）
  - 第七节（重建 `fix_hk_sg_autoselect.sh` 并注入 `openclash.sh`）
- 内核文件 `clash_meta` 在 `/etc/openclash/core/`（可写分区），一般升级不会丢。

### 6. 版本差异
- 本文档针对 `clash-linux-arm64`（aarch64 / mediatek mt7981）。
- 其他机型需从 OpenClash 官方 core 仓库下载对应架构内核：
  - `clash-linux-amd64`、`clash-linux-armv7`、`clash-linux-arm64`、`clash-linux-mips*` 等。
  - 路径格式：`https://cdn.jsdelivr.net/gh/vernesong/OpenClash@core/master/meta/clash-linux-<架构>.tar.gz`

---

## 五、快速恢复速查（升级后或出问题时）

```bash
# 1. SSH
ssh root@192.168.100.1    # 密码 password

# 2. 内核软链接
ln -sf /etc/openclash/core/clash_meta /etc/openclash/clash

# 3. external-ui 软链接
ln -sf /usr/share/openclash/ui /etc/openclash/ui

# 4. 修改 UA（解决假节点）
sed -i "s#User-Agent: Clash#User-Agent: clash-verge/v2.5.8#g" /usr/share/openclash/openclash.sh

# 5. 重建「自动选择=港新节点」脚本并注入（见第七节）
#    （把第七节的 fix_hk_sg_autoselect.sh 内容写回，再执行下面的 sed 注入）
sed -i '/^   rm -rf \/tmp\/Proxy_Group 2>\/dev\/null$/i\   # 注入: 订阅更新后自动限制「自动选择」组为港新节点\n   /usr/share/openclash/fix_hk_sg_autoselect.sh >> "$LOG_FILE" 2>/dev/null' \
  /usr/share/openclash/openclash.sh

# 6. 更新订阅
rm -f /tmp/lock/openclash_subs.lock
/usr/share/openclash/openclash.sh /etc/openclash/config/smjc.yaml

# 7. 验证
curl -sS -m 20 -o /dev/null -w '%{http_code}\n' https://www.google.com   # 期望 200
```

---

## 六、系统清理规则（精简瘦身）

> 本次清理目标：卸载不用的插件、删除孤儿文件，释放 overlay 空间。
> 清理前 overlay 97% 满（剩 1.1M），清理后 61%（剩 17.1M），释放约 26M。

### A. 卸载不用的插件

| 需求 | 对应包 |
|------|--------|
| 上网时间控制 | `luci-app-accesscontrol` |
| UPnP | `luci-app-upnp` + 后端 `miniupnpd` |
| KMS 激活服务 | `luci-app-vlmcsd` + 后端 `vlmcsd` |
| 全能网络工具（端口转发/反代） | `luci-app-lucky` + 后端 `lucky` |

```bash
# 1. 停止相关服务
/etc/init.d/miniupnpd stop 2>/dev/null
/etc/init.d/vlmcsd stop 2>/dev/null
/etc/init.d/lucky stop 2>/dev/null

# 2. 卸载（含中文语言包）
opkg remove --force-depends \
  luci-app-accesscontrol luci-i18n-accesscontrol-zh-cn \
  luci-app-upnp luci-i18n-upnp-zh-cn miniupnpd \
  luci-app-vlmcsd luci-i18n-vlmcsd-zh-cn vlmcsd \
  luci-app-lucky luci-i18n-lucky-zh-cn lucky
```

**卸载验证：**
```bash
# 应为空（无输出）
opkg list-installed | grep -iE 'accesscontrol|upnp|miniupnpd|vlmcsd|lucky'
ps w | grep -iE 'miniupnpd|vlmcsd|lucky' | grep -v grep
```

> ⚠️ **注意**：`libminiupnpc` 库被 **ZeroTier** 依赖，**不能删**，否则会破坏 ZeroTier。

---

### B. 删除孤儿文件（释放 overlay 空间）★★★

> overlay 只有 46.3M，空间告急时优先做这一步，安全且收益最大。

**排查方法**（找占用空间的大文件）：
```bash
# 查看 overlay 空间
df -h /overlay

# 列出 overlay 下所有 >500K 的文件，按大小排序
find /overlay/upper -type f -size +500k 2>/dev/null | xargs ls -lh 2>/dev/null | awk '{print $5, $9}' | sort -rn
```

**本次清理的孤儿文件**（无依赖、无自启、未运行）：

| 文件/目录 | 大小 | 说明 |
|-----------|------|------|
| `/usr/bin/xray` | 22.5M | xray 二进制，无插件依赖、配置 `enabled=0`、未运行 |
| `/etc/init.d/xray` + `/etc/config/xray` | 几 KB | xray 的启动脚本和配置 |
| `/etc/ssrplus/` | 4.0M | ssr-plus 插件根本没安装，纯残留（ad.conf/gfw_list.conf/china_ssr.txt） |
| `/etc/openclash/core/clash` | 2.3M | 旧 clash 内核，已被 `clash_meta` 取代，软链接已指向新内核 |

```bash
# 删除前确认
ls -lh /usr/bin/xray /etc/openclash/core/clash
du -sh /etc/ssrplus
ls -l /etc/init.d/xray /etc/config/xray

# 执行删除
rm -f /usr/bin/xray /etc/init.d/xray /etc/config/xray
rm -rf /etc/ssrplus
rm -f /etc/openclash/core/clash

# 验证（均应为 No such file or directory）
ls -l /usr/bin/xray /etc/init.d/xray /etc/config/xray /etc/ssrplus /etc/openclash/core/clash
df -h /overlay   # 应回到 ~61%
```

**删除后安全检查：**
```bash
# 新内核软链接应仍正常
ls -l /etc/openclash/clash /etc/openclash/core/clash_meta

# OpenClash 进程应仍在运行
ps w | grep -iE 'clash|mihomo' | grep -v grep
```

---

### C. 判断某个文件是否「孤儿」（通用方法）

删除任何二进制/目录前，先确认它不被使用：

```bash
# 1. 是否被 opkg 管理（无输出 = 孤儿文件，可安全删）
opkg list-installed | grep -iE '<包名>'

# 2. 是否有自启项
ls /etc/rc.d/ | grep -iE '<关键词>'

# 3. 是否有进程在运行
ps w | grep -iE '<关键词>' | grep -v grep

# 4. 配置是否启用
uci -q get <配置名>.<节>.enabled

# 5. 是否被其他包依赖（有输出 = 不能删）
opkg whatdepends <包名>
```

> 原则：只有「opkg 无记录 + 无自启 + 无进程 + 无依赖」四者都满足，才可安全删除。

---

## 七、「♻️ 自动选择」只使用香港/新加坡节点（保留全部节点）

> 需求：**不删除任何节点**——`三毛机场` 组保留全部节点供手动切换，但让
> `♻️ 自动选择`（url-test）组**只**在「香港 + 新加坡」节点之间测速、择优。
>
> ⚠️ 关键点：机场订阅**自带** `♻️ 自动选择` 这个 url-test 组（且里面塞满了全部节点，
> 含美国/日本/以及「剩余流量」「套餐到期」这类**假节点**）。它由机场生成，不是
> OpenClash 生成的，所以每次更新订阅都会**覆盖**我们对它的手动修改。
>
> ⚠️ 不要用 OpenClash 的「过滤关键字」——那会**删除节点**，与「保留全部节点」的需求矛盾。
> 正确做法是：写一个 post-update 脚本，在每次订阅更新后自动把「自动选择」组的
> `proxies` 重写为港新节点，其余节点一个不动。

### 原理

1. 机场订阅里有两个策略组：
   - `三毛机场`（select）：**全部 47 个节点**，供手动选择，保持不变。
   - `♻️ 自动选择`（url-test）：机场也塞了全部节点，需要被我们「裁剪」。
2. OpenClash 的订阅更新脚本 `/usr/share/openclash/openclash.sh` 里，`config_cus_up()`
   函数负责「下载→校验→写回配置」，且函数末尾没有自定义钩子。
3. 我们在 `config_cus_up()` 末尾注入一行，调用自定义脚本 `fix_hk_sg_autoselect.sh`，
   它用 ruby 读 YAML → 把「自动选择」组的 `proxies` 替换为港新节点名 → 写回。
   这样每次更新订阅后自动生效，手动选的节点不会被删。

### 已实施的脚本：`/usr/share/openclash/fix_hk_sg_autoselect.sh`

```bash
#!/bin/bash
# 修复「♻️ 自动选择」组：仅保留香港/新加坡节点，其余节点全部保留在「三毛机场」组中
# 由 openclash.sh 的 config_cus_up() 在每次订阅更新后自动调用

CONFIG_FILE="/etc/openclash/config/smjc.yaml"
[ -f "$CONFIG_FILE" ] || exit 0

ruby -ryaml -rYAML -I "/usr/share/openclash" -E UTF-8 -e '
begin
  Value = YAML.load_file(ARGV[0])
  if Value.has_key?("proxies") and Value.has_key?("proxy-groups") then
    hk_sg = Value["proxies"].select { |p| p["name"] =~ /2x专线-(香港|新加坡)|新加坡[0-9]/ }
    count = 0
    Value["proxy-groups"].each do |g|
      if g["name"].to_s.include?("自动选择") and g["type"] == "url-test" then
        g["proxies"] = hk_sg.map { |p| p["name"] }
        count = g["proxies"].size
      end
    end
    File.open(ARGV[0], "w") { |f| YAML.dump(Value, f) }
    puts "Fix Auto-Select Group: " + count.to_s + " HK/SG nodes"
  end
rescue Exception => e
  puts "Error: " + e.message
end
' "$CONFIG_FILE" 2>/dev/null
```

> 匹配规则 `2x专线-(香港|新加坡)|新加坡[0-9]` 命中 10 个真实节点：
> `2x专线-香港-1~4`、`2x专线-新加坡-1~4`、`新加坡1`、`新加坡2`。
> 若机场日后改名/加节点，按需调整正则即可。

### 注入到订阅更新脚本（核心，务必执行）

在 `/usr/share/openclash/openclash.sh` 的 `config_cus_up()` 函数末尾、
`rm -rf /tmp/Proxy_Group` 这一行**之前**插入调用：

```bash
# 备份后注入
cp /usr/share/openclash/openclash.sh /tmp/openclash.sh.bak

sed -i '/^   rm -rf \/tmp\/Proxy_Group 2>\/dev\/null$/i\   # 注入: 订阅更新后自动限制「自动选择」组为港新节点\n   /usr/share/openclash/fix_hk_sg_autoselect.sh >> "$LOG_FILE" 2>/dev/null' \
  /usr/share/openclash/openclash.sh

bash -n /usr/share/openclash/openclash.sh && echo "openclash.sh 语法 OK"
```

注入后 `config_cus_up()` 末尾应长这样：

```bash
   fi
   
   # 注入: 订阅更新后自动限制「自动选择」组为港新节点
   /usr/share/openclash/fix_hk_sg_autoselect.sh >> "$LOG_FILE" 2>/dev/null
   rm -rf /tmp/Proxy_Group 2>/dev/null
}
```

### 验证是否生效

```bash
# 1. 手动跑一次脚本，观察输出（应打印 Fix Auto-Select Group: 10 HK/SG nodes）
/usr/share/openclash/fix_hk_sg_autoselect.sh

# 2. 检查分组结构：三毛机场=47 节点（全保留）、自动选择=10 节点（仅港新）
ruby -ryaml -rYAML -I /usr/share/openclash -E UTF-8 -e 'y=YAML.load_file("/etc/openclash/config/smjc.yaml"); y["proxy-groups"].each{|g| puts "组名: #{g["name"]} | 类型: #{g["type"]} | 节点数: #{g["proxies"].to_a.size}"}' 2>/dev/null

# 3. 触发一次真实订阅更新，确认更新后自动选择组仍只有港新节点
rm -f /tmp/lock/openclash_subs.lock
/usr/share/openclash/openclash.sh /etc/openclash/config/smjc.yaml
ruby -ryaml -rYAML -I /usr/share/openclash -E UTF-8 -e 'y=YAML.load_file("/etc/openclash/config/smjc.yaml"); y["proxy-groups"].each{|g| puts "#{g["name"]}: #{g["proxies"].to_a.size}"}' 2>/dev/null
```

### 注意点

- **升级 OpenClash / 重装插件 / 恢复出厂后，本次修改会丢失**（squashfs 只读 + overlay 写时复制被重置），需要重新执行：
  1. 重建 `/usr/share/openclash/fix_hk_sg_autoselect.sh`（见上文脚本）
  2. 重新注入 `openclash.sh`（见上文 `sed` 命令）
  - 建议把「重建脚本 + 注入」也加进第五节的「快速恢复速查」里。
- 脚本只会改 `url-test` 类型的「自动选择」组，`select` 类型的 `三毛机场` 组**完全不动**，全部节点仍在。
- 若想改用「只自动选择香港」或「只新加坡」，把脚本里的正则改成 `/香港/` 或 `/新加坡/` 即可。
- 假节点（`剩余流量`、`距离下次重置`、`套餐到期`、`如果很少节点可用` 等）不在匹配正则内，**不会**进入自动选择组，自动被排除。

---

## 八、解决 OpenClash 经常崩溃重启（OOM 内存不足）

> 问题：`openclash_watchdog.sh` 反复打印 `Watchdog: Clash Core Problem, Restart...`，
> clash 内核进程每隔一段时间被系统杀掉、再被 watchdog 拉起，形成崩溃-重启循环。
>
> 根因：**内存不足，内核 OOM-killer 反复杀掉 clash 进程**。本机物理内存仅 230MB，
> 却同时运行 clash（Go 运行时虚拟内存峰值 1.35GB，RSS ~36MB + swap ~61MB）、
> netdata、haproxy、dnsmasq、mwan3 等二十多个服务，内存长期耗尽。

### 排查结论

| 项目 | 值 |
|------|-----|
| 物理内存 | 230,316 kB（约 225MB） |
| zram swap | 114,684 kB（lzo 压缩，`/dev/zram0`） |
| clash 进程 | RSS ~36MB + swap ~61MB ≈ 97MB，VmHWM 67MB，VmPeak 1.35GB |
| OOM 总次数 | 26 次（clash 14 次，`oom_score_adj:0`；netdata 12 次，`oom_score_adj:1000`） |
| 内核 | Mihomo Meta alpha-gbc76c13 (go1.26.9, with_gvisor) |
| 触发日志 | `2026-11-08 00:34:59 Watchdog: Clash Core Problem, Restart...` |

### 修复方案（已实施）

#### 1. 禁用不必要的大内存服务

netdata（曾被 OOM 杀 12 次）和 haproxy 都未在使用（haproxy 只做了个无用的示例
HTTP 代理，转发到不存在的 `192.168.1.10/20`），直接禁用释放内存：

```bash
/etc/init.d/netdata stop && /etc/init.d/netdata disable
/etc/init.d/haproxy stop && /etc/init.d/haproxy disable
```

> 效果：swap 使用量从 ~78MB 降到 ~25MB。

#### 2. 保护 clash 进程免于被 OOM 杀掉（核心）

给 clash 进程设 `oom_score_adj=-800`，让 OOM-killer **优先杀其它进程而不是 clash**，
从根源上避免「clash 被杀→watchdog 拉起→又被杀」的循环。

- **立即生效**（对当前进程）：

  ```bash
  CLASH_PID=$(pidof clash)
  echo -800 > /proc/$CLASH_PID/oom_score_adj
  ```

- **持久化**（写入 watchdog 脚本，clash 每次重启后自动重新设置）：
  已修改 `/usr/share/openclash/openclash_watchdog.sh`，在 `capsh ... nohup $CLASH ...` 启动、
  `sleep 3` 之后插入：

  ```bash
  CLASH_PID=$(pidof clash)
  [ -n "$CLASH_PID" ] && echo -800 > /proc/$CLASH_PID/oom_score_adj 2>/dev/null
  ```

  > 备份文件：`/usr/share/openclash/openclash_watchdog.sh.bak`

### 验证

```bash
# 1. watchdog 脚本语法
sh -n /usr/share/openclash/openclash_watchdog.sh && echo OK

# 2. clash 存活且已受保护（oom_score_adj 应为 -800）
CLASH_PID=$(pidof clash); cat /proc/$CLASH_PID/oom_score_adj

# 3. 服务自启状态（netdata/haproxy 应为 disabled，openclash 为 enabled）
for s in netdata haproxy openclash; do echo -n "$s: "; /etc/init.d/$s enabled 2>/dev/null && echo enabled || echo disabled; done
```

### 注意点

- **升级 OpenClash / 重装插件后，`openclash_watchdog.sh` 的修改会丢失**，需重新执行
  第二步的持久化插入（或按本节脚本重做一遍）。
- `oom_score_adj` 取值范围 `-1000 ~ 1000`，越小越「受保护」。设 `-800` 是折中：
  既让 clash 基本不会被 OOM 杀，又保留极端内存耗尽时内核仍能强制回收的最后手段
  （不建议直接设 `-1000`，那会让内核在真泄漏时无进程可杀、只能 panic）。
- 若未来内存仍紧张，可进一步：减少 DNS 服务器数量（当前 6 个 DoH/DoT 较重）、
  精简 rule-providers（当前 4 个远程 .mrs）、或增大 zram（当前 114MB）。
