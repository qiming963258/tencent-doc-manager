#!/usr/bin/env python3
"""
完全独立的原版热力图HTML文件生成器
"""
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 读取原版UI代码
try:
    with open('refer/热力图分析ui组件代码.txt', 'r', encoding='utf-8') as f:
        ui_code = f.read()
except:
    ui_code = ""

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档变更监控 - 热力图分析</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .heat-container {
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }
        .heat-container * {
            box-sizing: border-box;
        }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
''' + ui_code + '''

        // 渲染应用
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(AdvancedSortedHeatmap));
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("🚀 启动原版UI服务器...")
    print("🌐 访问地址: http://192.140.176.198:8089")
    app.run(host='0.0.0.0', port=8089, debug=False)