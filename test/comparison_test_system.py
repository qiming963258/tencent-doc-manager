#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档对比分析测试系统 - 端口8094
完整的端到端测试，包含密集的状态反馈
"""

import os
import sys
import json
import time
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

# 导入项目核心模块
from auto_download_ui_system import download_file_from_url
from simple_comparison_handler import simple_csv_compare, save_comparison_result

app = Flask(__name__)
CORS(app)

# 配置目录
BASE_DIR = Path('/root/projects/tencent-doc-manager')
TEST_DATA_DIR = BASE_DIR / 'test_data'
DOWNLOAD_DIR = BASE_DIR / 'test_downloads'
BASELINE_DIR = BASE_DIR / 'test_baseline'
CURRENT_DIR = BASE_DIR / 'test_current'
RESULT_DIR = BASE_DIR / 'test_results'
CONFIG_FILE = BASE_DIR / 'config.json'

# 创建必要的目录
for dir_path in [DOWNLOAD_DIR, BASELINE_DIR, CURRENT_DIR, RESULT_DIR]:
    dir_path.mkdir(exist_ok=True)

# 全局测试状态
TEST_STATUS = {
    'current_test': None,
    'test_history': [],
    'detailed_logs': []
}

def log_status(category, step, message, status='info', detail=None):
    """记录详细的状态日志"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    log_entry = {
        'timestamp': timestamp,
        'category': category,
        'step': step,
        'message': message,
        'status': status,
        'detail': detail
    }
    TEST_STATUS['detailed_logs'].append(log_entry)
    
    # 同时打印到控制台
    status_icon = {
        'info': '📝',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'progress': '⏳'
    }.get(status, '•')
    
    print(f"[{timestamp}] {status_icon} [{category}] {step}: {message}")
    if detail:
        print(f"    └─ 详情: {detail}")
    
    return log_entry

# HTML模板 - 密集状态反馈界面
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对比分析测试系统 - 密集反馈版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
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
        .test-mode-badge {
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .input-group {
            margin-bottom: 20px;
        }
        .input-group label {
            display: block;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }
        .input-group input, .input-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        .input-group input:focus, .input-group textarea:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .input-group textarea {
            min-height: 100px;
            resize: vertical;
            font-family: monospace;
        }
        .test-options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        .test-option {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .test-option:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .test-option.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102,126,234,0.4);
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-secondary {
            background: #6c757d;
            box-shadow: 0 4px 15px rgba(108,117,125,0.3);
        }
        
        /* 状态日志区域 - 极其详细 */
        .status-panel {
            background: #1a1a2e;
            color: #fff;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            max-height: 600px;
            overflow-y: auto;
        }
        .status-panel h3 {
            color: #fff;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .log-entry {
            margin-bottom: 8px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            border-left: 3px solid #667eea;
        }
        .log-entry.success {
            border-left-color: #28a745;
            background: rgba(40,167,69,0.1);
        }
        .log-entry.error {
            border-left-color: #dc3545;
            background: rgba(220,53,69,0.1);
        }
        .log-entry.warning {
            border-left-color: #ffc107;
            background: rgba(255,193,7,0.1);
        }
        .log-entry.progress {
            border-left-color: #17a2b8;
            background: rgba(23,162,184,0.1);
        }
        .log-timestamp {
            color: #999;
            margin-right: 10px;
        }
        .log-category {
            color: #667eea;
            font-weight: bold;
            margin-right: 10px;
        }
        .log-step {
            color: #ffc107;
            margin-right: 10px;
        }
        .log-detail {
            margin-top: 5px;
            padding-left: 20px;
            color: #aaa;
            font-size: 12px;
        }
        
        /* 进度指示器 */
        .progress-container {
            margin: 20px 0;
        }
        .progress-bar {
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        /* 测试步骤指示器 */
        .test-steps {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
        }
        .test-step {
            flex: 1;
            text-align: center;
            position: relative;
        }
        .test-step:not(:last-child)::after {
            content: '';
            position: absolute;
            top: 20px;
            right: -50%;
            width: 100%;
            height: 2px;
            background: #e0e0e0;
            z-index: -1;
        }
        .test-step.completed::after {
            background: #28a745;
        }
        .step-circle {
            width: 40px;
            height: 40px;
            margin: 0 auto 10px;
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #666;
        }
        .test-step.active .step-circle {
            background: #667eea;
            color: white;
            animation: pulse 1.5s infinite;
        }
        .test-step.completed .step-circle {
            background: #28a745;
            color: white;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(102,126,234,0.7); }
            70% { box-shadow: 0 0 0 10px rgba(102,126,234,0); }
            100% { box-shadow: 0 0 0 0 rgba(102,126,234,0); }
        }
        
        /* 结果展示 */
        .result-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
        }
        .result-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        /* 实时状态指示器 */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
            animation: blink 1s infinite;
        }
        .status-indicator.running {
            background: #28a745;
        }
        .status-indicator.idle {
            background: #6c757d;
            animation: none;
        }
        @keyframes blink {
            0%, 50%, 100% { opacity: 1; }
            25%, 75% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 对比分析测试系统</h1>
            <p>端口 8094 - 密集状态反馈版本</p>
            <div class="test-mode-badge">
                <span class="status-indicator running"></span>
                测试模式
            </div>
        </div>
        
        <!-- 测试步骤指示器 -->
        <div class="test-steps" id="testSteps">
            <div class="test-step" id="step1">
                <div class="step-circle">1</div>
                <div>配置Cookie</div>
            </div>
            <div class="test-step" id="step2">
                <div class="step-circle">2</div>
                <div>下载基线</div>
            </div>
            <div class="test-step" id="step3">
                <div class="step-circle">3</div>
                <div>下载当前</div>
            </div>
            <div class="test-step" id="step4">
                <div class="step-circle">4</div>
                <div>执行对比</div>
            </div>
            <div class="test-step" id="step5">
                <div class="step-circle">5</div>
                <div>生成报告</div>
            </div>
        </div>
        
        <!-- 主要输入区域 -->
        <div class="main-grid">
            <!-- 基线配置 -->
            <div class="card">
                <h2>📊 基线文档配置</h2>
                <div class="input-group">
                    <label>基线文档URL（腾讯文档）</label>
                    <input type="text" id="baselineUrl" placeholder="https://docs.qq.com/sheet/...">
                </div>
                <div class="input-group">
                    <label>基线Cookie（可选，留空使用默认）</label>
                    <textarea id="baselineCookie" placeholder="留空将使用config.json中的默认Cookie"></textarea>
                </div>
                <div class="test-options">
                    <div class="test-option" onclick="useTestData('baseline')">
                        <strong>使用测试数据</strong>
                        <div style="font-size:12px; color:#666; margin-top:5px;">
                            test_baseline.csv
                        </div>
                    </div>
                    <div class="test-option" onclick="useRealDownload('baseline')">
                        <strong>真实下载</strong>
                        <div style="font-size:12px; color:#666; margin-top:5px;">
                            从URL下载
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 当前版本配置 -->
            <div class="card">
                <h2>📈 当前文档配置</h2>
                <div class="input-group">
                    <label>当前文档URL（腾讯文档）</label>
                    <input type="text" id="currentUrl" placeholder="https://docs.qq.com/sheet/...">
                </div>
                <div class="input-group">
                    <label>当前Cookie（可选，留空使用默认）</label>
                    <textarea id="currentCookie" placeholder="留空将使用config.json中的默认Cookie"></textarea>
                </div>
                <div class="test-options">
                    <div class="test-option" onclick="useTestData('current')">
                        <strong>使用测试数据</strong>
                        <div style="font-size:12px; color:#666; margin-top:5px;">
                            test_current.csv
                        </div>
                    </div>
                    <div class="test-option" onclick="useRealDownload('current')">
                        <strong>真实下载</strong>
                        <div style="font-size:12px; color:#666; margin-top:5px;">
                            从URL下载
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 控制按钮 -->
        <div style="text-align: center; margin: 30px 0;">
            <button class="btn" onclick="startTest()" id="startBtn">
                🚀 开始测试
            </button>
            <button class="btn btn-secondary" onclick="clearLogs()" style="margin-left: 20px;">
                🗑️ 清空日志
            </button>
            <button class="btn btn-secondary" onclick="loadDefaultCookie()" style="margin-left: 20px;">
                📋 加载默认Cookie
            </button>
        </div>
        
        <!-- 进度条 -->
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar" style="width: 0%;">
                    0%
                </div>
            </div>
        </div>
        
        <!-- 详细状态日志 -->
        <div class="status-panel">
            <h3>📜 详细执行日志（实时更新）</h3>
            <div id="statusLogs"></div>
        </div>
        
        <!-- 测试结果 -->
        <div class="result-panel" id="resultPanel" style="display: none;">
            <h2>📊 测试结果</h2>
            <div class="result-stats" id="resultStats"></div>
            <div id="resultDetails"></div>
        </div>
    </div>
    
    <script>
        let testMode = {
            baseline: null,
            current: null
        };
        
        let statusInterval = null;
        let currentTestId = null;
        
        function useTestData(type) {
            testMode[type] = 'test';
            document.querySelectorAll(`.card:${type === 'baseline' ? 'first' : 'last'}-child .test-option`).forEach(el => {
                el.classList.remove('selected');
            });
            event.target.closest('.test-option').classList.add('selected');
            addLog('info', '配置', `${type} 选择使用测试数据`);
        }
        
        function useRealDownload(type) {
            testMode[type] = 'download';
            document.querySelectorAll(`.card:${type === 'baseline' ? 'first' : 'last'}-child .test-option`).forEach(el => {
                el.classList.remove('selected');
            });
            event.target.closest('.test-option').classList.add('selected');
            addLog('info', '配置', `${type} 选择真实下载`);
        }
        
        async function loadDefaultCookie() {
            addLog('progress', '加载Cookie', '正在读取默认Cookie配置...');
            try {
                const response = await fetch('/api/get-config');
                const data = await response.json();
                if (data.success && data.cookie) {
                    document.getElementById('baselineCookie').value = data.cookie;
                    document.getElementById('currentCookie').value = data.cookie;
                    addLog('success', '加载Cookie', `成功加载默认Cookie (长度: ${data.cookie.length})`);
                } else {
                    addLog('error', '加载Cookie', '未找到默认Cookie配置');
                }
            } catch (error) {
                addLog('error', '加载Cookie', '加载失败: ' + error.message);
            }
        }
        
        async function startTest() {
            const btn = document.getElementById('startBtn');
            btn.disabled = true;
            
            // 清空之前的结果
            document.getElementById('resultPanel').style.display = 'none';
            clearLogs();
            
            // 重置步骤指示器
            document.querySelectorAll('.test-step').forEach(step => {
                step.classList.remove('active', 'completed');
            });
            
            addLog('info', '测试开始', '初始化对比分析测试...');
            updateProgress(0);
            
            // 准备测试数据
            const testData = {
                baseline_url: document.getElementById('baselineUrl').value,
                baseline_cookie: document.getElementById('baselineCookie').value,
                baseline_mode: testMode.baseline || 'test',
                current_url: document.getElementById('currentUrl').value,
                current_cookie: document.getElementById('currentCookie').value,
                current_mode: testMode.current || 'test',
                enable_detailed_logging: true
            };
            
            addLog('info', '参数准备', `基线模式: ${testData.baseline_mode}, 当前模式: ${testData.current_mode}`);
            
            try {
                // 发起测试请求
                addLog('progress', 'API调用', '正在调用测试API...');
                const response = await fetch('/api/test-compare', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(testData)
                });
                
                const result = await response.json();
                currentTestId = result.test_id;
                
                // 启动状态轮询
                startStatusPolling();
                
            } catch (error) {
                addLog('error', '测试失败', error.message);
                btn.disabled = false;
            }
        }
        
        function startStatusPolling() {
            if (statusInterval) clearInterval(statusInterval);
            
            statusInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/test-status/${currentTestId}`);
                    const status = await response.json();
                    
                    // 更新进度
                    updateProgress(status.progress || 0);
                    
                    // 更新步骤指示器
                    updateSteps(status.current_step);
                    
                    // 添加新的日志
                    if (status.new_logs) {
                        status.new_logs.forEach(log => {
                            addLogEntry(log);
                        });
                    }
                    
                    // 检查是否完成
                    if (status.completed) {
                        clearInterval(statusInterval);
                        document.getElementById('startBtn').disabled = false;
                        displayResults(status.result);
                    }
                } catch (error) {
                    console.error('状态轮询错误:', error);
                }
            }, 500); // 每500ms轮询一次
        }
        
        function updateSteps(currentStep) {
            const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
            const currentIndex = steps.indexOf(currentStep);
            
            steps.forEach((step, index) => {
                const element = document.getElementById(step);
                if (index < currentIndex) {
                    element.classList.add('completed');
                    element.classList.remove('active');
                } else if (index === currentIndex) {
                    element.classList.add('active');
                    element.classList.remove('completed');
                } else {
                    element.classList.remove('active', 'completed');
                }
            });
        }
        
        function updateProgress(percent) {
            const bar = document.getElementById('progressBar');
            bar.style.width = percent + '%';
            bar.textContent = percent + '%';
        }
        
        function addLog(status, category, message, detail = null) {
            const log = {
                timestamp: new Date().toLocaleTimeString('zh-CN', {hour12: false}),
                status: status,
                category: category,
                message: message,
                detail: detail
            };
            addLogEntry(log);
        }
        
        function addLogEntry(log) {
            const logsContainer = document.getElementById('statusLogs');
            const entry = document.createElement('div');
            entry.className = `log-entry ${log.status}`;
            
            let html = `
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-category">[${log.category}]</span>
                <span class="log-step">${log.step || ''}</span>
                <span>${log.message}</span>
            `;
            
            if (log.detail) {
                html += `<div class="log-detail">└─ ${log.detail}</div>`;
            }
            
            entry.innerHTML = html;
            logsContainer.appendChild(entry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
        
        function clearLogs() {
            document.getElementById('statusLogs').innerHTML = '';
        }
        
        function displayResults(result) {
            const panel = document.getElementById('resultPanel');
            const stats = document.getElementById('resultStats');
            const details = document.getElementById('resultDetails');
            
            // 显示统计信息
            stats.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${result.total_changes || 0}</div>
                    <div class="stat-label">总变更数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${result.added_rows || 0}</div>
                    <div class="stat-label">新增行</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${result.modified_rows || 0}</div>
                    <div class="stat-label">修改行</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${result.similarity || 0}%</div>
                    <div class="stat-label">相似度</div>
                </div>
            `;
            
            // 显示详细结果
            details.innerHTML = `
                <h3>详细对比结果</h3>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            `;
            
            panel.style.display = 'block';
            addLog('success', '测试完成', `测试成功完成，相似度: ${result.similarity}%`);
        }
        
        // 页面加载时的初始化
        window.onload = function() {
            addLog('info', '系统', '测试系统已就绪');
            addLog('info', '系统', '可选择使用测试数据或真实下载');
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get-config', methods=['GET'])
def get_config():
    """获取默认配置"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cookie = config.get('cookie', '')
                return jsonify({
                    'success': True,
                    'cookie': cookie,
                    'cookie_length': len(cookie)
                })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': '配置文件不存在'})

@app.route('/api/test-compare', methods=['POST'])
def test_compare():
    """执行对比测试 - 带密集状态反馈"""
    test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        data = request.json
        log_status('初始化', '接收请求', f'测试ID: {test_id}', 'info')
        
        # 初始化测试状态
        TEST_STATUS['current_test'] = {
            'test_id': test_id,
            'start_time': time.time(),
            'progress': 0,
            'current_step': 'step1',
            'completed': False,
            'result': None,
            'logs': []
        }
        
        # 步骤1: 配置验证
        log_status('配置验证', '检查参数', '验证输入参数完整性', 'progress')
        baseline_mode = data.get('baseline_mode', 'test')
        current_mode = data.get('current_mode', 'test')
        
        log_status('配置验证', '模式确认', 
                  f'基线: {baseline_mode}, 当前: {current_mode}', 'success')
        
        TEST_STATUS['current_test']['progress'] = 10
        TEST_STATUS['current_test']['current_step'] = 'step2'
        
        # 步骤2: 获取基线文件
        log_status('基线处理', '开始获取', '准备获取基线文件...', 'progress')
        baseline_path = None
        
        if baseline_mode == 'test':
            # 使用测试数据
            log_status('基线处理', '使用测试数据', 'test_baseline.csv', 'info')
            test_file = TEST_DATA_DIR / 'test_baseline.csv'
            if test_file.exists():
                baseline_path = BASELINE_DIR / 'test_baseline.csv'
                shutil.copy(test_file, baseline_path)
                log_status('基线处理', '复制完成', 
                          f'文件大小: {baseline_path.stat().st_size} bytes', 'success')
            else:
                log_status('基线处理', '文件不存在', str(test_file), 'error')
                
        else:
            # 真实下载
            url = data.get('baseline_url')
            cookie = data.get('baseline_cookie')
            
            log_status('基线处理', '准备下载', f'URL: {url[:50]}...', 'info')
            log_status('基线处理', 'Cookie检查', 
                      f'Cookie长度: {len(cookie) if cookie else 0}', 'info')
            
            # 保存Cookie到配置
            if cookie:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({'cookie': cookie}, f)
                log_status('基线处理', 'Cookie保存', '已更新config.json', 'success')
            
            # 调用下载函数
            log_status('基线处理', '开始下载', '调用download_file_from_url', 'progress')
            download_start = time.time()
            
            try:
                result = download_file_from_url(url, 'csv')
                download_time = time.time() - download_start
                log_status('基线处理', '下载完成', 
                          f'耗时: {download_time:.2f}秒', 'success')
                
                if result and result.get('success'):
                    if result.get('files'):
                        source = Path(result['files'][0]['path'])
                        baseline_path = BASELINE_DIR / source.name
                        shutil.copy(source, baseline_path)
                        log_status('基线处理', '文件保存', 
                                  f'保存到: {baseline_path}', 'success')
            except Exception as e:
                log_status('基线处理', '下载失败', str(e), 'error')
        
        TEST_STATUS['current_test']['progress'] = 40
        TEST_STATUS['current_test']['current_step'] = 'step3'
        
        # 步骤3: 获取当前文件
        log_status('当前文件', '开始获取', '准备获取当前版本文件...', 'progress')
        current_path = None
        
        if current_mode == 'test':
            # 使用测试数据
            log_status('当前文件', '使用测试数据', 'test_current.csv', 'info')
            test_file = TEST_DATA_DIR / 'test_current.csv'
            if test_file.exists():
                current_path = CURRENT_DIR / 'test_current.csv'
                shutil.copy(test_file, current_path)
                log_status('当前文件', '复制完成', 
                          f'文件大小: {current_path.stat().st_size} bytes', 'success')
            else:
                log_status('当前文件', '文件不存在', str(test_file), 'error')
                
        else:
            # 真实下载（类似基线处理）
            url = data.get('current_url')
            cookie = data.get('current_cookie')
            
            log_status('当前文件', '准备下载', f'URL: {url[:50]}...', 'info')
            
            if cookie:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({'cookie': cookie}, f)
                    
            try:
                result = download_file_from_url(url, 'csv')
                if result and result.get('success'):
                    if result.get('files'):
                        source = Path(result['files'][0]['path'])
                        current_path = CURRENT_DIR / source.name
                        shutil.copy(source, current_path)
                        log_status('当前文件', '文件保存', 
                                  f'保存到: {current_path}', 'success')
            except Exception as e:
                log_status('当前文件', '下载失败', str(e), 'error')
        
        TEST_STATUS['current_test']['progress'] = 60
        TEST_STATUS['current_test']['current_step'] = 'step4'
        
        # 步骤4: 执行对比
        if baseline_path and current_path:
            log_status('对比分析', '开始对比', '调用simple_csv_compare', 'progress')
            
            try:
                # 记录文件信息
                log_status('对比分析', '基线文件', 
                          f'行数: {sum(1 for _ in open(baseline_path))}', 'info')
                log_status('对比分析', '当前文件', 
                          f'行数: {sum(1 for _ in open(current_path))}', 'info')
                
                # 执行对比
                comparison_start = time.time()
                result = simple_csv_compare(str(baseline_path), str(current_path))
                comparison_time = time.time() - comparison_start
                
                log_status('对比分析', '对比完成', 
                          f'耗时: {comparison_time:.2f}秒', 'success')
                
                # 分析结果
                log_status('对比分析', '结果统计', 
                          f'总变更: {result.get("total_changes", 0)}', 'info')
                log_status('对比分析', '详细变更', 
                          f'新增: {result.get("added_rows", 0)}, '
                          f'修改: {result.get("modified_rows", 0)}, '
                          f'删除: {result.get("deleted_rows", 0)}', 'info')
                
                TEST_STATUS['current_test']['progress'] = 80
                TEST_STATUS['current_test']['current_step'] = 'step5'
                
                # 步骤5: 保存结果
                log_status('保存结果', '生成报告', '保存对比结果...', 'progress')
                
                result_file = RESULT_DIR / f'result_{test_id}.json'
                save_comparison_result(result, str(result_file))
                
                log_status('保存结果', '保存成功', 
                          f'结果文件: {result_file}', 'success')
                
                # 完成
                TEST_STATUS['current_test']['progress'] = 100
                TEST_STATUS['current_test']['completed'] = True
                TEST_STATUS['current_test']['result'] = result
                
                log_status('测试完成', '成功', 
                          f'总耗时: {time.time() - TEST_STATUS["current_test"]["start_time"]:.2f}秒', 
                          'success')
                
                return jsonify({
                    'success': True,
                    'test_id': test_id,
                    'message': '测试已启动，请查看状态更新'
                })
            except Exception as e:
                log_status('对比分析', '执行失败', str(e), 'error')
                TEST_STATUS['current_test']['completed'] = True
                return jsonify({
                    'success': False,
                    'test_id': test_id,
                    'error': f'对比分析失败: {str(e)}'
                })
                
        else:
            log_status('测试失败', '文件缺失', '基线或当前文件获取失败', 'error')
            TEST_STATUS['current_test']['completed'] = True
            return jsonify({
                'success': False,
                'test_id': test_id,
                'error': '文件获取失败'
            })
            
    except Exception as e:
        log_status('系统错误', '异常', str(e), 'error', traceback.format_exc())
        if TEST_STATUS.get('current_test'):
            TEST_STATUS['current_test']['completed'] = True
        return jsonify({
            'success': False,
            'test_id': test_id,
            'error': str(e)
        })

@app.route('/api/test-status/<test_id>', methods=['GET'])
def get_test_status(test_id):
    """获取测试状态 - 实时更新"""
    if TEST_STATUS.get('current_test') and TEST_STATUS['current_test']['test_id'] == test_id:
        current = TEST_STATUS['current_test']
        
        # 获取新日志
        last_log_index = int(request.args.get('last_index', 0))
        new_logs = TEST_STATUS['detailed_logs'][last_log_index:]
        
        return jsonify({
            'test_id': test_id,
            'progress': current['progress'],
            'current_step': current['current_step'],
            'completed': current['completed'],
            'result': current['result'],
            'new_logs': new_logs,
            'total_logs': len(TEST_STATUS['detailed_logs'])
        })
    
    return jsonify({'error': '测试不存在'})

if __name__ == '__main__':
    print("=" * 60)
    print("对比分析测试系统 - 密集反馈版")
    print("访问地址: http://202.140.143.88:8094/")
    print("=" * 60)
    print("特性:")
    print("  ✓ 密集的状态反馈")
    print("  ✓ 每个步骤详细日志")
    print("  ✓ 支持测试数据和真实下载")
    print("  ✓ 完整的对比分析")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8094, debug=False)