#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量下载 HomeProxy 上游 master 分支的关键文件。"""
import urllib.request

PROXY = "http://127.0.0.1:7890"
BASE = "https://raw.githubusercontent.com/immortalwrt/homeproxy/master/"

files = {
    "root/etc/homeproxy/scripts/update_subscriptions.uc": "upstream_update_subscriptions.uc",
    "root/etc/homeproxy/scripts/homeproxy.uc": "upstream_homeproxy.uc",
    "root/etc/homeproxy/scripts/generate_client.uc": "upstream_generate_client.uc",
    "root/etc/homeproxy/scripts/generate_server.uc": "upstream_generate_server.uc",
    "root/etc/homeproxy/scripts/firewall_pre.uc": "upstream_firewall_pre.uc",
    "root/etc/homeproxy/scripts/migrate_config.uc": "upstream_migrate_config.uc",
    "htdocs/luci-static/resources/view/homeproxy/node.js": "upstream_node.js",
    "htdocs/luci-static/resources/view/homeproxy/client.js": "upstream_client.js",
    "htdocs/luci-static/resources/view/homeproxy/server.js": "upstream_server.js",
    "htdocs/luci-static/resources/view/homeproxy/status.js": "upstream_status.js",
    "htdocs/luci-static/resources/homeproxy.js": "upstream_homeproxy.js",
}


def fetch(url):
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return opener.open(req, timeout=30).read()


for path, out in files.items():
    url = BASE + path
    data = fetch(url)
    with open(out, "wb") as f:
        f.write(data)
    print(f"{out} len={len(data)}")
