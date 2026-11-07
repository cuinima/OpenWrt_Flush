#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复1：禁用 netdata + haproxy 释放内存。"""
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


for svc in ["netdata", "haproxy"]:
    code, out = run(f"/etc/init.d/{svc} stop")
    print(f"stop {svc}: exit={code} {out.strip()}")
    code, out = run(f"/etc/init.d/{svc} disable")
    print(f"disable {svc}: exit={code} {out.strip()}")

print("\n=== 释放后内存 ===")
code, out = run("free -m")
print(out)
c.close()
