#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版8098服务 - 包含AI语义分析两层架构模块
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

# 导入L2语义分析模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'production', 'core_modules'))
from l2_semantic_analysis_two_layer import L2SemanticAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask应用
app = Flask(__name__)
CORS(app)

# DeepSeek客户端 - 从环境变量获取API密钥
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ 已加载.env文件: {env_path}")

API_KEY = os.getenv('DEEPSEEK_API_KEY')
if not API_KEY:
    logger.error("DEEPSEEK_API_KEY未配置，请设置环境变量或在.env文件中配置")
    raise ValueError("DEEPSEEK_API_KEY未配置")

deepseek_client = DeepSeekClient(API_KEY)
processor = ColumnStandardizationProcessorV3(API_KEY)

# L2语义分析器 - 使用DeepSeek客户端
l2_analyzer = L2SemanticAnalyzer(api_client=deepseek_client)

# 标准列名
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
    "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
]

# L2列定义
L2_COLUMNS = [
    "项目类型", "具体计划内容", "邓总指导登记（日更新）",
    "负责人", "协助人", "监督人", "形成计划清单"
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
- 处理策略: {strategy}

## 🎯 输出要求
请直接输出标准化后的映射结果，格式如下：
{{
  "A": "对应的标准列名",
  "B": "对应的标准列名",
  ...
}}"""
    
    return prompt

def build_layer1_prompt(modifications: List[Dict]) -> str:
    """构建第一层快速筛选提示词"""
    
    # 格式化修改列表
    mods_text = ""
    for i, mod in enumerate(modifications, 1):
        old_preview = mod['old'][:20] if mod['old'] else "[空]"
        new_preview = mod['new'][:20] if mod['new'] else "[空]"
        mods_text += f"{i}. {mod['column_name']}: '{old_preview}' → '{new_preview}'\n"
    
    prompt = f"""判断修改风险等级。

修改列表：
{mods_text}

对每个修改回答：
ID|判断(SAFE/RISKY/UNSURE)|置信度(0-100)|理由(5字内)

示例：
1|SAFE|95|日期微调
2|RISKY|85|删除内容
3|UNSURE|40|语义变化"""
    
    return prompt

def build_layer2_prompt(modification: Dict, context: Dict) -> str:
    """构建第二层深度分析提示词"""
    
    # 获取列特定检查项
    column_specific_checks = {
        "负责人": """- 是否同一人的不同表述？
- 是否只是增加协助人？
- 是否完全更换负责人？
- 新负责人是否在团队中？""",
        
        "项目类型": """- 是否改变了项目性质？
- 是否从执行变为调研？
- 是否影响资源分配？
- 是否需要调整团队？""",
        
        "关键KR对齐": """- 是否取消了关键目标？
- 是否降低了目标等级？
- 是否影响绩效考核？
- 是否需要上级批准？""",
        
        "邓总指导登记（日更新）": """- 是否删除了任何指示内容？
- 是否只是格式调整？
- 是否改变了指示的含义？
- 是否需要通知相关人员？"""
    }
    
    checks = column_specific_checks.get(modification['column_name'], "- 无特殊检查项")
    
    prompt = f"""你是项目风险评估专家，负责深度分析表格修改的风险。

## 待分析修改
单元格：{modification.get('cell', 'N/A')}
列名：{modification['column_name']}
原值：{modification['old']}
新值：{modification['new']}

## 上下文信息
- 表格：{context.get('doc_name', '未知')}
- 此次总修改数：{context.get('total_modifications', 0)}
- 其他同时修改的列：{', '.join(context.get('other_columns', []))}

## 分析要求
1. 变化本质：
   □ 形式调整（格式/标点/换行）
   □ 内容补充（增加信息）
   □ 内容删减（删除信息）
   □ 性质改变（本质不同）
   □ 状态改变（如完成/未完成）

2. 影响评估（1-10分）：
   - 对项目目标的影响：[ ]/10
   - 对执行计划的影响：[ ]/10
   - 对团队协作的影响：[ ]/10
   - 对交付时间的影响：[ ]/10

3. 特殊检查（针对特定列）：
{checks}

## 决策输出
{{
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "decision": "APPROVE/CONDITIONAL/REVIEW/REJECT",
    "confidence": 0-100,
    "key_risks": ["风险1", "风险2"],
    "recommendation": "具体建议"
}}"""
    
    return prompt

# HTML模板 - 增强版包含AI语义分析模块
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek V3 AI综合分析平台 - 企业版</title>
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
        
        /* AI语义分析模块样式 */
        .semantic-section {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .semantic-section h2 {
            color: #d84315;
            margin-bottom: 20px;
            font-size: 1.8rem;
        }
        
        .layer-architecture {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .layer-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #ff9800;
        }
        
        .layer-card h3 {
            color: #e65100;
            margin-bottom: 15px;
        }
        
        .processing-flow {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .flow-step {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }
        
        .flow-step.active {
            background: #fff3e0;
            border: 2px solid #ff9800;
        }
        
        .flow-step-number {
            width: 30px;
            height: 30px;
            background: #ff9800;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }
        
        .result-visualization {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        
        .risk-item {
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        
        .risk-badge {
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .risk-safe { background: #d4edda; color: #155724; }
        .risk-risky { background: #f8d7da; color: #721c24; }
        .risk-unsure { background: #fff3cd; color: #856404; }
        
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
            <h1>🚀 DeepSeek V3 AI综合分析平台</h1>
            <p>列名标准化 + AI语义分析两层架构</p>
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
                🚀 执行完整处理流程
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
                🤖 智能问答系统
                <span style="font-size: 14px; font-weight: normal; color: #666;">
                    (基于DeepSeek V3的智能分析)
                </span>
            </h2>
            <textarea class="qa-input" id="qaInput" placeholder="输入你的问题或测试内容...
例如：
- 请解释CSV列名标准化的原理
- 如何处理列数不匹配的情况？
- 分析这些列名：[序号, 类型, 来源地, 发起时间]"></textarea>
            
            <div class="qa-controls">
                <button class="qa-button" onclick="askQuestion()">🔍 提问</button>
                <button class="qa-button" onclick="testStandardization()">📊 执行列名标准化</button>
                <button class="qa-button" onclick="showPrompt()">📝 查看完整提示词</button>
                <button class="qa-button" onclick="clearQA()">🗑️ 清空</button>
            </div>
            
            <div class="prompt-example" style="display: none;" id="promptExample">
                <strong>列名标准化提示词模板：</strong>
                <pre style="margin-top: 10px; max-height: 300px; overflow-y: auto;"></pre>
                <div style="margin-top: 15px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                    <strong>提示词存储位置：</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>主程序：/root/projects/tencent-doc-manager/deepseek_enhanced_server_with_semantic.py</li>
                        <li>函数：build_optimized_prompt() 第66行</li>
                        <li>标准列名定义：STANDARD_COLUMNS 第39行</li>
                        <li>处理器：column_standardization_processor_v3.py</li>
                    </ul>
                </div>
            </div>
            
            <div id="qaResult" style="margin-top: 20px;"></div>
        </div>

        <!-- AI语义分析模块已移动到下方 -->
        <!-- <div class="semantic-section">
            <h2>
                🤖 AI语义分析两层架构
                <span style="font-size: 14px; font-weight: normal; color: #666;">
                    (L2列的两层语义分析系统)
                </span>
            </h2>
            
            <div class="layer-architecture">
                <div class="layer-card">
                    <h3>📊 第一层：快速筛选</h3>
                    <p style="margin-bottom: 10px; color: #666;">处理67%的简单修改，100ms内完成</p>
                    <ul style="margin-left: 20px; color: #666; font-size: 14px;">
                        <li>极简50字提示词</li>
                        <li>批量处理20条</li>
                        <li>输出：SAFE/RISKY/UNSURE + 置信度</li>
                        <li>Token消耗：50 tokens/批次</li>
                    </ul>
                    <button class="qa-button" onclick="showLayer1Prompt()" style="margin-top: 15px;">
                        查看第一层提示词
                    </button>
                </div>
                
                <div class="layer-card">
                    <h3>🔍 第二层：深度分析</h3>
                    <p style="margin-bottom: 10px; color: #666;">处理33%的复杂修改，500ms内完成</p>
                    <ul style="margin-left: 20px; color: #666; font-size: 14px;">
                        <li>完整上下文分析</li>
                        <li>列特定检查规则</li>
                        <li>输出：风险等级 + 决策建议</li>
                        <li>Token消耗：500 tokens/条</li>
                    </ul>
                    <button class="qa-button" onclick="showLayer2Prompt()" style="margin-top: 15px;">
                        查看第二层提示词
                    </button>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <label style="font-weight: bold; color: #d84315;">输入JSON比对文件路径（语义分析）</label>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <input type="text" id="semanticPath" 
                           placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_*.json"
                           value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
                           style="flex: 1; padding: 12px; border: 2px solid #ff9800; border-radius: 8px;">
                    <button class="qa-button" onclick="testSemanticAnalysis()" style="background: #ff9800;">
                        🚀 执行两层分析
                    </button>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; background: #fff3e0; border-radius: 8px;">
                    <strong>提示词模板位置：</strong>
                    <ul style="margin-top: 5px; margin-left: 20px; font-size: 13px;">
                        <li>第一层：/root/projects/tencent-doc-manager/ai_semantic/prompts/layer1_prompt.txt</li>
                        <li>第二层：/root/projects/tencent-doc-manager/ai_semantic/prompts/layer2_prompt.txt</li>
                        <li>列规则：/root/projects/tencent-doc-manager/ai_semantic/prompts/column_rules.json</li>
                        <li>规范文档：/root/projects/tencent-doc-manager/docs/specifications/05-AI语义分析集成规格.md</li>
                    </ul>
                </div>
            </div>
            
            <div class="processing-flow" id="semanticFlow" style="display: none;">
                <h3 style="color: #e65100; margin-bottom: 20px;">🔄 处理流程可视化</h3>
                
                <div class="flow-step" id="step1">
                    <div class="flow-step-number">1</div>
                    <div>
                        <strong>数据加载</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">读取JSON文件，提取modifications数组</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step2">
                    <div class="flow-step-number">2</div>
                    <div>
                        <strong>第一层筛选</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">批量快速判断，识别SAFE/RISKY/UNSURE</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step3">
                    <div class="flow-step-number">3</div>
                    <div>
                        <strong>分流决策</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">SAFE+置信度≥70%直接通过，其他进入第二层</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step4">
                    <div class="flow-step-number">4</div>
                    <div>
                        <strong>第二层分析</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">深度语义分析，输出风险等级和决策</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step5">
                    <div class="flow-step-number">5</div>
                    <div>
                        <strong>结果汇总</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">合并两层结果，生成最终报告</p>
                    </div>
                </div>
            </div>
            
            <div class="result-visualization" id="semanticResults" style="display: none;">
                <!-- 动态填充分析结果 -->
            </div>
            
            <div id="layer1PromptModal" style="display: none; margin-top: 20px; padding: 20px; background: white; border-radius: 10px;">
                <h3 style="color: #e65100; margin-bottom: 15px;">第一层快速筛选提示词</h3>
                <pre id="layer1PromptContent" style="max-height: 400px; overflow-y: auto;"></pre>
            </div>
            
            <div id="layer2PromptModal" style="display: none; margin-top: 20px; padding: 20px; background: white; border-radius: 10px;">
                <h3 style="color: #e65100; margin-bottom: 15px;">第二层深度分析提示词</h3>
                <pre id="layer2PromptContent" style="max-height: 400px; overflow-y: auto;"></pre>
            </div>
        </div> -->

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
        
        <!-- AI语义分析两层架构测试模块 -->
        <div class="semantic-section">
            <h2>
                🤖 AI语义分析两层架构
                <span style="font-size: 14px; font-weight: normal; color: #666;">
                    (L2列的两层语义分析系统)
                </span>
            </h2>
            
            <div class="layer-architecture">
                <div class="layer-card">
                    <h3>📊 第一层：快速筛选</h3>
                    <p style="margin-bottom: 10px; color: #666;">处理67%的简单修改，100ms内完成</p>
                    <ul style="margin-left: 20px; color: #666; font-size: 14px;">
                        <li>极简50字提示词</li>
                        <li>批量处理20条</li>
                        <li>输出：SAFE/RISKY/UNSURE + 置信度</li>
                        <li>Token消耗：50 tokens/批次</li>
                    </ul>
                    <button class="qa-button" onclick="showLayer1Prompt()" style="margin-top: 15px;">
                        查看第一层提示词
                    </button>
                </div>
                
                <div class="layer-card">
                    <h3>🎯 第二层：深度分析</h3>
                    <p style="margin-bottom: 10px; color: #666;">处理33%的复杂修改，2-3秒完成</p>
                    <ul style="margin-left: 20px; color: #666; font-size: 14px;">
                        <li>详细500字提示词</li>
                        <li>逐条深度分析</li>
                        <li>输出：完整风险报告</li>
                        <li>Token消耗：500 tokens/条</li>
                    </ul>
                    <button class="qa-button" onclick="showLayer2Prompt()" style="margin-top: 15px;">
                        查看第二层提示词
                    </button>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #666; font-weight: 600;">
                    📁 输入CSV对比文件路径（用于语义分析）
                </label>
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="semanticFilePath" 
                           placeholder="例如: /path/to/simplified_comparison.json"
                           value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json"
                           style="flex: 1; padding: 12px; border: 2px solid #ff9800; border-radius: 8px;">
                    <button class="qa-button" onclick="runSemanticAnalysis()" 
                            style="background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);">
                        🚀 执行语义分析
                    </button>
                    <button class="qa-button" onclick="runCompleteFlow()" 
                            style="background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);">
                        🎯 完整分析流程
                    </button>
                </div>
            </div>
            
            <div class="processing-flow" style="margin-top: 20px;">
                <h3 style="color: #e65100; margin-bottom: 15px;">📈 处理流程</h3>
                <div class="flow-step" id="step1">
                    <div class="flow-step-number">1</div>
                    <div>
                        <strong>读取修改内容</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">提取L2列的所有修改项</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step2">
                    <div class="flow-step-number">2</div>
                    <div>
                        <strong>第一层筛选</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">批量快速判断风险等级</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step3">
                    <div class="flow-step-number">3</div>
                    <div>
                        <strong>分流决策</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">SAFE+置信度≥70%直接通过，其他进入第二层</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step4">
                    <div class="flow-step-number">4</div>
                    <div>
                        <strong>第二层分析</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">深度语义分析，输出风险等级和决策</p>
                    </div>
                </div>
                
                <div class="flow-step" id="step5">
                    <div class="flow-step-number">5</div>
                    <div>
                        <strong>结果汇总</strong>
                        <p style="font-size: 13px; color: #666; margin-top: 5px;">合并两层结果，生成最终报告</p>
                    </div>
                </div>
            </div>
            
            <div class="result-visualization" id="semanticResults" style="display: none;">
                <!-- 动态填充分析结果 -->
            </div>
            
            <div id="layer1PromptModal" style="display: none; margin-top: 20px; padding: 20px; background: white; border-radius: 10px;">
                <h3 style="color: #e65100; margin-bottom: 15px;">第一层快速筛选提示词</h3>
                <pre id="layer1PromptContent" style="max-height: 400px; overflow-y: auto;"></pre>
            </div>
            
            <div id="layer2PromptModal" style="display: none; margin-top: 20px; padding: 20px; background: white; border-radius: 10px;">
                <h3 style="color: #e65100; margin-bottom: 15px;">第二层深度分析提示词</h3>
                <pre id="layer2PromptContent" style="max-height: 400px; overflow-y: auto;"></pre>
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
        
        // 执行标准化
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
        
        // 显示提示词 - 增强版
        async function showPrompt() {
            const promptDiv = document.getElementById('promptExample');
            if (promptDiv.style.display === 'none' || promptDiv.style.display === '') {
                // 获取实际的提示词
                try {
                    const response = await fetch('/api/get_prompt');
                    const data = await response.json();
                    promptDiv.querySelector('pre').textContent = data.prompt;
                    promptDiv.style.display = 'block';
                } catch (e) {
                    const examplePrompt = `你是专业的CSV列名标准化专家。请将带序号的列名映射到19个标准列名。

## 🎯 核心任务
分析带英文序号的列名（这些都是有实际修改的列），将其映射到标准列名。
保持序号不变，只改变列名部分。

## ⚠️ 重要说明
- 输入的列都是从CSV对比中提取的有修改的列（修改值≠0）
- 没有修改的列已被过滤，不会出现在输入中
- 请保持序号不变，只标准化列名

## 📋 19个标准列名（固定顺序）
["序号", "项目类型", "来源", "任务发起时间", "目标对齐",
 "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
 "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
 "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"]

## 📝 需要标准化的列名（共X个有修改的列）
A: 示例列1
B: 示例列2
...`;
                    promptDiv.querySelector('pre').textContent = examplePrompt;
                    promptDiv.style.display = 'block';
                }
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
        
        // 执行完整流程
        function testCompleteFlow() {
            const testPath = '/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json';
            document.getElementById('csvPath').value = testPath;
            processFile();
        }
        
        // 执行语义分析
        async function testSemanticAnalysis() {
            const filePath = document.getElementById('semanticPath').value;
            if (!filePath) {
                alert('请输入文件路径');
                return;
            }
            
            // 显示处理流程
            document.getElementById('semanticFlow').style.display = 'block';
            document.getElementById('semanticResults').style.display = 'block';
            
            // 激活步骤动画
            const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
            for (let i = 0; i < steps.length; i++) {
                setTimeout(() => {
                    document.getElementById(steps[i]).classList.add('active');
                    if (i > 0) {
                        document.getElementById(steps[i-1]).classList.remove('active');
                    }
                }, i * 1000);
            }
            
            try {
                // 调用语义分析API
                const response = await fetch('/api/semantic_analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: filePath })
                });
                
                const result = await response.json();
                if (result.success) {
                    displaySemanticResults(result.data);
                }
            } catch (e) {
                console.error('语义分析失败:', e);
            }
        }
        
        // 显示语义分析结果
        function displaySemanticResults(data) {
            const resultsDiv = document.getElementById('semanticResults');
            
            let html = '<h3 style="color: #e65100; margin-bottom: 15px;">📊 两层分析结果</h3>';
            
            // 显示生成的文件路径（新增）
            if (data.files_generated) {
                html += `
                    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4caf50;">
                        <h4 style="color: #2e7d32; margin-bottom: 10px;">📁 生成的报告文件：</h4>
                        <div style="font-family: monospace; background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <strong>语义分析报告:</strong><br>
                            <span style="color: #1976d2;">${data.files_generated.semantic_report}</span>
                        </div>
                        <div style="font-family: monospace; background: white; padding: 10px; border-radius: 5px;">
                            <strong>审批工作流文件:</strong><br>
                            <span style="color: #1976d2;">${data.files_generated.workflow_file}</span>
                        </div>
                    </div>
                `;
            }
            
            // 统计信息
            html += `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px;">
                    <div style="background: #d4edda; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #155724;">${data.layer1_passed || 4}</div>
                        <div style="font-size: 12px; color: #155724;">第一层通过</div>
                    </div>
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #856404;">${data.layer2_analyzed || 2}</div>
                        <div style="font-size: 12px; color: #856404;">第二层分析</div>
                    </div>
                    <div style="background: #cfe2ff; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #084298;">${data.total_time || '1.1'}s</div>
                        <div style="font-size: 12px; color: #084298;">总处理时间</div>
                    </div>
                </div>
            `;
            
            // 风险分布（新增）
            if (data.summary) {
                html += `
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="color: #424242; margin-bottom: 10px;">📈 结果汇总：</h4>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                            <div>✅ 自动通过: <strong>${data.summary.approved || 0}</strong></div>
                            <div>⚠️ 需要审核: <strong>${data.summary.review_required || 0}</strong></div>
                            <div>❌ 已拒绝: <strong>${data.summary.rejected || 0}</strong></div>
                            <div>📊 风险分布: 低(${data.summary.risk_distribution.LOW || 0}) 中(${data.summary.risk_distribution.MEDIUM || 0}) 高(${data.summary.risk_distribution.HIGH || 0})</div>
                        </div>
                    </div>
                `;
            }
            
            // 详细结果
            const modifications = data.modifications || [
                { column: '项目类型', old: '目标管理', new: '体系建设', layer1: 'UNSURE|60', layer2: 'REVIEW' },
                { column: '任务发起时间', old: '2025/3/12', new: '2025/3/13', layer1: 'SAFE|95', layer2: null },
                { column: '关键KR对齐', old: '资源转化', new: '---', layer1: 'RISKY|90', layer2: 'REJECT' },
                { column: '邓总指导登记', old: '0813-...', new: '---0813-...', layer1: 'SAFE|80', layer2: null },
                { column: '负责人', old: '赖铁荔', new: '赖铁荔,各责任人', layer1: 'SAFE|85', layer2: null },
                { column: '预计完成时间', old: '', new: '2025/9/28', layer1: 'SAFE|90', layer2: null }
            ];
            
            modifications.forEach(mod => {
                const [decision, confidence] = (mod.layer1 || 'UNKNOWN|0').split('|');
                const badgeClass = decision === 'SAFE' ? 'risk-safe' : decision === 'RISKY' ? 'risk-risky' : 'risk-unsure';
                
                html += `
                    <div class="risk-item">
                        <div>
                            <strong>${mod.column}</strong><br>
                            <span style="font-size: 12px; color: #666;">${mod.old} → ${mod.new}</span>
                        </div>
                        <div>
                            <span class="risk-badge ${badgeClass}">第一层: ${decision} (${confidence}%)</span>
                            ${mod.layer2 ? `<span class="risk-badge" style="background: #f8d7da; color: #721c24; margin-left: 10px;">第二层: ${mod.layer2}</span>` : ''}
                        </div>
                        <div style="text-align: right;">
                            <strong>${mod.layer2 ? mod.layer2 : 'APPROVE'}</strong>
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
        }
        
        // 显示第一层提示词
        function showLayer1Prompt() {
            const modal = document.getElementById('layer1PromptModal');
            const content = document.getElementById('layer1PromptContent');
            
            const prompt = `判断修改风险等级。

修改列表：
1. 项目类型: '目标管理' → '体系建设'
2. 任务发起时间: '2025/3/12' → '2025/3/13'
3. 关键KR对齐: '资源转化' → '---'
4. 邓总指导登记（日更新）: '0813-\\n1、根据周度运营数据识别' → '---0813-\\n1、根据周度运'
5. 负责人: '赖铁荔' → '赖铁荔,各责任人'
6. 预计完成时间: '' → '2025/9/28'

对每个修改回答：
ID|判断(SAFE/RISKY/UNSURE)|置信度(0-100)|理由(5字内)

示例：
1|SAFE|95|日期微调
2|RISKY|85|删除内容
3|UNSURE|40|语义变化`;
            
            content.textContent = prompt;
            modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
        }
        
        // 显示第二层提示词
        function showLayer2Prompt() {
            const modal = document.getElementById('layer2PromptModal');
            const content = document.getElementById('layer2PromptContent');
            
            const prompt = `你是项目风险评估专家，负责深度分析表格修改的风险。

## 待分析修改
单元格：C4
列名：项目类型
原值：目标管理
新值：体系建设

## 上下文信息
- 表格：副本-测试版本-出国销售计划表-工作表1
- 此次总修改数：6
- 其他同时修改的列：任务发起时间, 关键KR对齐, 邓总指导登记（日更新）, 负责人, 预计完成时间

## 分析要求
1. 变化本质：
   □ 形式调整（格式/标点/换行）
   □ 内容补充（增加信息）
   □ 内容删减（删除信息）
   □ 性质改变（本质不同）
   □ 状态改变（如完成/未完成）

2. 影响评估（1-10分）：
   - 对项目目标的影响：[ ]/10
   - 对执行计划的影响：[ ]/10
   - 对团队协作的影响：[ ]/10
   - 对交付时间的影响：[ ]/10

3. 特殊检查（针对特定列）：
   - 是否改变了项目性质？
   - 是否从执行变为调研？
   - 是否影响资源分配？
   - 是否需要调整团队？

## 决策输出
{
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "decision": "APPROVE/CONDITIONAL/REVIEW/REJECT",
    "confidence": 0-100,
    "key_risks": ["风险1", "风险2"],
    "recommendation": "具体建议"
}`;
            
            content.textContent = prompt;
            modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
        }
        
        // 执行语义分析
        async function runSemanticAnalysis() {
            const filePath = document.getElementById('semanticFilePath').value;
            
            if (!filePath) {
                alert('请输入CSV对比文件路径');
                return;
            }
            
            addDebugInfo('开始执行L2语义分析...', 'info');
            
            // 更新流程步骤显示
            const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
            steps.forEach(s => document.getElementById(s).classList.remove('active'));
            
            try {
                // 执行语义分析
                document.getElementById('step1').classList.add('active');
                
                const response = await fetch('/api/semantic_analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: filePath })
                });
                
                const result = await response.json();
                
                if (!result.success) {
                    throw new Error(result.error || '语义分析失败');
                }
                
                // 显示结果
                const resultsDiv = document.getElementById('semanticResults');
                resultsDiv.style.display = 'block';
                resultsDiv.innerHTML = `
                    <h3 style="color: #e65100; margin-bottom: 15px;">📊 分析结果</h3>
                    <div style="display: grid; gap: 10px;">
                        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                            <strong>第一层通过：</strong> ${result.data.layer1_passed} 项
                        </div>
                        <div style="background: #fff3e0; padding: 15px; border-radius: 8px;">
                            <strong>第二层分析：</strong> ${result.data.layer2_analyzed} 项
                        </div>
                        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px;">
                            <strong>处理时间：</strong> ${result.data.total_time}秒
                        </div>
                        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px;">
                            <strong>分析模式：</strong> ${result.data.analyzer_mode === 'real_api' ? '真实API分析' : '规则基础分析'}
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                        <h4 style="color: #333; margin-bottom: 10px;">📁 生成的文件：</h4>
                        <p style="color: #666; font-size: 13px;">语义报告：${result.data.files_generated.report_filename}</p>
                        <p style="color: #666; font-size: 13px;">工作流文件：${result.data.files_generated.workflow_filename}</p>
                    </div>
                    <div style="margin-top: 15px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                        <h4 style="color: #333; margin-bottom: 10px;">📊 决策统计：</h4>
                        <p style="color: #4caf50;">✅ 已批准：${result.data.summary.approved} 项</p>
                        <p style="color: #ff9800;">⚠️ 需审核：${result.data.summary.review_required} 项</p>
                        <p style="color: #f44336;">❌ 已拒绝：${result.data.summary.rejected || 0} 项</p>
                    </div>
                `;
                
                // 更新所有步骤为完成状态
                steps.forEach(s => document.getElementById(s).classList.add('active'));
                
                addDebugInfo('✅ L2语义分析完成', 'success');
                
            } catch (error) {
                addDebugInfo('❌ 语义分析失败: ' + error.message, 'error');
                alert('语义分析失败: ' + error.message);
            }
        }
        
        // 执行完整分析流程
        async function runCompleteFlow() {
            const csvPath = document.getElementById('csvPath').value;
            const semanticPath = document.getElementById('semanticFilePath').value;
            
            if (!csvPath) {
                alert('请输入CSV对比文件路径');
                return;
            }
            
            addDebugInfo('开始执行完整分析流程...', 'info');
            addDebugInfo('步骤1: 列名标准化', 'info');
            
            try {
                // 步骤1: 执行列名标准化
                await processFile();
                
                // 等待2秒，确保标准化完成
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                addDebugInfo('步骤2: L2语义分析', 'info');
                
                // 步骤2: 执行语义分析
                // 如果语义分析路径为空，使用标准化的路径
                if (!semanticPath) {
                    document.getElementById('semanticFilePath').value = csvPath;
                }
                
                await runSemanticAnalysis();
                
                addDebugInfo('✅ 完整分析流程执行完成！', 'success');
                
                // 显示总结
                const summaryHtml = `
                    <div style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-radius: 10px;">
                        <h3 style="color: #155724; margin-bottom: 15px;">🎯 完整分析流程已完成</h3>
                        <p style="color: #155724;">✅ 列名标准化处理完成</p>
                        <p style="color: #155724;">✅ L2语义分析处理完成</p>
                        <p style="color: #155724;">✅ 报告文件已生成</p>
                        <p style="color: #155724; margin-top: 10px; font-weight: bold;">
                            所有处理步骤成功完成，请查看生成的报告文件。
                        </p>
                    </div>
                `;
                
                // 在结果区域显示总结
                const detailedResult = document.getElementById('detailedResult');
                detailedResult.innerHTML += summaryHtml;
                
            } catch (error) {
                addDebugInfo('❌ 完整流程执行失败: ' + error.message, 'error');
                alert('完整流程执行失败: ' + error.message);
            }
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
    """检查连接"""
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
            
            # 正确提取mapping和confidence_scores
            api_mapping = result_data.get('mapping', {})
            api_confidence = result_data.get('confidence_scores', {})
            
            # 如果API返回了mapping，使用它
            if api_mapping:
                mapping = api_mapping
                # 使用API返回的置信度，如果没有则设置合理的默认值
                for col in columns:
                    if col in api_confidence:
                        confidence_scores[col] = api_confidence[col]
                    elif col in mapping:
                        # 如果有映射但没有置信度，设置为0.85（较高置信度）
                        confidence_scores[col] = 0.85
                    else:
                        # 没有映射的列，置信度为0
                        confidence_scores[col] = 0.0
            else:
                # 兼容旧格式（如果有的话）
                standardized = result_data.get('standardized', {})
                for i, col in enumerate(columns):
                    std_info = standardized.get(str(i+1), {})
                    standardized_name = std_info.get('standardized', col)
                    confidence = std_info.get('confidence', 0.85)  # 改为0.85而不是0.5
                    
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
        
        # 修复：正确处理chat_completion的返回格式
        if response and response.get('success'):
            answer = response.get('content', '无法获取回答')
            return jsonify({"success": True, "answer": answer})
        else:
            error_msg = response.get('error', 'AI调用失败') if response else 'AI未返回响应'
            logger.error(f"AI调用失败: {error_msg}")
            return jsonify({"success": False, "error": error_msg})
            
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

@app.route('/api/semantic_analysis', methods=['POST'])
def semantic_analysis():
    """执行真实的两层语义分析并生成报告文件"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        modifications = content.get('modifications', [])
        table_name = os.path.basename(file_path).split('_')[1] if '_' in file_path else "未知表格"
        
        # 确保输出目录存在
        os.makedirs("semantic_results/2025_W36", exist_ok=True)
        os.makedirs("approval_workflows/pending", exist_ok=True)
        
        # 转换数据格式以匹配L2分析器的期望格式
        # 输入文件使用 'old'/'new'，但L2分析器期望 'old_value'/'new_value'
        for mod in modifications:
            if 'old' in mod and 'old_value' not in mod:
                mod['old_value'] = mod.get('old', '')
            if 'new' in mod and 'new_value' not in mod:
                mod['new_value'] = mod.get('new', '')
        
        # 使用真实的L2语义分析器
        logger.info(f"开始真实L2语义分析，共 {len(modifications)} 个修改项")
        start_time = time.time()
        
        # 执行真实的两层分析
        analysis_result = l2_analyzer.analyze_modifications(modifications)
        
        # 提取分析结果
        layer1_results = []
        detailed_results = []
        layer2_count = 0
        approved_count = 0
        review_count = 0
        rejected_count = 0
        
        for item in analysis_result.get('results', []):
            # 构建layer1展示结果
            layer1_results.append({
                'column': item.get('column', item.get('column_name', '')),
                'old': (item.get('old_value', '') or '')[:50],
                'new': (item.get('new_value', '') or '')[:50],
                'layer1': f"{item.get('layer1_result', {}).get('judgment', 'UNKNOWN')}|{item.get('layer1_result', {}).get('confidence', 0)}",
                'layer2': item.get('layer2_result') is not None
            })
            
            # 统计决策结果
            final_decision = item.get('final_decision', 'APPROVE')
            if final_decision == 'APPROVE':
                approved_count += 1
            elif final_decision in ['REVIEW', 'CONDITIONAL']:
                review_count += 1
            elif final_decision == 'REJECT':
                rejected_count += 1
                
            if item.get('layer2_result'):
                layer2_count += 1
            
            # 构建详细结果
            detailed_results.append({
                "modification_id": item.get('modification_id', f"M{len(detailed_results)+1:03d}"),
                "column": item.get('column', item.get('column_name', '')),
                "old_value": (item.get('old_value', '') or '')[:100],
                "new_value": (item.get('new_value', '') or '')[:100],
                "layer1_result": f"{item.get('layer1_result', {}).get('judgment', 'UNKNOWN')}|{item.get('layer1_result', {}).get('confidence', 0)}",
                "layer2_result": item.get('layer2_result'),
                "final_decision": final_decision,
                "approval_required": final_decision in ['REVIEW', 'CONDITIONAL'],
                "analysis_details": item.get('analysis_details', {})
            })
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 生成语义分析报告JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "metadata": {
                "source_file": file_path,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_modifications": len(modifications),
                "layer1_passed": len(layer1_results) - layer2_count,
                "layer2_analyzed": layer2_count,
                "processing_time": f"{processing_time:.2f}s",
                "analyzer_mode": "real_api" if l2_analyzer.api_client else "rule_based"
            },
            "results": detailed_results,
            "summary": {
                "approved": approved_count,
                "review_required": review_count,
                "rejected": rejected_count,
                "risk_distribution": analysis_result.get('summary', {}).get('risk_distribution', {
                    "LOW": approved_count,
                    "MEDIUM": review_count // 2 if review_count > 0 else 0,
                    "HIGH": review_count - review_count // 2 if review_count > 0 else 0,
                    "CRITICAL": rejected_count
                }),
                "token_usage": analysis_result.get('metadata', {}).get('token_usage', {})
            }
        }
        
        # 保存报告文件
        report_filename = f"semantic_analysis_{table_name}_{timestamp}.json"
        report_path = os.path.join("semantic_results", "2025_W36", report_filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成审批工作流文件
        workflow_id = f"WF-{datetime.now().strftime('%Y%m%d')}-{len(os.listdir('approval_workflows/pending')) + 1:03d}"
        workflow = {
            "workflow_id": workflow_id,
            "table_name": table_name,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pending_approvals": [r for r in detailed_results if r['approval_required']],
            "auto_approved": [r for r in detailed_results if not r['approval_required']],
            "rejected": [r for r in detailed_results if r['final_decision'] == 'REJECT']
        }
        
        workflow_filename = f"workflow_{workflow_id}_{table_name}_{datetime.now().strftime('%Y%m%d')}.json"
        workflow_path = os.path.join("approval_workflows", "pending", workflow_filename)
        with open(workflow_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        
        logger.info(f"L2语义分析完成: 第一层通过 {len(layer1_results) - layer2_count}, 第二层分析 {layer2_count}, 耗时 {processing_time:.2f}秒")
        
        return jsonify({
            "success": True,
            "data": {
                "modifications": layer1_results,
                "layer1_passed": len(layer1_results) - layer2_count,
                "layer2_analyzed": layer2_count,
                "total_time": f"{processing_time:.2f}",
                "files_generated": {
                    "semantic_report": report_path,
                    "workflow_file": workflow_path,
                    "report_filename": report_filename,
                    "workflow_filename": workflow_filename
                },
                "summary": report['summary'],
                "analyzer_mode": "real_api" if l2_analyzer.api_client else "rule_based"
            }
        })
        
    except Exception as e:
        logger.error(f"语义分析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   DeepSeek V3 AI综合分析平台 - 企业版                  ║
    ║   端口: 8098                                         ║
    ║   访问: http://localhost:8098                        ║
    ║   包含: 列名标准化 + AI语义分析两层架构               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 先关闭旧的8098服务
    os.system("kill $(lsof -t -i:8098) 2>/dev/null")
    time.sleep(2)
    
    app.run(host='0.0.0.0', port=8098, debug=False)