#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试综合打分数据的渲染问题
分析从JSON到热力图的完整数据流
"""

import json
import requests

def analyze_data_flow():
    """分析数据流程的每个步骤"""
    
    print("=" * 80)
    print("🔍 综合打分数据流分析")
    print("=" * 80)
    
    # 1. 分析原始JSON文件
    print("\n📄 步骤1: 原始JSON文件")
    with open('/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W03_20250912_105533.json', 'r') as f:
        json_data = json.load(f)
    
    total_modifications = 0
    for table in json_data['table_scores']:
        total_modifications += len(table.get('modifications', {}))
    
    print(f"  总表格数: {len(json_data['table_scores'])}")
    print(f"  总修改数: {total_modifications}")
    print(f"  数据结构: table_scores → modifications → risk_score")
    
    # 2. 加载数据到服务器
    print("\n📤 步骤2: 加载数据到服务器")
    try:
        response = requests.post(
            'http://localhost:8089/api/load_comprehensive_scoring',
            json={'file_path': '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W03_20250912_105533.json'}
        )
        result = response.json()
        print(f"  加载状态: {result.get('message', '失败')}")
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return
    
    # 3. 获取处理后的数据
    print("\n📥 步骤3: 获取处理后的热力图数据")
    try:
        response = requests.get('http://localhost:8089/api/data')
        api_data = response.json()
        
        if api_data['success']:
            heatmap = api_data['data']['heatmap_data']
            
            # 分析热力图矩阵
            print(f"  矩阵大小: {len(heatmap)}×{len(heatmap[0])}")
            
            # 统计非零值
            non_zero_count = 0
            all_values = []
            for row in heatmap:
                for val in row:
                    if val > 0:
                        non_zero_count += 1
                        all_values.append(val)
            
            print(f"  非零单元格: {non_zero_count}/{18*19} ({non_zero_count/(18*19)*100:.1f}%)")
            
            if all_values:
                print(f"  值范围: [{min(all_values):.3f}, {max(all_values):.3f}]")
                
                # 检查是否有不应该存在的值
                if non_zero_count > total_modifications:
                    print(f"  ⚠️ 问题: 非零值({non_zero_count}) > 实际修改({total_modifications})")
                    print(f"     后端填充了额外的值！")
            
            # 显示具体的数据样本
            print("\n  前3行数据详情:")
            for i in range(min(3, len(heatmap))):
                row = heatmap[i]
                non_zero_in_row = sum(1 for v in row if v > 0)
                if non_zero_in_row > 0:
                    # 找出非零值的位置
                    non_zero_positions = [(j, v) for j, v in enumerate(row) if v > 0]
                    print(f"    行{i+1}: {non_zero_in_row}个非零值")
                    for pos, val in non_zero_positions[:3]:
                        print(f"      列{pos+1}: {val:.3f}")
                else:
                    print(f"    行{i+1}: 全零")
        else:
            print(f"  ❌ API返回失败")
    
    except Exception as e:
        print(f"  ❌ 获取数据失败: {e}")
        return
    
    # 4. 分析前端渲染
    print("\n🎨 步骤4: 前端IDW渲染分析")
    print("  IDW参数:")
    print("    - 功率参数 p = 2.0")
    print("    - 影响半径 = 3个单元格")
    print("    - 热源阈值 = value > 0.05")
    print("  渲染流程:")
    print("    1. 提取热源点（value > 0.05）")
    print("    2. 对每个像素计算IDW插值")
    print("    3. 应用热成像色彩映射")
    
    # 5. 诊断结果
    print("\n🏥 诊断结果:")
    if non_zero_count == total_modifications:
        print("  ✅ 数据传递正确，非零值数量匹配")
    elif non_zero_count < total_modifications:
        print("  ⚠️ 数据丢失，可能是同列多修改合并导致")
    else:
        print("  ❌ 数据异常，后端添加了不应该存在的值")
    
    print("\n💡 建议:")
    print("  1. 确保后端只传递真实的修改值（稀疏矩阵）")
    print("  2. 不要添加背景值或填充值")
    print("  3. 让IDW算法自然地插值产生渐变效果")

if __name__ == "__main__":
    analyze_data_flow()