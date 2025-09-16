#!/usr/bin/env python3
"""
验证热力图数据的真实性和清晰度
"""

import requests
import json

def verify_data_authenticity():
    """验证数据真实性和模糊度"""
    
    # 获取热力图数据
    response = requests.get("http://localhost:8090/api/data")
    data = response.json()
    
    if not data.get('success'):
        print("❌ 获取数据失败")
        return
    
    heatmap = data['data']['heatmap_data']
    table_names = data['data']['table_names']
    column_names = data['data']['column_names']
    
    print("=" * 70)
    print("🔍 热力图数据真实性验证报告")
    print("=" * 70)
    
    # 1. 检查第一行（L1级别）的数据差异性
    print("\n📊 L1级别表格数据分析（前3行）:")
    print("-" * 50)
    
    for row_idx in range(min(3, len(heatmap))):
        row = heatmap[row_idx]
        table_name = table_names[row_idx]
        
        print(f"\n表格 {row_idx+1}: {table_name}")
        
        # 统计该行的唯一值数量
        unique_values = set(row)
        min_val = min(row)
        max_val = max(row)
        avg_val = sum(row) / len(row)
        
        # 显示前5个列的值
        print("  前5列值:")
        for col_idx in range(min(5, len(row))):
            print(f"    {column_names[col_idx][:12]:12}: {row[col_idx]:.3f}")
        
        print(f"  📈 统计:")
        print(f"    唯一值数量: {len(unique_values)}/{len(row)}")
        print(f"    值范围: [{min_val:.3f}, {max_val:.3f}]")
        print(f"    平均值: {avg_val:.3f}")
        
        # 判断是否过于均匀
        if len(unique_values) < 5:
            print("    ⚠️ 警告: 数据过于均匀，可能存在问题")
        else:
            print("    ✅ 数据差异性良好")
    
    # 2. 检查模糊程度
    print("\n🔬 模糊度分析:")
    print("-" * 50)
    
    # 计算相邻单元格的差异
    sharp_edges = 0
    smooth_edges = 0
    total_edges = 0
    
    for i in range(len(heatmap)):
        for j in range(len(heatmap[0]) - 1):
            diff = abs(heatmap[i][j] - heatmap[i][j+1])
            total_edges += 1
            
            if diff > 0.3:  # 较大的差异
                sharp_edges += 1
            elif diff < 0.05:  # 很小的差异
                smooth_edges += 1
    
    # 垂直方向
    for i in range(len(heatmap) - 1):
        for j in range(len(heatmap[0])):
            diff = abs(heatmap[i][j] - heatmap[i+1][j])
            total_edges += 1
            
            if diff > 0.3:
                sharp_edges += 1
            elif diff < 0.05:
                smooth_edges += 1
    
    sharp_ratio = (sharp_edges / total_edges) * 100
    smooth_ratio = (smooth_edges / total_edges) * 100
    
    print(f"  清晰边缘 (差异>0.3): {sharp_edges}/{total_edges} ({sharp_ratio:.1f}%)")
    print(f"  模糊边缘 (差异<0.05): {smooth_edges}/{total_edges} ({smooth_ratio:.1f}%)")
    
    if smooth_ratio > 70:
        print("  ⚠️ 警告: 图像过于模糊，细节丢失")
    elif sharp_ratio > 30:
        print("  ✅ 良好: 保留了足够的数据细节")
    else:
        print("  ✅ 平衡: 既有平滑过渡又保留了重要特征")
    
    # 3. 验证原始数据与渲染数据的对应关系
    print("\n🔗 原始数据对应关系验证:")
    print("-" * 50)
    
    # 读取原始测试数据
    with open('/tmp/test_scoring_data.json', 'r') as f:
        test_data = json.load(f)
    
    # 检查第一个有数据的表格
    for table_idx, table in enumerate(test_data['table_scores'][:3]):
        if table.get('column_scores'):
            print(f"\n表格: {table['table_name']}")
            
            # 获取一个有分数的列
            for col_name, col_data in list(table['column_scores'].items())[:1]:
                orig_score = col_data.get('aggregated_score', 0)
                print(f"  原始分数 ({col_name}): {orig_score:.3f}")
                
                # 尝试在渲染数据中找到对应值
                if col_name in column_names:
                    col_idx = column_names.index(col_name)
                    rendered_val = heatmap[table_idx][col_idx] if table_idx < len(heatmap) else 0
                    print(f"  渲染值: {rendered_val:.3f}")
                    
                    # 检查映射关系（考虑风险等级映射）
                    if rendered_val > 0.6:  # L1级别
                        expected_range = (0.70, 1.00)
                    elif rendered_val > 0.3:  # L2级别
                        expected_range = (0.40, 0.70)
                    else:  # L3级别
                        expected_range = (0.10, 0.40)
                    
                    print(f"  期望范围: {expected_range}")
                    
                    if expected_range[0] <= rendered_val <= expected_range[1]:
                        print("  ✅ 映射正确")
                    else:
                        print("  ⚠️ 映射可能有问题")
            break
    
    print("\n" + "=" * 70)
    print("📁 数据文件位置:")
    print(f"  测试数据: /tmp/test_scoring_data.json")
    print(f"  服务器代码: /root/projects/tencent-doc-manager/production/servers/test_heatmap_server_8090_clean.py")
    print("=" * 70)

if __name__ == "__main__":
    verify_data_authenticity()