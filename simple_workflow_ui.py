#!/usr/bin/env python3
"""
腾讯文档工作流简化测试UI
提供基本的Cookie管理和文档操作界面
端口: 8092
"""

from flask import Flask, render_template_string, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# HTML模板 - 简化版
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档工作流测试</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 36px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .workflow-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .step-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .step-card:hover {
            transform: translateY(-5px);
        }

        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }

        .step-number {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }

        .step-title {
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
        }

        .input-group {
            margin-bottom: 15px;
        }

        .input-label {
            display: block;
            margin-bottom: 5px;
            color: #6b7280;
            font-size: 14px;
        }

        .input-field, .textarea-field {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }

        .textarea-field {
            min-height: 100px;
            resize: vertical;
            font-family: 'Courier New', monospace;
        }

        .input-field:focus, .textarea-field:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
        }

        .btn-primary {
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        .status-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .info-box {
            background: #f0f9ff;
            border: 2px solid #0ea5e9;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .info-box h4 {
            color: #0369a1;
            margin-bottom: 10px;
        }

        .info-box p {
            color: #0c4a6e;
            font-size: 14px;
            line-height: 1.6;
        }

        .command-box {
            background: #1f2937;
            color: #10b981;
            padding: 10px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin: 10px 0;
            overflow-x: auto;
        }

        .example-url {
            color: #60a5fa;
            text-decoration: none;
            font-size: 14px;
        }

        .example-url:hover {
            text-decoration: underline;
        }

        .status-message {
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 14px;
            display: none;
        }

        .status-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
            display: block;
        }

        .status-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
            display: block;
        }

        .quick-test {
            background: #fef3c7;
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .quick-test h4 {
            color: #92400e;
            margin-bottom: 10px;
        }

        .test-buttons {
            display: flex;
            gap: 10px;
        }

        .test-btn {
            flex: 1;
            padding: 8px 12px;
            background: white;
            border: 1px solid #fbbf24;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .test-btn:hover {
            background: #fef3c7;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 腾讯文档工作流测试</h1>
            <p>Cookie管理 → 下载配置 → 文档操作 测试界面</p>
        </div>

        <div class="workflow-container">
            <!-- Step 1: Cookie设置 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">1</div>
                    <div class="step-title">Cookie配置</div>
                </div>
                
                <div class="info-box">
                    <h4>获取Cookie方法</h4>
                    <p>1. 打开腾讯文档网站并登录</p>
                    <p>2. 按F12打开开发者工具</p>
                    <p>3. 切换到Network标签</p>
                    <p>4. 刷新页面，找到docs.qq.com请求</p>
                    <p>5. 复制Request Headers中的Cookie值</p>
                </div>

                <div class="input-group">
                    <label class="input-label">腾讯文档Cookie</label>
                    <textarea class="textarea-field" id="cookieInput" 
                        placeholder="粘贴完整的Cookie字符串..."></textarea>
                </div>
                
                <button class="btn btn-primary" onclick="saveCookie()">
                    保存Cookie到配置
                </button>
                
                <div class="status-message" id="cookieStatus"></div>
            </div>

            <!-- Step 2: 下载配置 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">2</div>
                    <div class="step-title">下载配置</div>
                </div>
                
                <div class="quick-test">
                    <h4>测试URL示例</h4>
                    <div class="test-buttons">
                        <button class="test-btn" onclick="setTestUrl()">使用测试URL</button>
                        <button class="test-btn" onclick="checkConfig()">检查配置</button>
                    </div>
                </div>

                <div class="input-group">
                    <label class="input-label">文档URL</label>
                    <input type="text" class="input-field" id="docUrl" 
                        placeholder="https://docs.qq.com/sheet/xxx">
                    <small style="color: #6b7280;">支持腾讯文档表格链接</small>
                </div>
                
                <div class="input-group">
                    <label class="input-label">下载格式</label>
                    <select class="input-field" id="downloadFormat">
                        <option value="csv">CSV格式</option>
                        <option value="xlsx">Excel格式</option>
                    </select>
                </div>
                
                <button class="btn btn-primary" onclick="saveDownloadConfig()">
                    保存下载配置
                </button>
                
                <div class="status-message" id="downloadStatus"></div>
            </div>

            <!-- Step 3: 操作指南 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">3</div>
                    <div class="step-title">运行下载任务</div>
                </div>
                
                <div class="info-box">
                    <h4>自动下载系统</h4>
                    <p>配置完成后，可以通过以下方式运行：</p>
                </div>
                
                <div class="command-box">
                    # 运行自动下载UI系统<br>
                    python3 auto_download_ui_system.py<br><br>
                    # 访问UI界面<br>
                    http://202.140.143.88:8090/
                </div>
                
                <button class="btn btn-primary" onclick="startDownloadSystem()">
                    启动下载系统
                </button>
                
                <div class="status-message" id="systemStatus"></div>
            </div>

            <!-- Step 4: 修改与上传 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">4</div>
                    <div class="step-title">文档修改与上传</div>
                </div>
                
                <div class="info-box">
                    <h4>Excel修改工具</h4>
                    <p>使用Excel MCP工具修改下载的文件：</p>
                </div>
                
                <div class="command-box">
                    # 查看下载的文件<br>
                    ls auto_downloads/<br><br>
                    # 使用Python修改Excel<br>
                    python3 -c "import excel_marker; ..."
                </div>
                
                <div class="info-box">
                    <h4>上传工具</h4>
                    <p>修改完成后，使用上传脚本：</p>
                </div>
                
                <div class="command-box">
                    # 运行上传脚本<br>
                    python3 测试版本-性能优化开发-20250811-001430/tencent_upload_automation.py
                </div>
                
                <button class="btn btn-primary" onclick="showWorkflow()">
                    查看完整工作流
                </button>
            </div>
        </div>

        <!-- 状态面板 -->
        <div class="status-panel">
            <h3>系统状态</h3>
            <div id="currentConfig" style="margin-top: 15px;">
                <p><strong>当前配置：</strong></p>
                <div class="command-box" id="configDisplay">
                    正在加载配置...
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h4>快速链接</h4>
                <p>
                    <a href="http://202.140.143.88:8090/" target="_blank" class="example-url">
                        🚀 自动下载UI系统 (8090)
                    </a>
                </p>
                <p>
                    <a href="http://202.140.143.88:8081/" target="_blank" class="example-url">
                        🤖 AI测试界面 (8081)
                    </a>
                </p>
                <p>
                    <a href="/api/config" target="_blank" class="example-url">
                        📋 查看当前配置
                    </a>
                </p>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时获取配置
        window.onload = function() {
            loadCurrentConfig();
        };

        // 加载当前配置
        async function loadCurrentConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                document.getElementById('configDisplay').innerHTML = 
                    JSON.stringify(config, null, 2);
                
                // 如果有配置，填充到表单
                if (config.cookie) {
                    document.getElementById('cookieInput').value = 
                        config.cookie.substring(0, 50) + '...';
                }
                if (config.urls && config.urls.length > 0) {
                    document.getElementById('docUrl').value = config.urls[0];
                }
                if (config.format) {
                    document.getElementById('downloadFormat').value = config.format;
                }
            } catch (error) {
                document.getElementById('configDisplay').textContent = 
                    '加载配置失败: ' + error.message;
            }
        }

        // 设置测试URL
        function setTestUrl() {
            document.getElementById('docUrl').value = 
                'https://docs.qq.com/sheet/DV3BFVmRXekhqeGxi';
            showStatus('downloadStatus', 'success', '已填入测试URL');
        }

        // 保存Cookie
        async function saveCookie() {
            const cookie = document.getElementById('cookieInput').value.trim();
            
            if (!cookie) {
                showStatus('cookieStatus', 'error', '请输入Cookie');
                return;
            }
            
            try {
                const response = await fetch('/api/save-cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cookie})
                });
                
                const result = await response.json();
                if (result.success) {
                    showStatus('cookieStatus', 'success', 'Cookie保存成功！');
                    loadCurrentConfig();
                } else {
                    showStatus('cookieStatus', 'error', '保存失败: ' + result.message);
                }
            } catch (error) {
                showStatus('cookieStatus', 'error', '保存出错: ' + error.message);
            }
        }

        // 保存下载配置
        async function saveDownloadConfig() {
            const url = document.getElementById('docUrl').value.trim();
            const format = document.getElementById('downloadFormat').value;
            
            if (!url) {
                showStatus('downloadStatus', 'error', '请输入文档URL');
                return;
            }
            
            try {
                const response = await fetch('/api/save-download-config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url, format})
                });
                
                const result = await response.json();
                if (result.success) {
                    showStatus('downloadStatus', 'success', '下载配置保存成功！');
                    loadCurrentConfig();
                } else {
                    showStatus('downloadStatus', 'error', '保存失败: ' + result.message);
                }
            } catch (error) {
                showStatus('downloadStatus', 'error', '保存出错: ' + error.message);
            }
        }

        // 检查配置
        async function checkConfig() {
            try {
                const response = await fetch('/api/check-config');
                const result = await response.json();
                
                if (result.valid) {
                    showStatus('downloadStatus', 'success', 
                        '配置有效！Cookie: ' + (result.has_cookie ? '✓' : '✗') + 
                        ', URLs: ' + result.url_count);
                } else {
                    showStatus('downloadStatus', 'error', '配置不完整: ' + result.message);
                }
            } catch (error) {
                showStatus('downloadStatus', 'error', '检查失败: ' + error.message);
            }
        }

        // 启动下载系统
        async function startDownloadSystem() {
            showStatus('systemStatus', 'success', 
                '下载系统已在8090端口运行，请访问 http://202.140.143.88:8090/');
            
            // 在新标签页打开
            window.open('http://202.140.143.88:8090/', '_blank');
        }

        // 显示工作流
        function showWorkflow() {
            alert('完整工作流：\\n\\n' +
                  '1. 设置Cookie（从浏览器复制）\\n' +
                  '2. 配置下载URL和格式\\n' +
                  '3. 访问8090端口启动自动下载\\n' +
                  '4. 下载完成后在auto_downloads目录查看文件\\n' +
                  '5. 使用Excel MCP工具修改文件\\n' +
                  '6. 运行上传脚本将修改后的文件上传回腾讯文档');
        }

        // 显示状态消息
        function showStatus(elementId, type, message) {
            const element = document.getElementById(elementId);
            element.className = 'status-message status-' + type;
            element.textContent = message;
            element.style.display = 'block';
            
            // 3秒后自动隐藏
            setTimeout(() => {
                element.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/config')
def get_config():
    """获取当前配置"""
    config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 隐藏敏感信息
        if config.get('cookie'):
            config['cookie'] = config['cookie'][:30] + '...' if len(config['cookie']) > 30 else config['cookie']
        return jsonify(config)
    else:
        return jsonify({
            'cookie': '',
            'urls': [],
            'format': 'csv',
            'interval': 60,
            'download_dir': '/root/projects/tencent-doc-manager/auto_downloads'
        })

@app.route('/api/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie"""
    try:
        data = request.json
        cookie = data.get('cookie', '').strip()
        
        if not cookie:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
        
        # 读取现有配置
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                'urls': [],
                'format': 'csv',
                'interval': 60,
                'download_dir': '/root/projects/tencent-doc-manager/auto_downloads'
            }
        
        # 更新Cookie
        config['cookie'] = cookie
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Cookie保存成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/save-download-config', methods=['POST'])
def save_download_config():
    """保存下载配置"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        format_type = data.get('format', 'csv')
        
        if not url:
            return jsonify({'success': False, 'message': 'URL不能为空'})
        
        if not url.startswith('https://docs.qq.com/'):
            return jsonify({'success': False, 'message': 'URL必须是腾讯文档链接'})
        
        config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
        
        # 读取现有配置
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                'cookie': '',
                'interval': 60,
                'download_dir': '/root/projects/tencent-doc-manager/auto_downloads'
            }
        
        # 更新URL和格式
        config['urls'] = [url]
        config['format'] = format_type
        
        # 确保下载目录存在
        os.makedirs(config['download_dir'], exist_ok=True)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': '下载配置保存成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/check-config')
def check_config():
    """检查配置是否有效"""
    try:
        config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
        
        if not os.path.exists(config_path):
            return jsonify({
                'valid': False,
                'message': '配置文件不存在',
                'has_cookie': False,
                'url_count': 0
            })
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        has_cookie = bool(config.get('cookie'))
        url_count = len(config.get('urls', []))
        
        valid = has_cookie and url_count > 0
        
        return jsonify({
            'valid': valid,
            'message': '配置完整' if valid else '缺少Cookie或URL',
            'has_cookie': has_cookie,
            'url_count': url_count
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': str(e),
            'has_cookie': False,
            'url_count': 0
        })

if __name__ == '__main__':
    print("🚀 腾讯文档工作流测试UI (简化版)")
    print("📍 访问地址: http://202.140.143.88:8092/")
    print("="*50)
    app.run(host='0.0.0.0', port=8092, debug=False)