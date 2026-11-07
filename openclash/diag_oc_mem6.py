#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断6：确认可精简服务的运行状态和内存。"""
import paramiko

HOST = "192.168.100.1"
USER = "root"
PWD = "password"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PWD, timeout=15,
          allow_agent=False, look_for_keys=False)


def run(cmd):
    i, o, e = c.exec_command(cmd, timeout=60)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


print("=== 各服务进程状态 ===")
for svc in ["netdata", "ss-redir", "ss-server", "shadowsocks", "microsocks", "mwan3", "zerotier", "haproxy", "ttyd", "mtkhqos", "eqos", "turboacc"]:
    out = run(f"ps w | grep -iE '{svc}' | grep -v grep | head -3")
    if out.strip():
        print(f"[运行中] {svc}:")
        print("  " + out.strip().replace("\n", "\n  "))
    else:
        print(f"[未运行] {svc}")

print("\n=== 物理内存真实大小 ===")
print(run("cat /proc/meminfo | grep -E 'MemTotal|MemAvailable|MemFree'"))

print("\n=== zram 当前占物理内存 ===")
print(run("cat /sys/block/zram0/compr_data_size 2>/dev/null | awk '{print \"压缩后:\", $1/1024/1024, \"MB\"}'"))
print(run("cat /sys/block/zram0/mem_used_total 2>/dev/null | awk '{print \"实际占内存:\", $1/1024/1024, \"MB\"}'"))

print("\n=== clash 规则集 mrs 缓存文件 ===")
print(run("find /etc/openclash -name '*.mrs' -o -name '*.db' 2>/dev/null | head; ls -lh /etc/openclash/cache 2>/dev/null"))

print("\n=== watchdog 重启日志统计 ===")
print(run("grep -c 'Watchdog: Clash Core Problem' /tmp/openclash.log 2>/dev/null"))
print(run("grep 'Watchdog: Clash Core Problem' /tmp/openclash.log 2>/dev/null | tail -5"))

print("\n=== OpenClash 设置: 是否开启 watchdog ===")
print(run("uci -q show openclash 2>/dev/null | grep -iE 'watchdog|watch_dog|enable_watchdog|core' | head"))
c.close()
