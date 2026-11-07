#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenClash 路由器 (192.168.100.1) SSH 助手。"""
import sys
import paramiko

HOST = "192.168.100.1"
USER = "root"
PWD = "password"


def run(cmd, timeout=90):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PWD,
                       timeout=15, allow_agent=False, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        return code, out, err
    finally:
        client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ssh_helper_oc.py <命令>")
        sys.exit(1)
    cmd = " ".join(sys.argv[1:])
    code, out, err = run(cmd)
    print("=== EXIT:", code, "===")
    if out:
        print(out)
    if err:
        print("=== STDERR ===")
        print(err)
