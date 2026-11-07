#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断3：clash 峰值内存 + rule-provider mrs 规则文件大小 + 进程泄漏。"""
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


print("=== clash 峰值内存 VmHWM/VmPeak ===")
print(run("grep -E 'VmHWM|VmPeak|VmSize|VmRSS|VmSwap' /proc/19354/status 2>/dev/null"))

print("=== .mrs 规则文件大小 (运行时加载进内存) ===")
print(run("find /etc/openclash -name '*.mrs' -exec ls -lh {} \\; 2>/dev/null"))
print(run("du -sh /etc/openclash/rule_set /etc/openclash/rule_provider 2>/dev/null"))

print("=== 规则集下载缓存目录 ===")
print(run("ls -lh /etc/openclash/*.mrs /etc/openclash/cache/* 2>/dev/null | head -20"))

print("=== 进程数统计(按名字) ===")
print(run("""for d in /proc/[0-9]*; do
  cat $d/comm 2>/dev/null
done | sort | uniq -c | sort -rn | head -20"""))

print("=== 是否有大量僵尸进程 ===")
print(run("ps w | awk '$3==\"Z\"{print $0}' | head -20"))
print("僵尸进程数:", run("ps w | awk '$3==\"Z\"' | wc -l"))

print("=== haproxy 是什么 ===")
print(run("ps w | grep haproxy | grep -v grep; opkg list-installed 2>/dev/null | grep -i haproxy"))

print("=== 全量 rule-providers 数量 ===")
print(run("grep -cE '^  [a-zA-Z_-]+:$' /etc/openclash/config/smjc.yaml 2>/dev/null"))
print(run("awk '/rule-providers:/{f=1} f&&/type: http/{n++} END{print \"http rule-provider 数量:\", n}' /etc/openclash/config/smjc.yaml"))

print("=== 订阅配置里启用的规则模式 ===")
print(run("uci -q show openclash 2>/dev/null | grep -iE 'rule|geo|provider|enable' | head -30"))
c.close()
