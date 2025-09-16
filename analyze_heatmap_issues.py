#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析热力图生成算法中的问题
"""

import csv
import json
from pathlib import Path
import sys
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')
from real_data_loader import RealDataLoader

def deep_analyze_heatmap_issues():
    """深度分析热力图算法中的具体问题"""
    
    print("=== 热力图算法深度分析 ===\n")
    
    loader = RealDataLoader()
    real_files = loader.get_real_csv_files()
    
    # 选择有差异的文件进行分析
    test_file = None
    for file_info in real_files:
        prev_path = Path(file_info['previous_file'])
        curr_path = Path(file_info['current_file'])
        if prev_path.exists() and curr_path.exists():
            # 快速检查是否有差异
            result = loader.load_comparison_result(file_info['previous_file'], file_info['current_file'])
            if result['total_differences'] > 0:
                test_file = file_info
                test_file['comparison_result'] = result
                break
    
    if not test_file:
        print("❌ 未找到有差异的文件对")
        return
    
    print(f"测试文件: {test_file['name']}")
    print(f"总差异数: {test_file['comparison_result']['total_differences']}")
    
    # 模拟generate_heatmap_data方法的执行过程
    print("\n=== 模拟热力图生成过程 ===")
    
    import random
    random.seed(42)  # 固定随机种子以便复现
    
    real_files_with_data = [test_file]
    num_files = len(real_files_with_data)
    cols = 19
    
    print(f"1. 初始化参数:")
    print(f"   文件数: {num_files}")
    print(f"   列数: {cols}")
    
    # 初始化矩阵
    print(f"\n2. 初始化热力图矩阵:")
    heatmap_matrix = []
    for i in range(num_files):
        row = [0.05 + random.uniform(0, 0.03) for _ in range(cols)]
        heatmap_matrix.append(row)
    
    print(f"   初始矩阵第一行前10列: {[f'{v:.3f}' for v in heatmap_matrix[0][:10]]}")
    
    # 基于真实差异填充热力图
    print(f"\n3. 处理差异数据:")
    
    for i, file_info in enumerate(real_files_with_data):
        differences = file_info['comparison_result']['differences']
        print(f"   文件{i}: {len(differences)}个差异")
        
        # 统计每列的修改次数
        col_changes = {}
        for diff in differences:
            col_idx = min(diff['col'], cols - 1)  # 这是关键的映射逻辑
            print(f"     差异: 行{diff['row']}, 列{diff['col']} -> 映射到列{col_idx}")
            
            if col_idx not in col_changes:
                col_changes[col_idx] = 0
            col_changes[col_idx] += 1
        
        print(f"   列变更统计: {col_changes}")
        
        # 根据修改次数设置热力值
        print(f"   设置热力值:")
        for col_idx, count in col_changes.items():
            if count == 1:
                heat_value = 0.3
            elif count == 2:
                heat_value = 0.5
            elif count >= 3:
                heat_value = 0.7
            else:
                heat_value = 0.1
            
            print(f"     列{col_idx}: {count}次修改 -> 热力值{heat_value}")
            
            old_value = heatmap_matrix[i][col_idx]
            heatmap_matrix[i][col_idx] = heat_value
            
            print(f"       更新: {old_value:.3f} -> {heat_value}")
            
            # 邻近效应
            if col_idx > 0:
                old_left = heatmap_matrix[i][col_idx - 1]
                new_left = max(heatmap_matrix[i][col_idx - 1], heat_value * 0.3)
                heatmap_matrix[i][col_idx - 1] = new_left
                print(f"       左邻近({col_idx-1}): {old_left:.3f} -> {new_left:.3f}")
                
            if col_idx < cols - 1:
                old_right = heatmap_matrix[i][col_idx + 1]
                new_right = max(heatmap_matrix[i][col_idx + 1], heat_value * 0.3)
                heatmap_matrix[i][col_idx + 1] = new_right
                print(f"       右邻近({col_idx+1}): {old_right:.3f} -> {new_right:.3f}")
    
    print(f"\n4. 最终热力图矩阵:")
    for i, row in enumerate(heatmap_matrix):
        print(f"   文件{i}: {[f'{v:.3f}' for v in row[:10]]}")
    
    # 分析问题
    print(f"\n=== 问题分析 ===")
    
    issues = []
    
    # 问题1: 检查映射逻辑中的取模操作问题
    print("1. 检查代码中提到的取模操作问题:")
    code_line_269 = "col_idx = min(diff['col'], cols - 1)"
    print(f"   实际代码(第269行): {code_line_269}")
    print("   ❌ 用户提到的'col_idx = diff['col'] % cols'取模操作在当前代码中不存在")
    print("   ✅ 当前使用min()函数限制列索引，这是正确的做法")
    
    # 问题2: 检查% 19映射问题  
    print("\n2. 检查% 19映射问题:")
    print("   ❌ 用户提到的'% 19映射'在当前代码中不存在")
    print("   ✅ 当前代码使用cols=19作为列数限制，这是合理的")
    
    # 问题3: 热力值设置问题
    print("\n3. 热力值设置分析:")
    heat_values = []
    for row in heatmap_matrix:
        heat_values.extend(row)
    
    unique_heat_values = sorted(set(round(v, 3) for v in heat_values))
    print(f"   实际热力值分布: {unique_heat_values}")
    
    # 统计各热力值范围的数量
    ranges = {
        '基础值(0.05-0.08)': 0,
        '邻近效应(0.09-0.21)': 0, 
        '单次修改(0.3)': 0,
        '双次修改(0.5)': 0,
        '多次修改(0.7)': 0
    }
    
    for val in heat_values:
        if 0.05 <= val <= 0.08:
            ranges['基础值(0.05-0.08)'] += 1
        elif 0.09 <= val <= 0.21:
            ranges['邻近效应(0.09-0.21)'] += 1
        elif abs(val - 0.3) < 0.001:
            ranges['单次修改(0.3)'] += 1
        elif abs(val - 0.5) < 0.001:
            ranges['双次修改(0.5)'] += 1
        elif abs(val - 0.7) < 0.001:
            ranges['多次修改(0.7)'] += 1
    
    print("   热力值范围统计:")
    for range_name, count in ranges.items():
        print(f"     {range_name}: {count}个单元格")
    
    # 问题4: 0.15增量问题
    print("\n4. 检查0.15增量问题:")
    print("   ❌ 用户提到的'0.15的增量'在当前代码中不存在")
    print("   ✅ 当前代码使用固定的热力值(0.3, 0.5, 0.7)，这更加清晰")
    
    # 问题5: 列名映射问题
    print("\n5. 列名映射问题:")
    csv_column_names = [
        '序号', '项目类型', '来源', '任务发起时间', '目标对齐', 
        '关键KR对齐', '具体计划内容', '邓总指导', '负责人', 
        '协助人', '监督人', '重要程度', '预计完成时间', '完成进度',
        '形成计划清单', '复盘周期', '复盘时间', '对上汇报', '进度分析'
    ]
    
    actual_csv_columns = []
    with open(test_file['previous_file'], 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        actual_csv_columns = next(reader)
    
    print(f"   预设列名数量: {len(csv_column_names)}")
    print(f"   实际CSV列数: {len(actual_csv_columns)}")
    print(f"   实际CSV列名: {actual_csv_columns}")
    print("   ❌ 列名不匹配，使用了硬编码的列名而不是实际CSV的列名")
    
    # 真正的问题分析
    print(f"\n=== 真正的问题识别 ===")
    
    real_issues = []
    
    # 真正问题1: 列名不匹配
    if len(actual_csv_columns) != len(csv_column_names):
        real_issues.append("❌ 列名映射错误: 硬编码了19个列名，但实际CSV可能有不同数量的列")
    
    # 真正问题2: 热力图大小固定
    real_issues.append("❌ 热力图列数固定为19，不能动态适应实际CSV的列数")
    
    # 真正问题3: 基础热力值过低
    if ranges['单次修改(0.3)'] > 0:
        real_issues.append("✅ 热力值设置合理，0.3足够显示单次修改")
    else:
        real_issues.append("⚠️ 没有检测到明显的热力值变化")
    
    # 真正问题4: 初始化随机值可能掩盖真实热力
    base_range = max(heat_values) - min([v for v in heat_values if v < 0.1])
    if base_range > 0.05:
        real_issues.append("⚠️ 基础随机值范围过大，可能影响真实差异的显示")
    
    for issue in real_issues:
        print(issue)
    
    return heatmap_matrix, test_file

def propose_fixes():
    """提出修复建议"""
    print(f"\n=== 修复建议 ===")
    
    fixes = [
        {
            "问题": "列名映射错误",
            "建议": "动态读取CSV文件的第一行作为列名，而不是硬编码",
            "实现": "在generate_heatmap_data中读取实际CSV的header"
        },
        {
            "问题": "热力图列数固定",
            "建议": "根据实际CSV的列数动态设置热力图大小",
            "实现": "使用max(实际列数, 最小显示列数)来确定热力图大小"
        },
        {
            "问题": "基础随机值过大",
            "建议": "减小初始化随机值的范围，使真实差异更突出",
            "实现": "将random.uniform(0, 0.03)改为random.uniform(0, 0.01)"
        },
        {
            "问题": "列索引验证缺失",
            "建议": "在差异分析中添加更多的边界检查",
            "实现": "检查row和col索引是否在有效范围内"
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"{i}. {fix['问题']}:")
        print(f"   建议: {fix['建议']}")
        print(f"   实现: {fix['实现']}")
        print()

if __name__ == "__main__":
    deep_analyze_heatmap_issues()
    propose_fixes()