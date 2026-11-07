#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断4：mihomo版本、swap设备、内存增长趋势、DNS配置。"""
import paramiko, time

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


print("=== mihomo 内核版本 ===")
print(run("/etc/openclash/core/clash_meta -v 2>&1"))
print(run("ls -la /etc/openclash/clash /etc/openclash/core/ 2>&1"))

print("=== swap 设备 ===")
print(run("cat /proc/swaps; swapon -s 2>/dev/null; ls -la /swap* /etc/swap* 2>/dev/null"))

print("=== swap 配置 ===")
print(run("uci -q show fstab 2>/dev/null; cat /etc/config/fstab 2>/dev/null"))

print("=== clash 启动时间 ===")
print(run("cat /proc/19354/stat 2>/dev/null | awk '{print \"starttime_ticks=\"$22}'; cat /proc/uptime"))

print("=== 内存增长观察(间隔20秒采样3次) ===")
for i in range(3):
    print(run("awk '/VmRSS|VmSwap/{print}' /proc/19354/status 2>/dev/null | tr '\n' ' '; echo; free | awk 'NR==2{print \"free_mem=\"$4\" available=\"$7}'"))
    if i < 2:
        time.sleep(20)

print("=== 运行日志(最近clash输出) ===")
print(run("tail -40 /tmp/openclash.log 2>/dev/null"))

print("=== dns 配置(是否缓存泄漏) ===")
print(run("grep -nE 'dns:|enable:|cache|enhanced-mode|fake-ip|nameserver' /etc/openclash/config/smjc.yaml 2>/dev/null | head -40"))

print("=== 历史OOM统计(次数) ===")
print(run("logread 2>/dev/null | grep -c 'Out of memory: Killed process'"))
print(run("logread 2>/dev/null | grep 'Out of memory: Killed process' | awk '{print $NF}' | sort | uniq -c"))
c.close()
