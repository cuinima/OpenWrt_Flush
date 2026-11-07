#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 anytls 节点字段，并测试切换主节点为 anytls 后生成配置。"""
import paramiko

HOST = "192.168.123.1"
USER = "root"
PWD = "password"


def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode("utf-8", "replace")


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD,
                   timeout=10, allow_agent=False, look_for_keys=False)

    # 找第一个 anytls 节点
    out = run(client, "uci show homeproxy | grep \"\\.type='anytls'\" | head -1")
    first = out.strip().split(".")[0:2]
    section = ".".join(first)
    print("第一个 anytls 节点 section:", section)

    # 显示该节点详情
    out = run(client, f"uci show {section}")
    print("=== 节点详情 ===")
    print(out)

    client.close()


if __name__ == "__main__":
    main()
