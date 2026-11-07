#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断5：zram配置、可精简服务、rule-provider详情。"""
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


print("=== zram 配置 (system/fstab) ===")
print(run("grep -nE 'zram|zram_size|zram_comp' /etc/config/system 2>/dev/null"))
print(run("uci -q show system 2>/dev/null | grep -i zram"))
print(run("cat /etc/config/system 2>/dev/null | head -80"))

print("=== zram 设备实际大小 ===")
print(run("cat /sys/block/zram0/disksize 2>/dev/null; cat /sys/block/zram0/comp_algorithm 2>/dev/null; cat /sys/block/zram0/orig_data_size 2>/dev/null; cat /sys/block/zram0/compr_data_size 2>/dev/null"))

print("=== netdata 是否在运行 ===")
print(run("ps w | grep -iE 'netdata|collectd' | grep -v grep; opkg list-installed 2>/dev/null | grep -iE 'netdata|collectd'"))

print("=== 所有已安装但可能吃内存的服务 ===")
print(run("ls /etc/rc.d/S* 2>/dev/null | head -60"))

print("=== rule-providers 完整定义 ===")
print(run("sed -n '695,730p' /etc/openclash/config/smjc.yaml 2>/dev/null"))

print("=== rules 部分(看用了哪些 rule-set) ===")
print(run("awk '/^rules:/{f=1} f{print} /^[a-z-]+:$/ && f && NR>1{exit}' /etc/openclash/config/smjc.yaml 2>/dev/null | head -40"))

print("=== dns 完整配置 ===")
print(run("sed -n '14,50p' /etc/openclash/config/smjc.yaml 2>/dev/null"))

print("=== 当前 clash oom_score_adj ===")
print(run("cat /proc/19354/oom_score_adj 2>/dev/null; cat /proc/19354/oom_score 2>/dev/null"))
c.close()
