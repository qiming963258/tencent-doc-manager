#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器 - 用于测试AI列名标准化网页
"""

import http.server
import socketserver
import os

PORT = 8091
DIRECTORY = "/root/projects/tencent-doc-manager"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # 处理根路径
        if self.path == '/':
            self.path = '/test_column_standardization.html'
        # 处理直接访问
        elif self.path == '/test':
            self.path = '/test_column_standardization.html'
        return super().do_GET()

print(f"""
╔════════════════════════════════════════════╗
║   AI列名标准化测试平台（简单服务器）           ║
║   端口: {PORT}                              ║
║   目录: {DIRECTORY}                         ║
╚════════════════════════════════════════════╝

访问: http://localhost:{PORT}/test_column_standardization.html
""")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"服务器运行在端口 {PORT}")
    httpd.serve_forever()