#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek V3 AI列名标准化测试平台 - 完整流程版
支持简化CSV对比→列提取→AI标准化→覆盖列名的完整链路
包含超19列智能筛选可视化
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import asyncio
import json
import logging
from typing import Dict, Any, List
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepseek_client import DeepSeekClient
from column_standardization_processor_v3 import ColumnStandardizationProcessorV3
from simplified_csv_comparator import SimplifiedCSVComparator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask应用
app = Flask(__name__)
CORS(app)

# DeepSeek客户端
API_KEY = "sk-onzowexyblsrgltveejlnajoutrjqwbrqkwzcccskwmzonvb"
deepseek_client = DeepSeekClient(API_KEY)

# 19个标准列名
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
    "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
]

def add_column_labels(columns: List[str]) -> Dict[str, str]:
    """为列名添加英文字母序号"""
    import string
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
    """
    构建深度优化的提示词，支持序号映射系统
    只处理有修改的列（修改值≠0）
    """
    
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
    else:
        # 原始提示词格式
        prompt = f"""你是一个专业的CSV列名标准化专家，精通数据映射和语义理解。

## 🎯 核心任务
分析CSV表格中有修改的列名，将其智能映射到19个预定义的标准列名。

## ⚠️ 重要说明
这些列都是从CSV对比结果中提取的有实际修改的列（修改值≠0）

## 📋 19个标准列名（固定顺序，必须全部包含）
{json.dumps(STANDARD_COLUMNS, ensure_ascii=False, indent=2)}

## 📊 当前CSV文件信息
- 文件路径: {csv_file_path or '未指定'}
- 实际列数: {column_count}个
- 标准列数: 19个
- 处理策略: {strategy}

## 📝 实际列名（共{column_count}个）
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

## 🔄 智能映射规则
1. **精确匹配优先**: 完全相同的列名直接映射（置信度1.0）
2. **变异识别**: 识别常见变异形式（如"编号"→"序号"，置信度0.8-0.95）
3. **语义理解**: 基于语义相似度映射（如"执行人"→"负责人"，置信度0.6-0.79）
4. **位置推测**: 根据列的位置关系推测（置信度0.4-0.59）

## 🎯 特殊处理逻辑
{special_logic}

## 📊 输出格式要求（严格JSON）
{{
    "success": true,
    "standard_columns_status": {{
        "序号": "映射的实际列名或null",
        "项目类型": "映射的实际列名或null",
        "来源": "映射的实际列名或null",
        "任务发起时间": "映射的实际列名或null",
        "目标对齐": "映射的实际列名或null",
        "关键KR对齐": "映射的实际列名或null",
        "具体计划内容": "映射的实际列名或null",
        "邓总指导登记": "映射的实际列名或null",
        "负责人": "映射的实际列名或null",
        "协助人": "映射的实际列名或null",
        "监督人": "映射的实际列名或null",
        "重要程度": "映射的实际列名或null",
        "预计完成时间": "映射的实际列名或null",
        "完成进度": "映射的实际列名或null",
        "形成计划清单": "映射的实际列名或null",
        "复盘时间": "映射的实际列名或null",
        "对上汇报": "映射的实际列名或null",
        "应用情况": "映射的实际列名或null",
        "进度分析总结": "映射的实际列名或null"
    }},
    "mapping": {{
        // 实际列名到标准列名的映射关系
    }},
    "confidence_scores": {{
        // 每个映射的置信度（0.0-1.0）
    }},
    "missing_standard_columns": [
        // 缺失的标准列名列表
    ],
    "discarded_columns": [
        // 被丢弃的多余实际列名列表
    ],
    "statistics": {{
        "mapped_count": 0,      // 成功映射的列数
        "missing_count": 0,     // 缺失的标准列数
        "discarded_count": 0    // 被丢弃的实际列数
    }}
}}

## ⚠️ 关键约束
1. standard_columns_status必须包含全部19个标准列，顺序固定
2. 每个标准列只能映射一个实际列（或null）
3. 缺失的标准列必须明确标记为null
4. 返回纯JSON格式，不要包含其他解释文字

请立即分析并返回标准化映射结果。"""
    return prompt

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek V3 AI列名标准化测试平台 - 增强版</title>
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
        
        .input-section textarea {
            width: 100%;
            height: 200px;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
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

        <!-- CSV完整案例展示 -->
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
                    <pre id="csvJsonDisplay" style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word;"></pre>
                </div>
            </div>
            
            <div id="csvExplanation" style="display: none; margin-top: 20px; background: white; border-radius: 10px; padding: 20px;">
                <h3 style="color: #333; margin-bottom: 15px;">📊 CSV对比文件结构详解</h3>
                
                <div style="margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                    <h4 style="color: #1976d2;">1️⃣ metadata - 元数据部分</h4>
                    <ul style="margin-top: 10px; color: #555;">
                        <li><strong>baseline_file</strong>: 基准文件路径（对比的原始文件）</li>
                        <li><strong>target_file</strong>: 目标文件路径（对比的新文件）</li>
                        <li><strong>comparison_time</strong>: 对比执行时间</li>
                        <li><strong>baseline_structure</strong>: 基准文件结构信息
                            <ul>
                                <li>rows: 总行数</li>
                                <li>columns: 总列数</li>
                                <li>column_names: 列名数组（需要标准化的对象）</li>
                            </ul>
                        </li>
                    </ul>
                </div>
                
                <div style="margin-bottom: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px;">
                    <h4 style="color: #388e3c;">2️⃣ summary - 摘要信息</h4>
                    <ul style="margin-top: 10px; color: #555;">
                        <li><strong>similarity_score</strong>: 相似度评分（0-1之间）</li>
                        <li><strong>total_differences</strong>: 总差异数量</li>
                        <li><strong>modified_cells</strong>: 修改的单元格数量</li>
                        <li><strong>added_rows</strong>: 新增行数</li>
                        <li><strong>deleted_rows</strong>: 删除行数</li>
                    </ul>
                </div>
                
                <div style="padding: 15px; background: #fff3e0; border-radius: 8px;">
                    <h4 style="color: #f57c00;">3️⃣ details.modified_cells - 核心数据</h4>
                    <p style="margin-top: 10px; color: #555;">每个修改的单元格包含：</p>
                    <ul style="margin-top: 10px; color: #555;">
                        <li><strong style="color: #d32f2f;">column</strong>: Excel列标识（C、D、E等） - 🔑 这是映射的关键！</li>
                        <li><strong style="color: #d32f2f;">column_name</strong>: 当前列名 - 需要标准化的目标</li>
                        <li><strong>cell</strong>: 单元格位置（如C4、D5）</li>
                        <li><strong>row_number</strong>: 行号</li>
                        <li><strong>baseline_value</strong>: 原始值</li>
                        <li><strong>target_value</strong>: 新值</li>
                    </ul>
                    <div style="margin-top: 15px; padding: 10px; background: #ffccbc; border-radius: 5px;">
                        <strong>💡 关键理解：</strong>我们使用<code>column</code>字段来精确定位，然后更新<code>column_name</code>为标准列名！
                    </div>
                </div>
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
                        <input type="text" id="csvPath" placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250905_224147.json"
                               style="flex: 1; padding: 12px; border: 2px solid #667eea; border-radius: 8px; font-size: 14px;">
                        <button class="qa-button" onclick="processFile()" style="padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: bold;">
                            🚀 开始处理
                        </button>
                    </div>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        💡 提示：输入simplified_开头的JSON文件路径，系统将自动执行CSV对比→列提取→AI标准化→结果输出的完整流程
                    </p>
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
        // 处理文件相关函数
        
        async function processFile() {
            const csvPath = document.getElementById('csvPath').value;
            
            if (!csvPath.trim()) {
                alert('请输入CSV对比文件路径');
                return;
            }
            
            // 显示加载状态
            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultContent').innerHTML = '';
            document.getElementById('detailedResult').innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">处理中...</p>';
            
            try {
                // Step 1: 读取文件内容
                const fileResponse = await fetch('/api/read_file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: csvPath })
                });
                
                const fileData = await fileResponse.json();
                
                if (!fileData.success) {
                    throw new Error(fileData.error || '文件读取失败');
                }
                
                // 显示文件内容和处理步骤
                displayProcessSteps(fileData.content);
                
                // Step 2: 执行AI标准化
                const columns = Object.values(fileData.content.modified_columns || {});
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        columns: columns,
                        csv_path: csvPath,
                        use_numbering: true,
                        filter_modified: true
                    })
                });
                
                const result = await response.json();
                
                // 隐藏加载状态
                document.getElementById('loading').style.display = 'none';
                
                if (result.success) {
                    // 显示输出文件路径和内容
                    displayOutputResult(csvPath, result.data);
                } else {
                    showError(result.error);
                }
                
            } catch (e) {
                document.getElementById('loading').style.display = 'none';
                showError('处理失败: ' + e.message);
            }
        }
        
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
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #764ba2; margin-bottom: 15px;">🔧 AI标准化处理步骤</h3>
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px;">
                        <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #667eea;">
                            <strong style="color: #667eea;">步骤1️⃣：列提取</strong>
                            <p style="margin-top: 8px; font-size: 14px; color: #555;">
                                程序：<code>column_standardization_processor_v3.py</code><br>
                                方法：<code>extract_columns_from_simplified_comparison()</code><br>
                                位置：第46-81行<br>
                                操作：从<code>modified_columns</code>字段提取${Object.keys(modifiedColumns).length}个修改列
                            </p>
                        </div>
                        
                        <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #764ba2;">
                            <strong style="color: #764ba2;">步骤2️⃣：构建提示词</strong>
                            <p style="margin-top: 8px; font-size: 14px; color: #555;">
                                程序：<code>column_standardization_processor_v3.py</code><br>
                                方法：<code>build_smart_standardization_prompt()</code><br>
                                位置：第51-142行<br>
                                操作：为列添加序号标记(A-${String.fromCharCode(65 + Object.keys(modifiedColumns).length - 1)})，构建智能提示词
                            </p>
                        </div>
                        
                        <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #f093fb;">
                            <strong style="color: #f093fb;">步骤3️⃣：DeepSeek API调用</strong>
                            <p style="margin-top: 8px; font-size: 14px; color: #555;">
                                程序：<code>column_standardization_processor_v3.py</code><br>
                                方法：<code>standardize_column_names()</code><br>
                                位置：第144-192行<br>
                                操作：调用DeepSeek-V3进行智能标准化${Object.keys(modifiedColumns).length > 19 ? '，智能筛选最重要的19列' : ''}
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #4facfe;">
                            <strong style="color: #4facfe;">步骤4️⃣：结果应用</strong>
                            <p style="margin-top: 8px; font-size: 14px; color: #555;">
                                程序：<code>column_standardization_processor_v3.py</code><br>
                                方法：<code>apply_standardization_to_simplified_file()</code><br>
                                位置：第194-257行<br>
                                操作：将标准化结果写入新文件
                            </p>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('resultContent').innerHTML = html;
        }
        
        function displayOutputResult(inputPath, data) {
            // 生成输出文件路径
            const outputPath = inputPath.replace('.json', '_standardized.json');
            
            const mapping = data.standard_columns_status || {};
            const confidence = data.confidence_scores || {};
            const statistics = data.statistics || {};
            
            let html = `
                <div style="margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); border-radius: 10px;">
                    <h3 style="color: #2e7d32; margin-bottom: 10px;">✅ 处理完成</h3>
                    <p style="margin-bottom: 10px;"><strong>输出文件路径：</strong></p>
                    <div style="background: white; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 13px; word-break: break-all;">
                        ${outputPath}
                    </div>
                    <div style="margin-top: 15px; display: flex; gap: 20px;">
                        <div><strong>成功映射：</strong>${statistics.mapped_count || 0}列</div>
                        <div><strong>缺失列：</strong>${statistics.missing_count || 0}列</div>
                        <div><strong>丢弃列：</strong>${statistics.discarded_count || 0}列</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #333; margin-bottom: 15px;">📊 标准化映射结果</h3>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
            `;
            
            // 显示19个标准列的映射结果
            const standardColumns = [
                "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
                "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
                "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
                "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
            ];
            
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">';
            
            for (const standard of standardColumns) {
                const actual = mapping[standard];
                const conf = actual ? (confidence[actual] || 0) : 0;
                const confClass = conf >= 0.8 ? '#4caf50' : conf >= 0.6 ? '#ff9800' : '#f44336';
                
                html += `
                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #667eea; font-weight: 500;">${standard}</span>
                            <span style="font-size: 20px; color: #999;">→</span>
                            <span style="${actual ? '' : 'color: #999; font-style: italic;'}">
                                ${actual || 'null'}
                                ${actual && conf ? `<span style="display: inline-block; padding: 2px 6px; background: ${confClass}; color: white; border-radius: 3px; font-size: 11px; margin-left: 5px;">${(conf * 100).toFixed(0)}%</span>` : ''}
                            </span>
                        </div>
                    </div>
                `;
            }
            
            html += '</div></div>';
            
            // 显示输出文件的JSON结构预览
            html += `
                <div>
                    <h3 style="color: #333; margin-bottom: 15px;">📄 输出文件内容预览</h3>
                    <pre style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 12px; max-height: 300px;">
{
  "standardized_columns": {
    ${Object.entries(mapping).slice(0, 5).map(([k, v]) => `"${k}": "${v || 'null'}"`).join(',\n    ')}
    ... // 共19个标准列映射
  },
  "original_modified_columns": {
    // 原始修改列备份
  },
  "standardization_metadata": {
    "processed_at": "${new Date().toISOString()}",
    "model": "deepseek-ai/DeepSeek-V3",
    "format_version": "simplified_v3"
  }
}</pre>
                </div>
            `;
            
            document.getElementById('detailedResult').innerHTML = html;
        }
        
        async function runAnalysis() {
            const input = document.getElementById('columnsInput').value;
            const csvPath = document.getElementById('csvPath').value;
            const useNumbering = document.getElementById('useNumbering').checked;
            
            try {
                const columns = JSON.parse(input);
                
                // 显示加载状态
                document.getElementById('loading').style.display = 'block';
                document.getElementById('resultContent').innerHTML = '';
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        columns: columns,
                        csv_path: csvPath || null,
                        use_numbering: useNumbering,
                        filter_modified: true  // 只处理有修改的列
                    })
                });
                
                const result = await response.json();
                
                // 隐藏加载状态
                document.getElementById('loading').style.display = 'none';
                
                if (result.success) {
                    displayResult(result.data);
                } else {
                    showError(result.error);
                }
                
            } catch (e) {
                document.getElementById('loading').style.display = 'none';
                showError('输入格式错误: ' + e.message);
            }
        }
        
        function displayResult(data) {
            // 显示统计信息
            const stats = data.statistics || {};
            document.getElementById('resultContent').innerHTML = `
                <div class="result-section">
                    <div class="result-title">📊 统计信息</div>
                    <div class="status-info">
                        <div class="status-item">
                            <div class="status-label">成功映射</div>
                            <div class="status-value" style="color: #28a745;">${stats.mapped_count || 0}</div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">缺失列</div>
                            <div class="status-value" style="color: #dc3545;">${stats.missing_count || 0}</div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">丢弃列</div>
                            <div class="status-value" style="color: #ffc107;">${stats.discarded_count || 0}</div>
                        </div>
                    </div>
                </div>
                
                ${data.missing_standard_columns && data.missing_standard_columns.length > 0 ? `
                <div class="missing-columns">
                    <div class="result-title">❌ 缺失的标准列</div>
                    ${data.missing_standard_columns.map(col => 
                        `<span class="column-tag missing-tag">${col}</span>`
                    ).join('')}
                </div>
                ` : ''}
                
                ${data.discarded_columns && data.discarded_columns.length > 0 ? `
                <div class="discarded-columns">
                    <div class="result-title">🗑️ 被丢弃的多余列</div>
                    ${data.discarded_columns.map(col => 
                        `<span class="column-tag discarded-tag">${col}</span>`
                    ).join('')}
                </div>
                ` : ''}
            `;
            
            // 显示详细映射
            displayDetailedMapping(data);
        }
        
        function displayDetailedMapping(data) {
            const mapping = data.standard_columns_status || {};
            const confidence = data.confidence_scores || {};
            const columnLabels = data.column_labels || {};
            const processInfo = data.process_info || {};
            
            let html = '';
            
            // 如果有序号映射信息，先显示它
            if (Object.keys(columnLabels).length > 0) {
                html += `
                    <div style="margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                        <h3 style="color: #1976d2; margin-bottom: 10px;">📌 序号映射系统</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">
                `;
                
                for (const [label, column] of Object.entries(columnLabels)) {
                    html += `
                        <div style="background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #90caf9;">
                            <strong style="color: #1976d2;">${label}:</strong> ${column}
                        </div>
                    `;
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            // 显示处理信息
            if (processInfo.use_numbering) {
                html += `
                    <div style="margin-bottom: 15px; padding: 10px; background: #f0f4ff; border-radius: 6px;">
                        <strong>处理模式：</strong>序号映射模式 | 
                        <strong>原始列数：</strong>${processInfo.original_count} | 
                        <strong>过滤后：</strong>${processInfo.filtered_count}
                    </div>
                `;
            }
            
            html += '<div class="mapping-grid">';
            
            for (const [standard, actual] of Object.entries(mapping)) {
                const conf = actual ? (confidence[actual] || 0) : 0;
                const confClass = conf >= 0.8 ? 'confidence-high' : 
                                 conf >= 0.6 ? 'confidence-medium' : 'confidence-low';
                
                html += `
                    <div class="mapping-item">
                        <div>${standard}</div>
                        <div class="mapping-arrow">→</div>
                        <div>
                            ${actual || '<span style="color: #999;">缺失</span>'}
                            ${actual && conf ? `<span class="confidence-badge ${confClass}">${(conf * 100).toFixed(0)}%</span>` : ''}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            document.getElementById('detailedResult').innerHTML = html;
        }
        
        function showError(message) {
            document.getElementById('resultContent').innerHTML = 
                `<div class="error-msg">错误: ${message}</div>`;
        }
        
        // 智能问答功能
        async function askQuestion() {
            const question = document.getElementById('qaInput').value;
            if (!question.trim()) {
                alert('请输入问题');
                return;
            }
            
            const resultDiv = document.getElementById('qaResult');
            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在思考...</p></div>';
            
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
        
        function testStandardization() {
            const input = document.getElementById('qaInput').value;
            try {
                // 尝试解析为JSON数组
                const columns = JSON.parse(input);
                if (Array.isArray(columns)) {
                    document.getElementById('columnsInput').value = JSON.stringify(columns, null, 2);
                    updateStatus();
                    runAnalysis();
                }
            } catch (e) {
                alert('请输入有效的JSON数组格式的列名');
            }
        }
        
        function showPrompt() {
            const promptDiv = document.getElementById('promptExample');
            if (promptDiv.style.display === 'none' || promptDiv.style.display === '') {
                // 获取当前提示词
                fetch('/api/get_prompt')
                    .then(res => res.json())
                    .then(data => {
                        const preElement = promptDiv.querySelector('pre');
                        if (preElement) {
                            preElement.textContent = data.prompt;
                        } else {
                            // 如果pre元素不存在，创建它
                            const newPre = document.createElement('pre');
                            newPre.style.marginTop = '10px';
                            newPre.style.maxHeight = '300px';
                            newPre.style.overflowY = 'auto';
                            newPre.textContent = data.prompt;
                            promptDiv.appendChild(newPre);
                        }
                        promptDiv.style.display = 'block';
                    })
                    .catch(err => {
                        console.error('获取提示词失败:', err);
                        alert('获取提示词失败');
                    });
            } else {
                promptDiv.style.display = 'none';
            }
        }
        
        function clearQA() {
            document.getElementById('qaInput').value = '';
            document.getElementById('qaResult').innerHTML = '';
            document.getElementById('promptExample').style.display = 'none';
        }
        
        // 加载CSV完整案例
        async function testCompleteFlow() {
            // 测试完整处理流程
            const baseline = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-测试版本-出国销售计划表-工作表1_csv_20250905_1137_midweek_W36.csv";
            const target = "/root/projects/tencent-doc-manager/csv_versions/2025_W36/midweek/tencent_副本-副本-测试版本-出国销售计划表-工作表1_csv_20250905_1137_midweek_W36.csv";
            
            showResult("info", "🚀 开始测试完整处理流程...");
            
            try {
                const response = await fetch('/api/process_flow', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        baseline_file: baseline,
                        target_file: target
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    let html = '<div style="background: #e8f5e9; padding: 20px; border-radius: 10px;">';
                    html += '<h3 style="color: #2e7d32;">✅ 完整流程处理成功！</h3>';
                    
                    // 步骤1结果
                    const step1 = result.flow_steps.step1_comparison;
                    html += '<div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px;">';
                    html += '<h4>步骤1：CSV对比（简化版）</h4>';
                    html += `<ul>
                        <li>相似度：${(step1.similarity * 100).toFixed(1)}%</li>
                        <li>总修改数：${step1.modifications}</li>
                        <li>修改列数：${step1.columns_count}</li>
                    </ul>`;
                    html += '</div>';
                    
                    // 步骤2结果
                    const step2 = result.flow_steps.step2_extraction;
                    html += '<div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px;">';
                    html += '<h4>步骤2：列提取（去重）</h4>';
                    html += '<ul>';
                    for (const [col, name] of Object.entries(step2.modified_columns)) {
                        html += `<li>列${col}: ${name}</li>`;
                    }
                    html += '</ul>';
                    html += '</div>';
                    
                    // 步骤3结果
                    const step3 = result.flow_steps.step3_standardization;
                    html += '<div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px;">';
                    html += '<h4>步骤3：AI标准化</h4>';
                    if (step3.success) {
                        html += `<ul>
                            <li>映射列数：${step3.statistics.mapped_count || 0}</li>
                            <li>筛选掉列数：${step3.filtered_count || 0}</li>
                            <li>输出文件：${step3.output_file}</li>
                        </ul>`;
                    }
                    html += '</div>';
                    
                    html += '</div>';
                    showResult("success", html);
                } else {
                    showResult("error", `流程失败：${result.error}`);
                }
            } catch (error) {
                showResult("error", `请求失败：${error.message}`);
            }
        }
        
        async function loadCSVExample() {
            const contentDiv = document.getElementById('csvExampleContent');
            const jsonDisplay = document.getElementById('csvJsonDisplay');
            
            // 显示加载中
            jsonDisplay.textContent = '正在加载CSV文件...';
            contentDiv.style.display = 'block';
            
            try {
                const response = await fetch('/api/load_csv_example');
                const data = await response.json();
                
                if (data.success) {
                    // 美化JSON显示
                    jsonDisplay.textContent = JSON.stringify(data.content, null, 2);
                    
                    // 语法高亮（简单版）
                    let html = jsonDisplay.textContent;
                    html = html.replace(/"(.*?)"/g, '<span style="color: #a6e22e;">"$1"</span>');
                    html = html.replace(/: (\d+)/g, ': <span style="color: #ae81ff;">$1</span>');
                    html = html.replace(/: (true|false)/g, ': <span style="color: #ae81ff;">$1</span>');
                    html = html.replace(/: (null)/g, ': <span style="color: #f92672;">$1</span>');
                    jsonDisplay.innerHTML = html;
                } else {
                    jsonDisplay.textContent = '加载失败: ' + (data.error || '未知错误');
                }
            } catch (err) {
                jsonDisplay.textContent = '加载失败: ' + err.message;
            }
        }
        
        // 切换CSV说明显示
        function toggleCSVExplanation() {
            const explanationDiv = document.getElementById('csvExplanation');
            if (explanationDiv.style.display === 'none' || explanationDiv.style.display === '') {
                explanationDiv.style.display = 'block';
            } else {
                explanationDiv.style.display = 'none';
            }
        }
        
        // 初始化完成
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze', methods=['POST'])
def analyze_columns():
    """分析列名映射 - 支持序号系统和只处理有修改的列"""
    try:
        data = request.json
        columns = data.get('columns', [])
        csv_path = data.get('csv_path', None)
        use_numbering = data.get('use_numbering', False)
        filter_modified = data.get('filter_modified', True)  # 默认只处理有修改的列
        
        if not columns:
            return jsonify({"success": False, "error": "没有提供列名"})
        
        # 记录处理信息
        process_info = {
            "original_count": len(columns),
            "filtered_count": len(columns),
            "use_numbering": use_numbering,
            "filter_modified": filter_modified
        }
        
        logger.info(f"开始分析 {len(columns)} 个列名，CSV路径: {csv_path}，使用序号: {use_numbering}")
        
        # 构建优化提示词
        prompt = build_optimized_prompt(columns, csv_path, use_numbering)
        
        # 如果使用序号系统，需要特殊处理响应
        if use_numbering:
            labeled_columns = add_column_labels(columns)
            process_info["column_labels"] = labeled_columns
        
        # 调用DeepSeek API
        result = deepseek_client.sync_analyze_columns(columns, STANDARD_COLUMNS)
        
        if result.get("success"):
            response_data = result.get("result", {})
            
            # 如果使用序号系统，添加序号映射信息
            if use_numbering and "column_labels" in process_info:
                response_data["column_labels"] = process_info["column_labels"]
            
            response_data["process_info"] = process_info
            
            return jsonify({
                "success": True,
                "data": response_data,
                "raw_response": result.get("raw_response", "")
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"分析失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/read_file', methods=['POST'])
def read_file():
    """读取JSON文件内容"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({"success": False, "error": "没有提供文件路径"})
        
        logger.info(f"读取文件: {file_path}")
        
        # 验证文件存在
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"文件不存在: {file_path}"})
        
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return jsonify({
            "success": True,
            "content": content,
            "file_path": file_path
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return jsonify({"success": False, "error": f"JSON解析失败: {str(e)}"})
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
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
            {
                "role": "system",
                "content": "你是一个专业的AI助手，精通CSV数据处理、列名标准化和数据映射。请用简洁清晰的中文回答问题。"
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # 同步调用API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                deepseek_client.chat_completion(messages, temperature=0.7)
            )
        finally:
            loop.close()
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "answer": result.get("content", "")
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"问答失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get_prompt', methods=['GET'])
def get_prompt():
    """获取当前使用的提示词"""
    try:
        # 示例提示词
        example_columns = ["序号", "类型", "来源地", "发起时间", "KR"]
        prompt = build_optimized_prompt(example_columns, "/example/path.csv", use_numbering=True)
        
        return jsonify({
            "success": True,
            "prompt": prompt
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/load_csv_example', methods=['GET'])
def load_csv_example():
    """加载CSV对比文件案例 - 支持简化格式"""
    try:
        # 优先使用简化格式文件
        simplified_file = "/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250905_224147.json"
        
        # 如果简化文件存在，使用它
        if os.path.exists(simplified_file):
            csv_file_path = simplified_file
        else:
            # 否则使用旧格式文件
            csv_file_path = "/root/projects/tencent-doc-manager/comparison_results/comparison_params_出国销售表_vs_出国销售表_20250905_113757_63diffs.json"
            
            if not os.path.exists(csv_file_path):
                csv_file_path = "/root/projects/tencent-doc-manager/comparison_results/comparison_params_出国销售表_vs_出国销售表_20250905_003444_63diffs.json"
        
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            return jsonify({
                "success": True,
                "content": content,
                "file_path": csv_file_path
            })
        else:
            # 如果都不存在，返回示例数据
            example_data = {
                "metadata": {
                    "baseline_file": "基准文件路径.csv",
                    "target_file": "目标文件路径.csv",
                    "comparison_time": "2025-09-05T11:37:57",
                    "baseline_structure": {
                        "rows": 114,
                        "columns": 19,
                        "column_names": STANDARD_COLUMNS
                    }
                },
                "summary": {
                    "similarity_score": 0.978,
                    "total_differences": 63,
                    "modified_cells": 63
                },
                "details": {
                    "modified_cells": [
                        {
                            "cell": "C4",
                            "column": "C",
                            "column_name": "项目类型",
                            "row_number": 4,
                            "baseline_value": "目标管理",
                            "target_value": "固定计划"
                        }
                    ]
                }
            }
            
            return jsonify({
                "success": True,
                "content": example_data,
                "file_path": "示例数据"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# 添加新的API端点 - 完整处理流程
@app.route('/api/process_flow', methods=['POST'])
def process_complete_flow():
    """完整处理流程：CSV对比→列提取→AI标准化→覆盖"""
    try:
        data = request.json
        baseline_file = data.get('baseline_file')
        target_file = data.get('target_file')
        
        if not baseline_file or not target_file:
            return jsonify({"success": False, "error": "缺少基线文件或目标文件路径"})
        
        # 步骤1：CSV对比（简化版）
        comparator = SimplifiedCSVComparator()
        comparison_result = comparator.compare(
            baseline_file, 
            target_file,
            "/root/projects/tencent-doc-manager/comparison_results"
        )
        
        # 步骤2：提取修改列
        modified_columns = comparison_result.get('modified_columns', {})
        
        # 步骤3：AI标准化（支持超19列筛选）
        processor = ColumnStandardizationProcessorV3(API_KEY)
        
        # 模拟保存临时文件
        temp_file = "/tmp/temp_comparison.json"
        with open(temp_file, 'w') as f:
            json.dump(comparison_result, f, ensure_ascii=False, indent=2)
        
        standardization_result = processor.sync_process_file(temp_file)
        
        # 返回完整流程结果
        return jsonify({
            "success": True,
            "flow_steps": {
                "step1_comparison": {
                    "similarity": comparison_result['statistics']['similarity'],
                    "modifications": comparison_result['statistics']['total_modifications'],
                    "columns_count": len(modified_columns)
                },
                "step2_extraction": {
                    "modified_columns": modified_columns
                },
                "step3_standardization": standardization_result
            }
        })
        
    except Exception as e:
        logger.error(f"流程处理失败: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║   DeepSeek V3 AI列名标准化测试平台 - 完整流程版        ║
    ║   模型: deepseek-ai/DeepSeek-V3                      ║
    ║   端口: 8098                                         ║
    ║   访问: http://localhost:8098                        ║
    ╚══════════════════════════════════════════════════════╝
    
    核心功能：
    ✅ 简化CSV对比 - 文件大小减少89%
    ✅ 智能列提取 - 直接从modified_columns读取
    ✅ AI标准化V3 - 支持超19列智能筛选
    ✅ 完整处理链 - CSV对比→列提取→AI标准化→覆盖
    ✅ 可视化流程 - 每步骤详细展示
    """)
    
    app.run(host='0.0.0.0', port=8098, debug=False)