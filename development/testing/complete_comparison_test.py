#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的表格对比测试程序
用于详细分析修改识别的准确性和完整性
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import time

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')

from document_change_analyzer import DocumentChangeAnalyzer

def log_message(message):
    """记录日志消息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    return f"[{timestamp}] {message}\n"

def load_test_files():
    """加载测试文件"""
    log_message("=== 加载测试文件 ===")
    
    original_file = "/root/projects/tencent-doc-manager/refer/测试版本-小红书部门-工作表2.csv"
    modified_file = "/root/projects/tencent-doc-manager/test_modified_obvious.csv"
    
    # 检查文件是否存在
    if not os.path.exists(original_file):
        log_message(f"❌ 原始文件不存在: {original_file}")
        return None, None
    
    if not os.path.exists(modified_file):
        log_message(f"❌ 修改文件不存在: {modified_file}")
        return None, None
    
    try:
        # 读取原始文件
        original_df = pd.read_csv(original_file, encoding='utf-8', header=1)
        log_message(f"✅ 原始文件加载成功: {original_df.shape[0]}行 × {original_df.shape[1]}列")
        
        # 读取修改文件
        modified_df = pd.read_csv(modified_file, encoding='utf-8', header=1)
        log_message(f"✅ 修改文件加载成功: {modified_df.shape[0]}行 × {modified_df.shape[1]}列")
        
        return original_df, modified_df
        
    except Exception as e:
        log_message(f"❌ 文件加载失败: {str(e)}")
        return None, None

def analyze_data_structure(original_df, modified_df):
    """分析数据结构"""
    log_message("=== 分析数据结构 ===")
    
    analysis_result = {
        "original_info": {
            "shape": original_df.shape,
            "columns": list(original_df.columns),
            "dtypes": original_df.dtypes.to_dict()
        },
        "modified_info": {
            "shape": modified_df.shape,
            "columns": list(modified_df.columns),
            "dtypes": modified_df.dtypes.to_dict()
        }
    }
    
    log_message(f"原始数据: {original_df.shape[0]}行 × {original_df.shape[1]}列")
    log_message(f"修改数据: {modified_df.shape[0]}行 × {modified_df.shape[1]}列")
    
    # 列名对比
    original_cols = set(original_df.columns)
    modified_cols = set(modified_df.columns)
    
    if original_cols == modified_cols:
        log_message("✅ 列结构一致")
    else:
        log_message("⚠️ 列结构存在差异")
        if original_cols - modified_cols:
            log_message(f"原始文件独有列: {original_cols - modified_cols}")
        if modified_cols - original_cols:
            log_message(f"修改文件独有列: {modified_cols - original_cols}")
    
    return analysis_result

def perform_detailed_comparison(original_df, modified_df):
    """执行详细对比"""
    log_message("=== 执行详细对比分析 ===")
    
    analyzer = DocumentChangeAnalyzer()
    
    # 开始对比
    start_time = time.time()
    log_message("开始执行表格对比...")
    
    try:
        comparison_result = analyzer.compare_dataframes(original_df, modified_df)
        end_time = time.time()
        
        log_message(f"✅ 对比完成，耗时: {end_time - start_time:.2f}秒")
        log_message(f"检测到 {len(comparison_result.get('changes', []))} 个变更")
        
        return comparison_result
        
    except Exception as e:
        log_message(f"❌ 对比执行失败: {str(e)}")
        return None

def analyze_changes_in_detail(changes):
    """详细分析变更"""
    log_message("=== 详细分析变更内容 ===")
    
    if not changes:
        log_message("未检测到任何变更")
        return {}
    
    # 按类型分组统计
    change_stats = {
        "total_changes": len(changes),
        "by_type": {},
        "by_column": {},
        "by_risk_level": {}
    }
    
    # 详细变更列表
    detailed_changes = []
    
    for i, change in enumerate(changes):
        log_message(f"变更 {i+1}: {change}")
        
        # 统计类型
        change_type = change.get('change_type', 'unknown')
        change_stats["by_type"][change_type] = change_stats["by_type"].get(change_type, 0) + 1
        
        # 统计列
        column = change.get('column', 'unknown')
        change_stats["by_column"][column] = change_stats["by_column"].get(column, 0) + 1
        
        # 统计风险等级
        risk_level = change.get('risk_level', 'unknown')
        change_stats["by_risk_level"][risk_level] = change_stats["by_risk_level"].get(risk_level, 0) + 1
        
        # 收集详细信息
        detailed_changes.append({
            "change_id": i + 1,
            "change_type": change_type,
            "column": column,
            "row_index": change.get('row_index', 'unknown'),
            "original_value": change.get('original_value', ''),
            "new_value": change.get('new_value', ''),
            "risk_level": risk_level,
            "confidence": change.get('confidence', 0.0)
        })
    
    # 输出统计结果
    log_message(f"总变更数: {change_stats['total_changes']}")
    log_message(f"按类型统计: {change_stats['by_type']}")
    log_message(f"按列统计: {change_stats['by_column']}")
    log_message(f"按风险等级统计: {change_stats['by_risk_level']}")
    
    return {
        "statistics": change_stats,
        "detailed_changes": detailed_changes
    }

def find_specific_test_changes(original_df, modified_df):
    """查找特定的测试变更"""
    log_message("=== 查找特定测试变更 ===")
    
    # 我们知道的测试变更
    test_changes = []
    
    # 检查负责人字段变更
    log_message("检查【负责人】字段变更...")
    for idx in range(min(len(original_df), len(modified_df))):
        if '负责人' in original_df.columns and '负责人' in modified_df.columns:
            orig_val = str(original_df.iloc[idx]['负责人']) if pd.notna(original_df.iloc[idx]['负责人']) else ''
            new_val = str(modified_df.iloc[idx]['负责人']) if pd.notna(modified_df.iloc[idx]['负责人']) else ''
            
            if orig_val != new_val:
                test_changes.append({
                    "row": idx,
                    "column": "负责人",
                    "original": orig_val,
                    "modified": new_val,
                    "change_type": "责任人变更"
                })
                log_message(f"  发现变更 行{idx}: '{orig_val}' → '{new_val}'")
    
    # 检查具体计划内容字段变更
    log_message("检查【具体计划内容】字段变更...")
    for idx in range(min(len(original_df), len(modified_df))):
        if '具体计划内容' in original_df.columns and '具体计划内容' in modified_df.columns:
            orig_val = str(original_df.iloc[idx]['具体计划内容']) if pd.notna(original_df.iloc[idx]['具体计划内容']) else ''
            new_val = str(modified_df.iloc[idx]['具体计划内容']) if pd.notna(modified_df.iloc[idx]['具体计划内容']) else ''
            
            if orig_val != new_val:
                test_changes.append({
                    "row": idx,
                    "column": "具体计划内容", 
                    "original": orig_val,
                    "modified": new_val,
                    "change_type": "计划内容更新"
                })
                log_message(f"  发现变更 行{idx}: '{orig_val}' → '{new_val}'")
    
    log_message(f"手动检查发现 {len(test_changes)} 个变更")
    return test_changes

def generate_comprehensive_report(original_df, modified_df, comparison_result, change_analysis, manual_changes):
    """生成综合报告"""
    log_message("=== 生成综合测试报告 ===")
    
    report = {
        "test_metadata": {
            "test_time": datetime.now().isoformat(),
            "test_purpose": "验证表格对比程序的修改识别准确性",
            "original_file": "refer/测试版本-小红书部门-工作表2.csv",
            "modified_file": "test_modified_obvious.csv"
        },
        "data_structure_analysis": {
            "original_shape": original_df.shape,
            "modified_shape": modified_df.shape,
            "columns_count": len(original_df.columns),
            "columns_list": list(original_df.columns)
        },
        "comparison_results": comparison_result or {},
        "change_analysis": change_analysis,
        "manual_verification": {
            "manual_found_changes": manual_changes,
            "manual_change_count": len(manual_changes)
        },
        "accuracy_assessment": {},
        "conclusions": []
    }
    
    # 准确性评估
    program_change_count = len(comparison_result.get('changes', [])) if comparison_result else 0
    manual_change_count = len(manual_changes)
    
    report["accuracy_assessment"] = {
        "program_detected": program_change_count,
        "manual_verified": manual_change_count,
        "detection_accuracy": "需要进一步分析" if program_change_count != manual_change_count else "检测数量匹配"
    }
    
    # 结论
    if program_change_count > 0:
        report["conclusions"].append(f"✅ 程序成功检测到 {program_change_count} 个变更")
    else:
        report["conclusions"].append("❌ 程序未检测到任何变更")
    
    if manual_change_count > 0:
        report["conclusions"].append(f"✅ 手动验证发现 {manual_change_count} 个真实变更")
    
    if program_change_count == manual_change_count and manual_change_count > 0:
        report["conclusions"].append("🎯 检测数量完全匹配，准确性良好")
    elif program_change_count > manual_change_count:
        report["conclusions"].append("⚠️ 程序检测数量超过预期，可能存在误报")
    elif program_change_count < manual_change_count:
        report["conclusions"].append("⚠️ 程序检测数量不足，可能存在漏报")
    
    return report

def main():
    """主函数"""
    log_file_lines = []
    
    print("=" * 80)
    print("腾讯文档智能监控系统 - 完整对比测试")
    print("=" * 80)
    
    # 1. 加载测试文件
    original_df, modified_df = load_test_files()
    if original_df is None or modified_df is None:
        print("❌ 测试文件加载失败，退出测试")
        return
    
    # 2. 分析数据结构
    structure_analysis = analyze_data_structure(original_df, modified_df)
    
    # 3. 执行程序对比
    comparison_result = perform_detailed_comparison(original_df, modified_df)
    
    # 4. 分析变更详情
    change_analysis = analyze_changes_in_detail(comparison_result.get('changes', []) if comparison_result else [])
    
    # 5. 手动验证特定变更
    manual_changes = find_specific_test_changes(original_df, modified_df)
    
    # 6. 生成综合报告
    comprehensive_report = generate_comprehensive_report(
        original_df, modified_df, comparison_result, change_analysis, manual_changes
    )
    
    # 7. 保存完整结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"complete_comparison_test_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2, default=str)
        
        log_message(f"✅ 完整测试报告已保存: {report_file}")
        
        # 显示关键结果
        print("\n" + "=" * 60)
        print("🎯 测试结果总结")
        print("=" * 60)
        for conclusion in comprehensive_report["conclusions"]:
            print(conclusion)
        
        print(f"\n📊 详细报告文件: {report_file}")
        print("📁 测试完成！")
        
    except Exception as e:
        log_message(f"❌ 报告保存失败: {str(e)}")

if __name__ == "__main__":
    main()