#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接使用综合打分原始值，不做任何加工
每个格子的值就是对应修改的risk_score
"""

def get_comprehensive_heatmap_direct(comprehensive_scoring_data):
    """
    直接生成热力图数据，不做任何加工
    有修改的位置显示risk_score，无修改的位置为0
    """
    
    # 标准列名（必须与综合打分文件中的列名完全一致）
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
    
    # 1. 按风险分数排序表格（高风险优先）
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
    
    table_info.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # 2. 创建18×19的零矩阵
    num_tables = len(table_scores)
    heatmap_data = [[0.0] * 19 for _ in range(num_tables)]
    sorted_table_names = []
    
    # 3. 直接填充修改位置的risk_score值
    for new_idx, info in enumerate(table_info):
        sorted_table_names.append(info['name'])
        table = info['table']
        modifications = table.get('modifications', {})
        
        # 解析每个修改，直接使用risk_score
        for mod_key, mod_data in modifications.items():
            column_name = mod_data.get('column', '')
            risk_score = mod_data.get('risk_score', 0)
            
            # 找到列索引
            if column_name in standard_columns:
                col_idx = standard_columns.index(column_name)
                # 直接赋值，不做任何加工
                heatmap_data[new_idx][col_idx] = risk_score
    
    # 4. 统计信息
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
    result = get_comprehensive_heatmap_direct(data)
    
    if result:
        print("=" * 60)
        print("✅ 直接使用原始值的热力图数据")
        print("=" * 60)
        print(f"矩阵大小: {len(result['heatmap_data'])}×{len(result['heatmap_data'][0])}")
        print(f"非零单元格: {result['statistics']['non_zero_cells']}/{result['statistics']['total_cells']}")
        print(f"稀疏度: {result['statistics']['sparsity']}")
        print()
        
        # 显示实际的数据分布
        all_values = []
        for row in result['heatmap_data']:
            for val in row:
                if val > 0:
                    all_values.append(val)
        
        if all_values:
            print(f"非零值统计:")
            print(f"  最小值: {min(all_values):.3f}")
            print(f"  最大值: {max(all_values):.3f}")
            print(f"  平均值: {sum(all_values)/len(all_values):.3f}")
            print(f"  L1(>0.7): {sum(1 for v in all_values if v > 0.7)}个")
            print(f"  L2(0.4-0.7): {sum(1 for v in all_values if 0.4 <= v <= 0.7)}个")
            print(f"  L3(<0.4): {sum(1 for v in all_values if v < 0.4)}个")
        
        print("\n前5个表格的修改详情:")
        for i in range(min(5, len(result['heatmap_data']))):
            row = result['heatmap_data'][i]
            non_zero = [(j, v) for j, v in enumerate(row) if v > 0]
            if non_zero:
                print(f"\n{result['table_names'][i]}: {len(non_zero)}个修改")
                for col_idx, val in non_zero[:3]:  # 显示前3个修改
                    print(f"  - {result['column_names'][col_idx]}: {val:.3f}")
            else:
                print(f"\n{result['table_names'][i]}: 无修改")
    else:
        print("❌ 数据处理失败")