#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动下载UI系统
支持通过Web界面输入Cookie和URL，实现定时自动下载
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS

# 添加测试版本路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')
try:
    # 尝试从production模块导入
    from production.core_modules.tencent_export_automation import TencentDocAutoExporter
except ImportError:
    try:
        # 备用：从当前目录导入
        from tencent_export_automation import TencentDocAutoExporter
    except ImportError:
        print("警告：TencentDocAutoExporter无法导入")
        TencentDocAutoExporter = None

app = Flask(__name__)
CORS(app)

# 全局变量存储配置和状态
# 修改为使用统一的配置文件，与8093端口共享
CONFIG_FILE = '/root/projects/tencent-doc-manager/config.json'
# 备用配置文件路径
BACKUP_CONFIG_FILE = '/root/projects/tencent-doc-manager/auto_download_config.json'
DOWNLOAD_STATUS = {
    'is_running': False,
    'last_run': None,
    'next_run': None,
    'download_count': 0,
    'error_count': 0,
    'recent_downloads': [],
    'recent_errors': []
}

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档自动下载系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #555;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .url-list {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .url-item {
            background: white;
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .url-item button {
            background: #f44336;
            color: white;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-success {
            background: #4CAF50;
            color: white;
            margin-left: 10px;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
            margin-left: 10px;
        }
        
        .status-section {
            grid-column: span 2;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .status-item h3 {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        
        .status-item .value {
            color: #333;
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .status-running {
            background: #d4edda;
        }
        
        .status-stopped {
            background: #f8d7da;
        }
        
        .log-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-entry {
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 14px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        .log-success {
            background: #d4edda;
            color: #155724;
        }
        
        .log-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .log-info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .running-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 腾讯文档自动下载系统</h1>
            <p>通过Web界面配置，实现定时自动下载腾讯文档</p>
        </div>
        
        <div class="main-grid">
            <!-- 配置区域 -->
            <div class="card">
                <h2>📝 下载配置</h2>
                <div class="form-group">
                    <label>Cookie (必填)</label>
                    <textarea id="cookie" placeholder="粘贴完整的Cookie字符串..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>添加文档URL</label>
                    <input type="text" id="new-url" placeholder="https://docs.qq.com/sheet/...">
                    <button class="btn btn-success" onclick="addURL()" style="margin-top: 10px;">添加URL</button>
                </div>
                
                <div class="form-group">
                    <label>URL列表</label>
                    <div id="url-list" class="url-list">
                        <p style="color: #999;">暂无URL</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>下载格式</label>
                    <select id="format">
                        <option value="excel">Excel (.xlsx)</option>
                        <option value="csv">CSV (.csv)</option>
                    </select>
                </div>
            </div>
            
            <!-- 定时设置 -->
            <div class="card">
                <h2>⏰ 定时设置</h2>
                <div class="form-group">
                    <label>执行间隔</label>
                    <select id="interval">
                        <option value="30">每30分钟</option>
                        <option value="60">每1小时</option>
                        <option value="120">每2小时</option>
                        <option value="360">每6小时</option>
                        <option value="720">每12小时</option>
                        <option value="1440">每24小时</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>立即执行时间</label>
                    <input type="time" id="schedule-time">
                </div>
                
                <div class="form-group">
                    <label>下载目录</label>
                    <input type="text" id="download-dir" value="/root/projects/tencent-doc-manager/auto_downloads">
                </div>
                
                <div style="margin-top: 30px;">
                    <button class="btn btn-primary" onclick="saveConfig()">保存配置</button>
                    <button class="btn btn-success" onclick="startScheduler()">启动定时</button>
                    <button class="btn btn-danger" onclick="stopScheduler()">停止定时</button>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="testDownload()">立即测试下载</button>
                </div>
            </div>
            
            <!-- 状态监控 -->
            <div class="card status-section">
                <h2>📊 运行状态</h2>
                <div class="status-grid">
                    <div class="status-item" id="status-indicator">
                        <h3>运行状态</h3>
                        <div class="value">
                            <span id="running-status">停止</span>
                            <span class="running-indicator" style="display: none;"></span>
                        </div>
                    </div>
                    <div class="status-item">
                        <h3>下载次数</h3>
                        <div class="value" id="download-count">0</div>
                    </div>
                    <div class="status-item">
                        <h3>错误次数</h3>
                        <div class="value" id="error-count">0</div>
                    </div>
                    <div class="status-item">
                        <h3>下次执行</h3>
                        <div class="value" id="next-run" style="font-size: 1rem;">--:--</div>
                    </div>
                </div>
                
                <h3 style="margin: 20px 0 10px 0;">📋 运行日志</h3>
                <div class="log-section" id="log-section">
                    <div class="log-entry log-info">系统初始化完成，等待配置...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let urlList = [];
        let config = {};
        
        // 页面加载时获取配置
        window.onload = function() {
            loadConfig();
            updateStatus();
            setInterval(updateStatus, 5000);
        };
        
        function addURL() {
            const url = document.getElementById('new-url').value.trim();
            if (url && url.startsWith('https://docs.qq.com/')) {
                if (!urlList.includes(url)) {
                    urlList.push(url);
                    updateURLList();
                    document.getElementById('new-url').value = '';
                    addLog('添加URL: ' + url, 'info');
                }
            } else {
                alert('请输入有效的腾讯文档URL');
            }
        }
        
        function removeURL(index) {
            urlList.splice(index, 1);
            updateURLList();
        }
        
        function updateURLList() {
            const listDiv = document.getElementById('url-list');
            if (urlList.length === 0) {
                listDiv.innerHTML = '<p style="color: #999;">暂无URL</p>';
            } else {
                listDiv.innerHTML = urlList.map((url, index) => `
                    <div class="url-item">
                        <span>${url.substring(0, 50)}...</span>
                        <button onclick="removeURL(${index})">删除</button>
                    </div>
                `).join('');
            }
        }
        
        function saveConfig() {
            const cookie = document.getElementById('cookie').value.trim();
            const format = document.getElementById('format').value;
            const interval = document.getElementById('interval').value;
            const downloadDir = document.getElementById('download-dir').value;
            
            if (!cookie) {
                alert('请输入Cookie');
                return;
            }
            
            if (urlList.length === 0) {
                alert('请至少添加一个URL');
                return;
            }
            
            config = {
                cookie: cookie,
                urls: urlList,
                format: format,
                interval: parseInt(interval),
                download_dir: downloadDir
            };
            
            fetch('/api/save_config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('配置保存成功', 'success');
                    alert('配置保存成功！');
                } else {
                    addLog('配置保存失败: ' + data.error, 'error');
                }
            });
        }
        
        function loadConfig() {
            fetch('/api/get_config')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.config) {
                    config = data.config;
                    document.getElementById('cookie').value = config.cookie || '';
                    document.getElementById('format').value = config.format || 'excel';
                    document.getElementById('interval').value = config.interval || 60;
                    document.getElementById('download-dir').value = config.download_dir || '/root/projects/tencent-doc-manager/auto_downloads';
                    urlList = config.urls || [];
                    updateURLList();
                    addLog('配置加载成功', 'success');
                }
            });
        }
        
        function startScheduler() {
            fetch('/api/start_scheduler', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('定时任务已启动', 'success');
                    updateStatus();
                } else {
                    addLog('启动失败: ' + data.error, 'error');
                }
            });
        }
        
        function stopScheduler() {
            fetch('/api/stop_scheduler', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('定时任务已停止', 'info');
                    updateStatus();
                }
            });
        }
        
        function testDownload() {
            addLog('开始测试下载...', 'info');
            fetch('/api/test_download', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('测试下载成功！文件: ' + data.files.join(', '), 'success');
                } else {
                    addLog('测试下载失败: ' + data.error, 'error');
                }
            });
        }
        
        function updateStatus() {
            fetch('/api/get_status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('download-count').textContent = data.download_count;
                document.getElementById('error-count').textContent = data.error_count;
                
                const statusIndicator = document.getElementById('status-indicator');
                const runningStatus = document.getElementById('running-status');
                const runningIndicator = statusIndicator.querySelector('.running-indicator');
                
                if (data.is_running) {
                    runningStatus.textContent = '运行中';
                    runningIndicator.style.display = 'inline-block';
                    statusIndicator.classList.add('status-running');
                    statusIndicator.classList.remove('status-stopped');
                } else {
                    runningStatus.textContent = '停止';
                    runningIndicator.style.display = 'none';
                    statusIndicator.classList.add('status-stopped');
                    statusIndicator.classList.remove('status-running');
                }
                
                document.getElementById('next-run').textContent = data.next_run || '--:--';
                
                // 更新最近日志
                if (data.recent_logs) {
                    const logSection = document.getElementById('log-section');
                    logSection.innerHTML = data.recent_logs.map(log => 
                        `<div class="log-entry log-${log.type}">${log.time} - ${log.message}</div>`
                    ).join('');
                    logSection.scrollTop = logSection.scrollHeight;
                }
            });
        }
        
        function addLog(message, type) {
            const logSection = document.getElementById('log-section');
            const time = new Date().toLocaleTimeString('zh-CN');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            logEntry.textContent = `${time} - ${message}`;
            logSection.appendChild(logEntry);
            logSection.scrollTop = logSection.scrollHeight;
        }
    </script>
</body>
</html>
'''

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

async def download_documents():
    """执行下载任务"""
    config = load_config()
    if not config:
        return False, "未找到配置"
    
    downloaded_files = []
    errors = []
    
    exporter = TencentDocAutoExporter(
        download_dir=config.get('download_dir', '/root/projects/tencent-doc-manager/auto_downloads')
    )
    
    try:
        await exporter.start_browser(headless=True)
        await exporter.login_with_cookies(config.get('cookie', ''))
        
        for url in config.get('urls', []):
            try:
                print(f"下载: {url}")
                success = await exporter.export_document(
                    url, 
                    export_format=config.get('format', 'excel')
                )
                if success:
                    downloaded_files.append(url)
                    DOWNLOAD_STATUS['download_count'] += 1
                else:
                    errors.append(f"下载失败: {url}")
                    DOWNLOAD_STATUS['error_count'] += 1
            except Exception as e:
                errors.append(f"下载错误 {url}: {str(e)}")
                DOWNLOAD_STATUS['error_count'] += 1
        
    finally:
        await exporter.cleanup()
    
    DOWNLOAD_STATUS['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if downloaded_files:
        DOWNLOAD_STATUS['recent_downloads'].append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'files': downloaded_files,
            'type': 'success'
        })
    
    if errors:
        for error in errors:
            DOWNLOAD_STATUS['recent_errors'].append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'message': error,
                'type': 'error'
            })
    
    # 保持日志列表长度
    DOWNLOAD_STATUS['recent_downloads'] = DOWNLOAD_STATUS['recent_downloads'][-10:]
    DOWNLOAD_STATUS['recent_errors'] = DOWNLOAD_STATUS['recent_errors'][-10:]
    
    # 安全的后处理：版本管理（不影响下载功能）
    if downloaded_files and config.get('enable_version_management', False):
        try:
            from post_download_processor import PostDownloadProcessor
            processor = PostDownloadProcessor()
            process_result = processor.process_downloaded_files(downloaded_files)
            
            if process_result['success']:
                print(f"✅ 版本管理处理成功: {process_result['processed_count']} 个文件")
                DOWNLOAD_STATUS['recent_downloads'][-1]['version_managed'] = True
            else:
                print(f"⚠️ 版本管理处理部分成功")
        except Exception as e:
            print(f"⚠️ 后处理模块加载失败（不影响下载）: {e}")
            # 不影响下载功能，仅记录错误
    
    return len(downloaded_files) > 0, downloaded_files

def run_download_task():
    """同步包装器运行下载任务"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, files = loop.run_until_complete(download_documents())
    loop.close()
    return success, files

# 定时任务线程
scheduler_thread = None
scheduler_stop_flag = threading.Event()

def scheduler_worker():
    """定时任务工作线程"""
    config = load_config()
    interval = config.get('interval', 60)
    
    while not scheduler_stop_flag.is_set():
        # 执行下载
        run_download_task()
        
        # 更新下次运行时间
        next_time = datetime.now() + timedelta(minutes=interval)
        DOWNLOAD_STATUS['next_run'] = next_time.strftime('%H:%M:%S')
        
        # 等待下次执行
        for _ in range(interval * 60):
            if scheduler_stop_flag.is_set():
                break
            time.sleep(1)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    try:
        config = request.json
        save_config(config)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_config')
def api_get_config():
    try:
        config = load_config()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start_scheduler', methods=['POST'])
def api_start_scheduler():
    global scheduler_thread
    
    if DOWNLOAD_STATUS['is_running']:
        return jsonify({'success': False, 'error': '定时任务已在运行'})
    
    config = load_config()
    if not config:
        return jsonify({'success': False, 'error': '请先保存配置'})
    
    scheduler_stop_flag.clear()
    scheduler_thread = threading.Thread(target=scheduler_worker)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    DOWNLOAD_STATUS['is_running'] = True
    return jsonify({'success': True})

@app.route('/api/stop_scheduler', methods=['POST'])
def api_stop_scheduler():
    global scheduler_thread
    
    scheduler_stop_flag.set()
    if scheduler_thread:
        scheduler_thread.join(timeout=5)
    
    DOWNLOAD_STATUS['is_running'] = False
    DOWNLOAD_STATUS['next_run'] = None
    return jsonify({'success': True})

@app.route('/api/test_download', methods=['POST'])
def api_test_download():
    try:
        success, files = run_download_task()
        if success:
            return jsonify({'success': True, 'files': files})
        else:
            return jsonify({'success': False, 'error': '下载失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_status')
def api_get_status():
    # 合并日志
    recent_logs = []
    for log in DOWNLOAD_STATUS.get('recent_downloads', []):
        recent_logs.append({
            'time': log['time'],
            'message': f"成功下载 {len(log['files'])} 个文件",
            'type': 'success'
        })
    
    for log in DOWNLOAD_STATUS.get('recent_errors', []):
        recent_logs.append({
            'time': log['time'],
            'message': log['message'],
            'type': 'error'
        })
    
    # 按时间排序
    recent_logs.sort(key=lambda x: x['time'], reverse=True)
    
    return jsonify({
        'is_running': DOWNLOAD_STATUS['is_running'],
        'last_run': DOWNLOAD_STATUS['last_run'],
        'next_run': DOWNLOAD_STATUS['next_run'],
        'download_count': DOWNLOAD_STATUS['download_count'],
        'error_count': DOWNLOAD_STATUS['error_count'],
        'recent_logs': recent_logs[:20]
    })

if __name__ == '__main__':
    print("🚀 腾讯文档自动下载UI系统")
    print("📍 访问地址: http://202.140.143.88:8090/")
    print("=" * 60)
    
    # 创建下载目录
    os.makedirs('/root/projects/tencent-doc-manager/auto_downloads', exist_ok=True)
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=8090, debug=False)

# ============ 适配器函数 - 供8093端口调用 ============
def download_file_from_url(url, format_type='csv'):
    """
    同步适配器函数，供complete_workflow_ui.py调用
    修复8093端口无法下载真实文件的问题
    
    Args:
        url: 腾讯文档URL
        format_type: 下载格式 (csv/excel/pdf等)
    
    Returns:
        dict: {'success': bool, 'files': list, 'message': str}
    """
    from pathlib import Path
    from datetime import datetime
    
    print(f"[适配器] 开始下载: {url}, 格式: {format_type}")
    
    try:
        # 读取配置
        config = load_config()
        # 允许无Cookie下载（公开文档的CSV格式通常不需要Cookie）
        if not config:
            config = {'cookie': ''}
            print("[适配器] 警告：无配置文件，使用空Cookie尝试下载公开文档")
        
        # 检查TencentDocAutoExporter是否可用
        if TencentDocAutoExporter is None:
            print("[适配器] TencentDocAutoExporter不可用，尝试直接导入")
            try:
                from production.core_modules.tencent_export_automation import TencentDocAutoExporter as Exporter
            except:
                return {
                    'success': False,
                    'error': 'TencentDocAutoExporter无法导入，下载功能不可用'
                }
        else:
            Exporter = TencentDocAutoExporter
        
        # 创建下载器实例
        download_dir = '/root/projects/tencent-doc-manager/downloads'
        os.makedirs(download_dir, exist_ok=True)
        
        exporter = Exporter(download_dir=download_dir)
        
        # 使用同步的export_document方法
        cookie_str = config.get('cookie', '')
        print(f"[适配器] 使用Cookie长度: {len(cookie_str)}")
        
        # 调用同步方法（内部会处理异步）
        result = exporter.export_document(
            url=url,
            cookies=cookie_str,
            format=format_type,
            download_dir=download_dir
        )
        
        print(f"[适配器] 导出结果: {result}")
        
        if result.get('success'):
            # 获取下载的文件
            files_to_check = []
            
            # 从结果中获取文件
            if result.get('file_path'):
                files_to_check.append(Path(result['file_path']))
            if result.get('files'):
                for f in result['files']:
                    if isinstance(f, str):
                        files_to_check.append(Path(f))
                    elif isinstance(f, dict) and f.get('path'):
                        files_to_check.append(Path(f['path']))
            
            # 如果没有找到文件，不使用任何备用策略，直接报错
            if not files_to_check:
                print("[适配器] ❌ 下载失败：未能从下载结果中获取文件路径")
                print(f"[适配器] 调试信息 - result内容: {result}")
                return {
                    'success': False,
                    'error': '下载失败：未能获取到下载的文件路径',
                    'files': [],
                    'details': f'URL: {url}, 格式: {format_type}'
                }
                    
            if files_to_check:
                file_list = []
                content_check_results = []
                
                # 导入内容检查器
                try:
                    # 优先尝试轻量版（不依赖pandas）
                    from download_content_checker_lite import DownloadContentChecker
                    checker = DownloadContentChecker()
                    print("[适配器] 启用内容检查功能（轻量版）")
                except ImportError:
                    try:
                        # 备用：完整版
                        from download_content_checker import DownloadContentChecker
                        checker = DownloadContentChecker()
                        print("[适配器] 启用内容检查功能（完整版）")
                    except ImportError:
                        checker = None
                        print("[适配器] 内容检查器未找到，跳过检查")
                
                for f in files_to_check:
                    file_info = {
                        'path': str(f),
                        'name': f.name,
                        'size': f'{f.stat().st_size:,} bytes'
                    }
                    
                    # 执行内容检查
                    if checker:
                        try:
                            check_result = checker.check_file(str(f))
                            file_info['content_check'] = {
                                'is_demo_data': check_result.get('is_demo_data', None),
                                'authenticity_score': check_result.get('authenticity_score', 0),
                                'summary': check_result.get('summary', ''),
                                'row_count': check_result.get('row_count', None),
                                'column_count': check_result.get('column_count', None)
                            }
                            content_check_results.append(check_result)
                            print(f"[适配器] 文件检查: {f.name} - 真实性评分: {check_result.get('authenticity_score', 0):.1f}")
                        except Exception as e:
                            print(f"[适配器] 检查文件 {f.name} 时出错: {e}")
                            file_info['content_check'] = {'error': str(e)}
                    
                    file_list.append(file_info)
                
                # 生成总体评估
                overall_assessment = "未进行内容检查"
                if content_check_results:
                    avg_score = sum(r.get('authenticity_score', 0) for r in content_check_results) / len(content_check_results)
                    if avg_score >= 80:
                        overall_assessment = "✅ 高可信度：下载的文件很可能是真实的腾讯文档"
                    elif avg_score >= 60:
                        overall_assessment = "⚠️ 中等可信度：文件可能是真实的，但包含一些可疑特征"
                    elif avg_score >= 40:
                        overall_assessment = "⚠️ 低可信度：文件包含较多演示数据特征"
                    else:
                        overall_assessment = "❌ 极低可信度：文件很可能是演示或测试数据"
                
                return {
                    'success': True,
                    'files': file_list,
                    'message': f'成功下载 {len(file_list)} 个文件',
                    'content_assessment': overall_assessment
                }
            else:
                return {
                    'success': False,
                    'error': '下载似乎成功但未找到文件'
                }
        else:
            return {
                'success': False,
                'error': f'下载失败: {result.get("error", "未知错误")}'
            }
            
    except Exception as e:
        print(f"[适配器] 下载出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'下载异常: {str(e)}'
        }