#!/usr/bin/env python3
"""
验证风险等级分配和聚类排序效果
"""

import requests
import json

def verify_risk_distribution():
    """验证风险等级分布和聚类排序"""
    
    # 获取热力图数据
    response = requests.get("http://localhost:8090/api/data")
    data = response.json()
    
    if not data.get('success'):
        print("❌ 获取数据失败")
        return
    
    heatmap = data['data']['heatmap_data']
    table_names = data['data']['table_names']
    column_names = data['data']['column_names']
    
    print("=" * 60)
    print("🎯 风险等级分配验证")
    print("=" * 60)
    
    # 分析行数据（表格）的风险等级
    print("\n📊 表格风险等级分析（按行）:")
    print("-" * 40)
    
    l1_tables = []
    l2_tables = []
    l3_tables = []
    
    for i, (row, name) in enumerate(zip(heatmap, table_names)):
        avg_temp = sum(row) / len(row)
        
        # 根据平均温度判断风险等级
        if avg_temp >= 0.65:
            risk_level = "L1"
            l1_tables.append((i, name, avg_temp))
        elif avg_temp >= 0.35:
            risk_level = "L2"
            l2_tables.append((i, name, avg_temp))
        else:
            risk_level = "L3"
            l3_tables.append((i, name, avg_temp))
        
        # 打印前10个表格的信息
        if i < 10:
            print(f"  {i+1:2}. {name[:20]:20} | 平均温度: {avg_temp:.3f} | 风险: {risk_level}")
    
    print(f"\n📈 风险等级统计:")
    print(f"  L1 (高风险): {len(l1_tables)} 个表格")
    print(f"  L2 (中风险): {len(l2_tables)} 个表格")
    print(f"  L3 (低风险): {len(l3_tables)} 个表格")
    
    # 验证聚类排序是否生效
    print("\n🔍 聚类排序验证:")
    
    # 检查行是否按风险等级聚类
    is_clustered = True
    if l1_tables:
        l1_positions = [t[0] for t in l1_tables]
        if max(l1_positions) - min(l1_positions) + 1 != len(l1_positions):
            is_clustered = False
            print(f"  ❌ L1表格位置不连续: {l1_positions}")
        else:
            print(f"  ✅ L1表格聚集在位置 {min(l1_positions)}-{max(l1_positions)}")
    
    if l2_tables:
        l2_positions = [t[0] for t in l2_tables]
        if max(l2_positions) - min(l2_positions) + 1 != len(l2_positions):
            is_clustered = False
            print(f"  ❌ L2表格位置不连续: {l2_positions}")
        else:
            print(f"  ✅ L2表格聚集在位置 {min(l2_positions)}-{max(l2_positions)}")
    
    if l3_tables:
        l3_positions = [t[0] for t in l3_tables]
        if max(l3_positions) - min(l3_positions) + 1 != len(l3_positions):
            is_clustered = False
            print(f"  ❌ L3表格位置不连续: {l3_positions}")
        else:
            print(f"  ✅ L3表格聚集在位置 {min(l3_positions)}-{max(l3_positions)}")
    
    # 分析列的聚类排序
    print("\n📊 列聚类排序分析（前5个高温列）:")
    print("-" * 40)
    
    col_temps = []
    for j in range(len(column_names)):
        col_sum = sum(heatmap[i][j] for i in range(len(heatmap)))
        col_avg = col_sum / len(heatmap)
        col_temps.append((j, column_names[j], col_avg))
    
    # 显示前5个列
    for j, (idx, name, temp) in enumerate(col_temps[:5]):
        print(f"  列{j+1}: {name[:15]:15} | 平均温度: {temp:.3f}")
    
    # 验证列是否按温度降序排列
    temps_only = [t[2] for t in col_temps]
    is_col_sorted = all(temps_only[i] >= temps_only[i+1] for i in range(len(temps_only)-1))
    
    if is_col_sorted:
        print(f"\n  ✅ 列已按温度降序排列")
    else:
        print(f"\n  ❌ 列未正确排序")
    
    print("\n" + "=" * 60)
    
    # 总体验证结果
    if is_clustered and is_col_sorted and len(l1_tables) >= 2 and len(l2_tables) >= 5:
        print("✅ 风险等级分配和聚类排序成功！")
        print("   - L1/L2/L3按预期分配")
        print("   - 行按风险等级聚类")
        print("   - 列按温度排序")
        print("   - 热力图显示正确的温度梯度")
    else:
        print("⚠️ 部分功能需要调整:")
        if not is_clustered:
            print("   - 行聚类需要改进")
        if not is_col_sorted:
            print("   - 列排序需要修复")
        if len(l1_tables) < 2:
            print(f"   - L1表格数量不足（当前{len(l1_tables)}个）")

if __name__ == "__main__":
    verify_risk_distribution()