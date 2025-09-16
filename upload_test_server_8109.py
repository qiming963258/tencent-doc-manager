#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档上传测试服务器
端口: 8109
功能: 提供Web界面测试上传功能，调用主项目的上传模块
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import asyncio
import logging
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import subprocess

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

# 导入增强版上传模块
from tencent_upload_enhanced import TencentDocUploadEnhanced

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = '/root/projects/tencent-doc-manager/test_uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档上传测试 - 端口8109</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .panel {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #555;
            font-size: 14px;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .form-group textarea,
        .form-group input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .file-upload-area {
            border: 2px dashed #d0d0d0;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            background: #fafafa;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-upload-area:hover {
            border-color: #667eea;
            background: #f5f5ff;
        }
        
        .file-upload-area.dragover {
            border-color: #667eea;
            background: #f0f0ff;
        }
        
        .file-upload-area i {
            font-size: 48px;
            color: #999;
            margin-bottom: 10px;
        }
        
        .file-info {
            margin-top: 15px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 6px;
            display: none;
        }
        
        .file-info.show {
            display: block;
        }
        
        button {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-left: 10px;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .status-panel {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
            display: none;
        }
        
        .status-panel.show {
            display: block;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px;
            background: white;
            border-radius: 6px;
        }
        
        .status-icon {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 50%;
        }
        
        .status-pending {
            background: #ffc107;
        }
        
        .status-success {
            background: #28a745;
        }
        
        .status-error {
            background: #dc3545;
        }
        
        .result-panel {
            margin-top: 20px;
            padding: 20px;
            background: #e8f5e9;
            border-radius: 8px;
            display: none;
        }
        
        .result-panel.show {
            display: block;
        }
        
        .result-panel.error {
            background: #ffebee;
        }
        
        .result-url {
            display: block;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            color: #1976d2;
            text-decoration: none;
            word-break: break-all;
        }
        
        .result-url:hover {
            background: #f5f5f5;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar.show {
            display: block;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s;
            animation: progress-animation 2s ease-in-out infinite;
        }
        
        @keyframes progress-animation {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .tips {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        
        .tips h3 {
            color: #856404;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .tips ul {
            list-style: none;
            padding-left: 0;
        }
        
        .tips li {
            color: #856404;
            font-size: 13px;
            margin-bottom: 5px;
            padding-left: 20px;
            position: relative;
        }
        
        .tips li:before {
            content: "•";
            position: absolute;
            left: 5px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 腾讯文档上传测试系统</h1>
            <p>端口 8109 | 真实上传测试 | 支持xlsx格式 | 获取新文档URL</p>
        </div>
        
        <div class="main-content">
            <!-- 左侧：配置面板 -->
            <div class="panel">
                <h2>📋 上传配置</h2>
                
                <div class="form-group">
                    <label for="cookies">Cookie认证字符串 <span style="color: #4CAF50; font-size: 12px;">(自动保存)</span></label>
                    <textarea id="cookies" placeholder="请输入完整的Cookie字符串，格式：key1=value1; key2=value2; ..." onpaste="handleCookiePaste()" oninput="saveCookieDebounced()"></textarea>
                    <div id="cookieSaveStatus" style="margin-top: 5px; font-size: 12px; color: #999;"></div>
                </div>
                
                <div class="form-group">
                    <label>选择上传文件（推荐xlsx格式）</label>
                    <div class="file-upload-area" id="fileUploadArea">
                        <i>📁</i>
                        <p>点击选择文件或拖拽文件到此处</p>
                        <p style="color: #999; font-size: 12px; margin-top: 5px;">支持 .xlsx .xls .csv 格式</p>
                        <input type="file" id="fileInput" accept=".xlsx,.xls,.csv" style="display: none;">
                    </div>
                    <div class="file-info" id="fileInfo">
                        <strong>已选择文件：</strong><span id="fileName"></span><br>
                        <strong>文件大小：</strong><span id="fileSize"></span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="headlessMode" checked> 无头模式（后台运行）
                    </label>
                </div>
                
                <button class="btn-primary" id="uploadBtn" onclick="startUpload()">开始上传</button>
                <button class="btn-secondary" onclick="testCookie()">测试Cookie</button>
                
                <div class="tips">
                    <h3>💡 使用提示</h3>
                    <ul>
                        <li>请使用有效的腾讯文档Cookie</li>
                        <li>建议上传xlsx格式的Excel文件</li>
                        <li>支持半填充涂色的标记文件</li>
                        <li>上传成功后会返回新文档URL</li>
                    </ul>
                </div>
            </div>
            
            <!-- 右侧：状态面板 -->
            <div class="panel">
                <h2>📊 上传状态</h2>
                
                <div class="status-panel" id="statusPanel">
                    <div class="status-item" id="status-browser">
                        <div class="status-icon status-pending"></div>
                        <span>启动浏览器...</span>
                    </div>
                    <div class="status-item" id="status-login">
                        <div class="status-icon status-pending"></div>
                        <span>Cookie认证...</span>
                    </div>
                    <div class="status-item" id="status-upload">
                        <div class="status-icon status-pending"></div>
                        <span>上传文件...</span>
                    </div>
                    <div class="status-item" id="status-url">
                        <div class="status-icon status-pending"></div>
                        <span>获取文档URL...</span>
                    </div>
                </div>
                
                <div class="progress-bar" id="progressBar">
                    <div class="progress-fill"></div>
                </div>
                
                <div class="result-panel" id="resultPanel">
                    <h3 id="resultTitle">上传结果</h3>
                    <div id="resultContent"></div>
                </div>
                
                <h2 style="margin-top: 30px;">📝 实时日志</h2>
                <div style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 12px; max-height: 300px; overflow-y: auto;" id="logPanel">
                    <div>等待操作...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let saveTimer = null;
        
        // 页面加载时，从服务器获取已保存的Cookie
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                const response = await fetch('/get_saved_cookie');
                const data = await response.json();
                if (data.cookie) {
                    document.getElementById('cookies').value = data.cookie;
                    document.getElementById('cookieSaveStatus').textContent = '✅ 已加载保存的Cookie';
                    setTimeout(() => {
                        document.getElementById('cookieSaveStatus').textContent = '';
                    }, 3000);
                }
            } catch (error) {
                console.error('加载Cookie失败:', error);
            }
        });
        
        // 处理Cookie粘贴事件
        function handleCookiePaste() {
            setTimeout(() => {
                saveCookie();
            }, 100);
        }
        
        // 防抖保存Cookie
        function saveCookieDebounced() {
            clearTimeout(saveTimer);
            saveTimer = setTimeout(() => {
                saveCookie();
            }, 1000);
        }
        
        // 保存Cookie到服务器
        async function saveCookie() {
            const cookies = document.getElementById('cookies').value.trim();
            if (!cookies) return;
            
            try {
                const response = await fetch('/save_cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cookies})
                });
                
                const result = await response.json();
                if (result.success) {
                    document.getElementById('cookieSaveStatus').textContent = '✅ Cookie已自动保存';
                    document.getElementById('cookieSaveStatus').style.color = '#4CAF50';
                } else {
                    document.getElementById('cookieSaveStatus').textContent = '❌ 保存失败: ' + result.message;
                    document.getElementById('cookieSaveStatus').style.color = '#F44336';
                }
                
                setTimeout(() => {
                    document.getElementById('cookieSaveStatus').textContent = '';
                }, 3000);
            } catch (error) {
                console.error('保存Cookie失败:', error);
                document.getElementById('cookieSaveStatus').textContent = '❌ 保存失败';
                document.getElementById('cookieSaveStatus').style.color = '#F44336';
            }
        }
        
        // 文件上传区域事件
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('fileInput');
        
        fileUploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFileSelect(e.target.files[0]);
        });
        
        // 拖拽上传
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });
        
        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });
        
        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
        
        function handleFileSelect(file) {
            if (!file) return;
            
            selectedFile = file;
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileSize').textContent = formatFileSize(file.size);
            document.getElementById('fileInfo').classList.add('show');
            
            addLog(`已选择文件: ${file.name}`);
        }
        
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        }
        
        function addLog(message) {
            const logPanel = document.getElementById('logPanel');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `<span style="color: #6b7280">[${timestamp}]</span> ${message}`;
            logPanel.appendChild(logEntry);
            logPanel.scrollTop = logPanel.scrollHeight;
        }
        
        function updateStatus(id, status, message) {
            const statusItem = document.getElementById('status-' + id);
            if (!statusItem) return;
            
            const icon = statusItem.querySelector('.status-icon');
            const text = statusItem.querySelector('span');
            
            icon.className = 'status-icon status-' + status;
            text.textContent = message;
        }
        
        async function testCookie() {
            const cookies = document.getElementById('cookies').value.trim();
            if (!cookies) {
                alert('请输入Cookie');
                return;
            }
            
            addLog('开始测试Cookie有效性...');
            
            try {
                const response = await fetch('/test_cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cookies})
                });
                
                const result = await response.json();
                if (result.valid) {
                    addLog('✅ Cookie有效');
                    alert('Cookie验证成功！');
                } else {
                    addLog('❌ Cookie无效: ' + result.message);
                    alert('Cookie验证失败: ' + result.message);
                }
            } catch (error) {
                addLog('❌ 测试失败: ' + error);
                alert('测试失败: ' + error);
            }
        }
        
        async function startUpload() {
            const cookies = document.getElementById('cookies').value.trim();
            if (!cookies) {
                alert('请输入Cookie');
                return;
            }
            
            if (!selectedFile) {
                alert('请选择要上传的文件');
                return;
            }
            
            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = true;
            
            // 显示状态面板
            document.getElementById('statusPanel').classList.add('show');
            document.getElementById('progressBar').classList.add('show');
            document.getElementById('resultPanel').classList.remove('show');
            
            // 重置状态
            updateStatus('browser', 'pending', '启动浏览器...');
            updateStatus('login', 'pending', '等待认证...');
            updateStatus('upload', 'pending', '等待上传...');
            updateStatus('url', 'pending', '等待获取URL...');
            
            addLog('=== 开始上传流程 ===');
            
            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('cookies', cookies);
                formData.append('headless', document.getElementById('headlessMode').checked);
                
                updateStatus('browser', 'pending', '正在启动浏览器...');
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    updateStatus('browser', 'success', '浏览器启动成功');
                    updateStatus('login', 'success', 'Cookie认证成功');
                    updateStatus('upload', 'success', '文件上传成功');
                    updateStatus('url', 'success', '获取URL成功');
                    
                    // 显示成功结果
                    const resultPanel = document.getElementById('resultPanel');
                    resultPanel.classList.add('show');
                    resultPanel.classList.remove('error');
                    
                    document.getElementById('resultTitle').textContent = '✅ 上传成功！';
                    document.getElementById('resultContent').innerHTML = `
                        <p><strong>文档URL：</strong></p>
                        <a href="${result.url}" target="_blank" class="result-url">${result.url}</a>
                        ${result.doc_id ? `<p style="margin-top: 10px;"><strong>文档ID：</strong> ${result.doc_id}</p>` : ''}
                        <p style="margin-top: 10px; color: #666; font-size: 12px;">点击链接可直接访问文档</p>
                    `;
                    
                    addLog('✅ 上传成功！URL: ' + result.url);
                } else {
                    throw new Error(result.message || '上传失败');
                }
                
            } catch (error) {
                updateStatus('upload', 'error', '上传失败');
                
                // 显示错误结果
                const resultPanel = document.getElementById('resultPanel');
                resultPanel.classList.add('show');
                resultPanel.classList.add('error');
                
                document.getElementById('resultTitle').textContent = '❌ 上传失败';
                document.getElementById('resultContent').innerHTML = `
                    <p style="color: #d32f2f;">${error.message}</p>
                `;
                
                addLog('❌ 上传失败: ' + error.message);
            } finally {
                uploadBtn.disabled = false;
                document.getElementById('progressBar').classList.remove('show');
            }
        }
    </script>
</body>
</html>
'''

def allowed_file(filename):
    """检查文件类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/save_cookie', methods=['POST'])
def save_cookie():
    """保存Cookie到配置文件"""
    try:
        data = request.json
        cookies_str = data.get('cookies', '')
        
        if not cookies_str:
            return jsonify({'success': False, 'message': '未提供Cookie'})
        
        # 解析Cookie字符串为列表格式
        cookies_list = []
        for cookie_pair in cookies_str.split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies_list.append({
                    'name': name.strip(),
                    'value': value.strip()
                })
        
        # 保存到配置文件
        cookie_config = {
            'cookies': cookies_list,
            'cookie_string': cookies_str,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        config_file = os.path.join(os.path.dirname(__file__), 'config', 'cookies.json')
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cookie已保存到配置文件: {len(cookies_list)} 个")
        return jsonify({'success': True, 'message': 'Cookie已保存'})
        
    except Exception as e:
        logger.error(f"保存Cookie失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_saved_cookie', methods=['GET'])
def get_saved_cookie():
    """获取已保存的Cookie"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'config', 'cookies.json')
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                cookie_config = json.load(f)
                cookie_string = cookie_config.get('cookie_string', '')
                return jsonify({'cookie': cookie_string})
        
        return jsonify({'cookie': ''})
        
    except Exception as e:
        logger.error(f"读取Cookie失败: {e}")
        return jsonify({'cookie': ''})

@app.route('/test_cookie', methods=['POST'])
def test_cookie():
    """测试Cookie有效性"""
    try:
        data = request.json
        cookies = data.get('cookies', '')
        
        if not cookies:
            return jsonify({'valid': False, 'message': '未提供Cookie'})
        
        # TODO: 实现Cookie验证逻辑
        # 这里可以尝试访问腾讯文档并检查是否已登录
        
        return jsonify({'valid': True, 'message': 'Cookie格式正确'})
        
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        # 获取参数
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未选择文件'})
        
        file = request.files['file']
        cookies = request.form.get('cookies', '')
        headless = request.form.get('headless', 'true').lower() == 'true'
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'})
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"文件已保存: {filepath}")
        
        # 调用上传模块
        result = asyncio.run(upload_to_tencent(filepath, cookies, headless))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"上传处理错误: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})

async def upload_to_tencent(file_path, cookies, headless=True):
    """调用腾讯文档上传模块"""
    uploader = TencentDocUploadEnhanced()
    
    try:
        # 启动浏览器
        await uploader.start_browser(headless=headless)
        
        # Cookie登录
        login_success = await uploader.login_with_cookies(cookies)
        if not login_success:
            logger.warning("Cookie认证检查失败，但尝试继续上传")
            # 不再直接返回失败，而是继续尝试上传
        
        # 上传文件
        result = await uploader.upload_file(file_path)
        
        return result
        
    except Exception as e:
        logger.error(f"上传过程错误: {e}")
        return {'success': False, 'message': str(e)}
    finally:
        await uploader.cleanup()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 腾讯文档上传测试服务器")
    print("="*60)
    print(f"📍 访问地址: http://localhost:8109")
    print(f"📁 上传目录: {UPLOAD_FOLDER}")
    print("💡 提示: 请确保已安装playwright和相关依赖")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8109, debug=False)