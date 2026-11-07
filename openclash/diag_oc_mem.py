#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenClash 崩溃诊断：内存/swap/进程详细占用。"""
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
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    return out + err


print("=== 内存概况 ===")
print(run("free -m"))
print("=== 各进程内存(rss/swap) 排序 ===")
print(run("""for d in /proc/[0-9]*; do
  pid=${d#/proc/}
  [ -d "$d" ] || continue
  rss=$(awk '/VmRSS/{print $2}' $d/status 2>/dev/null)
  sw=$(awk '/VmSwap/{print $2}' $d/status 2>/dev/null)
  name=$(cat $d/comm 2>/dev/null)
  echo "$rss $sw $pid $name"
done | sort -rn | head -20"""))
print("=== clash 当前进程 ===")
print(run("ps w | grep -iE 'clash|mihomo' | grep -v grep"))
print("=== watchdog 进程 ===")
print(run("ps w | grep watchdog | grep -v grep"))
print("=== /etc/openclash 目录占用 ===")
print(run("du -sh /etc/openclash/* 2>/dev/null | sort -rh | head -20"))
print("=== /tmp 占用 ===")
print(run("du -sh /tmp/* 2>/dev/null | sort -rh | head -15"))
print("=== overlay 空间 ===")
print(run("df -h /overlay /tmp / 2>/dev/null"))
c.close()
