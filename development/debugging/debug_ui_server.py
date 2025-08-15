#!/usr/bin/env python3
"""
调试版本UI服务器 - 测试React是否能正常工作
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'debug_ui_test.html')

@app.route('/test')
def test():
    """简单的测试页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试页面</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>✅ Flask服务器正常运行</h1>
        <p>当前时间: <script>document.write(new Date().toLocaleString());</script></p>
        <p><a href="/">返回主页</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 启动调试版UI服务器...")
    print("🌐 主页: http://192.140.176.198:8089")
    print("🧪 测试页: http://192.140.176.198:8089/test")
    app.run(host='0.0.0.0', port=8089, debug=False)