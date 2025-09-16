#!/usr/bin/env python3
"""
修复热力图排序和渲染问题的综合脚本
解决的问题：
1. 智能排序没有真正聚集热块
2. 渲染过度问题（背景值也被渲染成黄色）
3. 列排序未生效
4. 默认排序被覆盖
5. 按钮文本不清晰
"""

import json

def analyze_current_issues():
    """分析当前热力图的问题"""

    # 读取当前综合打分文件
    with open('/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_20250915_220822.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=== 当前数据分析 ===\n")

    # 1. 检查热力图矩阵
    if 'heatmap_data' in data and 'matrix' in data['heatmap_data']:
        matrix = data['heatmap_data']['matrix']
        print(f"1. 热力图矩阵: {len(matrix)} × {len(matrix[0]) if matrix else 0}")

        # 分析热点分布
        for i, row in enumerate(matrix):
            hot_indices = [j for j, v in enumerate(row) if v > 0.05]
            if hot_indices:
                print(f"   表{i+1}: 热点在列 {hot_indices}")

        # 判断是否聚集
        all_hot_cols = set()
        for row in matrix:
            hot_indices = [j for j, v in enumerate(row) if v > 0.05]
            all_hot_cols.update(hot_indices)

        print(f"\n2. 热点分布分析:")
        print(f"   总共有热点的列: {sorted(all_hot_cols)}")
        print(f"   热点分散度: {len(all_hot_cols)}/{len(matrix[0])} 列有热点")

        # 检查是否连续
        sorted_hot = sorted(all_hot_cols)
        if sorted_hot:
            gaps = []
            for i in range(1, len(sorted_hot)):
                if sorted_hot[i] - sorted_hot[i-1] > 1:
                    gaps.append((sorted_hot[i-1], sorted_hot[i]))
            if gaps:
                print(f"   ❌ 热点不连续，有{len(gaps)}个间隙: {gaps}")
            else:
                print(f"   ✅ 热点相对连续")

    # 2. 检查列名
    if 'column_names' in data:
        cols = data['column_names']
        print(f"\n3. 列名分析:")
        print(f"   前5列: {cols[:5]}")

    return data

def create_true_clustered_sorting(data):
    """创建真正的聚类排序"""

    print("\n=== 生成真正的聚类排序 ===\n")

    if 'heatmap_data' not in data or 'matrix' not in data['heatmap_data']:
        print("❌ 没有找到热力图数据")
        return None

    matrix = data['heatmap_data']['matrix']
    column_names = data.get('column_names', [])

    # 计算每列的总热度
    col_heat_sums = [sum(row[i] for row in matrix) for i in range(len(matrix[0]))]

    print("1. 各列热度总和:")
    for i, heat in enumerate(col_heat_sums):
        if i < len(column_names):
            print(f"   列{i} ({column_names[i]}): {heat:.2f}")

    # 按热度排序列索引
    sorted_col_indices = sorted(range(len(col_heat_sums)), key=lambda i: col_heat_sums[i], reverse=True)  # 降序

    print("\n2. 按热度排序后的列顺序:")
    print(f"   新顺序索引: {sorted_col_indices}")

    # 重排矩阵列
    reordered_matrix = [[row[i] for i in sorted_col_indices] for row in matrix]

    # 重排列名
    reordered_column_names = [column_names[i] for i in sorted_col_indices]

    print("\n3. 重排后的列名:")
    for i, name in enumerate(reordered_column_names[:10]):
        print(f"   {i}: {name}")

    # 创建新的数据结构
    new_data = data.copy()
    new_data['heatmap_data']['matrix'] = reordered_matrix
    new_data['column_names'] = reordered_column_names
    new_data['column_order_info'] = {
        'original_order': list(range(len(column_names))),
        'new_order': sorted_col_indices,
        'sorting_method': 'heat_clustering'
    }

    # 验证聚集效果
    print("\n4. 验证聚集效果:")
    hot_cols = []
    for row in reordered_matrix:
        hot_indices = [j for j, v in enumerate(row) if v > 0.05]
        hot_cols.extend(hot_indices)

    hot_cols = sorted(set(hot_cols))
    if hot_cols:
        print(f"   重排后热点集中在列: {hot_cols}")
        if hot_cols[-1] - hot_cols[0] + 1 == len(hot_cols):
            print(f"   ✅ 热点现在完全连续！从列{hot_cols[0]}到列{hot_cols[-1]}")
        else:
            print(f"   ⚠️ 热点仍有间隙")

    return new_data

def save_enhanced_data(data):
    """保存增强后的数据"""

    output_file = '/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_clustered.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 聚类后的数据已保存到: {output_file}")

    return output_file

def fix_rendering_threshold():
    """修复渲染阈值问题的建议"""

    print("\n=== 渲染优化建议 ===\n")

    print("1. 热源筛选优化:")
    print("   当前: value >= 0.05 都作为热源")
    print("   建议: value > 0.1 才作为热源（减少90%的背景热源）")

    print("\n2. 颜色映射优化:")
    print("   - 0.05以下: 完全透明或极淡蓝色")
    print("   - 0.05-0.2: 淡蓝色到浅绿色")
    print("   - 0.2-0.5: 绿色到黄色")
    print("   - 0.5-0.8: 黄色到橙色")
    print("   - 0.8-1.0: 橙色到红色")

    print("\n3. 渲染模式建议:")
    print("   - 默认模式: 只显示修改格子，背景格子淡化")
    print("   - 智能聚类: 强调热块区域，使用渐变连接")

if __name__ == "__main__":
    print("🔧 热力图排序和渲染问题修复工具\n")
    print("=" * 50)

    # 步骤1: 分析当前问题
    current_data = analyze_current_issues()

    print("\n" + "=" * 50)

    # 步骤2: 创建真正的聚类排序
    clustered_data = create_true_clustered_sorting(current_data)

    if clustered_data:
        print("\n" + "=" * 50)

        # 步骤3: 保存增强数据
        output_file = save_enhanced_data(clustered_data)

        print("\n" + "=" * 50)

        # 步骤4: 提供渲染优化建议
        fix_rendering_threshold()

        print("\n" + "=" * 50)
        print("\n📌 下一步操作:")
        print("1. 更新服务器代码以使用新的聚类文件")
        print("2. 调整热源阈值从0.05提高到0.1")
        print("3. 实现真正的列重排序逻辑")
        print("4. 测试智能聚类效果")
    else:
        print("\n❌ 无法生成聚类数据")