#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复2：设置 clash oom_score_adj=-800 保护进程，并持久化到 watchdog 脚本。"""
import paramiko

HOST = "192.168.100.1"
USER = "root"
PWD = "password"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PWD, timeout=15,
          allow_agent=False, look_for_keys=False)


def run(cmd):
    i, o, e = c.exec_command(cmd, timeout=90)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out + err


# 1. 立即对当前 clash 进程生效
code, out = run("CLASH_PID=$(pidof clash); echo \"当前 clash PID: $CLASH_PID\"; echo -800 > /proc/$CLASH_PID/oom_score_adj 2>/dev/null && echo 'oom_score_adj 已设为 -800'")
print(out)

print("\n=== 验证当前 oom_score_adj ===")
code, out = run("CLASH_PID=$(pidof clash); cat /proc/$CLASH_PID/oom_score_adj; cat /proc/$CLASH_PID/oom_score")
print(out)

# 2. 备份 watchdog 脚本
code, out = run("cp -a /usr/share/openclash/openclash_watchdog.sh /usr/share/openclash/openclash_watchdog.sh.bak 2>/dev/null && echo 'watchdog 已备份'")
print(out)

# 3. 在 watchdog 启动 clash 后的 sleep 3 处插入 oom 保护
# 原行: "              sleep 3"
# 在其后插入设置 oom_score_adj 的代码
patch = r'''              sleep 3
              CLASH_PID=$(pidof clash)
              [ -n "$CLASH_PID" ] && echo -800 > /proc/$CLASH_PID/oom_score_adj 2>/dev/null'''

# 用 sed 精确替换第一个 sleep 3（在 capsh 启动之后）
sed_cmd = (
    "sed -i 's|^              sleep 3$|"
    "              sleep 3\\n"
    "              CLASH_PID=$(pidof clash)\\n"
    "              [ -n \"$CLASH_PID\" ] && echo -800 > /proc/$CLASH_PID/oom_score_adj 2>/dev/null|' "
    "/usr/share/openclash/openclash_watchdog.sh"
)
code, out = run(sed_cmd)
print(f"\nsed 替换 exit={code}: {out.strip()}")

print("\n=== 验证替换结果 ===")
code, out = run("grep -n -A2 'sleep 3' /usr/share/openclash/openclash_watchdog.sh | head -20")
print(out)
c.close()
