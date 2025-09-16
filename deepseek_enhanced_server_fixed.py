#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版的8098服务 - 解决按钮无响应问题
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepseek_client import DeepSeekClient
from column_standardization_processor_v3 import ColumnStandardizationProcessorV3

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask应用
app = Flask(__name__)
CORS(app)

# DeepSeek客户端
API_KEY = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
deepseek_client = DeepSeekClient(API_KEY)
processor = ColumnStandardizationProcessorV3(API_KEY)

# 标准列名
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
    "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
]

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek V3 AI列名标准化测试平台 - 修复版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1600px; margin: 0 auto; }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .error-msg {
            color: #e74c3c;
            padding: 10px;
            background: #ffe5e5;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .success-msg {
            color: #27ae60;
            padding: 10px;
            background: #e5ffe5;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .debug-info {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
        }
        
        button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        
        button:hover {
            opacity: 0.9;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 DeepSeek V3 AI列名标准化测试平台</h1>
            <p>修复版 - 解决按钮无响应问题</p>
        </div>
        
        <div class="card">
            <h2>📝 输入CSV对比文件路径</h2>
            
            <input type="text" id="csvPath" 
                   placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_*.json"
                   value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json">
            
            <button id="processBtn" onclick="processFileFixed()">
                🚀 开始处理
            </button>
            
            <button onclick="testConnection()" style="margin-left: 10px; background: #95a5a6;">
                🔧 测试连接
            </button>
            
            <p style="font-size: 12px; color: #666; margin-top: 10px;">
                💡 提示：输入simplified_开头的JSON文件路径，系统将自动执行处理
            </p>
        </div>
        
        <div class="card">
            <h2>🐛 调试信息</h2>
            <div id="debugInfo" class="debug-info">
                等待操作...
            </div>
        </div>
        
        <div class="card">
            <h2>📊 处理结果</h2>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px; color: #666;">正在处理...</p>
            </div>
            
            <div id="resultContent">
                <p style="color: #999; text-align: center; padding: 20px;">
                    等待处理...
                </p>
            </div>
        </div>
    </div>
    
    <script>
        // 全局错误捕获
        window.onerror = function(msg, url, lineNo, columnNo, error) {
            const errorMsg = `JavaScript错误: ${msg}\\n位置: ${url}:${lineNo}:${columnNo}`;
            addDebugInfo(errorMsg, 'error');
            console.error(errorMsg, error);
            return false;
        };
        
        // 添加调试信息
        function addDebugInfo(message, type = 'info') {
            const debugDiv = document.getElementById('debugInfo');
            const timestamp = new Date().toLocaleTimeString();
            const color = type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#333';
            debugDiv.innerHTML += `<div style="color: ${color}">[${timestamp}] ${message}</div>`;
            debugDiv.scrollTop = debugDiv.scrollHeight;
        }
        
        // 测试连接
        async function testConnection() {
            addDebugInfo('开始测试连接...', 'info');
            
            try {
                const response = await fetch('/api/test', {
                    method: 'GET'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    addDebugInfo('✅ 连接成功: ' + JSON.stringify(data), 'success');
                } else {
                    addDebugInfo('❌ 连接失败: HTTP ' + response.status, 'error');
                }
            } catch (error) {
                addDebugInfo('❌ 连接错误: ' + error.message, 'error');
            }
        }
        
        // 修复版的处理函数
        async function processFileFixed() {
            addDebugInfo('开始处理文件...', 'info');
            
            const csvPath = document.getElementById('csvPath').value;
            const processBtn = document.getElementById('processBtn');
            const loading = document.getElementById('loading');
            const resultContent = document.getElementById('resultContent');
            
            if (!csvPath || !csvPath.trim()) {
                addDebugInfo('错误: 请输入文件路径', 'error');
                alert('请输入CSV对比文件路径');
                return;
            }
            
            addDebugInfo('文件路径: ' + csvPath, 'info');
            
            // 禁用按钮，显示加载状态
            processBtn.disabled = true;
            loading.style.display = 'block';
            resultContent.innerHTML = '';
            
            try {
                // Step 1: 读取文件
                addDebugInfo('Step 1: 读取文件...', 'info');
                
                const fileResponse = await fetch('/api/read_file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: csvPath })
                });
                
                if (!fileResponse.ok) {
                    throw new Error(`读取文件失败: HTTP ${fileResponse.status}`);
                }
                
                const fileData = await fileResponse.json();
                
                if (!fileData.success) {
                    throw new Error(fileData.error || '文件读取失败');
                }
                
                addDebugInfo('✅ 文件读取成功', 'success');
                
                const modifiedColumns = fileData.content.modified_columns || {};
                const columns = Object.values(modifiedColumns);
                
                addDebugInfo(`找到 ${columns.length} 个修改列: ${columns.join(', ')}`, 'info');
                
                // Step 2: 执行AI标准化
                addDebugInfo('Step 2: 执行AI标准化...', 'info');
                
                const analyzeResponse = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        columns: columns,
                        csv_path: csvPath,
                        use_numbering: true,
                        filter_modified: true
                    })
                });
                
                if (!analyzeResponse.ok) {
                    throw new Error(`标准化失败: HTTP ${analyzeResponse.status}`);
                }
                
                const result = await analyzeResponse.json();
                
                if (!result.success) {
                    throw new Error(result.error || '标准化失败');
                }
                
                addDebugInfo('✅ AI标准化成功', 'success');
                
                // 显示结果
                displayResults(fileData.content, result.data);
                
            } catch (error) {
                addDebugInfo('❌ 错误: ' + error.message, 'error');
                resultContent.innerHTML = `<div class="error-msg">处理失败: ${error.message}</div>`;
            } finally {
                // 恢复按钮，隐藏加载状态
                processBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        // 显示结果
        function displayResults(fileContent, aiResult) {
            const resultContent = document.getElementById('resultContent');
            
            const modifiedColumns = fileContent.modified_columns || {};
            const mapping = aiResult.mapping || {};
            const confidence = aiResult.confidence_scores || {};
            
            let html = '<div class="success-msg">✅ 处理完成</div>';
            
            html += '<h3>📊 标准化结果</h3>';
            html += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">';
            html += '<tr style="background: #f0f0f0;"><th>列码</th><th>原始名称</th><th>标准化名称</th><th>置信度</th></tr>';
            
            Object.entries(modifiedColumns).forEach(([colCode, colName]) => {
                const stdName = mapping[colName] || colName;
                const conf = confidence[colName] || 0;
                html += `<tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 8px;">${colCode}</td>
                    <td style="padding: 8px;">${colName}</td>
                    <td style="padding: 8px; font-weight: bold; color: #667eea;">${stdName}</td>
                    <td style="padding: 8px;">${(conf * 100).toFixed(0)}%</td>
                </tr>`;
            });
            
            html += '</table>';
            
            resultContent.innerHTML = html;
            addDebugInfo('结果显示完成', 'success');
        }
        
        // 页面加载完成后的初始化
        window.onload = function() {
            addDebugInfo('页面加载完成', 'success');
            addDebugInfo('按钮状态: ' + (typeof processFileFixed === 'function' ? '正常' : '异常'), 'info');
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
def test():
    """测试连接"""
    return jsonify({
        "success": True,
        "message": "服务正常运行",
        "time": datetime.now().isoformat()
    })

@app.route('/api/read_file', methods=['POST'])
def read_file():
    """读取JSON文件"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({"success": False, "error": "没有提供文件路径"})
        
        logger.info(f"读取文件: {file_path}")
        
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"文件不存在: {file_path}"})
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return jsonify({
            "success": True,
            "content": content,
            "file_path": file_path
        })
        
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """执行AI标准化分析"""
    try:
        data = request.json
        columns = data.get('columns', [])
        csv_path = data.get('csv_path', '')
        
        if not columns:
            return jsonify({"success": False, "error": "没有提供列名"})
        
        logger.info(f"开始标准化 {len(columns)} 个列")
        
        # 调用DeepSeek进行标准化
        result = deepseek_client.sync_analyze_columns(columns, STANDARD_COLUMNS)
        
        # 处理结果
        mapping = {}
        confidence_scores = {}
        
        if result and result.get('success'):
            # 从result中提取映射数据
            result_data = result.get('result', {})
            standardized = result_data.get('standardized', {})
            
            for i, col in enumerate(columns):
                std_info = standardized.get(str(i+1), {})
                standardized_name = std_info.get('standardized', col)
                confidence = std_info.get('confidence', 0.5)
                
                mapping[col] = standardized_name
                confidence_scores[col] = confidence
        else:
            # 如果没有返回结果，使用原始列名
            for col in columns:
                mapping[col] = col
                confidence_scores[col] = 1.0
        
        # 保存结果到文件
        if csv_path:
            output_file = csv_path.replace('.json', '_standardized.json')
            try:
                # 读取原始文件
                with open(csv_path, 'r', encoding='utf-8') as f:
                    original_content = json.load(f)
                
                # 添加标准化结果
                original_content['standardized_columns'] = mapping
                original_content['standardization_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'model': 'deepseek-ai/DeepSeek-V3',
                    'confidence_scores': confidence_scores
                }
                
                # 保存到新文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(original_content, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"结果保存到: {output_file}")
            except Exception as e:
                logger.error(f"保存结果失败: {e}")
                output_file = None
        else:
            output_file = None
        
        return jsonify({
            "success": True,
            "data": {
                "mapping": mapping,
                "confidence_scores": confidence_scores,
                "output_file": output_file,
                "column_count": len(columns)
            }
        })
        
    except Exception as e:
        logger.error(f"标准化失败: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   DeepSeek V3 AI列名标准化测试平台 - 修复版           ║
    ║   端口: 8098                                         ║
    ║   访问: http://localhost:8098                        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 先关闭旧的8098服务
    os.system("kill $(lsof -t -i:8098) 2>/dev/null")
    time.sleep(2)
    
    app.run(host='0.0.0.0', port=8098, debug=False)