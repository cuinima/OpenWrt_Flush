#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 python repr 精确显示 capsh 启动段的原始字符。"""
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
    return o.read().decode("utf-8", "replace")


# 用 awk 定位 capsh 行，然后 cat 显示
print("=== 找到 capsh 启动行的行号 ===")
print(run("grep -n 'capsh' /usr/share/openclash/openclash_watchdog.sh"))

print("\n=== 用 od 显示该行十六进制(前200字节) ===")
# 直接 grep 到 capsh 那一行，显示 repr
print(run("""python3 - <<'EOF'
with open('/usr/share/openclash/openclash_watchdog.sh') as f:
    for i, line in enumerate(f, 1):
        if 'capsh' in line and 'nohup' in line:
            print(i, repr(line))
            # 打印前后各2行
        elif 140 <= i <= 146:
            print(i, repr(line))
EOF"""))
c.close()
