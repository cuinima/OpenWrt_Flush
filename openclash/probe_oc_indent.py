#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复2b：精确查看 watchdog 中 capsh 启动段缩进，用 Python 精确插入。"""
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
    return out + err


print("=== cat -A 查看 capsh 段 (136-150行) ===")
print(run("sed -n '136,150p' /usr/share/openclash/openclash_watchdog.sh | cat -A"))
c.close()
