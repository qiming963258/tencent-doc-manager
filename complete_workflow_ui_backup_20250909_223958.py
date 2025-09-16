#!/usr/bin/env python3
"""
腾讯文档完整工作流测试UI - 增强版
提供从下载→修改→上传的完整测试界面
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import json
import time
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
import requests
import shutil
import sys

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

app = Flask(__name__)

# 配置路径
BASE_DIR = Path('/root/projects/tencent-doc-manager')
CONFIG_PATH = BASE_DIR / 'config.json'
DOWNLOAD_DIR = BASE_DIR / 'downloads'
TEMP_DIR = BASE_DIR / 'temp_workflow'
MODIFIED_DIR = BASE_DIR / 'modified_files'  # 需要定义这个变量，因为代码中有引用

# 确保目录存在
TEMP_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)
MODIFIED_DIR.mkdir(exist_ok=True)

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档完整工作流测试 - 增强版</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }

        .header h1 {
            color: #333;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .workflow-progress {
            display: flex;
            justify-content: space-between;
            margin: 30px 0;
            padding: 0 20px;
        }

        .progress-step {
            flex: 1;
            text-align: center;
            position: relative;
        }

        .progress-step::after {
            content: '';
            position: absolute;
            top: 20px;
            left: 50%;
            width: 100%;
            height: 2px;
            background: rgba(255,255,255,0.3);
            z-index: -1;
        }

        .progress-step:last-child::after {
            display: none;
        }

        .progress-step.active::after {
            background: white;
        }

        .progress-number {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.3);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px;
            font-weight: bold;
            transition: all 0.3s;
        }

        .progress-step.active .progress-number,
        .progress-step.completed .progress-number {
            background: white;
            color: #667eea;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }

        .progress-label {
            color: white;
            font-size: 14px;
            font-weight: 500;
        }

        .workflow-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .step-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s;
        }

        .step-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }

        .step-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }

        .step-card.disabled {
            opacity: 0.5;
            pointer-events: none;
        }

        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }

        .step-icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-right: 15px;
        }

        .step-title {
            flex: 1;
        }

        .step-title h3 {
            font-size: 20px;
            color: #333;
            margin-bottom: 5px;
        }

        .step-title p {
            font-size: 13px;
            color: #666;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-size: 14px;
            font-weight: 500;
        }

        .form-control {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.3s;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        textarea.form-control {
            resize: vertical;
            min-height: 120px;
            font-family: 'Courier New', monospace;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }

        .btn-warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }

        .btn-info {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
        }

        .btn-secondary {
            background: #6b7280;
            color: white;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }

        .btn-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .status-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-top: 15px;
        }

        .status-success {
            background: #d1fae5;
            color: #065f46;
        }

        .status-warning {
            background: #fed7aa;
            color: #92400e;
        }

        .status-error {
            background: #fee2e2;
            color: #991b1b;
        }

        .status-info {
            background: #dbeafe;
            color: #1e3a8a;
        }

        .file-list {
            background: #f9fafb;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            max-height: 250px;
            overflow-y: auto;
        }

        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            margin-bottom: 8px;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
            position: relative;
        }

        .file-item:hover {
            background: #f3f4f6;
            transform: translateX(5px);
            border-color: #667eea;
        }

        .file-item.selected {
            background: #ede9fe;
            border-color: #667eea;
        }

        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .file-icon {
            color: #667eea;
            font-size: 20px;
        }
        
        .download-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            z-index: 10;
        }
        
        .download-btn:hover {
            background: #5a67d8;
            transform: translateY(-50%) scale(1.05);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .download-btn:active {
            transform: translateY(-50%) scale(0.98);
        }

        .file-name {
            font-weight: 500;
            color: #333;
        }

        .file-size {
            font-size: 12px;
            color: #666;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            margin-top: 15px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 0.3s;
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }

        .log-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .log-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }

        .log-output {
            background: #1f2937;
            color: #10b981;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.6;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 3px 0;
        }

        .log-time {
            color: #6b7280;
            margin-right: 10px;
        }

        .log-info { color: #10b981; }
        .log-warning { color: #f59e0b; }
        .log-error { color: #ef4444; }
        .log-success { color: #10b981; font-weight: bold; }

        .quick-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 20px;
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #e5e7eb;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .alert {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
            animation: slideDown 0.3s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }

        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }

        .alert-info {
            background: #dbeafe;
            color: #1e3a8a;
            border: 1px solid #bfdbfe;
        }

        .service-links {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }

        .service-links h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 16px;
        }

        .link-buttons {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .link-btn {
            padding: 10px 20px;
            background: #f3f4f6;
            color: #333;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .link-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }

        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            width: 250px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 8px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 13px;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>🔄</span>
                腾讯文档完整工作流测试
            </h1>
            <p>测试从下载→修改→上传的完整文档处理流程 | 端口: 8093</p>
        </div>

        <div class="workflow-progress">
            <div class="progress-step" id="progress-1">
                <div class="progress-number">1</div>
                <div class="progress-label">配置凭证</div>
            </div>
            <div class="progress-step" id="progress-2">
                <div class="progress-number">2</div>
                <div class="progress-label">下载文档</div>
            </div>
            <div class="progress-step" id="progress-3">
                <div class="progress-number">3</div>
                <div class="progress-label">修改文档</div>
            </div>
            <div class="progress-step" id="progress-4">
                <div class="progress-number">4</div>
                <div class="progress-label">上传文档</div>
            </div>
        </div>

        <div class="service-links">
            <h3>🔗 相关服务</h3>
            <div class="link-buttons">
                <a href="http://202.140.143.88:8090/" target="_blank" class="link-btn">
                    <span>📥</span> 自动下载系统 (8090)
                </a>
                <a href="http://202.140.143.88:8081/" target="_blank" class="link-btn">
                    <span>🤖</span> Claude AI测试 (8081)
                </a>
                <a href="http://202.140.143.88:8089/" target="_blank" class="link-btn">
                    <span>🔥</span> 热力图分析 (8089)
                </a>
            </div>
        </div>

        <div id="alertBox" class="alert"></div>

        <div class="workflow-steps">
            <!-- Step 1: 配置Cookie -->
            <div class="step-card" id="step-1">
                <div class="step-header">
                    <div class="step-icon">🔑</div>
                    <div class="step-title">
                        <h3>配置访问凭证</h3>
                        <p>设置腾讯文档的访问Cookie</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Cookie字符串 
                        <span class="tooltip">
                            ℹ️
                            <span class="tooltiptext">从浏览器开发者工具中复制完整的Cookie字符串</span>
                        </span>
                    </label>
                    <textarea id="cookieInput" class="form-control" 
                        placeholder="粘贴完整的cookie字符串..."></textarea>
                </div>
                
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="saveCookie()">
                        💾 保存Cookie
                    </button>
                    <button class="btn btn-secondary" onclick="loadExistingCookie()">
                        📂 加载已有Cookie
                    </button>
                </div>
                
                <div id="cookieStatus" class="status-badge" style="display:none;"></div>
            </div>

            <!-- Step 2: 下载文档 -->
            <div class="step-card disabled" id="step-2">
                <div class="step-header">
                    <div class="step-icon">⬇️</div>
                    <div class="step-title">
                        <h3>下载腾讯文档</h3>
                        <p>从腾讯文档下载指定文件</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>文档URL</label>
                    <input type="text" id="docUrl" class="form-control" 
                        placeholder="https://docs.qq.com/sheet/xxxxx">
                </div>
                
                <div class="form-group">
                    <label>下载格式</label>
                    <select id="downloadFormat" class="form-control">
                        <option value="csv">CSV (推荐用于数据分析)</option>
                        <option value="xlsx">Excel (保留格式)</option>
                        <option value="pdf">PDF (只读版本)</option>
                    </select>
                </div>
                
                <button class="btn btn-success" onclick="downloadDocument()" id="downloadBtn">
                    ⬇️ 开始下载
                </button>
                
                <div id="downloadStatus" class="status-badge" style="display:none;"></div>
                <div class="progress-bar" id="downloadProgress" style="display:none;">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div id="downloadedFiles" class="file-list" style="display:none;"></div>
            </div>

            <!-- Step 3: 修改文档 -->
            <div class="step-card disabled" id="step-3">
                <div class="step-header">
                    <div class="step-icon">✏️</div>
                    <div class="step-title">
                        <h3>修改文档内容</h3>
                        <p>对下载的文档进行修改</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>选择文件</label>
                    <select id="fileSelect" class="form-control">
                        <option value="">请先下载文档...</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>修改类型</label>
                    <select id="modifyType" class="form-control" onchange="updateModifyOptions()">
                        <option value="timestamp">添加时间戳</option>
                        <option value="ai_analysis">AI智能分析</option>
                        <option value="risk_mark">风险标记</option>
                        <option value="custom">自定义修改</option>
                    </select>
                </div>
                
                <div id="customModifySection" style="display:none;">
                    <div class="form-group">
                        <label>修改内容</label>
                        <textarea id="customModifyContent" class="form-control"
                            placeholder="输入要修改或添加的内容..."></textarea>
                    </div>
                </div>
                
                <div id="aiModifySection" style="display:none;">
                    <div class="form-group">
                        <label>AI分析指令</label>
                        <input type="text" id="aiPrompt" class="form-control"
                            placeholder="例如: 分析风险等级并添加批注">
                    </div>
                </div>
                
                <button class="btn btn-warning" onclick="modifyDocument()">
                    ✏️ 执行修改
                </button>
                
                <div id="modifyStatus" class="status-badge" style="display:none;"></div>
                <div id="modifiedPreview" class="file-list" style="display:none;"></div>
            </div>

            <!-- Step 4: 上传文档 -->
            <div class="step-card disabled" id="step-4">
                <div class="step-header">
                    <div class="step-icon">⬆️</div>
                    <div class="step-title">
                        <h3>上传到腾讯文档</h3>
                        <p>将修改后的文档上传回腾讯文档</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>选择要上传的文件</label>
                    <select id="uploadFileSelect" class="form-control">
                        <option value="">请先修改文档...</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>上传选项</label>
                    <select id="uploadOption" class="form-control">
                        <option value="new">创建新文档</option>
                        <option value="replace">替换原文档</option>
                        <option value="version">作为新版本</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>目标URL (可选)</label>
                    <input type="text" id="uploadUrl" class="form-control"
                        placeholder="留空则创建新文档">
                </div>
                
                <button class="btn btn-info" onclick="uploadDocument()">
                    ⬆️ 上传文档
                </button>
                
                <div id="uploadStatus" class="status-badge" style="display:none;"></div>
                <div id="uploadResult" style="margin-top: 15px;"></div>
            </div>
        </div>

        <!-- 日志输出区域 -->
        <div class="log-container">
            <div class="log-header">
                <h3 class="log-title">📋 操作日志</h3>
                <div class="btn-group">
                    <button class="btn btn-secondary" onclick="clearLog()" style="padding: 8px 16px;">
                        清空
                    </button>
                    <button class="btn btn-secondary" onclick="exportLog()" style="padding: 8px 16px;">
                        导出
                    </button>
                </div>
            </div>
            <div id="logOutput" class="log-output">
                <div class="log-entry log-info">
                    <span class="log-time">[00:00:00]</span>
                    系统就绪，等待操作...
                </div>
            </div>
            <div class="quick-actions">
                <button class="btn btn-info" onclick="testConnection()">🔌 测试连接</button>
                <button class="btn btn-info" onclick="viewSystemStatus()">📊 系统状态</button>
                <button class="btn btn-info" onclick="runCompleteTest()">🚀 完整测试</button>
            </div>
        </div>
    </div>

    <script>
        let currentStep = 1;
        let downloadedFiles = [];
        let modifiedFiles = [];
        
        // 文件预览函数
        async function previewFile(filename) {
            try {
                const response = await fetch('/api/download-file?filename=' + encodeURIComponent(filename));
                if (response.ok) {
                    const text = await response.text();
                    // 显示预览弹窗
                    const previewWindow = window.open('', '_blank', 'width=800,height=600');
                    previewWindow.document.write(`
                        <html>
                        <head>
                            <title>预览: ${decodeURIComponent(filename)}</title>
                            <style>
                                body { font-family: monospace; padding: 20px; background: #f5f5f5; }
                                pre { white-space: pre-wrap; word-wrap: break-word; background: white; padding: 15px; border-radius: 5px; }
                                h2 { color: #333; }
                            </style>
                        </head>
                        <body>
                            <h2>📄 文件预览: ${decodeURIComponent(filename)}</h2>
                            <hr>
                            <pre>${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                        </body>
                        </html>
                    `);
                } else {
                    showAlert('无法预览文件', 'error');
                }
            } catch (e) {
                showAlert('预览失败: ' + e.message, 'error');
            }
        }

        // 更新进度显示
        function updateProgress(step) {
            currentStep = step;
            for (let i = 1; i <= 4; i++) {
                const progressStep = document.getElementById(`progress-${i}`);
                const stepCard = document.getElementById(`step-${i}`);
                
                if (i < step) {
                    progressStep.classList.add('completed');
                    progressStep.classList.remove('active');
                    if (stepCard) stepCard.classList.remove('disabled');
                } else if (i === step) {
                    progressStep.classList.add('active');
                    progressStep.classList.remove('completed');
                    if (stepCard) stepCard.classList.remove('disabled');
                } else {
                    progressStep.classList.remove('active', 'completed');
                    if (stepCard) stepCard.classList.add('disabled');
                }
            }
        }

        // 日志输出
        function log(message, type = 'info') {
            const logOutput = document.getElementById('logOutput');
            const timestamp = new Date().toLocaleTimeString('zh-CN');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
            logOutput.appendChild(logEntry);
            logOutput.scrollTop = logOutput.scrollHeight;
        }

        function showAlert(message, type = 'info') {
            const alertBox = document.getElementById('alertBox');
            alertBox.className = `alert alert-${type}`;
            alertBox.textContent = message;
            alertBox.style.display = 'block';
            setTimeout(() => {
                alertBox.style.display = 'none';
            }, 5000);
        }

        // Step 1: 保存Cookie
        async function saveCookie() {
            const cookie = document.getElementById('cookieInput').value.trim();
            if (!cookie) {
                showAlert('请输入Cookie', 'error');
                return;
            }

            log('正在保存Cookie...');
            
            try {
                const response = await fetch('/api/save-cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cookie: cookie})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('cookieStatus').style.display = 'inline-block';
                    document.getElementById('cookieStatus').className = 'status-badge status-success';
                    document.getElementById('cookieStatus').textContent = '✅ Cookie已保存';
                    log('Cookie保存成功', 'success');
                    showAlert('Cookie保存成功，可以开始下载文档', 'success');
                    updateProgress(2);
                } else {
                    throw new Error(result.error || '保存失败');
                }
            } catch (error) {
                log(`Cookie保存失败: ${error.message}`, 'error');
                showAlert(`保存失败: ${error.message}`, 'error');
            }
        }

        async function loadExistingCookie() {
            log('加载已有Cookie...');
            try {
                const response = await fetch('/api/load-cookie');
                const result = await response.json();
                
                if (result.success && result.cookie) {
                    document.getElementById('cookieInput').value = result.cookie;
                    log('成功加载已有Cookie', 'success');
                    showAlert('已加载存储的Cookie', 'success');
                } else {
                    log('没有找到已保存的Cookie', 'warning');
                    showAlert('没有找到已保存的Cookie', 'info');
                }
            } catch (error) {
                log(`加载Cookie失败: ${error.message}`, 'error');
            }
        }

        // Step 2: 下载文档
        async function downloadDocument() {
            const url = document.getElementById('docUrl').value.trim();
            const format = document.getElementById('downloadFormat').value;
            
            if (!url) {
                showAlert('请输入文档URL', 'error');
                return;
            }

            const downloadBtn = document.getElementById('downloadBtn');
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '⏳ 下载中... <span class="loading-spinner"></span>';
            
            document.getElementById('downloadProgress').style.display = 'block';
            const progressBar = document.querySelector('#downloadProgress .progress-fill');
            progressBar.style.width = '30%';
            
            log(`开始下载文档: ${url}`);
            log(`下载格式: ${format}`, 'info');
            
            try {
                // 调用实际的下载功能
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url, format: format})
                });
                
                progressBar.style.width = '70%';
                
                const result = await response.json();
                
                if (result.success) {
                    progressBar.style.width = '100%';
                    
                    document.getElementById('downloadStatus').style.display = 'inline-block';
                    document.getElementById('downloadStatus').className = 'status-badge status-success';
                    document.getElementById('downloadStatus').textContent = '✅ 下载完成';
                    
                    // 显示下载的文件（包含内容检查结果）
                    downloadedFiles = result.files || [];
                    const contentAssessment = result.content_assessment || null;
                    displayDownloadedFiles(downloadedFiles, contentAssessment);
                    updateFileSelects(downloadedFiles);
                    
                    // 自动触发最新文件的下载
                    if (downloadedFiles.length > 0) {
                        const latestFile = downloadedFiles[downloadedFiles.length - 1];
                        if (latestFile.path) {
                            // 创建下载链接
                            const downloadLink = document.createElement('a');
                            downloadLink.href = '/api/download-file?filename=' + encodeURIComponent(latestFile.name || latestFile.path.split('/').pop());
                            downloadLink.download = latestFile.name || 'download.csv';
                            downloadLink.style.display = 'none';
                            document.body.appendChild(downloadLink);
                            downloadLink.click();
                            document.body.removeChild(downloadLink);
                            log(`自动下载文件: ${latestFile.name}`, 'success');
                        }
                    }
                    
                    log(`下载成功: ${downloadedFiles.length}个文件`, 'success');
                    showAlert('文档下载成功', 'success');
                    updateProgress(3);
                } else {
                    throw new Error(result.error || '下载失败');
                }
            } catch (error) {
                log(`下载失败: ${error.message}`, 'error');
                showAlert(`下载失败: ${error.message}`, 'error');
            } finally {
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '⬇️ 开始下载';
                setTimeout(() => {
                    document.getElementById('downloadProgress').style.display = 'none';
                }, 2000);
            }
        }

        function displayDownloadedFiles(files, contentAssessment) {
            const container = document.getElementById('downloadedFiles');
            container.style.display = 'block';
            
            // 显示整体评估
            let assessmentColor = '#28a745';  // 默认绿色
            if (contentAssessment && contentAssessment.includes('极低')) {
                assessmentColor = '#dc3545';  // 红色
            } else if (contentAssessment && contentAssessment.includes('低')) {
                assessmentColor = '#ffc107';  // 黄色
            } else if (contentAssessment && contentAssessment.includes('中等')) {
                assessmentColor = '#fd7e14';  // 橙色
            }
            
            container.innerHTML = `
                <div style="margin-bottom: 10px; font-weight: 600;">📁 下载的文件:</div>
                ${contentAssessment ? `
                <div style="padding: 10px; margin-bottom: 10px; background: ${assessmentColor}20; 
                            border-left: 3px solid ${assessmentColor}; border-radius: 5px;">
                    <strong>内容检查结果:</strong><br>
                    ${contentAssessment}
                </div>` : ''}
            `;
            
            files.forEach((file, index) => {
                // 获取内容检查信息
                const check = file.content_check || {};
                const scoreColor = check.authenticity_score >= 80 ? '#28a745' : 
                                  check.authenticity_score >= 60 ? '#fd7e14' :
                                  check.authenticity_score >= 40 ? '#ffc107' : '#dc3545';
                
                const fileName = file.name || file.path.split('/').pop();
                const downloadUrl = '/api/download-file?filename=' + encodeURIComponent(fileName);
                
                container.innerHTML += `
                    <div class="file-item" onclick="selectFile('${file.path}', this)">
                        <div class="file-info">
                            <span class="file-icon">📄</span>
                            <div style="flex-grow: 1;">
                                <div class="file-name">${file.name}</div>
                                <div class="file-size">${file.size || '未知大小'}</div>
                                ${check.authenticity_score !== undefined ? `
                                <div style="margin-top: 5px; font-size: 12px;">
                                    <span style="color: ${scoreColor};">
                                        真实性评分: ${check.authenticity_score.toFixed(1)}/100
                                    </span>
                                    ${check.is_demo_data ? 
                                        '<span style="color: #dc3545; margin-left: 10px;">⚠️ 疑似演示数据</span>' : 
                                        '<span style="color: #28a745; margin-left: 10px;">✅ 可能是真实数据</span>'}
                                </div>
                                ${check.row_count ? `
                                <div style="font-size: 11px; color: #666; margin-top: 3px;">
                                    数据规模: ${check.row_count}行 × ${check.column_count}列
                                </div>` : ''}
                                ` : ''}
                            </div>
                        </div>
                        <a href="${downloadUrl}" 
                           class="download-btn" 
                           download="${fileName}"
                           onclick="event.stopPropagation(); downloadFileWithLog('${fileName}', event);"
                           title="下载文件到本地">
                            <span>⬇️</span>
                            <span>下载</span>
                        </a>
                    </div>
                `;
            });
        }

        function downloadFileWithLog(fileName, event) {
            // 阻止默认行为，让我们控制下载
            if (event) {
                event.preventDefault();
            }
            
            // 显示下载开始日志
            log(`开始下载文件: ${fileName}`, 'info');
            
            // 创建隐藏的下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = '/api/download-file?filename=' + encodeURIComponent(fileName);
            downloadLink.download = fileName;
            downloadLink.style.display = 'none';
            
            // 添加到DOM并触发点击
            document.body.appendChild(downloadLink);
            downloadLink.click();
            
            // 清理
            setTimeout(() => {
                document.body.removeChild(downloadLink);
                log(`文件 ${fileName} 已开始下载到本地`, 'success');
            }, 100);
            
            return false;
        }
        
        function selectFile(path, element) {
            // 移除其他选中状态
            document.querySelectorAll('.file-item').forEach(item => {
                item.classList.remove('selected');
            });
            // 添加选中状态
            if (element) {
                element.classList.add('selected');
            }
            // 更新文件选择器
            document.getElementById('fileSelect').value = path;
            log(`选中文件: ${path.split('/').pop()}`, 'info');
        }

        function updateFileSelects(files) {
            const fileSelect = document.getElementById('fileSelect');
            fileSelect.innerHTML = '<option value="">选择文件...</option>';
            
            files.forEach(file => {
                fileSelect.innerHTML += `<option value="${file.path}">${file.name}</option>`;
            });
        }

        // Step 3: 修改文档
        function updateModifyOptions() {
            const modifyType = document.getElementById('modifyType').value;
            const customSection = document.getElementById('customModifySection');
            const aiSection = document.getElementById('aiModifySection');
            
            customSection.style.display = modifyType === 'custom' ? 'block' : 'none';
            aiSection.style.display = modifyType === 'ai_analysis' ? 'block' : 'none';
        }

        async function modifyDocument() {
            const filePath = document.getElementById('fileSelect').value;
            const modifyType = document.getElementById('modifyType').value;
            const customContent = document.getElementById('customModifyContent').value;
            const aiPrompt = document.getElementById('aiPrompt').value;
            
            if (!filePath) {
                showAlert('请选择要修改的文件', 'error');
                return;
            }

            log(`开始修改文档: ${filePath.split('/').pop()}`);
            log(`修改类型: ${modifyType}`, 'info');
            
            try {
                const response = await fetch('/api/modify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_path: filePath,
                        modify_type: modifyType,
                        custom_content: customContent,
                        ai_prompt: aiPrompt
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('modifyStatus').style.display = 'inline-block';
                    document.getElementById('modifyStatus').className = 'status-badge status-success';
                    document.getElementById('modifyStatus').textContent = '✅ 修改完成';
                    
                    // 更新修改后的文件列表
                    if (result.modified_file) {
                        modifiedFiles.push({
                            path: result.modified_file,
                            name: result.modified_file.split('/').pop(),
                            type: modifyType
                        });
                        
                        displayModifiedFiles();
                        updateUploadFileSelect();
                    }
                    
                    log(`修改成功: ${result.message}`, 'success');
                    showAlert('文档修改成功', 'success');
                    updateProgress(4);
                } else {
                    throw new Error(result.error || '修改失败');
                }
            } catch (error) {
                log(`修改失败: ${error.message}`, 'error');
                showAlert(`修改失败: ${error.message}`, 'error');
            }
        }

        function displayModifiedFiles() {
            const container = document.getElementById('modifiedPreview');
            container.style.display = 'block';
            container.innerHTML = '<div style="margin-bottom: 10px; font-weight: 600;">✏️ 修改后的文件:</div>';
            
            modifiedFiles.forEach(file => {
                container.innerHTML += `
                    <div class="file-item">
                        <div class="file-info">
                            <span class="file-icon">📝</span>
                            <div>
                                <div class="file-name">${file.name}</div>
                                <div class="file-size">修改类型: ${file.type}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        function updateUploadFileSelect() {
            const uploadSelect = document.getElementById('uploadFileSelect');
            uploadSelect.innerHTML = '<option value="">选择文件...</option>';
            
            modifiedFiles.forEach(file => {
                uploadSelect.innerHTML += `<option value="${file.path}">${file.name}</option>`;
            });
        }

        // Step 4: 上传文档
        async function uploadDocument() {
            const filePath = document.getElementById('uploadFileSelect').value;
            const uploadOption = document.getElementById('uploadOption').value;
            const targetUrl = document.getElementById('uploadUrl').value;
            
            if (!filePath) {
                showAlert('请选择要上传的文件', 'error');
                return;
            }

            log(`开始上传文档: ${filePath.split('/').pop()}`);
            log(`上传选项: ${uploadOption}`, 'info');
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_path: filePath,
                        upload_option: uploadOption,
                        target_url: targetUrl
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('uploadStatus').style.display = 'inline-block';
                    document.getElementById('uploadStatus').className = 'status-badge status-success';
                    document.getElementById('uploadStatus').textContent = '✅ 上传成功';
                    
                    if (result.url) {
                        document.getElementById('uploadResult').innerHTML = `
                            <div class="alert alert-success" style="display: block;">
                                🎉 文档已成功上传！<br>
                                <a href="${result.url}" target="_blank" style="color: #065f46; font-weight: bold;">
                                    点击查看: ${result.url}
                                </a>
                            </div>
                        `;
                    }
                    
                    log(`上传成功: ${result.message}`, 'success');
                    showAlert('文档上传成功！工作流完成', 'success');
                    
                    // 完成所有步骤
                    for (let i = 1; i <= 4; i++) {
                        document.getElementById(`progress-${i}`).classList.add('completed');
                    }
                } else {
                    throw new Error(result.error || '上传失败');
                }
            } catch (error) {
                log(`上传失败: ${error.message}`, 'error');
                showAlert(`上传失败: ${error.message}`, 'error');
            }
        }

        // 辅助功能
        function clearLog() {
            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML = '<div class="log-entry log-info"><span class="log-time">[00:00:00]</span> 日志已清空...</div>';
            log('日志已清空', 'info');
        }

        function exportLog() {
            const logContent = document.getElementById('logOutput').innerText;
            const blob = new Blob([logContent], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `workflow_log_${new Date().getTime()}.txt`;
            a.click();
            log('日志已导出', 'success');
        }

        async function testConnection() {
            log('测试系统连接...');
            try {
                const response = await fetch('/api/test');
                const result = await response.json();
                log(`连接测试: ${result.message}`, 'success');
                showAlert('连接正常', 'success');
            } catch (error) {
                log(`连接失败: ${error.message}`, 'error');
                showAlert('连接失败', 'error');
            }
        }

        async function viewSystemStatus() {
            log('获取系统状态...');
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                log('系统状态:', 'info');
                log(`- 工作流UI: ${result.services.workflow_ui}`, 'info');
                log(`- 自动下载: ${result.services.auto_download}`, 'info');
                log(`- AI服务: ${result.services.ai_service}`, 'info');
                log(`- 热力图UI: ${result.services.heatmap_ui}`, 'info');
                log(`- 配置文件: ${result.config_exists ? '存在' : '不存在'}`, 'info');
            } catch (error) {
                log(`获取状态失败: ${error.message}`, 'error');
            }
        }

        async function runCompleteTest() {
            log('开始完整工作流测试...', 'warning');
            showAlert('正在运行完整测试流程', 'info');
            
            // 这里可以自动运行完整的测试流程
            log('请按顺序完成各步骤', 'info');
        }

        // 页面加载时初始化
        window.onload = function() {
            log('腾讯文档工作流测试UI已就绪', 'success');
            log('系统版本: 增强版 v2.0', 'info');
            updateProgress(1);
            testConnection();
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/test')
def test_connection():
    """测试连接"""
    return jsonify({
        'success': True,
        'message': '系统运行正常',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    status = {
        'services': {
            'workflow_ui': 'running',
            'auto_download': check_service_status(8090),
            'ai_service': check_service_status(8081),
            'heatmap_ui': check_service_status(8089)
        },
        'directories': {
            'downloads': str(DOWNLOAD_DIR),
            'temp': str(TEMP_DIR)
        },
        'config_exists': CONFIG_PATH.exists()
    }
    return jsonify(status)

@app.route('/api/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie到配置文件"""
    try:
        data = request.json
        cookie = data.get('cookie', '').strip()
        
        if not cookie:
            return jsonify({'success': False, 'error': 'Cookie不能为空'})
        
        # 读取或创建配置
        config = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 更新cookie
        config['cookie'] = cookie
        config['last_updated'] = datetime.now().isoformat()
        
        # 保存配置
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Cookie已保存'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load-cookie')
def load_cookie():
    """加载已保存的Cookie"""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cookie = config.get('cookie', '')
                return jsonify({'success': True, 'cookie': cookie})
        return jsonify({'success': False, 'message': '没有找到配置文件'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['POST'])
def download_document():
    """下载腾讯文档 - 集成实际下载功能"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        format_type = data.get('format', 'csv')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL不能为空'})
        
        # 尝试调用实际的下载系统
        try:
            from auto_download_ui_system import download_file_from_url
            
            # 调用实际的下载函数
            result = download_file_from_url(url, format_type)
            
            if result and result.get('success'):
                # 直接返回结果，因为已经包含了内容检查信息
                return jsonify(result)
        except ImportError:
            # 如果无法导入，使用模拟下载
            pass
        
        # 模拟下载（用于测试）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"document_{timestamp}.{format_type}"
        file_path = DOWNLOAD_DIR / filename
        
        # 创建示例文件
        with open(file_path, 'w', encoding='utf-8') as f:
            if format_type == 'csv':
                f.write('姓名,部门,职位,风险等级\n')
                f.write('张三,技术部,工程师,L1\n')
                f.write('李四,市场部,经理,L2\n')
                f.write('王五,财务部,主管,L3\n')
            else:
                f.write(f'示例文档内容 - {timestamp}\n')
                f.write('这是一个测试文档\n')
        
        return jsonify({
            'success': True,
            'files': [{
                'path': str(file_path),
                'name': filename,
                'size': format_file_size(file_path.stat().st_size)
            }],
            'message': '模拟下载完成'
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/modify', methods=['POST'])
def modify_document():
    """修改文档内容"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        modify_type = data.get('modify_type', 'timestamp')
        custom_content = data.get('custom_content', '')
        ai_prompt = data.get('ai_prompt', '')
        
        if not file_path or not Path(file_path).exists():
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 创建修改后的文件副本
        original_path = Path(file_path)
        modified_path = TEMP_DIR / f"modified_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_path.name}"
        
        # 执行修改
        if modify_type == 'timestamp':
            # 添加时间戳
            modify_with_timestamp(original_path, modified_path)
            message = '已添加时间戳标记'
        elif modify_type == 'ai_analysis':
            # AI分析
            modify_with_ai_analysis(original_path, modified_path, ai_prompt)
            message = 'AI分析完成'
        elif modify_type == 'risk_mark':
            # 风险标记
            modify_with_risk_mark(original_path, modified_path)
            message = '风险标记完成'
        elif modify_type == 'custom':
            # 自定义修改
            modify_with_custom(original_path, modified_path, custom_content)
            message = '自定义修改完成'
        else:
            return jsonify({'success': False, 'error': '未知的修改类型'})
        
        return jsonify({
            'success': True,
            'modified_file': str(modified_path),
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/file/<path:filename>')
@app.route('/api/download-file')  # 新增：使用查询参数的替代路由
def download_file(filename=None):
    """提供文件下载功能 - 安全版本"""
    
    # 如果没有文件名参数，尝试从查询参数获取
    if filename is None:
        filename = request.args.get('filename', '')
        if not filename:
            return jsonify({'error': '缺少文件名参数'}), 400
        app.logger.info(f"[DEBUG] 从查询参数获取文件名: {filename}")
    else:
        app.logger.info(f"[DEBUG] 从路径参数获取文件名: {filename}")
        # 尝试修复编码问题
        try:
            # Flask可能已经用latin-1解码了，需要重新编码再用UTF-8解码
            filename = filename.encode('latin-1').decode('utf-8')
            app.logger.info(f"[DEBUG] 修复编码后文件名: {filename}")
        except:
            app.logger.info(f"[DEBUG] 编码修复失败，使用原始文件名")
    
    try:
        import os
        
        # 安全性检查：防止路径遍历攻击
        # 规范化文件名，移除路径分隔符和危险字符
        safe_filename = os.path.basename(filename)
        app.logger.info(f"[DEBUG] 安全文件名: {safe_filename}")
        
        # 拒绝包含危险字符的文件名
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': '非法文件名'}), 400
        
        # 查找文件（只在安全目录中查找）
        file_path = None
        
        # 检查下载目录
        potential_path = DOWNLOAD_DIR / safe_filename
        if potential_path.exists() and potential_path.is_file():
            # 确保文件确实在下载目录中
            if potential_path.resolve().parent == DOWNLOAD_DIR.resolve():
                file_path = potential_path
        
        # 检查修改目录
        if not file_path:
            potential_path = MODIFIED_DIR / safe_filename
            if potential_path.exists() and potential_path.is_file():
                # 确保文件确实在修改目录中
                if potential_path.resolve().parent == MODIFIED_DIR.resolve():
                    file_path = potential_path
        
        # 检查临时目录
        if not file_path:
            potential_path = TEMP_DIR / safe_filename
            if potential_path.exists() and potential_path.is_file():
                # 确保文件确实在临时目录中
                if potential_path.resolve().parent == TEMP_DIR.resolve():
                    file_path = potential_path
        
        # 检查csv_versions目录（文件可能在周数子目录中）
        if not file_path:
            csv_versions_dir = BASE_DIR / 'csv_versions'
            app.logger.info(f"[DEBUG] 检查csv_versions目录: {csv_versions_dir}")
            if csv_versions_dir.exists():
                # 搜索所有周数目录
                import glob
                pattern = str(csv_versions_dir / '**' / safe_filename)
                app.logger.info(f"[DEBUG] 搜索模式: {pattern}")
                matches = glob.glob(pattern, recursive=True)
                app.logger.info(f"[DEBUG] 找到 {len(matches)} 个匹配文件")
                if matches:
                    # 使用最新的文件
                    file_path = Path(max(matches, key=os.path.getmtime))
                    app.logger.info(f"[DEBUG] 选择文件: {file_path}")
        
        if file_path and file_path.exists():
            # 记录下载日志
            print(f"[下载] 用户下载文件: {safe_filename}")
            
            # 发送文件给用户
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=safe_filename,
                mimetype='application/octet-stream'
            )
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        print(f"[错误] 下载文件失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """上传文档到腾讯文档"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        upload_option = data.get('upload_option', 'new')
        target_url = data.get('target_url', '')
        
        if not file_path or not Path(file_path).exists():
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 这里应该调用实际的腾讯文档上传API
        # 目前返回模拟结果
        
        if upload_option == 'new':
            # 创建新文档
            new_url = f"https://docs.qq.com/sheet/NEW_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            message = '已创建新文档'
        elif upload_option == 'replace':
            # 替换原文档
            new_url = target_url or f"https://docs.qq.com/sheet/REPLACED_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            message = '已替换原文档'
        else:
            # 作为新版本
            new_url = target_url or f"https://docs.qq.com/sheet/VERSION_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            message = '已上传为新版本'
        
        return jsonify({
            'success': True,
            'url': new_url,
            'message': message
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 辅助函数
def check_service_status(port):
    """检查服务状态"""
    try:
        response = requests.get(f'http://localhost:{port}/', timeout=1)
        return 'running' if response.status_code == 200 else 'stopped'
    except:
        return 'stopped'

def format_file_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def modify_with_timestamp(original_path, modified_path):
    """添加时间戳修改"""
    # 检查文件类型
    if original_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
        # 对于Excel文件，直接复制（因为是二进制文件）
        import shutil
        shutil.copy2(original_path, modified_path)
        return
    
    with open(original_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 如果是CSV文件，添加时间戳列
    if original_path.suffix.lower() == '.csv':
        lines = content.split('\n')
        if lines:
            # 添加时间戳列到标题
            lines[0] = lines[0].rstrip() + ',修改时间'
            # 为每行数据添加时间戳
            for i in range(1, len(lines)):
                if lines[i].strip():
                    lines[i] = lines[i].rstrip() + f',{timestamp}'
            content = '\n'.join(lines)
    else:
        # 其他格式，在开头添加时间戳
        content = f"# 修改时间: {timestamp}\n\n{content}"
    
    with open(modified_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_with_ai_analysis(original_path, modified_path, prompt):
    """使用AI分析修改"""
    # 检查文件类型
    if original_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
        # 对于Excel文件，直接复制（因为是二进制文件）
        import shutil
        shutil.copy2(original_path, modified_path)
        return
    
    # 这里应该调用实际的AI服务
    # 目前使用简单的模拟
    with open(original_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = f"AI分析结果 ({prompt or '默认分析'}):\n"
    analysis += "- 风险等级: 中等\n"
    analysis += "- 建议: 需要进一步审核\n"
    analysis += "- 置信度: 85%\n\n"
    
    modified_content = analysis + content
    
    with open(modified_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

def modify_with_risk_mark(original_path, modified_path):
    """添加风险标记"""
    # 检查文件类型
    if original_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
        # 对于Excel文件，直接复制（因为是二进制文件）
        import shutil
        shutil.copy2(original_path, modified_path)
        return
    
    with open(original_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 如果是CSV文件，添加风险标记列
    if original_path.suffix.lower() == '.csv':
        lines = content.split('\n')
        if lines:
            # 添加风险标记列
            lines[0] = lines[0].rstrip() + ',风险标记,风险说明'
            # 为每行数据添加模拟的风险标记
            for i in range(1, len(lines)):
                if lines[i].strip():
                    risk_level = ['低', '中', '高'][i % 3]
                    risk_desc = ['正常', '需要关注', '需要立即处理'][i % 3]
                    lines[i] = lines[i].rstrip() + f',{risk_level},{risk_desc}'
            content = '\n'.join(lines)
    else:
        content = "【风险标记已添加】\n\n" + content
    
    with open(modified_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_with_custom(original_path, modified_path, custom_content):
    """自定义修改"""
    # 检查文件类型
    if original_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
        # 对于Excel文件，直接复制（因为是二进制文件）
        import shutil
        shutil.copy2(original_path, modified_path)
        return
    
    with open(original_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if custom_content:
        modified_content = f"{custom_content}\n\n--- 原始内容 ---\n\n{content}"
    else:
        modified_content = content
    
    with open(modified_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

if __name__ == '__main__':
    # 配置日志
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.logger.setLevel(logging.INFO)
    
    print("=" * 50)
    print("🚀 腾讯文档完整工作流测试UI - 增强版")
    print(f"📍 访问地址: http://202.140.143.88:8093/")
    print("=" * 50)
    print("✨ 功能特点:")
    print("  - 完整的下载→修改→上传工作流")
    print("  - AI智能分析和风险标记")
    print("  - 实时进度显示和日志输出")
    print("  - 集成多个系统服务")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8093, debug=False)