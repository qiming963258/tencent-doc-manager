#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整版的8098服务 - 包含所有原始功能和修复
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
import asyncio
from typing import Dict, Any, List, Optional
import string

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

def add_column_labels(columns: List[str]) -> Dict[str, str]:
    """为列名添加英文字母序号"""
    labels = {}
    chars = string.ascii_uppercase
    
    for i, col in enumerate(columns):
        if i < 26:
            label = chars[i]
        else:
            # 处理超过26列的情况 (AA, AB, AC...)
            first = (i - 26) // 26
            second = (i - 26) % 26
            if first < 26:
                label = chars[first] + chars[second]
            else:
                label = f"COL{i+1}"
        labels[label] = col
    
    return labels

def build_optimized_prompt(actual_columns: List[str], csv_file_path: str = None, use_numbering: bool = False) -> str:
    """构建深度优化的提示词，支持序号映射系统"""
    
    column_count = len(actual_columns)
    if column_count < 19:
        strategy = "少列策略：识别缺失的标准列，自动标记为空白"
    elif column_count > 19:
        strategy = "多列策略：智能选择最符合标准的19项，舍弃其余"
    else:
        strategy = "等列策略：优化一对一映射"
    
    # 如果使用序号系统
    if use_numbering:
        labeled_columns = add_column_labels(actual_columns)
        columns_display = "\n".join([f"{label}: {col}" for label, col in labeled_columns.items()])
        
        prompt = f"""你是专业的CSV列名标准化专家。请将带序号的列名映射到19个标准列名。

## 🎯 核心任务
分析带英文序号的列名（这些都是有实际修改的列），将其映射到标准列名。
保持序号不变，只改变列名部分。

## ⚠️ 重要说明
- 输入的列都是从CSV对比中提取的有修改的列（修改值≠0）
- 没有修改的列已被过滤，不会出现在输入中
- 请保持序号不变，只标准化列名

## 📋 19个标准列名（固定顺序）
{json.dumps(STANDARD_COLUMNS, ensure_ascii=False, indent=2)}

## 📝 需要标准化的列名（共{column_count}个有修改的列）
{columns_display}

## 📊 当前处理策略
- 实际列数: {column_count}个
- 标准列数: 19个
- 处理策略: {strategy}"""
    
    return prompt

# HTML模板 - 完整版包含所有功能
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek V3 AI列名标准化测试平台 - 完整版</title>
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { font-size: 1.2rem; opacity: 0.95; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 1024px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 3px solid #1e3c72;
            padding-bottom: 10px;
        }
        
        /* 智能问答框样式 */
        .qa-section {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .qa-section h2 {
            color: #2a5298;
            margin-bottom: 20px;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .qa-input {
            width: 100%;
            min-height: 120px;
            padding: 15px;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
            background: white;
        }
        
        .qa-controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .qa-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .qa-button:hover { transform: translateY(-2px); }
        
        .prompt-example {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 10px 15px;
            margin-top: 10px;
            border-radius: 5px;
            font-size: 13px;
            color: #555;
        }
        
        .input-section { margin-bottom: 20px; }
        
        .input-section label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        
        .test-buttons {
            display: grid;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .test-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .test-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .status-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .status-label {
            color: #666;
            font-size: 12px;
            margin-bottom: 5px;
        }
        
        .status-value {
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }
        
        .result-section {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .result-title {
            color: #333;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .mapping-grid {
            display: grid;
            gap: 8px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .mapping-item {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            padding: 10px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e1e1e1;
        }
        
        .mapping-arrow {
            padding: 0 15px;
            color: #667eea;
            font-size: 18px;
        }
        
        .confidence-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }
        
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
        
        .missing-columns, .discarded-columns {
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }
        
        .column-tag {
            display: inline-block;
            padding: 5px 12px;
            margin: 3px;
            background: #e9ecef;
            border-radius: 15px;
            font-size: 13px;
        }
        
        .missing-tag { background: #ffe5e5; color: #c00; }
        .discarded-tag { background: #fff5e5; color: #f90; }
        
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
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
        
        .error-msg {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .success-msg {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .debug-info {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepSeek V3 AI列名标准化测试平台</h1>
            <p>智能版 - 只处理有修改的列 | 支持序号映射系统</p>
            <p style="margin-top: 10px; font-size: 14px; opacity: 0.9;">
                模型：deepseek-ai/DeepSeek-V3 | 平台：硅基流动(SiliconFlow)
            </p>
        </div>
        
        <!-- 工作流程说明 -->
        <div class="card" style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); margin-bottom: 20px;">
            <h2 style="color: #2a5298;">📋 智能标准化工作流程</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px;">
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
                    <strong style="color: #667eea;">步骤1：列提取</strong>
                    <p style="margin-top: 5px; font-size: 14px; color: #666;">
                        从CSV对比结果中提取所有修改值≠0的列，自动过滤无修改的列
                    </p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #764ba2;">
                    <strong style="color: #764ba2;">步骤2：序号标记</strong>
                    <p style="margin-top: 5px; font-size: 14px; color: #666;">
                        为每个列添加英文字母序号(A、B、C...)，建立精确映射关系
                    </p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #f093fb;">
                    <strong style="color: #f093fb;">步骤3：AI标准化</strong>
                    <p style="margin-top: 5px; font-size: 14px; color: #666;">
                        AI分析并映射到19个标准列名，超过19列时智能选择最重要的
                    </p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4facfe;">
                    <strong style="color: #4facfe;">步骤4：结果回写</strong>
                    <p style="margin-top: 5px; font-size: 14px; color: #666;">
                        根据序号对应关系，将标准列名覆盖原始列名，生成标准CSV
                    </p>
                </div>
            </div>
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px;">
                <strong>⚠️ 重要说明：</strong>
                <ul style="margin-top: 10px; margin-left: 20px; font-size: 14px; color: #856404;">
                    <li>只处理有实际修改的列（修改值≠0），提高处理效率</li>
                    <li>序号系统确保映射准确性，避免列名混淆</li>
                    <li>最终输出严格的19列标准格式，缺失列标记为null</li>
                    <li>超出19列的部分会被智能丢弃，保留最重要的信息</li>
                </ul>
            </div>
        </div>

        <!-- CSV案例展示 -->
        <div class="card" style="background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);">
            <h2 style="color: #fff;">📄 CSV对比文件案例（支持简化格式）</h2>
            <p style="color: #fff; opacity: 0.9; margin-bottom: 15px;">
                ✨ 新：简化格式文件大小减少89%，只包含必要信息
            </p>
            <button class="qa-button" onclick="loadCSVExample()" style="background: white; color: #333;">
                📂 加载CSV对比文件（简化版优先）
            </button>
            <button class="qa-button" onclick="toggleCSVExplanation()" style="background: white; color: #333; margin-left: 10px;">
                📖 查看结构说明
            </button>
            <button class="qa-button" onclick="testCompleteFlow()" style="background: #4CAF50; color: white; margin-left: 10px;">
                🚀 测试完整处理流程
            </button>
            
            <div id="csvExampleContent" style="display: none; margin-top: 20px;">
                <div style="background: white; border-radius: 10px; padding: 20px; max-height: 600px; overflow-y: auto;">
                    <pre id="csvJsonDisplay"></pre>
                </div>
            </div>
            
            <div id="csvExplanation" style="display: none; margin-top: 20px; background: white; border-radius: 10px; padding: 20px;">
                <h3 style="color: #333; margin-bottom: 15px;">📊 CSV对比文件结构详解</h3>
                <p style="color: #666;">简化格式包含：modified_columns（修改列映射）、modifications（修改详情）、statistics（统计信息）</p>
            </div>
        </div>
        
        <!-- 智能问答框 -->
        <div class="qa-section">
            <h2>
                🤖 智能问答测试
                <span style="font-size: 14px; font-weight: normal; color: #666;">
                    (自由提问或测试AI能力)
                </span>
            </h2>
            <textarea class="qa-input" id="qaInput" placeholder="输入你的问题或测试内容...
例如：
- 请解释CSV列名标准化的原理
- 如何处理列数不匹配的情况？
- 分析这些列名：[序号, 类型, 来源地, 发起时间]"></textarea>
            
            <div class="qa-controls">
                <button class="qa-button" onclick="askQuestion()">🔍 提问</button>
                <button class="qa-button" onclick="testStandardization()">📊 测试列名标准化</button>
                <button class="qa-button" onclick="showPrompt()">📝 查看提示词</button>
                <button class="qa-button" onclick="clearQA()">🗑️ 清空</button>
            </div>
            
            <div class="prompt-example" style="display: none;" id="promptExample">
                <strong>当前使用的优化提示词：</strong>
                <pre style="margin-top: 10px; max-height: 300px; overflow-y: auto;"></pre>
            </div>
            
            <div id="qaResult" style="margin-top: 20px;"></div>
        </div>

        <div class="main-grid">
            <div class="card">
                <h2>📝 输入CSV对比文件路径</h2>
                
                <div class="input-section">
                    <label>输入简化版CSV对比结果文件路径（simplified_*.json）</label>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="csvPath" 
                               placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_*.json"
                               value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
                               style="flex: 1; padding: 12px; border: 2px solid #667eea; border-radius: 8px; font-size: 14px;">
                        <button class="qa-button" onclick="processFile()" style="padding: 12px 24px;">
                            🚀 开始处理
                        </button>
                    </div>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        💡 提示：输入simplified_开头的JSON文件路径，系统将自动执行处理
                    </p>
                </div>
                
                <!-- 调试信息 -->
                <div style="margin-top: 20px;">
                    <h3 style="color: #666; font-size: 14px;">🐛 调试信息</h3>
                    <div id="debugInfo" class="debug-info">
                        等待操作...
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 文件内容与AI分析过程</h2>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 10px; color: #666;">正在处理...</p>
                </div>
                
                <div id="resultContent">
                    <p style="color: #999; text-align: center; padding: 40px;">
                        请输入CSV对比文件路径并点击"开始处理"
                    </p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔍 输出文件与标准化结果</h2>
            <div id="detailedResult">
                <p style="color: #999; text-align: center; padding: 20px;">
                    等待处理...
                </p>
            </div>
        </div>
    </div>
    
    <script>
        // 添加调试信息
        function addDebugInfo(message, type = 'info') {
            const debugDiv = document.getElementById('debugInfo');
            const timestamp = new Date().toLocaleTimeString();
            const color = type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#333';
            debugDiv.innerHTML += `<div style="color: ${color}">[${timestamp}] ${message}</div>`;
            debugDiv.scrollTop = debugDiv.scrollHeight;
        }
        
        // 处理文件
        async function processFile() {
            addDebugInfo('开始处理文件...', 'info');
            
            const csvPath = document.getElementById('csvPath').value;
            const loading = document.getElementById('loading');
            const resultContent = document.getElementById('resultContent');
            const detailedResult = document.getElementById('detailedResult');
            
            if (!csvPath || !csvPath.trim()) {
                addDebugInfo('错误: 请输入文件路径', 'error');
                alert('请输入CSV对比文件路径');
                return;
            }
            
            addDebugInfo('文件路径: ' + csvPath, 'info');
            
            // 显示加载状态
            loading.style.display = 'block';
            resultContent.innerHTML = '';
            detailedResult.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">处理中...</p>';
            
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
                
                // 显示文件内容
                displayProcessSteps(fileData.content);
                
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
                
                // 隐藏加载状态
                loading.style.display = 'none';
                
                // 显示结果
                displayOutputResult(csvPath, result.data);
                
            } catch (error) {
                addDebugInfo('❌ 错误: ' + error.message, 'error');
                loading.style.display = 'none';
                resultContent.innerHTML = `<div class="error-msg">处理失败: ${error.message}</div>`;
            }
        }
        
        // 显示处理步骤
        function displayProcessSteps(fileContent) {
            const modifiedColumns = fileContent.modified_columns || {};
            const modifications = fileContent.modifications || [];
            const statistics = fileContent.statistics || {};
            
            const html = `
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">📄 输入文件内容</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p><strong>修改列数：</strong>${Object.keys(modifiedColumns).length}列</p>
                        <p><strong>修改单元格：</strong>${modifications.length}个</p>
                        <p><strong>相似度：</strong>${(statistics.similarity * 100).toFixed(1)}%</p>
                        <div style="margin-top: 10px;">
                            <strong>修改的列：</strong>
                            <div style="margin-top: 5px;">
                                ${Object.entries(modifiedColumns).map(([col, name]) => 
                                    `<span style="display: inline-block; padding: 3px 8px; margin: 2px; background: #e3f2fd; border-radius: 4px;">${col}: ${name}</span>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('resultContent').innerHTML = html;
        }
        
        // 显示输出结果
        function displayOutputResult(inputPath, data) {
            const outputPath = inputPath.replace('.json', '_standardized.json');
            const mapping = data.mapping || {};
            const confidence = data.confidence_scores || {};
            
            let html = `
                <div style="margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); border-radius: 10px;">
                    <h3 style="color: #2e7d32; margin-bottom: 10px;">✅ 处理完成</h3>
                    <p style="margin-bottom: 10px;"><strong>输出文件路径：</strong></p>
                    <div style="background: white; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 13px; word-break: break-all;">
                        ${data.output_file || outputPath}
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #333; margin-bottom: 15px;">📊 标准化映射结果</h3>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="background: #e3f2fd;">
                                <th style="padding: 10px; text-align: left;">原始列名</th>
                                <th style="padding: 10px; text-align: left;">标准列名</th>
                                <th style="padding: 10px; text-align: left;">置信度</th>
                            </tr>
                            ${Object.entries(mapping).map(([orig, std]) => `
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px;">${orig}</td>
                                    <td style="padding: 8px; font-weight: bold; color: #667eea;">${std}</td>
                                    <td style="padding: 8px;">${(confidence[orig] * 100).toFixed(0)}%</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                </div>
            `;
            
            document.getElementById('detailedResult').innerHTML = html;
            addDebugInfo('结果显示完成', 'success');
        }
        
        // 智能问答功能
        async function askQuestion() {
            const question = document.getElementById('qaInput').value;
            if (!question.trim()) {
                alert('请输入问题');
                return;
            }
            
            const resultDiv = document.getElementById('qaResult');
            resultDiv.innerHTML = '<div class="loading" style="display: block;"><div class="spinner"></div><p>正在思考...</p></div>';
            
            try {
                const response = await fetch('/api/qa', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="success-msg">
                            <strong>DeepSeek回答：</strong>
                            <pre style="margin-top: 10px; white-space: pre-wrap;">${result.answer}</pre>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="error-msg">错误: ${result.error}</div>`;
                }
            } catch (e) {
                resultDiv.innerHTML = `<div class="error-msg">请求失败: ${e.message}</div>`;
            }
        }
        
        // 测试标准化
        function testStandardization() {
            const input = document.getElementById('qaInput').value;
            try {
                const columns = JSON.parse(input);
                if (Array.isArray(columns)) {
                    document.getElementById('csvPath').value = '';
                    processFileWithColumns(columns);
                }
            } catch (e) {
                alert('请输入有效的JSON数组格式的列名');
            }
        }
        
        // 显示提示词
        function showPrompt() {
            const promptDiv = document.getElementById('promptExample');
            if (promptDiv.style.display === 'none' || promptDiv.style.display === '') {
                const prompt = build_optimized_prompt(['示例列1', '示例列2'], null, true);
                promptDiv.querySelector('pre').textContent = prompt;
                promptDiv.style.display = 'block';
            } else {
                promptDiv.style.display = 'none';
            }
        }
        
        // 清空问答
        function clearQA() {
            document.getElementById('qaInput').value = '';
            document.getElementById('qaResult').innerHTML = '';
        }
        
        // 加载CSV示例
        async function loadCSVExample() {
            const content = document.getElementById('csvExampleContent');
            const display = document.getElementById('csvJsonDisplay');
            
            if (content.style.display === 'none') {
                // 加载示例文件
                const examplePath = '/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json';
                
                try {
                    const response = await fetch('/api/read_file', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file_path: examplePath })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        display.textContent = JSON.stringify(data.content, null, 2);
                        content.style.display = 'block';
                    }
                } catch (e) {
                    display.textContent = '加载示例失败: ' + e.message;
                    content.style.display = 'block';
                }
            } else {
                content.style.display = 'none';
            }
        }
        
        // 切换说明
        function toggleCSVExplanation() {
            const explanation = document.getElementById('csvExplanation');
            explanation.style.display = explanation.style.display === 'none' ? 'block' : 'none';
        }
        
        // 测试完整流程
        function testCompleteFlow() {
            const testPath = '/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json';
            document.getElementById('csvPath').value = testPath;
            processFile();
        }
        
        // 页面加载完成后的初始化
        window.onload = function() {
            addDebugInfo('页面加载完成', 'success');
            addDebugInfo('系统就绪，等待操作', 'info');
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
        use_numbering = data.get('use_numbering', True)
        
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
        output_file = None
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

@app.route('/api/qa', methods=['POST'])
def qa_endpoint():
    """智能问答接口"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({"success": False, "error": "没有提供问题"})
        
        logger.info(f"收到问题: {question[:100]}...")
        
        # 构建问答提示词
        messages = [
            {"role": "system", "content": "你是一个专业的CSV数据处理专家，精通列名标准化和数据映射。"},
            {"role": "user", "content": question}
        ]
        
        # 调用DeepSeek API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(deepseek_client.chat_completion(messages))
        
        if response and 'choices' in response:
            answer = response['choices'][0]['message']['content']
            return jsonify({"success": True, "answer": answer})
        else:
            return jsonify({"success": False, "error": "AI未返回有效响应"})
            
    except Exception as e:
        logger.error(f"问答失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get_prompt')
def get_prompt():
    """获取当前提示词"""
    prompt = build_optimized_prompt(
        ['示例列1', '示例列2', '示例列3'],
        'example.csv',
        use_numbering=True
    )
    return jsonify({"prompt": prompt})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   DeepSeek V3 AI列名标准化测试平台 - 完整版           ║
    ║   端口: 8098                                         ║
    ║   访问: http://localhost:8098                        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 先关闭旧的8098服务
    os.system("kill $(lsof -t -i:8098) 2>/dev/null")
    time.sleep(2)
    
    app.run(host='0.0.0.0', port=8098, debug=False)