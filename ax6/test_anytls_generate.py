#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时切换主节点为 anytls，验证 generate_client.uc 能生成 anytls 出站，然后恢复。"""
import paramiko

HOST = "192.168.123.1"
USER = "root"
PWD = "password"


def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return out, err


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD,
                   timeout=10, allow_agent=False, look_for_keys=False)

    # 保存当前主节点
    out, _ = run(client, "uci get homeproxy.config.main_node")
    old_main = out.strip()
    print("当前主节点:", old_main)

    # 找第一个 anytls 节点 section
    out, _ = run(client, "uci show homeproxy | grep \"\\.type='anytls'\" | head -1")
    anytls_section = out.strip().split("=")[0]
    anytls_id = anytls_section.split(".")[1]
    print("anytls 节点 id:", anytls_id)

    # 临时切换主节点
    run(client, f"uci set homeproxy.config.main_node={anytls_id}")
    run(client, "uci commit homeproxy")

    # 生成配置
    out, err = run(client, "ucode -S /etc/homeproxy/scripts/generate_client.uc 2>&1")
    print("=== generate_client 输出 ===")
    print(out)
    if err.strip():
        print("STDERR:", err)

    # 检查生成的配置中 anytls 出站
    out, _ = run(client, "grep -n 'anytls\\|main-out\\|server_port\\|password' /var/run/homeproxy/sing-box-c.json")
    print("=== sing-box-c.json 关键字段 ===")
    print(out)

    # 恢复主节点
    run(client, f"uci set homeproxy.config.main_node={old_main}")
    run(client, "uci commit homeproxy")
    run(client, "ucode -S /etc/homeproxy/scripts/generate_client.uc 2>&1")
    print(f"=== 已恢复主节点: {old_main} ===")

    client.close()


if __name__ == "__main__":
    main()
