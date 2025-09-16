#!/usr/bin/env python3
"""
验证热力图颜色映射效果
"""

import requests
import json

def analyze_heatmap():
    """分析热力图数据的颜色分布"""
    
    # 获取热力图数据
    response = requests.get("http://localhost:8090/api/data")
    data = response.json()
    
    if not data.get('success'):
        print("❌ 获取数据失败")
        return
    
    heatmap = data['data']['heatmap_data']
    
    print("=" * 60)
    print("🎨 热力图颜色分析")
    print("=" * 60)
    
    # 统计各值区间的单元格数量
    ranges = {
        "0.00-0.05": 0,  # 基础背景色
        "0.05-0.10": 0,  # 浅蓝
        "0.10-0.20": 0,  # 蓝
        "0.20-0.30": 0,  # 青
        "0.30-0.40": 0,  # 绿  
        "0.40-0.50": 0,  # 黄绿
        "0.50-0.60": 0,  # 黄
        "0.60-0.70": 0,  # 橙
        "0.70-0.80": 0,  # 红橙
        "0.80-0.90": 0,  # 红
        "0.90-1.00": 0   # 深红
    }
    
    total_cells = 0
    min_val = 1.0
    max_val = 0.0
    
    for row_idx, row in enumerate(heatmap):
        for col_idx, value in enumerate(row):
            total_cells += 1
            min_val = min(min_val, value)
            max_val = max(max_val, value)
            
            # 分类统计
            if value < 0.05:
                ranges["0.00-0.05"] += 1
            elif value < 0.10:
                ranges["0.05-0.10"] += 1
            elif value < 0.20:
                ranges["0.10-0.20"] += 1
            elif value < 0.30:
                ranges["0.20-0.30"] += 1
            elif value < 0.40:
                ranges["0.30-0.40"] += 1
            elif value < 0.50:
                ranges["0.40-0.50"] += 1
            elif value < 0.60:
                ranges["0.50-0.60"] += 1
            elif value < 0.70:
                ranges["0.60-0.70"] += 1
            elif value < 0.80:
                ranges["0.70-0.80"] += 1
            elif value < 0.90:
                ranges["0.80-0.90"] += 1
            else:
                ranges["0.90-1.00"] += 1
    
    print(f"📊 热力图尺寸: {len(heatmap)} × {len(heatmap[0]) if heatmap else 0}")
    print(f"📈 数值范围: [{min_val:.3f}, {max_val:.3f}]")
    print(f"🔢 总单元格数: {total_cells}")
    print()
    
    print("🌈 颜色分布统计:")
    for range_key, count in ranges.items():
        if count > 0:
            percentage = (count / total_cells) * 100
            bar = "█" * int(percentage / 2)  # 简单的条形图
            
            # 根据范围设置颜色说明
            color_desc = {
                "0.00-0.05": "⚪ 白色(无数据)",
                "0.05-0.10": "🔵 浅蓝(基础)",  
                "0.10-0.20": "🔷 蓝色",
                "0.20-0.30": "🟦 青色",
                "0.30-0.40": "🟢 绿色",
                "0.40-0.50": "🟡 黄绿",
                "0.50-0.60": "🟨 黄色",
                "0.60-0.70": "🟠 橙色",
                "0.70-0.80": "🔶 红橙",
                "0.80-0.90": "🔴 红色",
                "0.90-1.00": "🟥 深红"
            }
            
            color = color_desc.get(range_key, "")
            print(f"  {range_key}: {color:12} {count:4}个 ({percentage:5.1f}%) {bar}")
    
    print()
    
    # 检查渐变效果
    print("🔍 渐变效果检查:")
    
    # 检查是否所有值都大于等于0.05（基础热度）
    cells_with_base_heat = sum(1 for row in heatmap for val in row if val >= 0.05)
    print(f"  ✅ 有背景色的单元格: {cells_with_base_heat}/{total_cells} ({cells_with_base_heat/total_cells*100:.1f}%)")
    
    # 检查相邻单元格的值差异（渐变平滑度）
    smooth_transitions = 0
    sharp_transitions = 0
    
    for i in range(len(heatmap)):
        for j in range(len(heatmap[0]) - 1):
            diff = abs(heatmap[i][j] - heatmap[i][j+1])
            if diff < 0.2:
                smooth_transitions += 1
            else:
                sharp_transitions += 1
    
    total_transitions = smooth_transitions + sharp_transitions
    if total_transitions > 0:
        smoothness = (smooth_transitions / total_transitions) * 100
        print(f"  ✅ 平滑过渡: {smooth_transitions}/{total_transitions} ({smoothness:.1f}%)")
    
    print("=" * 60)
    
    # 结论
    if min_val >= 0.05 and smoothness > 70:
        print("✅ 热力图渲染效果良好:")
        print("   - 所有单元格都有背景色")
        print("   - 渐变过渡平滑自然")
        print("   - 颜色分布合理")
    else:
        print("⚠️ 热力图可能需要调整:")
        if min_val < 0.05:
            print("   - 部分单元格缺少背景色")
        if smoothness <= 70:
            print("   - 渐变过渡不够平滑")

if __name__ == "__main__":
    analyze_heatmap()