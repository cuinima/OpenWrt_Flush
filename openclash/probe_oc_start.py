#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查 OpenClash 启动机制，找到 clash 进程启动点。"""
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


print("=== OpenClash 核心脚本文件 ===")
print(run("ls -la /usr/share/openclash/ | head -40"))

print("\n=== 当前 clash 进程 ===")
print(run("ps w | grep '/etc/openclash/clash' | grep -v grep"))

print("\n=== watchdog 脚本关键内容 ===")
print(run("grep -nE 'start|core|clash_meta|/etc/openclash/clash' /usr/share/openclash/openclash_watchdog.sh 2>/dev/null | head -30"))

print("\n=== 启动脚本里启动 core 的部分 ===")
print(run("grep -rn 'clash_meta\\|core_type\\|start_core\\|/etc/openclash/clash' /usr/share/openclash/*.sh 2>/dev/null | head -30"))
c.close()
