#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断7：确认 WAN 数量(mwan3 是否可关)、haproxy 用途、netdata 自启。"""
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


print("=== WAN 接口数量 ===")
print(run("uci -q show network 2>/dev/null | grep -E \"interface.*=.*'wan|'wan6?'\" | head; echo '---'; uci -q show mwan3 2>/dev/null | head -30"))

print("=== haproxy 配置用途 ===")
print(run("cat /etc/haproxy.cfg 2>/dev/null | grep -vE '^#|^$' | head -40"))

print("=== netdata 是否自启 ===")
print(run("ls -la /etc/rc.d/*netdata* 2>/dev/null; /etc/init.d/netdata enabled 2>/dev/null && echo 'netdata 开机自启'"))

print("=== 网络接口列表 ===")
print(run("ip -o link show 2>/dev/null | awk '{print $2}' | head -20"))

print("=== 当前连接跟踪表大小(内存) ===")
print(run("cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null; cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null"))

print("=== CPU 信息 ===")
print(run("cat /proc/cpuinfo | grep -E 'Hardware|model name' | head -3"))
c.close()
