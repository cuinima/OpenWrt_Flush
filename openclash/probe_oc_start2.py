#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找 clash 进程实际启动位置。"""
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


print("=== openclash.sh 中启动 core 的部分 ===")
print(run("grep -nE '\\$CLASH|\\$\\{CLASH\\}|clash_meta|nohup|start-stop-daemon|su .*nobody' /usr/share/openclash/openclash.sh"))

print("\n=== openclash.sh 中 nohup 启动上下文 ===")
print(run("grep -n 'nohup' /usr/share/openclash/openclash.sh"))
c.close()
