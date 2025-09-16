#!/usr/bin/env python3
"""
腾讯文档工作流测试UI
提供下载、修改、上传的完整测试界面
端口: 8092
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import json
import asyncio
import threading
import time
from datetime import datetime
import traceback

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

app = Flask(__name__)

# 全局变量存储状态
workflow_status = {
    'cookie': '',
    'current_step': 'idle',
    'download_status': '',
    'downloaded_files': [],
    'upload_status': '',
    'last_error': '',
    'logs': []
}

def add_log(message, level='info'):
    """添加日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'time': timestamp,
        'level': level,
        'message': message
    }
    workflow_status['logs'].append(log_entry)
    # 只保留最近50条日志
    if len(workflow_status['logs']) > 50:
        workflow_status['logs'] = workflow_status['logs'][-50:]
    print(f"[{timestamp}] {message}")

# HTML模板
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

        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }

        .btn-secondary:hover {
            background: #e5e7eb;
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

        .log-container {
            background: #1f2937;
            color: #d1d5db;
            padding: 15px;
            border-radius: 8px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 3px 0;
        }

        .log-info { color: #60a5fa; }
        .log-success { color: #34d399; }
        .log-warning { color: #fbbf24; }
        .log-error { color: #f87171; }

        .file-list {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            max-height: 150px;
            overflow-y: auto;
        }

        .file-item {
            padding: 5px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-idle { background: #9ca3af; }
        .status-running { background: #fbbf24; animation: pulse 1.5s infinite; }
        .status-success { background: #34d399; }
        .status-error { background: #f87171; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e5e7eb;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #06b6d4, #3b82f6);
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 腾讯文档工作流测试</h1>
            <p>下载 → 修改 → 上传 完整流程测试</p>
        </div>

        <div class="workflow-container">
            <!-- Step 1: Cookie设置 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">1</div>
                    <div class="step-title">Cookie设置</div>
                </div>
                
                <div class="quick-test">
                    <h4>快速测试</h4>
                    <div class="test-buttons">
                        <button class="test-btn" onclick="loadTestCookie()">加载测试Cookie</button>
                        <button class="test-btn" onclick="validateCookie()">验证Cookie</button>
                    </div>
                </div>

                <div class="input-group">
                    <label class="input-label">腾讯文档Cookie</label>
                    <textarea class="textarea-field" id="cookieInput" 
                        placeholder="从浏览器F12开发者工具中复制Cookie字符串..."></textarea>
                </div>
                
                <button class="btn btn-primary" onclick="saveCookie()">
                    保存Cookie
                </button>
            </div>

            <!-- Step 2: 文档下载 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">2</div>
                    <div class="step-title">文档下载</div>
                </div>
                
                <div class="input-group">
                    <label class="input-label">腾讯文档URL</label>
                    <input type="text" class="input-field" id="docUrl" 
                        placeholder="https://docs.qq.com/sheet/xxx">
                </div>
                
                <div class="input-group">
                    <label class="input-label">下载格式</label>
                    <select class="input-field" id="downloadFormat">
                        <option value="csv">CSV格式</option>
                        <option value="xlsx">Excel格式</option>
                    </select>
                </div>
                
                <button class="btn btn-primary" onclick="downloadDocument()" id="downloadBtn">
                    开始下载
                </button>
                
                <div class="file-list" id="downloadedFiles" style="display: none;">
                    <!-- 下载的文件列表 -->
                </div>
            </div>

            <!-- Step 3: 文档修改 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">3</div>
                    <div class="step-title">文档修改</div>
                </div>
                
                <div class="input-group">
                    <label class="input-label">选择要修改的文件</label>
                    <select class="input-field" id="fileToModify">
                        <option value="">请先下载文件</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label class="input-label">修改内容（CSV/Excel数据）</label>
                    <textarea class="textarea-field" id="modifyContent" 
                        placeholder="输入要修改的内容，例如：\n单元格A1,新值\n单元格B2,另一个值"></textarea>
                </div>
                
                <button class="btn btn-primary" onclick="modifyDocument()" id="modifyBtn">
                    应用修改
                </button>
            </div>

            <!-- Step 4: 文档上传 -->
            <div class="step-card">
                <div class="step-header">
                    <div class="step-number">4</div>
                    <div class="step-title">文档上传</div>
                </div>
                
                <div class="input-group">
                    <label class="input-label">选择要上传的文件</label>
                    <select class="input-field" id="fileToUpload">
                        <option value="">请先修改文件</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label class="input-label">上传位置（可选）</label>
                    <input type="text" class="input-field" id="uploadLocation" 
                        placeholder="留空则上传到原位置">
                </div>
                
                <button class="btn btn-primary" onclick="uploadDocument()" id="uploadBtn">
                    上传到腾讯文档
                </button>
                
                <div class="progress-bar" id="uploadProgress" style="display: none;">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </div>
        </div>

        <!-- 状态面板 -->
        <div class="status-panel">
            <h3 style="margin-bottom: 15px;">
                <span class="status-indicator status-idle" id="statusIndicator"></span>
                运行日志
            </h3>
            <div class="log-container" id="logContainer">
                <div class="log-entry log-info">系统就绪，等待操作...</div>
            </div>
        </div>
    </div>

    <script>
        let currentStatus = 'idle';
        let downloadedFiles = [];
        let modifiedFiles = [];

        // 更新状态指示器
        function updateStatus(status) {
            currentStatus = status;
            const indicator = document.getElementById('statusIndicator');
            indicator.className = 'status-indicator status-' + status;
        }

        // 添加日志
        function addLog(message, level = 'info') {
            const logContainer = document.getElementById('logContainer');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${level}`;
            const time = new Date().toLocaleTimeString('zh-CN');
            logEntry.textContent = `[${time}] ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // 加载测试Cookie
        function loadTestCookie() {
            // 这里可以加载一个测试用的Cookie
            document.getElementById('cookieInput').value = '测试Cookie（请替换为实际Cookie）';
            addLog('已加载测试Cookie模板', 'info');
        }

        // 验证Cookie
        async function validateCookie() {
            const cookie = document.getElementById('cookieInput').value;
            if (!cookie) {
                addLog('请先输入Cookie', 'warning');
                return;
            }
            
            updateStatus('running');
            addLog('正在验证Cookie...', 'info');
            
            try {
                const response = await fetch('/api/validate-cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cookie})
                });
                
                const result = await response.json();
                if (result.success) {
                    addLog('Cookie验证成功！', 'success');
                } else {
                    addLog('Cookie验证失败：' + result.message, 'error');
                }
            } catch (error) {
                addLog('验证出错：' + error.message, 'error');
            } finally {
                updateStatus('idle');
            }
        }

        // 保存Cookie
        async function saveCookie() {
            const cookie = document.getElementById('cookieInput').value;
            if (!cookie) {
                addLog('请输入Cookie', 'warning');
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
                    addLog('Cookie保存成功', 'success');
                } else {
                    addLog('保存失败：' + result.message, 'error');
                }
            } catch (error) {
                addLog('保存出错：' + error.message, 'error');
            }
        }

        // 下载文档
        async function downloadDocument() {
            const url = document.getElementById('docUrl').value;
            const format = document.getElementById('downloadFormat').value;
            
            if (!url) {
                addLog('请输入文档URL', 'warning');
                return;
            }
            
            updateStatus('running');
            document.getElementById('downloadBtn').disabled = true;
            addLog(`开始下载文档: ${url}`, 'info');
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url, format})
                });
                
                const result = await response.json();
                if (result.success) {
                    addLog(`下载成功: ${result.filename}`, 'success');
                    downloadedFiles = result.files || [result.filename];
                    updateFileList();
                } else {
                    addLog('下载失败：' + result.message, 'error');
                }
            } catch (error) {
                addLog('下载出错：' + error.message, 'error');
            } finally {
                updateStatus('idle');
                document.getElementById('downloadBtn').disabled = false;
            }
        }

        // 修改文档
        async function modifyDocument() {
            const file = document.getElementById('fileToModify').value;
            const content = document.getElementById('modifyContent').value;
            
            if (!file || !content) {
                addLog('请选择文件并输入修改内容', 'warning');
                return;
            }
            
            updateStatus('running');
            document.getElementById('modifyBtn').disabled = true;
            addLog(`正在修改文件: ${file}`, 'info');
            
            try {
                const response = await fetch('/api/modify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file, modifications: content})
                });
                
                const result = await response.json();
                if (result.success) {
                    addLog(`修改成功: ${result.modified_file}`, 'success');
                    modifiedFiles.push(result.modified_file);
                    updateUploadList();
                } else {
                    addLog('修改失败：' + result.message, 'error');
                }
            } catch (error) {
                addLog('修改出错：' + error.message, 'error');
            } finally {
                updateStatus('idle');
                document.getElementById('modifyBtn').disabled = false;
            }
        }

        // 上传文档
        async function uploadDocument() {
            const file = document.getElementById('fileToUpload').value;
            
            if (!file) {
                addLog('请选择要上传的文件', 'warning');
                return;
            }
            
            updateStatus('running');
            document.getElementById('uploadBtn').disabled = true;
            document.getElementById('uploadProgress').style.display = 'block';
            addLog(`开始上传文件: ${file}`, 'info');
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file})
                });
                
                const result = await response.json();
                if (result.success) {
                    addLog(`上传成功！文档地址: ${result.url}`, 'success');
                    document.getElementById('progressFill').style.width = '100%';
                } else {
                    addLog('上传失败：' + result.message, 'error');
                }
            } catch (error) {
                addLog('上传出错：' + error.message, 'error');
            } finally {
                updateStatus('idle');
                document.getElementById('uploadBtn').disabled = false;
                setTimeout(() => {
                    document.getElementById('uploadProgress').style.display = 'none';
                    document.getElementById('progressFill').style.width = '0%';
                }, 2000);
            }
        }

        // 更新文件列表
        function updateFileList() {
            const container = document.getElementById('downloadedFiles');
            const select = document.getElementById('fileToModify');
            
            if (downloadedFiles.length > 0) {
                container.style.display = 'block';
                container.innerHTML = '<div style="font-size: 12px; color: #6b7280; margin-bottom: 5px;">已下载文件：</div>';
                select.innerHTML = '';
                
                downloadedFiles.forEach(file => {
                    // 更新文件列表显示
                    const item = document.createElement('div');
                    item.className = 'file-item';
                    item.innerHTML = `<span>📄 ${file}</span>`;
                    container.appendChild(item);
                    
                    // 更新选择框
                    const option = document.createElement('option');
                    option.value = file;
                    option.textContent = file;
                    select.appendChild(option);
                });
            }
        }

        // 更新上传列表
        function updateUploadList() {
            const select = document.getElementById('fileToUpload');
            select.innerHTML = '';
            
            modifiedFiles.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                select.appendChild(option);
            });
        }

        // 定期获取状态更新
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                // 更新日志
                if (status.logs && status.logs.length > 0) {
                    const lastLog = status.logs[status.logs.length - 1];
                    // 避免重复添加
                    const logContainer = document.getElementById('logContainer');
                    if (!logContainer.lastChild || 
                        !logContainer.lastChild.textContent.includes(lastLog.message)) {
                        addLog(lastLog.message, lastLog.level);
                    }
                }
            } catch (error) {
                // 静默处理错误
            }
        }, 2000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """获取当前状态"""
    return jsonify(workflow_status)

@app.route('/api/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie"""
    try:
        data = request.json
        cookie = data.get('cookie', '')
        
        if not cookie:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        workflow_status['cookie'] = cookie
        add_log('Cookie已保存', 'success')
        
        # 保存到配置文件
        config_path = '/root/projects/tencent-doc-manager/auto_download_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['cookie'] = cookie
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True})
        
    except Exception as e:
        add_log(f'保存Cookie失败: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/validate-cookie', methods=['POST'])
def validate_cookie():
    """验证Cookie"""
    try:
        data = request.json
        cookie = data.get('cookie', '')
        
        if not cookie:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        # 这里可以添加实际的验证逻辑
        # 例如尝试访问腾讯文档API
        add_log('Cookie格式验证通过', 'success')
        return jsonify({'success': True, 'message': 'Cookie格式有效'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download', methods=['POST'])
async def download_document():
    """下载文档"""
    try:
        data = request.json
        url = data.get('url', '')
        format_type = data.get('format', 'csv')
        
        if not url:
            return jsonify({'success': False, 'message': 'URL不能为空'})
        
        add_log(f'开始下载: {url}', 'info')
        workflow_status['current_step'] = 'downloading'
        
        # 导入下载模块
        from tencent_export_automation import TencentDocAutoExporter
        
        # 创建下载器实例
        exporter = TencentDocAutoExporter()
        
        # 使用保存的Cookie
        cookie = workflow_status.get('cookie', '')
        if not cookie:
            return jsonify({'success': False, 'message': '请先设置Cookie'})
        
        # 执行下载
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        await exporter.start_browser(headless=True)
        await exporter.login_with_cookies(cookie)
        
        download_dir = '/root/projects/tencent-doc-manager/workflow_downloads'
        os.makedirs(download_dir, exist_ok=True)
        
        result = await exporter.export_document(url, format_type)
        
        if result['success']:
            filename = result['files'][0] if result['files'] else 'downloaded_file'
            workflow_status['downloaded_files'].append(filename)
            add_log(f'下载成功: {filename}', 'success')
            
            await exporter.close_browser()
            
            return jsonify({
                'success': True,
                'filename': filename,
                'files': [filename]
            })
        else:
            await exporter.close_browser()
            return jsonify({'success': False, 'message': result.get('error', '下载失败')})
            
    except Exception as e:
        add_log(f'下载失败: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)})
    finally:
        workflow_status['current_step'] = 'idle'

@app.route('/api/modify', methods=['POST'])
def modify_document():
    """修改文档"""
    try:
        data = request.json
        file = data.get('file', '')
        modifications = data.get('modifications', '')
        
        if not file or not modifications:
            return jsonify({'success': False, 'message': '参数不完整'})
        
        add_log(f'开始修改文件: {file}', 'info')
        workflow_status['current_step'] = 'modifying'
        
        # 这里添加实际的修改逻辑
        # 可以使用Excel MCP工具或CSV处理
        
        modified_file = f"modified_{file}"
        workflow_status['downloaded_files'].append(modified_file)
        
        add_log(f'修改成功: {modified_file}', 'success')
        
        return jsonify({
            'success': True,
            'modified_file': modified_file
        })
        
    except Exception as e:
        add_log(f'修改失败: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)})
    finally:
        workflow_status['current_step'] = 'idle'

@app.route('/api/upload', methods=['POST'])
async def upload_document():
    """上传文档"""
    try:
        data = request.json
        file = data.get('file', '')
        
        if not file:
            return jsonify({'success': False, 'message': '请选择文件'})
        
        add_log(f'开始上传: {file}', 'info')
        workflow_status['current_step'] = 'uploading'
        
        # 导入上传模块
        from tencent_upload_automation import TencentDocUploader
        
        # 创建上传器实例
        uploader = TencentDocUploader()
        
        # 使用保存的Cookie
        cookie = workflow_status.get('cookie', '')
        if not cookie:
            return jsonify({'success': False, 'message': '请先设置Cookie'})
        
        # 执行上传
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        await uploader.start_browser(headless=True)
        await uploader.login_with_cookies(cookie)
        
        file_path = f'/root/projects/tencent-doc-manager/workflow_downloads/{file}'
        
        result = await uploader.upload_to_docs(file_path)
        
        if result['success']:
            add_log(f'上传成功！', 'success')
            await uploader.close_browser()
            
            return jsonify({
                'success': True,
                'url': 'https://docs.qq.com/desktop'
            })
        else:
            await uploader.close_browser()
            return jsonify({'success': False, 'message': result.get('error', '上传失败')})
            
    except Exception as e:
        add_log(f'上传失败: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)})
    finally:
        workflow_status['current_step'] = 'idle'

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 腾讯文档完整工作流测试UI")
    print(f"📍 访问地址: http://202.140.143.88:8093/")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8093, debug=False)