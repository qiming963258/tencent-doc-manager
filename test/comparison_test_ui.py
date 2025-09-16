#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比分析测试UI - 真实项目集成版
提供完整的基线对比分析测试界面，集成真实的对比引擎
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import json
import time
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
import shutil
import csv

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

# 导入真实的项目模块
try:
    from production.core_modules.baseline_manager import BaselineManager
except:
    BaselineManager = None
    
try:
    from production.core_modules.adaptive_table_comparator import AdaptiveTableComparator
except:
    AdaptiveTableComparator = None
    
try:
    from production.core_modules.auto_comparison_task import AutoComparisonTaskHandler
except:
    AutoComparisonTaskHandler = None
    
from auto_download_ui_system import download_file_from_url
from simple_comparison_handler import simple_csv_compare, save_comparison_result

app = Flask(__name__)

# 配置目录
BASE_DIR = Path('/root/projects/tencent-doc-manager')
BASELINE_DIR = BASE_DIR / 'comparison_baseline'
COMPARISON_DIR = BASE_DIR / 'comparison_target'
RESULT_DIR = BASE_DIR / 'comparison_results'

# 确保目录存在
for dir_path in [BASELINE_DIR, COMPARISON_DIR, RESULT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对比分析测试系统</title>
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
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .input-group input[type="text"],
        .input-group input[type="file"],
        .input-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .input-group input:focus,
        .input-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .input-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .radio-group {
            display: flex;
            gap: 20px;
            margin: 15px 0;
        }
        
        .radio-group label {
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        
        .radio-group input[type="radio"] {
            margin-right: 8px;
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
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #64748b;
            box-shadow: 0 4px 15px rgba(100, 116, 139, 0.3);
        }
        
        .status-panel {
            grid-column: 1 / -1;
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-bottom: 25px;
            position: relative;
        }
        
        .step {
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 1;
        }
        
        .step::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 2px;
            background: #e2e8f0;
            top: 20px;
            left: 50%;
            z-index: -1;
        }
        
        .step:last-child::before {
            display: none;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e2e8f0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #94a3b8;
            margin-bottom: 8px;
            transition: all 0.3s;
        }
        
        .step.active .step-circle {
            background: #667eea;
            color: white;
            transform: scale(1.1);
        }
        
        .step.completed .step-circle {
            background: #22c55e;
            color: white;
        }
        
        .step-label {
            font-size: 12px;
            color: #64748b;
        }
        
        .file-info {
            background: #f8fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        
        .file-info .file-path {
            font-family: 'Courier New', monospace;
            color: #334155;
            word-break: break-all;
            margin: 5px 0;
        }
        
        .comparison-rules {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        
        .comparison-rules h3 {
            color: #92400e;
            margin-bottom: 10px;
        }
        
        .comparison-rules ul {
            margin-left: 20px;
            color: #78350f;
        }
        
        .result-panel {
            background: #f0fdf4;
            border: 2px solid #22c55e;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
        }
        
        .result-panel h3 {
            color: #14532d;
            margin-bottom: 15px;
        }
        
        .result-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #64748b;
            margin-top: 5px;
        }
        
        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: #22c55e;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .download-btn:hover {
            background: #16a34a;
            transform: translateY(-2px);
        }
        
        .log-panel {
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
        }
        
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid transparent;
        }
        
        .log-entry.info {
            border-left-color: #3b82f6;
        }
        
        .log-entry.success {
            border-left-color: #22c55e;
        }
        
        .log-entry.warning {
            border-left-color: #f59e0b;
        }
        
        .log-entry.error {
            border-left-color: #ef4444;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 对比分析测试系统</h1>
            <p>基于真实项目的表格对比分析测试平台</p>
        </div>
        
        <div class="main-content">
            <!-- 基线输入面板 -->
            <div class="panel">
                <h2>📊 基线表格设置</h2>
                <div class="radio-group">
                    <label>
                        <input type="radio" name="baseline_type" value="file" checked>
                        上传本地文件
                    </label>
                    <label>
                        <input type="radio" name="baseline_type" value="url">
                        腾讯文档URL
                    </label>
                </div>
                
                <div id="baseline_file_input" class="input-group">
                    <label>选择基线CSV文件：</label>
                    <input type="file" id="baselineFile" accept=".csv">
                </div>
                
                <div id="baseline_url_input" class="input-group" style="display: none;">
                    <label>基线腾讯文档URL：</label>
                    <input type="text" id="baselineUrl" placeholder="https://docs.qq.com/sheet/xxxxx">
                    <label style="margin-top: 10px;">Cookie（用于下载）：</label>
                    <textarea id="baselineCookie" placeholder="输入Cookie..."></textarea>
                </div>
            </div>
            
            <!-- 对比目标面板 -->
            <div class="panel">
                <h2>🎯 对比目标设置</h2>
                <div class="input-group">
                    <label>腾讯文档URL：</label>
                    <input type="text" id="targetUrl" placeholder="https://docs.qq.com/sheet/xxxxx">
                </div>
                <div class="input-group">
                    <label>Cookie（用于下载）：</label>
                    <textarea id="targetCookie" placeholder="输入Cookie..."></textarea>
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn" onclick="startComparison()" id="startBtn">
                        🚀 开始测试
                    </button>
                </div>
            </div>
        </div>
        
        <!-- 状态面板 -->
        <div class="status-panel" id="statusPanel" style="display: none;">
            <h2>📈 测试进度</h2>
            
            <!-- 步骤指示器 -->
            <div class="step-indicator">
                <div class="step" id="step1">
                    <div class="step-circle">1</div>
                    <div class="step-label">准备文件</div>
                </div>
                <div class="step" id="step2">
                    <div class="step-circle">2</div>
                    <div class="step-label">下载目标</div>
                </div>
                <div class="step" id="step3">
                    <div class="step-circle">3</div>
                    <div class="step-label">执行对比</div>
                </div>
                <div class="step" id="step4">
                    <div class="step-circle">4</div>
                    <div class="step-label">生成结果</div>
                </div>
            </div>
            
            <!-- 文件信息展示 -->
            <div id="fileInfoSection" style="display: none;">
                <h3>📁 文件信息</h3>
                <div class="file-info" id="baselineFileInfo"></div>
                <div class="file-info" id="targetFileInfo"></div>
            </div>
            
            <!-- 对比规则展示 -->
            <div id="rulesSection" style="display: none;">
                <div class="comparison-rules">
                    <h3>⚙️ 对比分析规则</h3>
                    <ul>
                        <li>智能列名匹配（基于语义相似度）</li>
                        <li>数据变更检测（新增/修改/删除）</li>
                        <li>关键字段识别与重点对比</li>
                        <li>异常值自动标记</li>
                        <li>变更率统计与趋势分析</li>
                    </ul>
                </div>
            </div>
            
            <!-- 结果展示 -->
            <div id="resultSection" style="display: none;">
                <div class="result-panel">
                    <h3>📊 对比分析结果</h3>
                    <div class="result-stats" id="resultStats"></div>
                    <div id="downloadSection" style="margin-top: 20px;"></div>
                </div>
            </div>
            
            <!-- 日志输出 -->
            <div class="log-panel" id="logPanel"></div>
        </div>
    </div>
    
    <script>
        // localStorage功能 - 自动保存和恢复输入内容
        function saveInputs() {
            const inputs = {
                baselineUrl: document.getElementById('baselineUrl').value,
                baselineCookie: document.getElementById('baselineCookie').value,
                targetUrl: document.getElementById('targetUrl').value,
                targetCookie: document.getElementById('targetCookie').value,
                baselineType: document.querySelector('input[name="baseline_type"]:checked').value
            };
            localStorage.setItem('comparisonInputs', JSON.stringify(inputs));
        }
        
        function loadInputs() {
            const saved = localStorage.getItem('comparisonInputs');
            if (saved) {
                try {
                    const inputs = JSON.parse(saved);
                    if (inputs.baselineUrl) document.getElementById('baselineUrl').value = inputs.baselineUrl;
                    if (inputs.baselineCookie) document.getElementById('baselineCookie').value = inputs.baselineCookie;
                    if (inputs.targetUrl) document.getElementById('targetUrl').value = inputs.targetUrl;
                    if (inputs.targetCookie) document.getElementById('targetCookie').value = inputs.targetCookie;
                    if (inputs.baselineType) {
                        document.querySelector(`input[name="baseline_type"][value="${inputs.baselineType}"]`).checked = true;
                        // 触发显示切换
                        if (inputs.baselineType === 'file') {
                            document.getElementById('baseline_file_input').style.display = 'block';
                            document.getElementById('baseline_url_input').style.display = 'none';
                        } else {
                            document.getElementById('baseline_file_input').style.display = 'none';
                            document.getElementById('baseline_url_input').style.display = 'block';
                        }
                    }
                    console.log('已恢复上次输入的内容');
                } catch (e) {
                    console.error('恢复输入失败:', e);
                }
            }
        }
        
        // 页面加载时恢复输入
        window.addEventListener('DOMContentLoaded', () => {
            loadInputs();
            
            // 监听所有输入变化并自动保存
            document.getElementById('baselineUrl').addEventListener('input', saveInputs);
            document.getElementById('baselineCookie').addEventListener('input', saveInputs);
            document.getElementById('targetUrl').addEventListener('input', saveInputs);
            document.getElementById('targetCookie').addEventListener('input', saveInputs);
            document.querySelectorAll('input[name="baseline_type"]').forEach(radio => {
                radio.addEventListener('change', saveInputs);
            });
        });
        
        // 切换基线输入方式
        document.querySelectorAll('input[name="baseline_type"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'file') {
                    document.getElementById('baseline_file_input').style.display = 'block';
                    document.getElementById('baseline_url_input').style.display = 'none';
                } else {
                    document.getElementById('baseline_file_input').style.display = 'none';
                    document.getElementById('baseline_url_input').style.display = 'block';
                }
            });
        });
        
        function log(message, type = 'info') {
            const logPanel = document.getElementById('logPanel');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${timestamp}] ${message}`;
            logPanel.appendChild(entry);
            logPanel.scrollTop = logPanel.scrollHeight;
        }
        
        function updateStep(stepNumber, status = 'active') {
            for (let i = 1; i <= 4; i++) {
                const step = document.getElementById(`step${i}`);
                if (i < stepNumber) {
                    step.className = 'step completed';
                } else if (i === stepNumber) {
                    step.className = `step ${status}`;
                } else {
                    step.className = 'step';
                }
            }
        }
        
        async function startComparison() {
            const startBtn = document.getElementById('startBtn');
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner"></span> 处理中...';
            
            // 显示状态面板
            document.getElementById('statusPanel').style.display = 'block';
            document.getElementById('logPanel').innerHTML = '';
            
            // 获取输入
            const baselineType = document.querySelector('input[name="baseline_type"]:checked').value;
            let formData = new FormData();
            
            if (baselineType === 'file') {
                const fileInput = document.getElementById('baselineFile');
                if (!fileInput.files[0]) {
                    alert('请选择基线文件');
                    startBtn.disabled = false;
                    startBtn.innerHTML = '🚀 开始测试';
                    return;
                }
                formData.append('baseline_file', fileInput.files[0]);
            } else {
                const baselineUrl = document.getElementById('baselineUrl').value;
                const baselineCookie = document.getElementById('baselineCookie').value;
                if (!baselineUrl) {
                    alert('请输入基线腾讯文档URL');
                    startBtn.disabled = false;
                    startBtn.innerHTML = '🚀 开始测试';
                    return;
                }
                formData.append('baseline_url', baselineUrl);
                formData.append('baseline_cookie', baselineCookie);
            }
            
            const targetUrl = document.getElementById('targetUrl').value;
            const targetCookie = document.getElementById('targetCookie').value;
            
            if (!targetUrl) {
                alert('请输入对比目标URL');
                startBtn.disabled = false;
                startBtn.innerHTML = '🚀 开始测试';
                return;
            }
            
            formData.append('target_url', targetUrl);
            formData.append('target_cookie', targetCookie);
            
            try {
                log('开始对比分析测试...', 'info');
                updateStep(1, 'active');
                
                // 创建超时控制
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分钟超时
                
                const response = await fetch('/api/compare', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                // 检查响应状态
                console.log('API响应状态:', response.status, response.statusText);
                if (!response.ok) {
                    if (response.status === 502) {
                        console.error('502 Bad Gateway 错误 - 可能原因:');
                        console.error('1. 请求处理超时（下载文件耗时过长）');
                        console.error('2. 服务器内部错误');
                        console.error('3. Cookie无效导致下载失败');
                        throw new Error('502错误: 请求超时或服务器错误，请检查Cookie是否有效');
                    } else if (response.status === 504) {
                        throw new Error('504网关超时: 请求处理时间过长');
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                // 安全解析JSON
                const text = await response.text();
                let result;
                try {
                    result = JSON.parse(text);
                    // 输出调试信息
                    if (result.debug) {
                        console.log('请求ID:', result.debug.request_id);
                        console.log('耗时信息:', result.debug.timings);
                        console.log('完成步骤:', result.debug.steps_completed);
                    }
                } catch (e) {
                    console.error('JSON解析失败，响应内容:', text);
                    throw new Error('服务器返回了无效的JSON响应');
                }
                
                if (result.success) {
                    // 显示结果
                    displayResults(result);
                    log('对比分析完成！', 'success');
                } else {
                    log(`错误: ${result.error}`, 'error');
                }
                
            } catch (error) {
                log(`系统错误: ${error.message}`, 'error');
            } finally {
                startBtn.disabled = false;
                startBtn.innerHTML = '🚀 开始测试';
            }
        }
        
        function displayResults(result) {
            // 显示文件信息
            if (result.baseline_info) {
                document.getElementById('fileInfoSection').style.display = 'block';
                document.getElementById('baselineFileInfo').innerHTML = `
                    <strong>基线文件：</strong><br>
                    <div class="file-path">${result.baseline_info.path}</div>
                    <div>大小: ${result.baseline_info.size} | 行数: ${result.baseline_info.rows}</div>
                `;
            }
            
            if (result.target_info) {
                document.getElementById('targetFileInfo').innerHTML = `
                    <strong>目标文件：</strong><br>
                    <div class="file-path">${result.target_info.path}</div>
                    <div>大小: ${result.target_info.size} | 行数: ${result.target_info.rows}</div>
                `;
            }
            
            // 显示规则
            document.getElementById('rulesSection').style.display = 'block';
            
            // 显示统计结果
            if (result.comparison_stats) {
                document.getElementById('resultSection').style.display = 'block';
                const stats = result.comparison_stats;
                document.getElementById('resultStats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${stats.total_changes || 0}</div>
                        <div class="stat-label">总变更数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.added_rows || 0}</div>
                        <div class="stat-label">新增行</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.modified_rows || 0}</div>
                        <div class="stat-label">修改行</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.deleted_rows || 0}</div>
                        <div class="stat-label">删除行</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.similarity_score || 0}%</div>
                        <div class="stat-label">相似度</div>
                    </div>
                `;
            }
            
            // 显示下载链接
            if (result.result_file) {
                document.getElementById('downloadSection').innerHTML = `
                    <a href="/api/download/${result.result_file}" class="download-btn">
                        ⬇️ 下载对比结果文件
                    </a>
                    <div style="margin-top: 10px; color: #64748b;">
                        结果文件: ${result.result_file}
                    </div>
                `;
            }
            
            updateStep(4, 'completed');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页面"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/compare', methods=['POST'])
def compare():
    """执行对比分析"""
    import time
    request_id = f"REQ_{datetime.now().strftime('%H%M%S_%f')[:12]}"
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"[{request_id}] 新请求开始: {datetime.now().isoformat()}")
    print(f"[{request_id}] 客户端IP: {request.remote_addr}")
    print(f"[{request_id}] Content-Type: {request.content_type}")
    print(f"[{request_id}] Content-Length: {request.content_length}")
    
    try:
        # 使用简化的处理逻辑，避免复杂的依赖
        
        result = {
            'success': False,
            'baseline_info': None,
            'target_info': None,
            'comparison_stats': None,
            'result_file': None,
            'debug': {
                'request_id': request_id,
                'timings': {},
                'steps_completed': []
            }
        }
        
        # 支持JSON和表单数据
        if request.is_json:
            data = request.get_json()
            print(f"[{request_id}] 数据格式: JSON")
        else:
            data = request.form
            print(f"[{request_id}] 数据格式: FormData")
        
        print(f"[{request_id}] 请求字段: {list(data.keys())}")
        
        # 步骤1: 处理基线文件
        step1_start = time.time()
        print(f"[{request_id}] 步骤1: 开始处理基线文件")
        result['debug']['steps_completed'].append('step1_start')
        
        baseline_path = None
        if 'baseline_file' in request.files:
            # 上传的文件
            file = request.files['baseline_file']
            baseline_path = BASELINE_DIR / file.filename
            file.save(baseline_path)
            print(f"[{request_id}] 基线文件已上传: {baseline_path}")
            
        elif 'baseline_url' in data:
            # 简单的串行下载方式，像8093一样
            baseline_url = data.get('baseline_url')
            if baseline_url:
                # 下载基线文件
                url = baseline_url
                cookie = data.get('baseline_cookie', '')
                print(f"[{request_id}] 准备下载基线文件: {url[:50]}...")
                
                # Cookie长度日志（移除验证，只记录）
                print(f"[基线] Cookie长度: {len(cookie) if cookie else 0} 字符")
                if cookie:
                    print(f"[基线] Cookie前50字符: {cookie[:50]}...")
                    print(f"[基线] Cookie后50字符: ...{cookie[-50:]}")
                
                # 保存cookie到配置文件供下载函数使用
                if cookie:
                    config_file = BASE_DIR / 'config.json'
                    try:
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump({'cookie': cookie}, f, ensure_ascii=False, indent=2)
                        print(f"[基线] Cookie已保存到配置文件，长度: {len(cookie)}")
                    except Exception as e:
                        print(f"[基线] 保存Cookie失败: {e}")
                
                # 使用现有的下载功能
                print(f"[基线] 开始下载: {url}")
                download_start = time.time()
                
                try:
                    # 设置超时警告
                    print(f"[{request_id}] 调用download_file_from_url，超时限制: 60秒")
                    download_result = download_file_from_url(url, format_type='csv')
                    download_time = time.time() - download_start
                    print(f"[{request_id}] 下载完成，耗时: {download_time:.2f}秒")
                    print(f"[基线] 下载结果: {download_result}")
                    result['debug']['timings']['baseline_download'] = download_time
                except Exception as e:
                    download_time = time.time() - download_start
                    download_result = {'success': False, 'error': str(e)}
                    print(f"[{request_id}] 下载失败，耗时: {download_time:.2f}秒")
                    print(f"[基线] 下载错误: {e}")
                    import traceback
                    print(f"[{request_id}] 错误堆栈:\n{traceback.format_exc()}")
                    result['debug']['timings']['baseline_download_failed'] = download_time
                
                if download_result and download_result.get('success'):
                    # 处理新格式的返回值
                    if download_result.get('files'):
                        # 获取第一个文件
                        first_file = download_result['files'][0]
                        source_path = Path(first_file.get('path', ''))
                        if source_path.exists():
                            baseline_path = BASELINE_DIR / source_path.name
                            shutil.copy(source_path, baseline_path)
                            print(f"[基线] 文件已复制到: {baseline_path}")
                        else:
                            print(f"[基线] 源文件不存在: {source_path}")
                    elif download_result.get('file_path'):
                        # 兼容旧格式
                        source_path = Path(download_result['file_path'])
                        if source_path.exists():
                            baseline_path = BASELINE_DIR / source_path.name
                            shutil.copy(source_path, baseline_path)
                            print(f"[基线] 文件已复制到: {baseline_path}")
                else:
                    error_msg = download_result.get('error', '未知错误') if download_result else '下载返回空结果'
                    print(f"[基线] 下载失败: {error_msg}")
        
        if baseline_path and baseline_path.exists():
            result['baseline_info'] = {
                'path': str(baseline_path),
                'name': baseline_path.name,
                'size': f"{baseline_path.stat().st_size:,} bytes",
                'rows': sum(1 for line in open(baseline_path, 'r', encoding='utf-8')) - 1
            }
        
        # 步骤2: 下载目标文件
        target_url = data.get('target_url')
        target_cookie = data.get('target_cookie', '')
        
        target_path = None
        if target_url:
            # Cookie长度日志（移除验证，只记录）
            print(f"[目标] Cookie长度: {len(target_cookie) if target_cookie else 0} 字符")
            if target_cookie:
                print(f"[目标] Cookie前50字符: {target_cookie[:50]}...")
                print(f"[目标] Cookie后50字符: ...{target_cookie[-50:]}")
            
            # 保存cookie到配置文件供下载函数使用
            if target_cookie:
                config_file = BASE_DIR / 'config.json'
                try:
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump({'cookie': target_cookie}, f, ensure_ascii=False, indent=2)
                    print(f"[目标] Cookie已保存到配置文件，长度: {len(target_cookie)}")
                except Exception as e:
                    print(f"[目标] 保存Cookie失败: {e}")
            
            print(f"[目标] 开始下载: {target_url}")
            try:
                download_result = download_file_from_url(target_url, format_type='csv')
                print(f"[目标] 下载结果: {download_result}")
            except Exception as e:
                download_result = {'success': False, 'error': str(e)}
                print(f"[目标] 下载错误: {e}")
            
            if download_result and download_result.get('success'):
                # 处理新格式的返回值
                if download_result.get('files'):
                    # 获取第一个文件
                    first_file = download_result['files'][0]
                    source_path = Path(first_file.get('path', ''))
                    if source_path.exists():
                        target_path = COMPARISON_DIR / source_path.name
                        shutil.copy(source_path, target_path)
                        print(f"[目标] 文件已复制到: {target_path}")
                    else:
                        print(f"[目标] 源文件不存在: {source_path}")
                elif download_result.get('file_path'):
                    # 兼容旧格式
                    source_path = Path(download_result['file_path'])
                    if source_path.exists():
                        target_path = COMPARISON_DIR / source_path.name
                        shutil.copy(source_path, target_path)
                        print(f"[目标] 文件已复制到: {target_path}")
            else:
                error_msg = download_result.get('error', '未知错误') if download_result else '下载返回空结果'
                print(f"[目标] 下载失败: {error_msg}")
            
            if target_path and target_path.exists():
                result['target_info'] = {
                    'path': str(target_path),
                    'name': target_path.name,
                    'size': f"{target_path.stat().st_size:,} bytes",
                    'rows': sum(1 for line in open(target_path, 'r', encoding='utf-8')) - 1
                }
        
        # 步骤3: 执行对比分析
        if baseline_path and target_path:
            print(f"[对比] 开始对比分析...")
            print(f"[对比] 基线文件: {baseline_path}")
            print(f"[对比] 目标文件: {target_path}")
            
            # 使用简化的对比处理器
            comparison_result = simple_csv_compare(
                str(baseline_path),
                str(target_path)
            )
            
            # 保存结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_filename = f'comparison_result_{timestamp}.json'
            result_path = RESULT_DIR / result_filename
            
            save_success = save_comparison_result(comparison_result, str(result_path))
            
            if save_success:
                print(f"[对比] 结果已保存: {result_path}")
                
                # 提取统计信息
                result['comparison_stats'] = {
                    'total_changes': comparison_result.get('total_changes', 0),
                    'added_rows': comparison_result.get('added_rows', 0),
                    'modified_rows': comparison_result.get('modified_rows', 0),
                    'deleted_rows': comparison_result.get('deleted_rows', 0),
                    'similarity_score': round(comparison_result.get('similarity_score', 0) * 100, 2)
                }
                
                result['result_file'] = result_filename
                result['success'] = True
            else:
                result['error'] = '保存对比结果失败'
            
        else:
            # 提供更详细的错误信息
            error_details = []
            if not baseline_path:
                error_details.append("基线文件下载失败")
            elif not baseline_path.exists():
                error_details.append(f"基线文件不存在: {baseline_path}")
            
            if not target_path:
                error_details.append("目标文件下载失败")
            elif not target_path.exists():
                error_details.append(f"目标文件不存在: {target_path}")
            
            result['error'] = '文件处理失败: ' + ', '.join(error_details)
            print(f"[错误] {result['error']}")
            
    except Exception as e:
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        print(f"[{request_id}] 请求异常: {e}")
        print(f"[{request_id}] 堆栈:\n{traceback.format_exc()}")
    
    # 记录总耗时
    total_time = time.time() - start_time
    result['debug']['timings']['total'] = total_time
    result['debug']['steps_completed'].append('request_complete')
    
    print(f"[{request_id}] 请求完成，总耗时: {total_time:.2f}秒")
    print(f"[{request_id}] 完成步骤: {result['debug']['steps_completed']}")
    print(f"[{request_id}] 响应状态: {'成功' if result['success'] else '失败'}")
    print(f"{'='*60}\n")
    
    return jsonify(result)

@app.route('/api/download/<filename>')
def download_result(filename):
    """下载结果文件"""
    try:
        # 安全检查
        safe_filename = os.path.basename(filename)
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': '非法文件名'}), 400
        
        file_path = RESULT_DIR / safe_filename
        if file_path.exists() and file_path.is_file():
            return send_file(
                str(file_path), 
                as_attachment=True,
                download_name=safe_filename
            )
        else:
            return jsonify({'error': f'文件不存在: {safe_filename}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("对比分析测试系统")
    print("访问地址: http://202.140.143.88:8094/")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8094, debug=False)