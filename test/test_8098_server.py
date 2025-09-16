#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的测试服务器用于调试8098问题
"""

from flask import Flask, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域

@app.route('/')
def index():
    return send_file('test_8098_browser.html')

if __name__ == '__main__':
    print("测试服务器启动在 http://0.0.0.0:8099")
    print("请访问 http://202.140.143.88:8099 进行测试")
    app.run(host='0.0.0.0', port=8099, debug=True)