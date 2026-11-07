#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过本地 HTTP 服务器 + 路由器 wget 部署 HomeProxy 上游文件（支持 anytls）。

用法:
    python deploy_homeproxy.py
"""
import os
import sys
import http.server
import socketserver
import threading
import time
import paramiko

HOST = "192.168.123.1"
USER = "root"
PWD = "password"
LOCAL_DIR = r"e:\openwrt\hp_deploy"
PORT = 8000

# 目标路径映射: 本地相对路径 -> 远端绝对路径
FILES = {
    "scripts/update_subscriptions.uc": "/etc/homeproxy/scripts/update_subscriptions.uc",
    "scripts/homeproxy.uc": "/etc/homeproxy/scripts/homeproxy.uc",
    "scripts/generate_client.uc": "/etc/homeproxy/scripts/generate_client.uc",
    "scripts/generate_server.uc": "/etc/homeproxy/scripts/generate_server.uc",
    "scripts/migrate_config.uc": "/etc/homeproxy/scripts/migrate_config.uc",
    "view/node.js": "/www/luci-static/resources/view/homeproxy/node.js",
    "view/client.js": "/www/luci-static/resources/view/homeproxy/client.js",
    "view/server.js": "/www/luci-static/resources/view/homeproxy/server.js",
    "view/status.js": "/www/luci-static/resources/view/homeproxy/status.js",
    "view/homeproxy.js": "/www/luci-static/resources/homeproxy.js",
}

WINDOWS_IP = "192.168.123.214"


def start_http_server():
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(LOCAL_DIR)
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    httpd = start_http_server()
    print(f"HTTP 服务器已启动: http://{WINDOWS_IP}:{PORT}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD,
                   timeout=10, allow_agent=False, look_for_keys=False)

    ok = True
    for local_rel, remote in FILES.items():
        base = os.path.basename(local_rel)
        tmp = f"/tmp/{base}"
        url = f"http://{WINDOWS_IP}:{PORT}/{local_rel}"
        cmd = (f"wget -q -O {tmp} {url} && "
               f"echo 'DL_OK {base}' || echo 'DL_FAIL {base}'")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", "replace")
        print(out.strip())

    # 校验并替换
    for local_rel, remote in FILES.items():
        base = os.path.basename(local_rel)
        tmp = f"/tmp/{base}"
        local_path = os.path.join(LOCAL_DIR, local_rel)
        local_md5 = _md5_file(local_path)
        cmd = (f"remote_md5=$(md5sum {tmp} | awk '{{print $1}}'); "
               f"if [ \"$remote_md5\" = \"{local_md5}\" ]; then "
               f"cp -f {tmp} {remote} && chmod 755 {remote} 2>/dev/null; "
               f"echo 'OK {base}'; "
               f"else echo 'MD5_MISMATCH {base} local={local_md5} remote='$remote_md5; fi")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", "replace")
        print(out.strip())

    # 验证 anytls 是否生效
    print("\n=== 验证 anytls 支持 ===")
    stdin, stdout, stderr = client.exec_command(
        "grep -c anytls /etc/homeproxy/scripts/update_subscriptions.uc; "
        "grep -c anytls /etc/homeproxy/scripts/generate_client.uc; "
        "grep -c anytls /www/luci-static/resources/view/homeproxy/node.js"
    )
    print(stdout.read().decode("utf-8", "replace"))

    client.close()
    httpd.shutdown()


def _md5_file(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    main()
