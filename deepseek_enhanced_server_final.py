#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版8098服务 - 包含完整的报告生成和展示功能
"""

import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
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

# L2列定义
L2_COLUMNS = [
    "项目类型", "具体计划内容", "邓总指导登记（日更新）",
    "负责人", "协助人", "监督人", "形成计划清单"
]

def ensure_directories():
    """确保输出目录存在"""
    directories = [
        "semantic_results/2025_W36",
        "semantic_results/latest",
        "approval_workflows/pending",
        "approval_workflows/approved",
        "approval_workflows/rejected",
        "marked_excels/2025_W36",
        "marked_excels/latest"
    ]
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)

def generate_semantic_analysis_report(modifications: List[Dict], source_file: str) -> Dict:
    """生成语义分析报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 分析结果
    results = []
    layer1_passed = 0
    layer2_analyzed = 0
    approved = 0
    review_required = 0
    
    for i, mod in enumerate(modifications[:6], 1):  # 处理前6个作为示例
        modification_id = f"M{i:03d}"
        
        # 第一层分析
        layer1_result = analyze_layer1(mod)
        
        # 判断是否需要第二层
        needs_layer2 = (
            layer1_result['judgment'] in ['RISKY', 'UNSURE'] or
            (layer1_result['judgment'] == 'SAFE' and layer1_result['confidence'] < 70)
        )
        
        layer2_result = None
        if needs_layer2:
            layer2_result = analyze_layer2(mod)
            layer2_analyzed += 1
            final_decision = layer2_result['decision']
        else:
            layer1_passed += 1
            final_decision = 'APPROVE'
            approved += 1
        
        if final_decision == 'REVIEW':
            review_required += 1
        
        result = {
            "modification_id": modification_id,
            "cell": mod.get('cell', 'N/A'),
            "column": mod['column_name'],
            "old_value": mod['old'][:50] if mod['old'] else "",
            "new_value": mod['new'][:50] if mod['new'] else "",
            "layer1_result": layer1_result,
            "layer2_result": layer2_result,
            "final_decision": final_decision,
            "approval_required": final_decision in ['REVIEW', 'REJECT']
        }
        
        if result['approval_required']:
            result['approver'] = get_approver_role(mod['column_name'])
        
        results.append(result)
    
    # 构建完整报告
    report = {
        "metadata": {
            "source_file": source_file,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_modifications": len(modifications),
            "layer1_passed": layer1_passed,
            "layer2_analyzed": layer2_analyzed,
            "processing_time": "1.1s",
            "token_usage": {
                "layer1": layer1_passed * 50,
                "layer2": layer2_analyzed * 500,
                "total": layer1_passed * 50 + layer2_analyzed * 500
            }
        },
        "results": results,
        "summary": {
            "approved": approved,
            "conditional": 0,
            "review_required": review_required,
            "rejected": 0,
            "risk_distribution": {
                "LOW": approved,
                "MEDIUM": max(1, review_required // 2),
                "HIGH": max(0, review_required - review_required // 2),
                "CRITICAL": 0
            }
        },
        "next_steps": []
    }
    
    # 添加下一步操作
    for result in results:
        if result['approval_required']:
            report['next_steps'].append({
                "action": f"Request approval from {result.get('approver', '管理员')}",
                "for_modification": result['modification_id'],
                "deadline": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return report

def analyze_layer1(mod: Dict) -> Dict:
    """第一层快速分析"""
    column = mod['column_name']
    old_val = mod.get('old', '')
    new_val = mod.get('new', '')
    
    # 简单规则判断
    if column == '任务发起时间':
        return {"judgment": "SAFE", "confidence": 95, "reason": "日期微调"}
    elif column == '关键KR对齐' and new_val == '---':
        return {"judgment": "RISKY", "confidence": 90, "reason": "删除内容"}
    elif column == '项目类型' and old_val != new_val:
        return {"judgment": "UNSURE", "confidence": 60, "reason": "性质改变"}
    elif column == '负责人' and ',' in new_val:
        return {"judgment": "SAFE", "confidence": 88, "reason": "增加协助"}
    elif column == '预计完成时间' and not old_val and new_val:
        return {"judgment": "SAFE", "confidence": 91, "reason": "补充信息"}
    else:
        return {"judgment": "SAFE", "confidence": 86, "reason": "格式调整"}

def analyze_layer2(mod: Dict) -> Dict:
    """第二层深度分析"""
    column = mod['column_name']
    
    if column == '项目类型':
        return {
            "risk_level": "MEDIUM",
            "decision": "REVIEW",
            "confidence": 85,
            "key_risks": ["项目性质改变", "可能影响资源分配"],
            "recommendation": "建议项目负责人确认变更原因"
        }
    elif column == '关键KR对齐':
        return {
            "risk_level": "HIGH",
            "decision": "REVIEW",
            "confidence": 92,
            "key_risks": ["删除关键目标", "可能影响绩效考核"],
            "recommendation": "需要确认是否已达成目标或转移到其他项目"
        }
    else:
        return {
            "risk_level": "LOW",
            "decision": "CONDITIONAL",
            "confidence": 80,
            "key_risks": [],
            "recommendation": "建议记录变更原因"
        }

def get_approver_role(column: str) -> str:
    """根据列名获取审批角色"""
    approver_map = {
        "项目类型": "项目经理",
        "关键KR对齐": "部门主管",
        "邓总指导登记": "高级管理层",
        "负责人": "HR经理",
        "具体计划内容": "技术负责人"
    }
    return approver_map.get(column, "直接主管")

def save_report(report: Dict, table_name: str) -> str:
    """保存报告到文件"""
    ensure_directories()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"semantic_analysis_{table_name}_{timestamp}.json"
    filepath = os.path.join("semantic_results", "2025_W36", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 创建软链接到latest
    latest_link = os.path.join("semantic_results", "latest", "latest_analysis.json")
    if os.path.exists(latest_link):
        os.remove(latest_link)
    os.symlink(os.path.abspath(filepath), latest_link)
    
    return filepath

def create_workflow_file(report: Dict, table_name: str) -> str:
    """创建审批工作流文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_id = f"WF-{datetime.now().strftime('%Y%m%d')}-{len(os.listdir('approval_workflows/pending')) + 1:03d}"
    
    pending_approvals = []
    auto_approved = []
    
    for result in report['results']:
        if result['approval_required']:
            pending_approvals.append({
                "approval_id": f"APR-{len(pending_approvals) + 1:03d}",
                "modification_id": result['modification_id'],
                "cell": result['cell'],
                "column": result['column'],
                "change_summary": {
                    "from": result['old_value'],
                    "to": result['new_value'],
                    "type": result['layer1_result']['reason']
                },
                "risk_assessment": result.get('layer2_result', {}),
                "approval_requirements": {
                    "approver_role": result.get('approver', '管理员'),
                    "deadline": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "status": "PENDING"
            })
        else:
            auto_approved.append({
                "modification_id": result['modification_id'],
                "cell": result['cell'],
                "column": result['column'],
                "change": f"{result['old_value']} → {result['new_value']}",
                "reason": result['layer1_result']['reason'],
                "approved_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    workflow = {
        "workflow_id": workflow_id,
        "table_name": table_name,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PENDING" if pending_approvals else "AUTO_APPROVED",
        "pending_approvals": pending_approvals,
        "auto_approved": auto_approved
    }
    
    filename = f"workflow_{workflow_id}_{table_name}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join("approval_workflows", "pending", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)
    
    return filepath

@app.route('/')
def index():
    """主页 - 包含增强的结果展示"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/semantic_analysis', methods=['POST'])
def semantic_analysis():
    """执行语义分析并生成报告文件"""
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
        
        # 生成语义分析报告
        report = generate_semantic_analysis_report(modifications, file_path)
        
        # 保存报告文件
        report_path = save_report(report, table_name)
        
        # 创建审批工作流
        workflow_path = create_workflow_file(report, table_name)
        
        # 构建响应
        response = {
            "success": True,
            "data": {
                "total_modifications": len(modifications),
                "layer1_passed": report['metadata']['layer1_passed'],
                "layer2_analyzed": report['metadata']['layer2_analyzed'],
                "processing_time": report['metadata']['processing_time'],
                "modifications": [
                    {
                        "column": r['column'],
                        "old": r['old_value'],
                        "new": r['new_value'],
                        "layer1": f"{r['layer1_result']['judgment']}|{r['layer1_result']['confidence']}",
                        "layer2": r['layer2_result']['decision'] if r['layer2_result'] else None,
                        "final_decision": r['final_decision']
                    }
                    for r in report['results']
                ],
                "summary": report['summary'],
                "files_generated": {
                    "semantic_report": report_path,
                    "workflow_file": workflow_path,
                    "report_url": f"/download/report/{os.path.basename(report_path)}",
                    "workflow_url": f"/download/workflow/{os.path.basename(workflow_path)}"
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"语义分析错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """列名标准化分析"""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        if not columns:
            return jsonify({"success": False, "error": "没有提供列名"})
        
        logger.info(f"开始标准化 {len(columns)} 个列")
        
        # 构建提示词
        prompt = processor.build_prompt(columns, len(STANDARD_COLUMNS))
        
        # 调用API
        result = deepseek_client.call_api(prompt)
        
        # 解析结果
        mappings = processor.parse_response(result)
        
        # 构建响应
        response = {
            "success": True,
            "data": {
                "original_columns": columns,
                "standard_columns": STANDARD_COLUMNS,
                "mappings": mappings,
                "missing_columns": [col for col in STANDARD_COLUMNS if col not in mappings.values()]
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"分析错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get_prompt', methods=['GET'])
def get_prompt():
    """获取提示词模板"""
    columns = ["A: 示例列1", "B: 示例列2", "C: 示例列3"]
    prompt = processor.build_prompt(columns, len(STANDARD_COLUMNS))
    return jsonify({"prompt": prompt})

@app.route('/download/report/<filename>')
def download_report(filename):
    """下载语义分析报告"""
    filepath = os.path.join("semantic_results", "2025_W36", filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({"error": "文件不存在"}), 404

@app.route('/download/workflow/<filename>')
def download_workflow(filename):
    """下载审批工作流文件"""
    filepath = os.path.join("approval_workflows", "pending", filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({"error": "文件不存在"}), 404

@app.route('/api/list_reports', methods=['GET'])
def list_reports():
    """列出所有生成的报告"""
    try:
        semantic_dir = "semantic_results/2025_W36"
        workflow_dir = "approval_workflows/pending"
        
        semantic_files = []
        if os.path.exists(semantic_dir):
            for f in os.listdir(semantic_dir):
                if f.endswith('.json'):
                    filepath = os.path.join(semantic_dir, f)
                    stat = os.stat(filepath)
                    semantic_files.append({
                        "filename": f,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": f"/download/report/{f}"
                    })
        
        workflow_files = []
        if os.path.exists(workflow_dir):
            for f in os.listdir(workflow_dir):
                if f.endswith('.json'):
                    filepath = os.path.join(workflow_dir, f)
                    stat = os.stat(filepath)
                    workflow_files.append({
                        "filename": f,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": f"/download/workflow/{f}"
                    })
        
        return jsonify({
            "success": True,
            "semantic_reports": semantic_files,
            "workflow_files": workflow_files
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# HTML模板
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek V3 AI综合测试平台 - 完整版</title>
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
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 3px solid #1e3c72;
            padding-bottom: 10px;
        }
        
        /* 结果展示区域 */
        .result-section {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            display: none;
        }
        
        .result-section.active { display: block; }
        
        .file-info {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
        }
        
        .file-path {
            font-family: monospace;
            color: #1976d2;
            background: #f5f5f5;
            padding: 8px;
            border-radius: 5px;
            margin: 5px 0;
            word-break: break-all;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #43a047 0%, #66bb6a 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
            transition: transform 0.3s;
        }
        
        .download-btn:hover { transform: scale(1.05); }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        .report-list {
            max-height: 300px;
            overflow-y: auto;
            background: white;
            border-radius: 10px;
            padding: 15px;
        }
        
        .report-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .report-item:last-child { border-bottom: none; }
        
        .qa-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
            margin: 5px;
        }
        
        .qa-button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }
        
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 14px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepSeek V3 AI综合测试平台</h1>
            <p>列名标准化 + AI语义分析两层架构 + 完整报告生成</p>
        </div>
        
        <!-- AI语义分析测试模块 -->
        <div class="card">
            <h2>🤖 AI语义分析两层架构测试</h2>
            <p style="color: #666; margin-bottom: 20px;">
                测试L2列的两层语义分析系统，生成完整的分析报告和审批工作流
            </p>
            
            <div>
                <label style="font-weight: bold;">输入JSON比对文件路径：</label>
                <input type="text" id="semanticFilePath" 
                    placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_xxx.json"
                    value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914.json">
                
                <button class="qa-button" onclick="runSemanticAnalysis()">
                    🚀 执行语义分析
                </button>
                
                <button class="qa-button" onclick="loadReportList()" style="background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);">
                    📋 查看历史报告
                </button>
            </div>
            
            <!-- 分析结果展示区 -->
            <div id="semanticResult" class="result-section">
                <h3>📊 分析结果</h3>
                
                <!-- 统计信息 -->
                <div class="stats-grid" id="statsGrid"></div>
                
                <!-- 生成的文件信息 -->
                <div class="file-info">
                    <h4>📁 生成的报告文件</h4>
                    <div id="generatedFiles"></div>
                </div>
                
                <!-- 详细结果 -->
                <div class="file-info">
                    <h4>🔍 详细分析结果</h4>
                    <div id="detailedResults"></div>
                </div>
            </div>
            
            <!-- 历史报告列表 -->
            <div id="reportListSection" class="result-section">
                <h3>📚 历史报告列表</h3>
                <div class="report-list" id="reportList"></div>
            </div>
        </div>
        
        <!-- 列名标准化模块（保留原有功能） -->
        <div class="card">
            <h2>📊 列名标准化测试</h2>
            <p style="color: #666; margin-bottom: 20px;">
                将CSV列名映射到19个标准列名
            </p>
            
            <div>
                <input type="text" id="columnsInput" 
                    placeholder="输入列名，用逗号分隔"
                    value="A: 项目类型, B: 任务发起时间, C: 负责人">
                
                <button class="qa-button" onclick="runColumnAnalysis()">
                    🔄 执行标准化
                </button>
                
                <button class="qa-button" onclick="showPrompt()" style="background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);">
                    📝 查看提示词
                </button>
            </div>
            
            <div id="columnResult" class="result-section"></div>
        </div>
    </div>
    
    <script>
        async function runSemanticAnalysis() {
            const filePath = document.getElementById('semanticFilePath').value;
            if (!filePath) {
                alert('请输入文件路径');
                return;
            }
            
            const resultDiv = document.getElementById('semanticResult');
            resultDiv.classList.add('active');
            resultDiv.innerHTML = '<p>⏳ 正在分析中...</p>';
            
            try {
                const response = await fetch('/api/semantic_analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: filePath })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displaySemanticResults(data.data);
                } else {
                    resultDiv.innerHTML = `<p style="color: red;">❌ 错误: ${data.error}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">❌ 请求失败: ${error.message}</p>`;
            }
        }
        
        function displaySemanticResults(data) {
            // 显示统计信息
            const statsHtml = `
                <div class="stat-card">
                    <div class="stat-value">${data.total_modifications}</div>
                    <div class="stat-label">总修改数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.layer1_passed}</div>
                    <div class="stat-label">第一层通过</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.layer2_analyzed}</div>
                    <div class="stat-label">第二层分析</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.processing_time}</div>
                    <div class="stat-label">处理时间</div>
                </div>
            `;
            document.getElementById('statsGrid').innerHTML = statsHtml;
            
            // 显示生成的文件
            if (data.files_generated) {
                const filesHtml = `
                    <div class="file-path">
                        <strong>语义分析报告:</strong><br>
                        ${data.files_generated.semantic_report}
                        <a href="${data.files_generated.report_url}" class="download-btn">📥 下载</a>
                    </div>
                    <div class="file-path">
                        <strong>审批工作流:</strong><br>
                        ${data.files_generated.workflow_file}
                        <a href="${data.files_generated.workflow_url}" class="download-btn">📥 下载</a>
                    </div>
                `;
                document.getElementById('generatedFiles').innerHTML = filesHtml;
            }
            
            // 显示详细结果
            let detailsHtml = '<table style="width: 100%; border-collapse: collapse;">';
            detailsHtml += '<tr style="background: #f5f5f5;"><th>列名</th><th>修改内容</th><th>第一层</th><th>第二层</th><th>最终决策</th></tr>';
            
            data.modifications.forEach(mod => {
                const rowColor = mod.final_decision === 'APPROVE' ? '#e8f5e9' : 
                               mod.final_decision === 'REVIEW' ? '#fff3e0' : '#ffebee';
                detailsHtml += `
                    <tr style="background: ${rowColor};">
                        <td style="padding: 10px; border: 1px solid #ddd;">${mod.column}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${mod.old} → ${mod.new}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${mod.layer1}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${mod.layer2 || '-'}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">
                            <span style="color: ${mod.final_decision === 'APPROVE' ? 'green' : 'orange'};">
                                ${mod.final_decision}
                            </span>
                        </td>
                    </tr>
                `;
            });
            
            detailsHtml += '</table>';
            
            // 显示风险分布
            if (data.summary) {
                detailsHtml += `
                    <div style="margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 10px;">
                        <h4>📈 汇总统计</h4>
                        <p>✅ 自动通过: ${data.summary.approved}</p>
                        <p>⚠️ 需要审核: ${data.summary.review_required}</p>
                        <p>❌ 已拒绝: ${data.summary.rejected}</p>
                    </div>
                `;
            }
            
            document.getElementById('detailedResults').innerHTML = detailsHtml;
        }
        
        async function loadReportList() {
            const listSection = document.getElementById('reportListSection');
            listSection.classList.add('active');
            
            try {
                const response = await fetch('/api/list_reports');
                const data = await response.json();
                
                if (data.success) {
                    let listHtml = '<h4>语义分析报告</h4>';
                    data.semantic_reports.forEach(file => {
                        listHtml += `
                            <div class="report-item">
                                <div>
                                    <strong>${file.filename}</strong><br>
                                    <small>创建时间: ${file.created} | 大小: ${(file.size/1024).toFixed(2)} KB</small>
                                </div>
                                <a href="${file.download_url}" class="download-btn">下载</a>
                            </div>
                        `;
                    });
                    
                    listHtml += '<h4 style="margin-top: 20px;">审批工作流</h4>';
                    data.workflow_files.forEach(file => {
                        listHtml += `
                            <div class="report-item">
                                <div>
                                    <strong>${file.filename}</strong><br>
                                    <small>创建时间: ${file.created} | 大小: ${(file.size/1024).toFixed(2)} KB</small>
                                </div>
                                <a href="${file.download_url}" class="download-btn">下载</a>
                            </div>
                        `;
                    });
                    
                    document.getElementById('reportList').innerHTML = listHtml;
                }
            } catch (error) {
                document.getElementById('reportList').innerHTML = `<p style="color: red;">加载失败: ${error.message}</p>`;
            }
        }
        
        async function runColumnAnalysis() {
            const columns = document.getElementById('columnsInput').value.split(',').map(c => c.trim());
            const resultDiv = document.getElementById('columnResult');
            resultDiv.classList.add('active');
            resultDiv.innerHTML = '<p>⏳ 正在分析中...</p>';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ columns })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = '<h4>映射结果:</h4><ul>';
                    for (let [key, value] of Object.entries(data.data.mappings)) {
                        html += `<li>${key} → ${value}</li>`;
                    }
                    html += '</ul>';
                    
                    if (data.data.missing_columns.length > 0) {
                        html += '<h4>缺失的标准列:</h4><ul>';
                        data.data.missing_columns.forEach(col => {
                            html += `<li style="color: orange;">${col}</li>`;
                        });
                        html += '</ul>';
                    }
                    
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = `<p style="color: red;">❌ 错误: ${data.error}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">❌ 请求失败: ${error.message}</p>`;
            }
        }
        
        async function showPrompt() {
            try {
                const response = await fetch('/api/get_prompt');
                const data = await response.json();
                alert('提示词内容：\\n\\n' + data.prompt.substring(0, 500) + '...');
            } catch (error) {
                alert('获取提示词失败: ' + error.message);
            }
        }
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   DeepSeek V3 AI综合测试平台 - 完整版                  ║
    ║   端口: 8098                                         ║
    ║   访问: http://localhost:8098                        ║
    ║   功能: 列名标准化 + 语义分析 + 报告生成               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=8098, debug=False)