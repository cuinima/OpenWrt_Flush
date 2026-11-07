#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 watchdog capsh 段精确缩进（用 sed -n l 显示行尾/制表符）。"""
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
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


print("=== sed -n '136,150l' 显示不可见字符 ===")
print(run("sed -n '136,150l' /usr/share/openclash/openclash_watchdog.sh"))
c.close()
