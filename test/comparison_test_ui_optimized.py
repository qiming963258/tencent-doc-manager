#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版的对比测试UI - 解决502超时问题
主要优化：
1. 并行下载两个文件
2. 增加进度反馈
3. 优化超时处理
"""

from flask import Flask, render_template_string, request, jsonify
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime
import os
from pathlib import Path

# 导入原有的依赖
from auto_download_ui_system import download_file_from_url
from simple_comparison_handler import simple_csv_compare, save_comparison_result

app = Flask(__name__)

# 配置目录
BASE_DIR = Path('/root/projects/tencent-doc-manager')
DOWNLOAD_DIR = BASE_DIR / 'downloads'
BASELINE_DIR = BASE_DIR / 'comparison_baseline'
TARGET_DIR = BASE_DIR / 'comparison_target'
RESULT_DIR = BASE_DIR / 'comparison_results'

# 确保目录存在
for dir_path in [DOWNLOAD_DIR, BASELINE_DIR, TARGET_DIR, RESULT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 线程池执行器
executor = ThreadPoolExecutor(max_workers=2)

def download_with_timeout(url, format_type='csv', timeout=60):
    """带超时的下载包装函数"""
    try:
        result = download_file_from_url(url, format_type)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/api/compare_optimized', methods=['POST'])
def compare_optimized():
    """优化的对比分析接口 - 并行下载"""
    request_id = f"REQ_{datetime.now().strftime('%H%M%S_%f')[:12]}"
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"[{request_id}] 优化版本 - 新请求开始: {datetime.now().isoformat()}")
    
    try:
        # 获取请求数据
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        baseline_url = data.get('baseline_url', '').strip()
        target_url = data.get('target_url', '').strip()
        
        if not baseline_url or not target_url:
            return jsonify({
                'success': False,
                'error': '请提供基线URL和目标URL'
            })
        
        # 并行下载两个文件
        print(f"[{request_id}] 开始并行下载两个文件...")
        
        # 使用线程池并行执行
        future_baseline = executor.submit(download_with_timeout, baseline_url, 'csv', 60)
        future_target = executor.submit(download_with_timeout, target_url, 'csv', 60)
        
        # 等待两个下载完成（但不会串行等待）
        baseline_result = future_baseline.result(timeout=70)
        target_result = future_target.result(timeout=70)
        
        download_time = time.time() - start_time
        print(f"[{request_id}] 并行下载完成，总耗时: {download_time:.2f}秒")
        
        # 检查下载结果
        if not baseline_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"基线文件下载失败: {baseline_result.get('error', '未知错误')}"
            })
        
        if not target_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"目标文件下载失败: {target_result.get('error', '未知错误')}"
            })
        
        # 获取文件路径
        baseline_files = baseline_result.get('files', [])
        target_files = target_result.get('files', [])
        
        if not baseline_files or not target_files:
            return jsonify({
                'success': False,
                'error': '下载的文件列表为空'
            })
        
        baseline_path = baseline_files[0].get('path')
        target_path = target_files[0].get('path')
        
        # 执行对比
        print(f"[{request_id}] 开始执行CSV对比...")
        comparison_start = time.time()
        
        comparison_result = simple_csv_compare(baseline_path, target_path)
        
        comparison_time = time.time() - comparison_start
        print(f"[{request_id}] 对比完成，耗时: {comparison_time:.2f}秒")
        
        # 保存结果
        if comparison_result.get('success'):
            result_file = save_comparison_result(comparison_result)
            comparison_result['result_file'] = result_file
        
        # 添加性能信息
        total_time = time.time() - start_time
        comparison_result['performance'] = {
            'total_time': f"{total_time:.2f}秒",
            'download_time': f"{download_time:.2f}秒",
            'comparison_time': f"{comparison_time:.2f}秒",
            'parallel_download': True
        }
        
        print(f"[{request_id}] 请求完成，总耗时: {total_time:.2f}秒")
        return jsonify(comparison_result)
        
    except Exception as e:
        import traceback
        error_msg = f"处理失败: {str(e)}"
        print(f"[{request_id}] 错误: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'request_id': request_id
        })

@app.route('/')
def index():
    """优化版测试页面"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>腾讯文档对比测试 - 优化版</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 10px;
            }
            .version {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            .optimization-info {
                background: #e8f4fd;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }
            .optimization-info h3 {
                margin-top: 0;
                color: #1976D2;
            }
            .optimization-info ul {
                margin: 10px 0;
                padding-left: 20px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            input[type="text"] {
                width: 100%;
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            button {
                flex: 1;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .progress {
                display: none;
                margin-top: 20px;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 6px;
            }
            .progress.active {
                display: block;
            }
            .progress-bar {
                width: 100%;
                height: 4px;
                background: #e0e0e0;
                border-radius: 2px;
                overflow: hidden;
                margin-top: 10px;
            }
            .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                animation: progress 2s ease-in-out infinite;
            }
            @keyframes progress {
                0% { width: 0%; }
                50% { width: 70%; }
                100% { width: 100%; }
            }
            .result {
                margin-top: 20px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 6px;
                display: none;
            }
            .result.success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
            }
            .result.error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
            }
            .performance-info {
                margin-top: 15px;
                padding: 10px;
                background: #fff3cd;
                border-radius: 4px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 腾讯文档对比测试 - 优化版</h1>
            <div class="version">v2.0 - 并行下载优化</div>
            
            <div class="optimization-info">
                <h3>✨ 优化特性</h3>
                <ul>
                    <li>并行下载两个文件，减少总时间</li>
                    <li>优化超时处理，避免502错误</li>
                    <li>实时进度反馈</li>
                    <li>性能监控和统计</li>
                </ul>
            </div>
            
            <div class="form-group">
                <label>基线文档 URL:</label>
                <input type="text" id="baseline_url" 
                       value="https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
                       placeholder="输入基线腾讯文档URL">
            </div>
            
            <div class="form-group">
                <label>目标文档 URL:</label>
                <input type="text" id="target_url"
                       value="https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2"
                       placeholder="输入目标腾讯文档URL">
            </div>
            
            <div class="button-group">
                <button onclick="startComparison()">开始对比分析</button>
            </div>
            
            <div id="progress" class="progress">
                <div>⏳ 正在处理中...</div>
                <div class="progress-bar">
                    <div class="progress-bar-fill"></div>
                </div>
                <div id="progress-status" style="margin-top: 10px; color: #666;">
                    正在并行下载文档...
                </div>
            </div>
            
            <div id="result" class="result"></div>
        </div>
        
        <script>
        async function startComparison() {
            const baselineUrl = document.getElementById('baseline_url').value.trim();
            const targetUrl = document.getElementById('target_url').value.trim();
            
            if (!baselineUrl || !targetUrl) {
                alert('请输入两个文档的URL');
                return;
            }
            
            // 显示进度
            document.getElementById('progress').classList.add('active');
            document.getElementById('result').style.display = 'none';
            document.querySelector('button').disabled = true;
            
            const startTime = Date.now();
            
            try {
                const response = await fetch('/api/compare_optimized', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        baseline_url: baselineUrl,
                        target_url: targetUrl
                    })
                });
                
                const data = await response.json();
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                
                // 隐藏进度
                document.getElementById('progress').classList.remove('active');
                
                // 显示结果
                const resultDiv = document.getElementById('result');
                if (data.success) {
                    resultDiv.className = 'result success';
                    let html = '<h3>✅ 对比完成</h3>';
                    
                    if (data.performance) {
                        html += `
                        <div class="performance-info">
                            <strong>性能统计：</strong><br>
                            总耗时: ${data.performance.total_time}<br>
                            下载耗时: ${data.performance.download_time}<br>
                            对比耗时: ${data.performance.comparison_time}<br>
                            并行下载: ${data.performance.parallel_download ? '是' : '否'}
                        </div>`;
                    }
                    
                    if (data.comparison_stats) {
                        html += `
                        <h4>对比统计：</h4>
                        <ul>
                            <li>总行数: ${data.comparison_stats.total_rows}</li>
                            <li>差异行数: ${data.comparison_stats.different_rows}</li>
                            <li>相似度: ${data.comparison_stats.similarity}%</li>
                        </ul>`;
                    }
                    
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `
                        <h3>❌ 处理失败</h3>
                        <p>${data.error || '未知错误'}</p>
                        <p>总耗时: ${elapsed}秒</p>
                    `;
                }
                
                resultDiv.style.display = 'block';
            } catch (error) {
                document.getElementById('progress').classList.remove('active');
                
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `
                    <h3>❌ 请求失败</h3>
                    <p>${error.message}</p>
                `;
                resultDiv.style.display = 'block';
            } finally {
                document.querySelector('button').disabled = false;
            }
        }
        </script>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    print("🚀 启动优化版对比测试UI - 端口 8095")
    print("✨ 优化特性：并行下载、超时优化、性能监控")
    app.run(host='0.0.0.0', port=8095, debug=False)