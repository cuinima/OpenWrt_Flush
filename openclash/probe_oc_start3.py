#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 watchdog 中实际启动 clash 的代码段。"""
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


print("=== watchdog 完整 100-220 行 ===")
print(run("sed -n '100,220p' /usr/share/openclash/openclash_watchdog.sh"))
c.close()
