#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复2c：本地精确修改 watchdog 脚本，插入 oom 保护代码后上传。"""
import paramiko

HOST = "192.168.100.1"
USER = "root"
PWD = "password"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PWD, timeout=15,
          allow_agent=False, look_for_keys=False)

# 1. 下载 watchdog 脚本
sftp = c.open_sftp()
local = "openclash_watchdog.sh"
sftp.get("/usr/share/openclash/openclash_watchdog.sh", local)
print("已下载 watchdog 脚本")

# 2. 读取并精确修改
with open(local, "r", encoding="utf-8") as f:
    content = f.read()

# 锚点：capsh 启动行（唯一）
anchor = 'capsh --caps="${capabilties}+eip"'
if anchor not in content:
    print("错误：未找到 capsh 启动行")
    c.close()
    exit(1)

# 找到 capsh 行，在其后的 sleep 3 行后插入 oom 保护
lines = content.split("\n")
inserted = False
for i, line in enumerate(lines):
    # 找到 capsh 启动行之后的 sleep 3 行
    if line.strip() == "sleep 3" and i > 0 and "capsh" in lines[i - 1] and i - 1 >= 0:
        # 更精确：找 capsh 启动行之后最近的 sleep 3
        pass

# 用更直接的方式：定位 capsh 行索引，向后找 sleep 3
capsh_idx = None
for i, line in enumerate(lines):
    if anchor in line:
        capsh_idx = i
        break

if capsh_idx is None:
    print("错误：未找到 capsh 行索引")
    c.close()
    exit(1)

# 从 capsh 行向后找第一个 sleep 3
indent = ""
for j in range(capsh_idx + 1, capsh_idx + 5):
    if lines[j].strip() == "sleep 3":
        indent = lines[j][: len(lines[j]) - len(lines[j].lstrip())]
        # 在 sleep 3 之后插入
        insert_lines = [
            indent + 'CLASH_PID=$(pidof clash)',
            indent + '[ -n "$CLASH_PID" ] && echo -800 > /proc/$CLASH_PID/oom_score_adj 2>/dev/null',
        ]
        lines[j + 1:j + 1] = insert_lines
        inserted = True
        break

if not inserted:
    print("错误：未找到 sleep 3 行")
    c.close()
    exit(1)

new_content = "\n".join(lines)
with open(local, "w", encoding="utf-8", newline="\n") as f:
    f.write(new_content)
print("已插入 oom 保护代码")

# 3. 上传回路由器
sftp.put(local, "/usr/share/openclash/openclash_watchdog.sh")
print("已上传修改后的 watchdog")

# 4. 验证
i, o, e = c.exec_command("grep -n -B1 -A2 'oom_score_adj' /usr/share/openclash/openclash_watchdog.sh", timeout=60)
print("\n=== 验证插入结果 ===")
print(o.read().decode("utf-8", "replace"))

c.close()
