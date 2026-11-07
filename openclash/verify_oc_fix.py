#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证：watchdog 语法、clash 存活、内存状态。"""
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


print("=== watchdog 脚本语法检查 ===")
code, out = run("sh -n /usr/share/openclash/openclash_watchdog.sh && echo '语法 OK'")
print(f"exit={code} {out.strip()}")

print("\n=== clash 进程存活 ===")
code, out = run("ps w | grep '/etc/openclash/clash' | grep -v grep")
print(out)

print("\n=== clash oom 保护状态 ===")
code, out = run("CLASH_PID=$(pidof clash); echo PID=$CLASH_PID; cat /proc/$CLASH_PID/oom_score_adj")
print(out)

print("\n=== 当前内存 ===")
code, out = run("free -m")
print(out)

print("\n=== 最近 watchdog 重启日志 ===")
code, out = run("grep 'Watchdog: Clash Core Problem' /tmp/openclash.log 2>/dev/null | tail -3")
print(out or "(无重启记录)")

print("\n=== 开机自启状态 ===")
code, out = run("for s in netdata haproxy openclash; do echo -n \"$s: \"; /etc/init.d/$s enabled 2>/dev/null && echo enabled || echo disabled; done")
print(out)
c.close()
