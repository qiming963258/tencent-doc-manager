#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV对比测试脚本 - 测试实际的CSV文件比对功能
"""

import os
import sys
import csv
import json

# 添加生产模块路径
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

def load_csv_as_table_data(file_path):
    """加载CSV文件为表格数据格式，处理多行标题结构"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:  # 处理BOM
        reader = csv.reader(f)
        data = list(reader)
    
    if not data:
        raise ValueError(f"文件为空: {file_path}")
    
    # 检测并处理多行标题结构
    if len(data) >= 3:
        # 检查第1行是否为标题行（大部分列为空）
        first_row = data[0]
        if first_row[0] and not any(first_row[1:10]):  # 第一列有内容，后面大部分为空
            print(f"🏷️ 检测到标题行: {first_row[0]}")
            # 合并第2、3行作为列名，从第4行开始作为数据
            if len(data) >= 4:
                header1 = data[1]  # 主要列名
                header2 = data[2]  # 补充列名
                
                # 合并列名：优先使用非空的列名
                merged_header = []
                max_cols = max(len(header1), len(header2))
                for i in range(max_cols):
                    col1 = header1[i] if i < len(header1) else ""
                    col2 = header2[i] if i < len(header2) else ""
                    # 优先使用非空且有意义的列名
                    final_col = col1 if col1.strip() else col2
                    merged_header.append(final_col)
                
                # 构建新的数据结构：[合并后的标题] + [数据行]
                processed_data = [merged_header] + data[3:]
                print(f"📋 处理后结构: {len(processed_data)}行 x {len(merged_header)}列")
                print(f"📋 主要列名: {merged_header[:10]}...")  # 显示前10个列名
                return processed_data
    
    return data

def main():
    """主测试函数"""
    print("🔍 开始CSV文件比对测试...")
    
    # 文件路径
    baseline_file = "/root/projects/tencent-doc-manager/csv_versions/2025_W34/baseline/tencent_csv_20250818_1200_baseline_W34.csv"
    current_file = "/root/projects/tencent-doc-manager/csv_versions/current_小红书部门工作表2_20250818_1400_v001.csv"
    
    try:
        # 1. 检查文件存在性
        print(f"📁 基准文件: {baseline_file}")
        print(f"📁 当前文件: {current_file}")
        
        if not os.path.exists(baseline_file):
            print(f"❌ 基准文件不存在: {baseline_file}")
            return
        
        if not os.path.exists(current_file):
            print(f"❌ 当前文件不存在: {current_file}")
            return
        
        # 2. 加载文件数据
        print("\n📋 加载CSV文件数据...")
        baseline_data = load_csv_as_table_data(baseline_file)
        current_data = load_csv_as_table_data(current_file)
        
        print(f"✅ 基准文件加载成功: {len(baseline_data)}行 x {len(baseline_data[0]) if baseline_data else 0}列")
        print(f"✅ 当前文件加载成功: {len(current_data)}行 x {len(current_data[0]) if current_data else 0}列")
        
        # 3. 导入并初始化对比器
        print("\n🔧 初始化自适应表格对比器...")
        from adaptive_table_comparator import AdaptiveTableComparator
        
        comparator = AdaptiveTableComparator()
        print("✅ 对比器初始化成功")
        
        # 4. 准备表格数据
        current_tables = [
            {
                "name": "当前版本-小红书部门工作表2",
                "data": current_data
            }
        ]
        
        reference_tables = [
            {
                "name": "基准版本-小红书部门工作表2", 
                "data": baseline_data
            }
        ]
        
        # 5. 执行对比分析
        print("\n🚀 开始执行自适应表格对比...")
        result = comparator.adaptive_compare_tables(
            current_tables=current_tables,
            reference_tables=reference_tables
        )
        
        # 6. 输出结果
        print("\n📊 对比分析完成!")
        print("=" * 60)
        
        # 处理报告
        print("📋 处理报告:")
        print(result['processing_report'])
        
        # 质量汇总
        print("\n📈 质量汇总:")
        quality_summary = result['quality_summary']
        print(f"• 平均质量分数: {quality_summary['average_quality_score']:.3f}")
        print(f"• 处理成功率: {quality_summary['processing_success_rate']:.1%}")
        print(f"• 检测到的变更数: {quality_summary['total_changes_detected']}")
        
        # 风险分布
        risk_dist = quality_summary['risk_distribution']
        print(f"• 风险分布: L1={risk_dist['L1']}, L2={risk_dist['L2']}, L3={risk_dist['L3']}")
        
        # 标准化矩阵
        matrix = result['standardized_matrix']
        print(f"\n🔥 标准化矩阵: {len(matrix)}行 x {len(matrix[0]) if matrix else 0}列")
        
        # 详细结果（第一个表格）
        if result['comparison_results']:
            first_result = result['comparison_results'][0]
            if 'matching_result' in first_result:
                print("\n🎯 列匹配详情:")
                matching = first_result['matching_result']
                print(f"• 匹配成功: {len(matching['mapping'])}列")
                print(f"• 未匹配列: {len(matching['unmatched_columns'])}列")
                print(f"• 缺失标准列: {len(matching['missing_columns'])}列")
                
                if matching['unmatched_columns']:
                    print(f"• 未匹配列列表: {matching['unmatched_columns']}")
                
            if 'change_detection_result' in first_result and first_result['change_detection_result']:
                change_result = first_result['change_detection_result']
                changes = change_result.get('changes', [])
                print(f"\n🔍 变更检测:")
                print(f"• 总变更数: {len(changes)}")
                
                # 显示前5个变更示例
                for i, change in enumerate(changes[:5]):
                    print(f"  {i+1}. 行{change['row_index']} {change['column_name']}: '{change['original_value']}' → '{change['new_value']}' (风险:{change['risk_level']})")
                
                if len(changes) > 5:
                    print(f"  ... 还有 {len(changes) - 5} 个变更")
        
        print("\n✅ CSV对比测试完成!")
        
        # 保存结果到文件
        output_file = "/root/projects/tencent-doc-manager/csv_versions/comparison_cache/test_comparison_result.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 完整结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()