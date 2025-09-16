#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI列名标准化测试服务器
端口：8096
功能：测试CSV列名到19个标准列名的映射
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')
sys.path.insert(0, '/root/projects/tencent-doc-manager/production/core_modules')

app = Flask(__name__)

# 导入列名标准化模块
try:
    from column_standardization_prompt import ColumnStandardizationPrompt
    PROMPT_GENERATOR_AVAILABLE = True
except ImportError:
    PROMPT_GENERATOR_AVAILABLE = False
    print("⚠️ column_standardization_prompt模块不可用，使用模拟模式")

# 读取HTML模板
HTML_FILE = Path('/root/projects/tencent-doc-manager/test_column_standardization.html')
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    HTML_TEMPLATE = f.read()

@app.route('/')
def index():
    """主页面"""
    return HTML_TEMPLATE

@app.route('/api/standardize', methods=['POST'])
def api_standardize():
    """执行列名标准化"""
    try:
        data = request.json
        actual_columns = data.get('columns', [])
        
        if not actual_columns:
            return jsonify({'success': False, 'error': '没有提供列名'})
        
        if PROMPT_GENERATOR_AVAILABLE:
            # 使用真实的提示词生成器
            prompt_gen = ColumnStandardizationPrompt()
            prompt = prompt_gen.build_single_session_prompt(actual_columns)
            
            # 模拟AI响应（实际应调用Claude API）
            result = simulate_ai_response(actual_columns, prompt_gen)
        else:
            # 使用模拟响应
            result = simulate_standardization(actual_columns)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-prompt', methods=['POST'])
def api_generate_prompt():
    """生成提示词"""
    try:
        data = request.json
        actual_columns = data.get('columns', [])
        
        if not actual_columns:
            return jsonify({'success': False, 'error': '没有提供列名'})
        
        if PROMPT_GENERATOR_AVAILABLE:
            prompt_gen = ColumnStandardizationPrompt()
            prompt = prompt_gen.build_single_session_prompt(actual_columns)
        else:
            prompt = generate_mock_prompt(actual_columns)
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'column_count': len(actual_columns)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load-real-file')
def api_load_real_file():
    """加载真实的CSV对比文件"""
    try:
        # 查找最新的对比结果文件
        comparison_dir = Path('/root/projects/tencent-doc-manager/comparison_results')
        json_files = list(comparison_dir.glob('*.json'))
        
        if not json_files:
            return jsonify({'success': False, 'error': '没有找到对比结果文件'})
        
        # 使用最新的文件
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)
        
        # 提取列名
        columns = set()
        
        # 从metadata提取
        if 'metadata' in comparison_data:
            for key in ['baseline_structure', 'target_structure']:
                if key in comparison_data['metadata']:
                    cols = comparison_data['metadata'][key].get('column_names', [])
                    columns.update(cols)
        
        # 从modified_cells提取
        if 'details' in comparison_data and 'modified_cells' in comparison_data['details']:
            for cell in comparison_data['details']['modified_cells']:
                if 'column_name' in cell:
                    columns.add(cell['column_name'])
        
        return jsonify({
            'success': True,
            'columns': list(columns),
            'filename': latest_file.name,
            'total_differences': comparison_data.get('summary', {}).get('total_differences', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def simulate_ai_response(actual_columns, prompt_gen):
    """模拟AI响应（使用真实的提示词生成器）"""
    # 这里应该调用真实的Claude API
    # 现在使用模拟逻辑
    
    result = {
        "success": True,
        "standard_columns_status": {},
        "mapping": {},
        "confidence_scores": {},
        "missing_standard_columns": [],
        "discarded_columns": [],
        "statistics": {
            "total_standard": 19,
            "mapped_count": 0,
            "missing_count": 0,
            "discarded_count": 0
        }
    }
    
    # 初始化所有标准列
    for col in prompt_gen.standard_columns:
        result["standard_columns_status"][col] = None
    
    # 映射逻辑
    mapped_standards = set()
    
    for actual_col in actual_columns:
        best_match = None
        best_score = 0
        
        # 精确匹配
        if actual_col in prompt_gen.standard_columns:
            best_match = actual_col
            best_score = 1.0
        else:
            # 变异匹配
            for standard, variations in prompt_gen.variation_patterns.items():
                if actual_col in variations and standard not in mapped_standards:
                    best_match = standard
                    best_score = 0.9
                    break
        
        if best_match and best_match not in mapped_standards:
            result["mapping"][actual_col] = best_match
            result["confidence_scores"][actual_col] = best_score
            result["standard_columns_status"][best_match] = actual_col
            mapped_standards.add(best_match)
            result["statistics"]["mapped_count"] += 1
        else:
            result["discarded_columns"].append(actual_col)
            result["statistics"]["discarded_count"] += 1
    
    # 识别缺失的标准列
    for col in prompt_gen.standard_columns:
        if result["standard_columns_status"][col] is None:
            result["missing_standard_columns"].append(col)
            result["statistics"]["missing_count"] += 1
    
    return result

def simulate_standardization(actual_columns):
    """模拟标准化（当模块不可用时）"""
    # 19个标准列名
    STANDARD_COLUMNS = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", 
        "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
    ]
    
    result = {
        "success": True,
        "standard_columns_status": {},
        "mapping": {},
        "confidence_scores": {},
        "missing_standard_columns": [],
        "discarded_columns": [],
        "statistics": {
            "total_standard": 19,
            "mapped_count": 0,
            "missing_count": 0,
            "discarded_count": 0
        }
    }
    
    # 初始化
    for col in STANDARD_COLUMNS:
        result["standard_columns_status"][col] = None
    
    # 简单的映射逻辑
    common_mappings = {
        "ID": "序号",
        "编号": "序号",
        "产品名称": "项目类型",
        "价格": "重要程度",
        "库存": "完成进度",
        "状态": "应用情况",
        "更新时间": "复盘时间"
    }
    
    mapped_standards = set()
    
    for actual_col in actual_columns:
        if actual_col in common_mappings and common_mappings[actual_col] not in mapped_standards:
            standard_col = common_mappings[actual_col]
            result["mapping"][actual_col] = standard_col
            result["confidence_scores"][actual_col] = 0.8
            result["standard_columns_status"][standard_col] = actual_col
            mapped_standards.add(standard_col)
            result["statistics"]["mapped_count"] += 1
        elif actual_col in STANDARD_COLUMNS and actual_col not in mapped_standards:
            result["mapping"][actual_col] = actual_col
            result["confidence_scores"][actual_col] = 1.0
            result["standard_columns_status"][actual_col] = actual_col
            mapped_standards.add(actual_col)
            result["statistics"]["mapped_count"] += 1
        else:
            result["discarded_columns"].append(actual_col)
            result["statistics"]["discarded_count"] += 1
    
    # 识别缺失列
    for col in STANDARD_COLUMNS:
        if result["standard_columns_status"][col] is None:
            result["missing_standard_columns"].append(col)
            result["statistics"]["missing_count"] += 1
    
    return result

def generate_mock_prompt(actual_columns):
    """生成模拟提示词"""
    return f"""你是一个专业的列名标准化专家。

任务：将以下{len(actual_columns)}个实际列名映射到19个标准列名。

实际列名：
{json.dumps(actual_columns, ensure_ascii=False, indent=2)}

19个标准列名：
["序号", "项目类型", "来源", "任务发起时间", "目标对齐", "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人", "监督人", "重要程度", "预计完成时间", "完成进度", "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"]

请输出映射结果。"""

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════╗
    ║   AI列名标准化测试平台                        ║
    ║   端口: 8088                                ║
    ║   访问: http://localhost:8088               ║
    ╚════════════════════════════════════════════╝
    """)
    
    if PROMPT_GENERATOR_AVAILABLE:
        print("✅ 列名标准化模块已加载")
    else:
        print("⚠️ 使用模拟模式运行")
    
    app.run(host='0.0.0.0', port=8088, debug=False)