#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复综合打分热力图数据生成逻辑
只在实际修改位置显示值，其他位置为0
"""

def get_comprehensive_heatmap_data_fixed(comprehensive_scoring_data):
    """正确处理综合打分数据并生成稀疏热力图"""
    
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
        table_info.append({
            'index': idx,
            'name': table_name,
            'risk_score': risk_score,
            'table': table
        })
    
    # 2. 按风险分数排序（高风险优先）
    table_info.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # 3. 创建18×19的零矩阵
    num_tables = len(table_scores)
    heatmap_data = [[0.0] * 19 for _ in range(num_tables)]
    sorted_table_names = []
    
    # 4. 填充实际修改位置的值
    for new_idx, info in enumerate(table_info):
        sorted_table_names.append(info['name'])
        table = info['table']
        modifications = table.get('modifications', {})
        
        # 解析每个修改
        for mod_key, mod_data in modifications.items():
            # mod_key格式: "row_行号_列名"
            # 我们只需要列名来确定列索引
            column_name = mod_data.get('column', '')
            risk_score = mod_data.get('risk_score', 0)
            
            # 找到列索引
            if column_name in standard_columns:
                col_idx = standard_columns.index(column_name)
                # 在对应位置填充风险分数
                heatmap_data[new_idx][col_idx] = risk_score
    
    # 5. 统计信息
    total_modifications = sum(
        table.get('modification_count', 0) 
        for table in table_scores
    )
    non_zero_cells = sum(
        1 for row in heatmap_data 
        for val in row if val > 0
    )
    
    return {
        "heatmap_data": heatmap_data,
        "table_names": sorted_table_names,
        "column_names": standard_columns,
        "statistics": {
            "total_modifications": total_modifications,
            "non_zero_cells": non_zero_cells,
            "total_cells": num_tables * 19,
            "sparsity": f"{non_zero_cells/(num_tables*19)*100:.1f}%"
        }
    }

# 测试函数
if __name__ == "__main__":
    import json
    
    # 加载数据
    with open('/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W03_20250912_105533.json', 'r') as f:
        data = json.load(f)
    
    # 生成热力图
    result = get_comprehensive_heatmap_data_fixed(data)
    
    if result:
        print("✅ 修复后的热力图数据：")
        print(f"  矩阵大小: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
        print(f"  非零单元格: {result['statistics']['non_zero_cells']}/{result['statistics']['total_cells']}")
        print(f"  稀疏度: {result['statistics']['sparsity']}")
        print()
        print("前3个表格的修改分布：")
        for i in range(min(3, len(result['heatmap_data']))):
            row = result['heatmap_data'][i]
            non_zero = [(j, v) for j, v in enumerate(row) if v > 0]
            print(f"  {result['table_names'][i]}: {len(non_zero)}个修改")
            for col_idx, val in non_zero[:3]:
                print(f"    - {result['column_names'][col_idx]}: {val:.3f}")
    else:
        print("❌ 数据处理失败")