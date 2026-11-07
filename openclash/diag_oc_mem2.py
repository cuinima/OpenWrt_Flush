#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断2：用户态进程内存 + clash 配置规模。"""
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


print("=== 用户态进程内存(仅非内核) ===")
print(run("""for d in /proc/[0-9]*; do
  pid=${d#/proc/}
  name=$(cat $d/comm 2>/dev/null)
  # 跳过内核线程(无 /proc/pid/maps 内容且 rss 来自内核的,kworker/ksoftirqd等)
  case "$name" in
    kworker*|ksoftirqd*|kthreadd*|rcu_*|watchdog*|migration*|irq/*|cpuhp*) continue ;;
  esac
  rss=$(awk '/VmRSS/{print $2}' $d/status 2>/dev/null)
  sw=$(awk '/VmSwap/{print $2}' $d/status 2>/dev/null)
  [ -z "$rss" ] && rss=0
  [ -z "$sw" ] && sw=0
  total=$((rss + sw))
  echo "$total ${rss}kB ${sw}kB $pid $name"
done | sort -rn | head -25"""))
print("=== 进程总数 ===")
print(run("ls /proc/[0-9]* 2>/dev/null | wc -l"))
print("=== clash 配置规模 ===")
print(run("ls -la /etc/openclash/smjc.yaml /etc/openclash/config/smjc.yaml 2>/dev/null"))
print(run("echo 'proxies/proxy-groups/rules 数量:'; grep -c 'name:' /etc/openclash/config/smjc.yaml 2>/dev/null; grep -c 'rules:' /etc/openclash/config/smjc.yaml 2>/dev/null; grep -cE 'RULE-SET|GEOSITE|GEOIP' /etc/openclash/config/smjc.yaml 2>/dev/null"))
print("=== geodata 文件大小 ===")
print(run("ls -lh /etc/openclash/*.mmdb /etc/openclash/*.dat /etc/openclash/GeoIP* /etc/openclash/GeoSite* /etc/openclash/rule_provider/* /etc/openclash/rule_set/* 2>/dev/null"))
print("=== rule-provider 定义 ===")
print(run("grep -nE 'rule-providers|behavior|type: http|url:' /etc/openclash/config/smjc.yaml 2>/dev/null | head -30"))
c.close()
