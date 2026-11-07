#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 SFTP 上传 sing-box 二进制到路由器 /tmp。"""
import paramiko

HOST = "192.168.123.1"
USER = "root"
PWD = "password"
LOCAL = r"e:\openwrt\sing-box-1.12.24-linux-arm64\sing-box"
REMOTE = "/tmp/sing-box-1.12.24"


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD,
                   timeout=10, allow_agent=False, look_for_keys=False)
    sftp = client.open_sftp()
    print("上传中 ...")
    sftp.put(LOCAL, REMOTE)
    sftp.chmod(REMOTE, 0o755)
    st = sftp.stat(REMOTE)
    print("上传完成, 远端大小 =", st.st_size, "字节")
    sftp.close()
    client.close()


if __name__ == "__main__":
    main()
