#!/usr/bin/env python3
"""
综合打分算法服务器
提供详细打分和综合汇总的Web界面
"""

import os
import sys
import json
import glob
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'production'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'production/scoring_engine'))

# 导入打分模块
from scoring_engine.integrated_scorer import IntegratedScorer
from scoring_engine.comprehensive_aggregator import ComprehensiveAggregator

app = Flask(__name__)
# 增强CORS配置，解决异步响应错误
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>综合打分算法分析平台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
        }
        
        .module-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .module {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .module h2 {
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            color: #555;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .input-group input,
        .input-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus,
        .input-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .input-group textarea {
            min-height: 80px;
            resize: vertical;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
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
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
            color: white;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .process-display {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .process-display h3 {
            color: #333;
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        .process-item {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 3px;
        }
        
        .process-item.l1 {
            border-left: 3px solid #ff4444;
        }
        
        .process-item.l2 {
            border-left: 3px solid #ffaa00;
        }
        
        .process-item.l3 {
            border-left: 3px solid #00aa00;
        }
        
        .result-display {
            margin-top: 20px;
            padding: 15px;
            background: #282c34;
            border-radius: 5px;
            color: #abb2bf;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .result-display pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .full-process {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .full-process h2 {
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .risk-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 5px;
        }
        
        .risk-extreme-high {
            background: #ff4444;
            color: white;
        }
        
        .risk-high {
            background: #ff8800;
            color: white;
        }
        
        .risk-medium {
            background: #ffdd00;
            color: #333;
        }
        
        .risk-low {
            background: #00dd00;
            color: white;
        }
        
        .risk-extreme-low {
            background: #0088ff;
            color: white;
        }
        
        .algorithm-info {
            background: #f0f8ff;
            border: 1px solid #b0d4ff;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .algorithm-info h4 {
            color: #0066cc;
            margin-bottom: 10px;
        }
        
        .algorithm-info code {
            background: #e0f0ff;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
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
            <h1>🎯 综合打分算法分析平台</h1>
            <p>基于L1/L2/L3规则与AI语义分析的综合集成系统 v1.0</p>
        </div>
        
        <div class="module-container">
            <!-- 模块1：详细打分 -->
            <div class="module">
                <h2>📊 模块1：详细打分（格子级）</h2>
                
                <div class="algorithm-info">
                    <h4>算法位置</h4>
                    <p><code>/production/scoring_engine/integrated_scorer.py</code></p>
                    <h4>核心公式</h4>
                    <p>最终评分 = 基础风险分 × 变更系数 × 重要性权重 × AI调整系数 × 置信度加权</p>
                    
                    <h4>L1/L2/L3分类策略</h4>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li><strong>L1列（高风险）</strong>: 基础分0.8，纯规则打分，不使用AI</li>
                        <li><strong>L2列（中风险）</strong>: 基础分0.5，<span style="color: #ff6600;">必须使用AI语义分析</span>，禁止降级</li>
                        <li><strong>L3列（低风险）</strong>: 基础分0.2，纯规则打分，不使用AI</li>
                    </ul>
                    
                    <h4>L2语义分析调用链路与打分影响</h4>
                    <div style="background: #fff3cd; padding: 10px; border-radius: 3px; margin-top: 10px;">
                        <p style="margin: 5px 0;"><strong>1. 输入:</strong> <code>/comparison_results/simplified_*.json</code> (标准化后的对比文件)</p>
                        <p style="margin: 5px 0;"><strong>2. L2分析器:</strong> <code>/production/core_modules/l2_semantic_analysis_two_layer.py</code></p>
                        <p style="margin: 5px 0;"><strong>3. API客户端:</strong> <code>/production/core_modules/deepseek_client.py</code> (硅基流动DeepSeek V3)</p>
                        <p style="margin: 5px 0;"><strong>4. 两层AI架构:</strong></p>
                        <ul style="margin-left: 20px;">
                            <li><strong>第一层:</strong> 快速筛选（批量20条，50 tokens/批）</li>
                            <li><strong>第二层:</strong> 深度分析（单条处理，500 tokens/条）</li>
                        </ul>
                        <p style="margin: 5px 0;"><strong>5. L2打分计算公式:</strong></p>
                        <div style="background: white; padding: 8px; border-radius: 3px; margin: 5px 0; font-family: monospace;">
                            最终分数 = 基础分(0.5) × 变更因子 × 重要性权重 × <span style="color: #ff6600;">AI调整系数</span> × 置信度权重
                        </div>
                        <p style="margin: 5px 0;"><strong>6. AI调整系数影响:</strong></p>
                        <ul style="margin-left: 20px; font-size: 0.9em;">
                            <li><strong>APPROVE（批准）:</strong> AI系数 = 0.6，降低分数40%（风险较低）</li>
                            <li><strong>CONDITIONAL（有条件批准）:</strong> AI系数 = 0.8，降低分数20%</li>
                            <li><strong>REVIEW（需审核）:</strong> AI系数 = 1.2，提高分数20%</li>
                            <li><strong>REJECT（拒绝）:</strong> AI系数 = 1.5，提高分数50%（风险较高）</li>
                            <li><strong>UNSURE（不确定）:</strong> AI系数 = 1.0，保持原分数</li>
                        </ul>
                        <p style="margin: 5px 0;"><strong>7. 置信度权重计算:</strong></p>
                        <div style="background: white; padding: 8px; border-radius: 3px; margin: 5px 0; font-family: monospace;">
                            <span style="color: #666;">原公式：置信度权重 = 0.5 + (AI置信度/100) × 0.5</span><br>
                            <strong>实际使用：</strong><br>
                            • 置信度 ≥ 90%: 权重 = 1.0<br>
                            • 置信度 70-89%: 权重 = 0.9<br>
                            • 置信度 50-69%: 权重 = 0.8<br>
                            • 置信度 < 50%: 权重 = 0.7
                        </div>
                        <p style="margin: 5px 0; color: #d32f2f;"><strong>⚠️ 重要:</strong> L2列必须使用AI分析，禁止任何降级或mock数据</p>
                        <p style="margin: 5px 0;"><strong>8. 详细打分输出:</strong> <code>/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_[时间戳].json</code></p>
                        <p style="margin: 5px 0;"><strong>9. 审批工作流输出:</strong> <code>/root/projects/tencent-doc-manager/approval_workflows/pending/workflow_WF-L2-[时间戳].json</code></p>
                    </div>
                    
                    <h4>🗂️ 核心文件位置说明</h4>
                    <div style="background: #fff3e0; padding: 10px; border-radius: 3px; margin-top: 10px; border: 2px solid #ff9800;">
                        <p style="margin: 5px 0;"><strong>📥 输入文件：</strong></p>
                        <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/comparison_results/simplified_*.json</code>
                        <p style="margin: 10px 0 5px 0;"><strong>📤 输出文件：</strong></p>
                        <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_*.json</code>
                        <p style="margin: 10px 0 5px 0;"><strong>🤖 L2语义分析输出：</strong></p>
                        <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/semantic_results/2025_W36/semantic_analysis_L2_*.json</code>
                        <p style="margin: 10px 0 5px 0;"><strong>📂 核心程序位置：</strong></p>
                        <ul style="margin-left: 20px; font-size: 0.9em;">
                            <li>打分引擎: <code>/root/projects/tencent-doc-manager/production/scoring_engine/integrated_scorer.py</code></li>
                            <li>L2分析器: <code>/root/projects/tencent-doc-manager/production/core_modules/l2_semantic_analysis_two_layer.py</code></li>
                            <li>DeepSeek客户端: <code>/root/projects/tencent-doc-manager/production/core_modules/deepseek_client.py</code></li>
                            <li>综合汇总器: <code>/root/projects/tencent-doc-manager/production/scoring_engine/comprehensive_aggregator.py</code></li>
                        </ul>
                    </div>
                    
                    <h4>🔄 L2 AI打分数据流程</h4>
                    <div style="background: #e8f5e9; padding: 10px; border-radius: 3px; margin-top: 10px;">
                        <p style="margin: 5px 0;"><strong>L2 AI数据来源与使用：</strong></p>
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                            <tr style="background: #f0f0f0;">
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>数据来源</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">输入文件中标记为column_level="L2"的修改项</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>AI分析位置</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">process_l2_modification()函数调用DeepSeek V3</td>
                            </tr>
                            <tr style="background: #f0f0f0;">
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>第一层结果</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">SAFE/RISKY/UNSURE + 置信度%</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>第二层结果</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">APPROVE/REVIEW/REJECT + 风险分析</td>
                            </tr>
                            <tr style="background: #f0f0f0;">
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>影响打分</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">AI调整系数(0.8-1.5) × 置信度权重</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>最终输出</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">写入detailed_score_*.json的ai_analysis字段</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <div class="input-group">
                    <label>输入文件路径（简化对比JSON）：</label>
                    <input type="text" id="detailed-input" 
                           placeholder="/root/projects/tencent-doc-manager/comparison_results/simplified_*.json"
                           value="/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914_standardized.json">
                </div>
                
                <button class="btn btn-primary" onclick="runDetailedScoring()">
                    执行详细打分
                </button>
                
                <div class="process-display" id="detailed-process" style="display:none;">
                    <h3>打分过程</h3>
                    <div id="detailed-process-content"></div>
                </div>
                
                <div class="result-display" id="detailed-result" style="display:none;">
                    <pre id="detailed-result-content"></pre>
                </div>
            </div>
            
            <!-- 模块2：综合汇总 -->
            <div class="module">
                <h2>📈 模块2：综合汇总（列级）</h2>
                
                <div class="algorithm-info">
                    <h4>📝 算法位置</h4>
                    <p><code>/root/projects/tencent-doc-manager/production/scoring_engine/comprehensive_aggregator.py</code></p>
                    <h4>📈 汇总策略</h4>
                    <p>加权平均 + 风险趋势分析 + 跨表模式检测</p>
                    
                    <h4>🧮 综合汇总算法详解</h4>
                    <div style="background: #f0f8ff; padding: 10px; border-radius: 3px; margin: 10px 0; border: 1px solid #4169e1;">
                        <p style="margin: 5px 0;"><strong>1️⃣ 列级聚合算法：</strong></p>
                        <div style="background: white; padding: 8px; border-radius: 3px; margin: 5px 0; font-family: monospace;">
                            aggregated_score = sum(scores) / count(scores)  // 平均分<br>
                            max_score = max(scores)  // 最高分<br>
                            min_score = min(scores)  // 最低分<br>
                            risk_trend = analyze_trend(scores)  // stable/increasing/decreasing
                        </div>
                        
                        <p style="margin: 10px 0 5px 0;"><strong>2️⃣ 系统风险评分计算：</strong></p>
                        <div style="background: white; padding: 8px; border-radius: 3px; margin: 5px 0; font-family: monospace;">
                            system_risk_score = sum(所有修改项得分) / count(所有修改项)<br>
                            <span style="color: #666;">您的案例: (0.54+1.0+0.8+0.172+0.432+0.96) / 6 = 0.651</span>
                        </div>
                        
                        <p style="margin: 10px 0 5px 0;"><strong>3️⃣ 风险等级判定：</strong></p>
                        <ul style="margin-left: 20px; font-size: 0.9em;">
                            <li>≥ 0.7: CRITICAL 🔴</li>
                            <li>0.5-0.7: HIGH 🟠 <span style="color: #ff6600;">(您的系统: 0.651)</span></li>
                            <li>0.3-0.5: MEDIUM 🟡</li>
                            <li>< 0.3: LOW 🟢</li>
                        </ul>
                        
                        <p style="margin: 10px 0 5px 0;"><strong>4️⃣ AI介入率计算：</strong></p>
                        <div style="background: white; padding: 8px; border-radius: 3px; margin: 5px 0; font-family: monospace;">
                            ai_intervention_rate = (L2列修改数 / 总修改数) × 100%<br>
                            <span style="color: #666;">您的案例: (3 / 6) × 100% = 50% (实际显示100%可能是bug)</span>
                        </div>
                        
                        <p style="margin: 10px 0 5px 0;"><strong>5️⃣ 模式检测算法：</strong></p>
                        <ul style="margin-left: 20px; font-size: 0.9em;">
                            <li><strong>多列高风险</strong>: 同表中≥3列得分≥0.8</li>
                            <li><strong>系统性变更</strong>: 同列在多表中都有变更</li>
                            <li><strong>异常模式</strong>: 风险分布偏离正常范围</li>
                        </ul>
                    </div>
                    
                    <h4>🗿️ 核心文件位置</h4>
                    <div style="background: #fff3e0; padding: 10px; border-radius: 3px; margin-top: 10px; border: 2px solid #ff9800;">
                        <p style="margin: 5px 0;"><strong>📥 输入文件（详细打分结果）：</strong></p>
                        <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_*.json</code>
                        <p style="margin: 5px 0; color: #d84315; font-size: 0.9em;"><strong>⚠️ 注意：</strong>详细打分文件存储在 /root/projects/ 根目录下，而非 tencent-doc-manager 子目录</p>
                        <p style="margin: 10px 0 5px 0;"><strong>📤 输出文件（综合汇总报告）：</strong></p>
                        <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W[XX]_[时间戳].json</code>
                        <p style="margin: 10px 0 5px 0;"><strong>📊 汇总内容：</strong></p>
                        <ul style="margin-left: 20px; font-size: 0.9em;">
                            <li>列级风险排名</li>
                            <li>跨表风险模式</li>
                            <li>AI介入率统计</li>
                            <li>系统风险评分</li>
                        </ul>
                    </div>
                </div>
                
                <div class="input-group">
                    <label>输入文件路径（多个详细打分文件，每行一个）：</label>
                    <textarea id="comprehensive-input" 
                              placeholder="输入详细打分文件路径，每行一个..."></textarea>
                </div>
                
                <div class="input-group">
                    <label>周数标识（可选，空白则自动计算）：</label>
                    <input type="text" id="week-input" placeholder="如：W37" value="">
                </div>
                
                <button class="btn btn-success" onclick="runComprehensiveAggregation()">
                    执行综合汇总
                </button>
                
                <div class="process-display" id="comprehensive-process" style="display:none;">
                    <h3>汇总过程</h3>
                    <div id="comprehensive-process-content"></div>
                </div>
                
                <div class="result-display" id="comprehensive-result" style="display:none;">
                    <pre id="comprehensive-result-content"></pre>
                </div>
            </div>
        </div>
        
        <!-- 整体流程 -->
        <div class="full-process">
            <h2>🚀 整体流程（端到端分析）</h2>
            
            <div class="algorithm-info">
                <h4>🔄 完整处理链路</h4>
                <p>简化对比JSON → L1/L2/L3分类 → 详细打分 → 综合汇总 → 风险报告</p>
                <h4>📁 完整流程文件路径</h4>
                <div style="background: #e8f5e9; padding: 10px; border-radius: 3px; margin-top: 10px; border: 2px solid #4caf50;">
                    <p style="margin: 5px 0;"><strong>第1步 - 输入：</strong></p>
                    <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/comparison_results/simplified_*.json</code>
                    <p style="margin: 10px 0 5px 0;"><strong>第2步 - 详细打分输出：</strong></p>
                    <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/scoring_results/detailed/detailed_score_*.json</code>
                    <p style="margin: 10px 0 5px 0;"><strong>第3步 - L2语义分析输出：</strong></p>
                    <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/semantic_results/2025_W[XX]/semantic_analysis_L2_*.json</code>
                    <p style="margin: 10px 0 5px 0;"><strong>第4步 - 审批工作流：</strong></p>
                    <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/approval_workflows/pending/workflow_WF-L2-*.json</code>
                    <p style="margin: 10px 0 5px 0;"><strong>第5步 - 综合汇总输出：</strong></p>
                    <code style="background: white; padding: 5px; display: block;">/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W[XX]_*.json</code>
                </div>
            </div>
            
            <div class="input-group">
                <label>输入多个简化对比JSON文件（每行一个）：</label>
                <textarea id="full-process-input" rows="4"
                          placeholder="输入简化对比JSON文件路径，每行一个...">/root/projects/tencent-doc-manager/comparison_results/simplified_副本-测试版本-出国销售计划表-工作表1_vs_副本-副本-测试版本-出国销售计划表-工作表1_20250906_222914_standardized.json</textarea>
            </div>
            
            <button class="btn btn-warning" onclick="runFullProcess()">
                运行完整流程
            </button>
            
            <div class="loading" id="full-process-loading">
                <div class="spinner"></div>
                <p>正在处理，请稍候...</p>
            </div>
            
            <div class="process-display" id="full-process-display" style="display:none;">
                <h3>处理进度</h3>
                <div id="full-process-content"></div>
            </div>
            
            <div class="result-display" id="full-result" style="display:none;">
                <pre id="full-result-content"></pre>
            </div>
        </div>
    </div>
    
    <script>
        // 详细打分
        async function runDetailedScoring() {
            const inputPath = document.getElementById('detailed-input').value;
            if (!inputPath) {
                alert('请输入文件路径');
                return;
            }
            
            // 显示处理区域和进度
            document.getElementById('detailed-process').style.display = 'block';
            document.getElementById('detailed-result').style.display = 'none';
            
            // 添加动态进度提示
            const processDiv = document.getElementById('detailed-process-content');
            processDiv.innerHTML = `
                <div style="padding: 20px; background: #e3f2fd; border-radius: 8px; margin-bottom: 10px;">
                    <h4 style="color: #1976d2;">⏳ 正在处理...</h4>
                    <div style="margin-top: 10px;">
                        <div style="animation: pulse 1.5s infinite;">📁 读取输入文件: ${inputPath}</div>
                        <div style="margin-top: 5px; animation: pulse 1.5s infinite 0.3s;">🔍 识别L1/L2/L3列...</div>
                        <div style="margin-top: 5px; animation: pulse 1.5s infinite 0.6s;">🤖 调用DeepSeek V3 AI分析L2列...</div>
                        <div style="margin-top: 5px; animation: pulse 1.5s infinite 0.9s;">📊 计算风险评分...</div>
                    </div>
                </div>
                <style>
                    @keyframes pulse {
                        0% { opacity: 0.4; }
                        50% { opacity: 1; }
                        100% { opacity: 0.4; }
                    }
                </style>
            `;
            
            try {
                const response = await fetch('/api/detailed_scoring', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input_file: inputPath})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // 显示处理完成提示
                    processDiv.innerHTML = `
                        <div style="padding: 20px; background: #e8f5e9; border-radius: 8px; margin-bottom: 10px;">
                            <h4 style="color: #2e7d32;">✅ 处理完成！</h4>
                            <p>输出文件已保存到: <code>${data.output_file || '未知路径'}</code></p>
                            <p>处理了 ${data.summary ? data.summary.total_modifications : 0} 个修改项</p>
                        </div>
                    `;
                    
                    // 显示处理过程统计
                    if (data.process_info) {
                        displayDetailedProcess(data.process_info);
                    }
                    
                    // 优化结果显示 - 只显示摘要，避免显示大量数据导致卡顿
                    document.getElementById('detailed-result').style.display = 'block';
                    const summary = data.summary || {};
                    const resultHtml = `
                        <h3>📊 打分结果摘要</h3>
                        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                            <p><strong>总修改数:</strong> ${summary.total_modifications || 0}</p>
                            <p><strong>平均分数:</strong> ${summary.average_score ? summary.average_score.toFixed(3) : 'N/A'}</p>
                            <p><strong>AI使用统计:</strong></p>
                            <ul>
                                <li>总AI调用: ${summary.ai_usage ? summary.ai_usage.total_ai_calls : 0}</li>
                                <li>第一层通过: ${summary.ai_usage ? summary.ai_usage.layer1_passes : 0}</li>
                                <li>第二层分析: ${summary.ai_usage ? summary.ai_usage.layer2_analyses : 0}</li>
                            </ul>
                            <p><strong>风险分布:</strong></p>
                            <ul>
                                <li>🔴 极高风险: ${summary.risk_distribution ? summary.risk_distribution.EXTREME_HIGH : 0}</li>
                                <li>🟠 高风险: ${summary.risk_distribution ? summary.risk_distribution.HIGH : 0}</li>
                                <li>🟡 中风险: ${summary.risk_distribution ? summary.risk_distribution.MEDIUM : 0}</li>
                                <li>🟢 低风险: ${summary.risk_distribution ? summary.risk_distribution.LOW : 0}</li>
                                <li>🔵 极低风险: ${summary.risk_distribution ? summary.risk_distribution.EXTREME_LOW : 0}</li>
                            </ul>
                        </div>
                        <p style="margin-top: 10px; color: #666;">
                            完整结果已保存到: <code>${data.output_file}</code><br>
                            使用 <code>cat ${data.output_file} | python3 -m json.tool</code> 查看详细内容
                        </p>
                    `;
                    document.getElementById('detailed-result-content').innerHTML = resultHtml;
                } else {
                    alert('处理失败: ' + data.error);
                }
            } catch (error) {
                alert('请求失败: ' + error);
            }
        }
        
        // 显示详细打分过程
        function displayDetailedProcess(info) {
            const container = document.getElementById('detailed-process-content');
            container.innerHTML = '';
            
            // 显示L1/L2/L3分类统计
            if (info.classification) {
                const classDiv = document.createElement('div');
                classDiv.className = 'process-item';
                classDiv.innerHTML = `
                    <strong>列分类统计：</strong><br>
                    L1列（高风险）: ${info.classification.L1.count}个 - ${info.classification.L1.columns.join(', ')}<br>
                    L2列（中风险）: ${info.classification.L2.count}个 - ${info.classification.L2.columns.join(', ')}<br>
                    L3列（低风险）: ${info.classification.L3.count}个 - ${info.classification.L3.columns.join(', ')}
                `;
                container.appendChild(classDiv);
            }
            
            // 显示打分样例
            if (info.sample_scores) {
                info.sample_scores.forEach(score => {
                    const scoreDiv = document.createElement('div');
                    scoreDiv.className = `process-item ${score.level.toLowerCase()}`;
                    
                    let riskClass = '';
                    if (score.final_score >= 0.8) riskClass = 'risk-extreme-high';
                    else if (score.final_score >= 0.6) riskClass = 'risk-high';
                    else if (score.final_score >= 0.4) riskClass = 'risk-medium';
                    else if (score.final_score >= 0.2) riskClass = 'risk-low';
                    else riskClass = 'risk-extreme-low';
                    
                    let aiDetails = '';
                    if (score.level === 'L2' && score.ai_used) {
                        aiDetails = `
                            <div style="margin-top: 5px; padding: 5px; background: #e8f4fd; border-left: 3px solid #2196F3;">
                                <strong>L2 AI语义分析结果:</strong><br>
                                • 第一层判断: ${score.layer1_judgment || 'N/A'} ${score.layer1_confidence > 0 ? '(置信度: ' + score.layer1_confidence + '%)' : ''}<br>
                                • 需要第二层: ${score.needs_layer2 ? '是' : '否'}<br>
                                • AI决策: <strong>${score.ai_decision}</strong> (置信度: ${score.ai_confidence}%)<br>
                                • AI调整系数: ${score.ai_adjustment || 1.0}<br>
                                ${score.layer1_judgment && score.layer1_judgment !== 'N/A' ? '• 第一层判断正常执行 ✅' : '• 第一层未返回有效结果 ⚠️'}
                            </div>
                        `;
                    }
                    
                    scoreDiv.innerHTML = `
                        <strong>${score.column}</strong> (${score.level})
                        <span class="risk-badge ${riskClass}">${score.final_score.toFixed(3)}</span><br>
                        基础分: ${score.base_score} × 变更系数: ${score.change_factor} × 
                        权重: ${score.importance_weight}<br>
                        ${score.ai_used ? `AI决策: ${score.ai_decision} (置信度: ${score.ai_confidence}%)` : '规则打分'}
                        ${aiDetails}
                    `;
                    container.appendChild(scoreDiv);
                });
            }
        }
        
        // 综合汇总
        async function runComprehensiveAggregation() {
            const inputText = document.getElementById('comprehensive-input').value;
            const week = document.getElementById('week-input').value;
            
            if (!inputText) {
                alert('请输入详细打分文件路径');
                return;
            }
            
            const files = inputText.split('\\n').filter(f => f.trim());
            
            document.getElementById('comprehensive-process').style.display = 'block';
            document.getElementById('comprehensive-result').style.display = 'none';
            
            try {
                const response = await fetch('/api/comprehensive_aggregation', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({files, week})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayComprehensiveProcess(data.process_info);
                    
                    document.getElementById('comprehensive-result').style.display = 'block';
                    document.getElementById('comprehensive-result-content').textContent = 
                        JSON.stringify(data.result, null, 2);
                } else {
                    alert('处理失败: ' + data.error);
                }
            } catch (error) {
                alert('请求失败: ' + error);
            }
        }
        
        // 显示综合汇总过程
        function displayComprehensiveProcess(info) {
            const container = document.getElementById('comprehensive-process-content');
            container.innerHTML = '';
            
            if (info.tables_processed) {
                const tableDiv = document.createElement('div');
                tableDiv.className = 'process-item';
                tableDiv.innerHTML = `
                    <strong>处理表格：</strong><br>
                    ${info.tables_processed.map(t => `${t.name} (${t.modifications}个修改)`).join('<br>')}
                `;
                container.appendChild(tableDiv);
            }
            
            if (info.risk_summary) {
                const riskDiv = document.createElement('div');
                riskDiv.className = 'process-item';
                riskDiv.innerHTML = `
                    <strong>风险汇总：</strong><br>
                    系统风险分: ${info.risk_summary.system_risk}<br>
                    高风险列: ${info.risk_summary.high_risk_columns.join(', ')}<br>
                    AI介入率: ${info.risk_summary.ai_intervention_rate}
                `;
                container.appendChild(riskDiv);
            }
        }
        
        // 完整流程
        async function runFullProcess() {
            const inputText = document.getElementById('full-process-input').value;
            if (!inputText) {
                alert('请输入文件路径');
                return;
            }
            
            const files = inputText.split('\\n').filter(f => f.trim());
            
            document.getElementById('full-process-loading').classList.add('active');
            document.getElementById('full-process-display').style.display = 'none';
            document.getElementById('full-result').style.display = 'none';
            
            try {
                const response = await fetch('/api/full_process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input_files: files})
                });
                
                const data = await response.json();
                
                document.getElementById('full-process-loading').classList.remove('active');
                
                if (data.success) {
                    displayFullProcess(data.process_steps);
                    
                    document.getElementById('full-result').style.display = 'block';
                    document.getElementById('full-result-content').textContent = 
                        JSON.stringify(data.comprehensive_result, null, 2);
                } else {
                    alert('处理失败: ' + data.error);
                }
            } catch (error) {
                document.getElementById('full-process-loading').classList.remove('active');
                alert('请求失败: ' + error);
            }
        }
        
        // 显示完整流程
        function displayFullProcess(steps) {
            const container = document.getElementById('full-process-content');
            container.innerHTML = '';
            document.getElementById('full-process-display').style.display = 'block';
            
            steps.forEach((step, index) => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'process-item';
                stepDiv.innerHTML = `
                    <strong>步骤 ${index + 1}: ${step.name}</strong><br>
                    状态: ${step.status}<br>
                    ${step.details || ''}
                `;
                container.appendChild(stepDiv);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/detailed_scoring', methods=['POST'])
def detailed_scoring():
    """详细打分API"""
    try:
        data = request.get_json()
        input_file = data.get('input_file')
        
        if not input_file or not os.path.exists(input_file):
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 创建打分器
        scorer = IntegratedScorer(use_ai=True, cache_enabled=True)
        
        # 读取输入文件获取修改信息
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        # 分析列分类
        modifications = input_data.get('modifications', [])
        classification = {'L1': {'count': 0, 'columns': []}, 
                         'L2': {'count': 0, 'columns': []},
                         'L3': {'count': 0, 'columns': []}}
        
        columns_seen = set()
        for mod in modifications:
            col_name = mod.get('column_name', '')
            if col_name not in columns_seen:
                columns_seen.add(col_name)
                level = scorer.get_column_level(col_name)
                classification[level]['count'] += 1
                classification[level]['columns'].append(col_name)
        
        # 执行打分
        output_file = scorer.process_file(input_file)
        
        # 读取结果
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # 准备样例打分展示
        sample_scores = []
        for score in result['scores'][:5]:  # 只展示前5个
            score_info = {
                'column': score['column_name'],
                'level': score['column_level'],
                'base_score': score['scoring_details']['base_score'],
                'change_factor': score['scoring_details']['change_factor'],
                'importance_weight': score['scoring_details']['importance_weight'],
                'final_score': score['scoring_details']['final_score'],
                'ai_used': score['ai_analysis']['ai_used'],
                'ai_decision': score['ai_analysis'].get('ai_decision'),
                'ai_confidence': score['ai_analysis'].get('ai_confidence'),
                'ai_adjustment': score['scoring_details'].get('ai_adjustment', 1.0)
            }
            
            # 如果是L2列，添加更多AI分析细节
            if score['column_level'] == 'L2' and score['ai_analysis'].get('ai_used'):
                # 修复: 直接从ai_analysis获取数据，不要双重嵌套
                layer1_result = score['ai_analysis'].get('layer1_result', {})
                layer2_result = score['ai_analysis'].get('layer2_result')
                
                # 安全地获取第一层判断信息
                if layer1_result:
                    score_info['layer1_judgment'] = layer1_result.get('judgment', 'N/A')
                    score_info['layer1_confidence'] = layer1_result.get('confidence', 0)
                else:
                    score_info['layer1_judgment'] = 'N/A'
                    score_info['layer1_confidence'] = 0
                    
                score_info['needs_layer2'] = layer2_result is not None
            
            sample_scores.append(score_info)
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'result': result,
            'process_info': {
                'classification': classification,
                'sample_scores': sample_scores
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/api/comprehensive_aggregation', methods=['POST'])
def comprehensive_aggregation():
    """综合汇总API"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        week = data.get('week')
        
        if not files:
            return jsonify({'success': False, 'error': '没有输入文件'})
        
        # 检查文件存在性
        valid_files = []
        for file_path in files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
        
        if not valid_files:
            return jsonify({'success': False, 'error': '没有有效的输入文件'})
        
        # 创建汇总器
        aggregator = ComprehensiveAggregator()
        
        # 执行汇总
        report = aggregator.aggregate_files(valid_files, week)
        output_file = aggregator.save_report(report)
        
        # 准备处理信息
        process_info = {
            'tables_processed': [
                {'name': t['table_name'], 'modifications': t['modifications_count']}
                for t in report['table_scores']
            ],
            'risk_summary': {
                'system_risk': report['cross_table_analysis']['overall_metrics']['system_risk_score'],
                'high_risk_columns': [
                    col['column'] for col in 
                    report['cross_table_analysis']['column_risk_ranking']
                    if col['avg_score'] >= 0.6
                ],
                'ai_intervention_rate': report['cross_table_analysis']['overall_metrics']['ai_intervention_rate']
            }
        }
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'result': report,
            'process_info': process_info
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/api/full_process', methods=['POST'])
def full_process():
    """完整流程API"""
    try:
        data = request.get_json()
        input_files = data.get('input_files', [])
        
        if not input_files:
            return jsonify({'success': False, 'error': '没有输入文件'})
        
        process_steps = []
        detailed_files = []
        
        # Step 1: 详细打分
        scorer = IntegratedScorer(use_ai=True, cache_enabled=True)
        
        for input_file in input_files:
            if not os.path.exists(input_file):
                process_steps.append({
                    'name': f'处理文件: {os.path.basename(input_file)}',
                    'status': '失败',
                    'details': '文件不存在'
                })
                continue
            
            try:
                output_file = scorer.process_file(input_file)
                detailed_files.append(output_file)
                
                process_steps.append({
                    'name': f'详细打分: {os.path.basename(input_file)}',
                    'status': '完成',
                    'details': f'输出: {os.path.basename(output_file)}'
                })
            except Exception as e:
                process_steps.append({
                    'name': f'详细打分: {os.path.basename(input_file)}',
                    'status': '失败',
                    'details': str(e)
                })
        
        if not detailed_files:
            return jsonify({
                'success': False,
                'error': '没有成功处理的文件',
                'process_steps': process_steps
            })
        
        # Step 2: 综合汇总
        process_steps.append({
            'name': '综合汇总',
            'status': '处理中',
            'details': f'汇总 {len(detailed_files)} 个详细打分文件'
        })
        
        aggregator = ComprehensiveAggregator()
        # 使用ISO 8601标准计算周数
        week = datetime.now().strftime('W%V')  # %V是ISO周数（1-53）
        report = aggregator.aggregate_files(detailed_files, week)
        output_file = aggregator.save_report(report)
        
        process_steps.append({
            'name': '综合汇总',
            'status': '完成',
            'details': f'输出: {os.path.basename(output_file)}'
        })
        
        # Step 3: 生成最终统计
        process_steps.append({
            'name': '最终统计',
            'status': '完成',
            'details': f"处理 {report['metadata']['total_tables']} 个表格，"
                      f"{report['metadata']['total_modifications']} 个修改，"
                      f"系统风险等级: {report['cross_table_analysis']['overall_metrics']['risk_level']}"
        })
        
        return jsonify({
            'success': True,
            'process_steps': process_steps,
            'detailed_files': detailed_files,
            'comprehensive_file': output_file,
            'comprehensive_result': report
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc(),
            'process_steps': process_steps if 'process_steps' in locals() else []
        })

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   综合打分算法分析平台                                ║
    ║   端口: 8100                                         ║
    ║   访问: http://localhost:8100                        ║
    ║   功能: 详细打分 + 综合汇总 + 完整流程                 ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 创建必要的目录
    os.makedirs('scoring_results/detailed', exist_ok=True)
    os.makedirs('scoring_results/comprehensive', exist_ok=True)
    
    app.run(host='0.0.0.0', port=8100, debug=True)