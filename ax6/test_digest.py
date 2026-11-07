#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 ucode digest/md5 内置函数可用性（通过 base64 传输避免引号问题）。"""
import paramiko

HOST = "192.168.123.1"
USER = "root"
PWD = "password"


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD,
                   timeout=10, allow_agent=False, look_for_keys=False)

    test_script = "import { md5 } from 'digest'; print('md5(abc)=' + md5('abc')); print('md5()=' + md5(''));"
    cmd = "ucode -e \"" + test_script + "\""
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    print("STDOUT:", out)
    if err.strip():
        print("STDERR:", err)
    client.close()


if __name__ == "__main__":
    main()
