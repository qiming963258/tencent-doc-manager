#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复综合打分热力图数据生成逻辑 V2
保留背景值，在修改位置叠加热点
"""

import random

def get_comprehensive_heatmap_data_v2(comprehensive_scoring_data):
    """
    生成热力图数据：
    1. 根据表格风险等级设置背景温度
    2. 在实际修改位置叠加热点值
    3. 形成热点聚集效果
    """
    
    # 标准列名
    standard_columns = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", 
        "完成进度", "形成计划清单", "复盘时间", "对上汇报",
        "应用情况", "进度分析总结"
    ]
    
    table_scores = comprehensive_scoring_data.get('table_scores', [])
    
    if not table_scores:
        return None
    
    # 1. 收集表格信息和排序
    table_info = []
    for idx, table in enumerate(table_scores):
        risk_score = table.get('overall_risk_score', 0)
        table_name = table.get('table_name', f'表格_{idx+1}')
        mod_count = table.get('modification_count', 0)
        
        # 根据综合风险分数分配风险等级
        if risk_score > 0.6:
            risk_level = 'L1'
        elif risk_score > 0.4:
            risk_level = 'L2'
        elif risk_score > 0:
            risk_level = 'L3'
        else:
            risk_level = 'L3'  # 无修改的表格默认低风险
        
        table_info.append({
            'index': idx,
            'name': table_name,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'mod_count': mod_count,
            'table': table
        })
    
    # 2. 按风险分数排序（高风险优先）
    table_info.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # 3. 创建基础热力图矩阵
    num_tables = len(table_scores)
    heatmap_data = []
    sorted_table_names = []
    
    # 4. 为每个表格生成一行数据
    for new_idx, info in enumerate(table_info):
        sorted_table_names.append(info['name'])
        table = info['table']
        modifications = table.get('modifications', {})
        risk_level = info['risk_level']
        
        # 初始化该行的背景值
        row = []
        for col_idx in range(19):
            # 设置基础背景温度（根据风险等级）
            if risk_level == 'L1':
                # L1: 较高背景温度 0.15-0.25
                base_value = 0.15 + random.uniform(0, 0.10)
            elif risk_level == 'L2':
                # L2: 中等背景温度 0.08-0.15
                base_value = 0.08 + random.uniform(0, 0.07)
            else:  # L3
                # L3: 较低背景温度 0.02-0.08
                base_value = 0.02 + random.uniform(0, 0.06)
            
            row.append(base_value)
        
        # 5. 在修改位置叠加热点值
        for mod_key, mod_data in modifications.items():
            column_name = mod_data.get('column', '')
            risk_score = mod_data.get('risk_score', 0)
            risk_level_mod = mod_data.get('risk_level', 'L3')
            
            # 找到列索引
            if column_name in standard_columns:
                col_idx = standard_columns.index(column_name)
                
                # 叠加热点值（在背景值基础上增加）
                # 使用修改的风险分数作为增量
                heat_increment = risk_score * 0.8  # 缩放到合适范围
                row[col_idx] = min(1.0, row[col_idx] + heat_increment)
                
                # 为相邻单元格添加少量热量（热扩散效果）
                if col_idx > 0:
                    row[col_idx - 1] = min(1.0, row[col_idx - 1] + heat_increment * 0.3)
                if col_idx < 18:
                    row[col_idx + 1] = min(1.0, row[col_idx + 1] + heat_increment * 0.3)
        
        heatmap_data.append(row)
    
    # 6. 应用简单的平滑（垂直方向的热扩散）
    smoothed_data = simple_smooth_vertical(heatmap_data)
    
    # 7. 统计信息
    total_modifications = sum(
        table.get('modification_count', 0) 
        for table in table_scores
    )
    
    # 计算热点单元格（值显著高于背景的）
    hot_cells = 0
    for row in smoothed_data:
        for val in row:
            if val > 0.35:  # 热点阈值
                hot_cells += 1
    
    return {
        "heatmap_data": smoothed_data,
        "table_names": sorted_table_names,
        "column_names": standard_columns,
        "statistics": {
            "total_modifications": total_modifications,
            "hot_cells": hot_cells,
            "total_cells": num_tables * 19,
            "heat_ratio": f"{hot_cells/(num_tables*19)*100:.1f}%"
        }
    }

def simple_smooth_vertical(matrix):
    """简单的垂直方向平滑，增强热点聚集效果"""
    if not matrix or len(matrix) < 2:
        return matrix
    
    rows = len(matrix)
    cols = len(matrix[0])
    smoothed = [[0] * cols for _ in range(rows)]
    
    for i in range(rows):
        for j in range(cols):
            # 计算3×3邻域的加权平均
            total = 0
            weight = 0
            
            # 中心点权重最高
            total += matrix[i][j] * 4
            weight += 4
            
            # 上下邻居
            if i > 0:
                total += matrix[i-1][j] * 2
                weight += 2
            if i < rows - 1:
                total += matrix[i+1][j] * 2
                weight += 2
            
            # 左右邻居（权重较低）
            if j > 0:
                total += matrix[i][j-1]
                weight += 1
            if j < cols - 1:
                total += matrix[i][j+1]
                weight += 1
            
            smoothed[i][j] = total / weight
    
    return smoothed

# 测试函数
if __name__ == "__main__":
    import json
    
    # 加载数据
    with open('/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W03_20250912_105533.json', 'r') as f:
        data = json.load(f)
    
    # 生成热力图
    result = get_comprehensive_heatmap_data_v2(data)
    
    if result:
        print("✅ 修复后的热力图数据 V2：")
        print(f"  矩阵大小: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
        print(f"  热点单元格: {result['statistics']['hot_cells']}/{result['statistics']['total_cells']}")
        print(f"  热点比例: {result['statistics']['heat_ratio']}")
        print()
        
        print("数据分布检查：")
        for i in range(min(3, len(result['heatmap_data']))):
            row = result['heatmap_data'][i]
            min_val = min(row)
            max_val = max(row)
            avg_val = sum(row) / len(row)
            hot_spots = sum(1 for v in row if v > 0.35)
            
            print(f"  {result['table_names'][i]}:")
            print(f"    值范围: [{min_val:.3f}, {max_val:.3f}]")
            print(f"    平均值: {avg_val:.3f}")
            print(f"    热点数: {hot_spots}/19")
            
            # 显示前5个值作为示例
            print(f"    前5列: {[f'{v:.2f}' for v in row[:5]]}")
    else:
        print("❌ 数据处理失败")